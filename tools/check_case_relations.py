#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_case_relations.py — 案例库关联关系一致性检查/修复/关系图生成

能力：
  --check       检查：引用缺失、单向关系、同一对案例关系类型冲突（默认）
  --fix         修复：补全反向关系、统一冲突类型（少数人工指定），并写回 frontmatter
  --write-graph 重新生成 案例关联关系图.md 的 Mermaid 图与"全部案例关联一览（自动生成）"表

命名约定：案例 frontmatter 的 `name:` 即 slug；示范文件不在案例库内，作为外部目标列入 DEMO_SLUGS。
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "historical-review" / "行业案例档案库"
GRAPH_FILE = CASE_DIR / "案例关联关系图.md"

DEMO_SLUGS = {
    "solar-coal-benchmark-demo",
    "semiconductor-benchmark-demo",
    "sportswear-benchmark-demo",
}
TYPE_ORDER = ["depends-on", "composes-with", "contrasts-with"]
# 人工裁决的冲突对（以 frontmatter 备注语义为准）
CANONICAL = {
    frozenset({"construction-machinery-case", "auto-case"}): "composes-with",
    frozenset({"education-case", "pharma-case"}): "composes-with",
    frozenset({"papermaking-case", "copper-cycle-case"}): "composes-with",
}
FOLDER_ORDER = {"周期制造型": 0, "技术迭代型": 1, "品牌消费型": 2}


def parse_case(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    info = {"path": path, "text": text, "lines": lines, "name": None,
            "entries": [], "block": None}
    if not lines or lines[0].strip() != "---":
        return info
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return info
    fm = lines[1:end]
    rel_i = None
    for i, ln in enumerate(fm):
        m = re.match(r"^name:\s*(\S+)", ln)
        if m:
            info["name"] = m.group(1).strip()
        if ln.strip() == "related_cases:":
            rel_i = i
    if rel_i is None:
        return info
    entries = []
    cur = None
    j = rel_i + 1
    while j < len(fm):
        ln = fm[j]
        m_slug = re.match(r"^\s{2}-\s+slug:\s*(\S+)", ln)
        if m_slug:
            if cur:
                entries.append(cur)
            cur = {"slug": m_slug.group(1).strip(), "relation": "composes-with", "note": ""}
            j += 1
            continue
        m_rel = re.match(r"^\s{4}relation:\s*(\S+)", ln)
        if m_rel and cur:
            cur["relation"] = m_rel.group(1).strip()
            j += 1
            continue
        m_note = re.match(r"^\s{4}note:\s*(.*)$", ln)
        if m_note and cur:
            cur["note"] = m_note.group(1).strip()
            j += 1
            continue
        if ln.startswith(" ") or ln == "":
            j += 1
            continue
        break
    if cur:
        entries.append(cur)
    info["entries"] = entries
    info["block"] = (rel_i, j)  # frontmatter 内行号区间（含 related_cases: 行）
    info["fm_start"] = 1
    return info


def load_cases() -> list[dict]:
    files = sorted(CASE_DIR.rglob("*_完整案例.md"))
    return [parse_case(p) for p in files]


def slug_map(cases: list[dict]) -> dict:
    return {c["name"]: c for c in cases if c["name"]}


def find_entry(case: dict, target: str):
    for e in case["entries"]:
        if e["slug"] == target:
            return e
    return None


def desired_entries(cases: list[dict]) -> dict:
    """按 pair 聚合 → 决定每对案例的唯一关系类型与备注，然后为每个案例生成期望条目。"""
    sm = slug_map(cases)
    pairs: dict[frozenset, list[dict]] = {}
    for c in cases:
        for e in c["entries"]:
            key = frozenset({c["name"], e["slug"]})
            pairs.setdefault(key, []).append({"src": c["name"], "dst": e["slug"],
                                              "type": e["relation"], "note": e["note"]})
    pair_decision = {}
    for key, es in pairs.items():
        if key in CANONICAL:
            ptype = CANONICAL[key]
        else:
            types = {e["type"] for e in es}
            ptype = list(types)[0] if len(types) == 1 else max(set(types), key=[e["type"] for e in es].count)
        note = next((e["note"] for e in es if e["note"]), "")
        pair_decision[key] = {"type": ptype, "note": note}

    desired = {}
    for c in cases:
        name = c["name"]
        out = []
        seen = set()
        for e in c["entries"]:
            key = frozenset({name, e["slug"]})
            dec = pair_decision.get(key)
            ptype = dec["type"] if dec else e["relation"]
            note = e["note"] or (dec["note"] if dec else "")
            out.append({"slug": e["slug"], "relation": ptype, "note": note})
            if e["slug"] in sm:
                seen.add(e["slug"])
        for key, dec in pair_decision.items():
            if name not in key:
                continue
            other = next(iter(key - {name}), None)
            if not other or other in DEMO_SLUGS or other not in sm or other in seen:
                continue
            out.append({"slug": other, "relation": dec["type"],
                        "note": dec["note"] or "反向引用"})
            seen.add(other)
        desired[name] = out
    return desired


def check(cases: list[dict]) -> list[str]:
    sm = slug_map(cases)
    issues = []
    for c in cases:
        if not c["name"]:
            issues.append(f"{c['path'].name}: 缺少 frontmatter name(slug)")
            continue
        for e in c["entries"]:
            t = sm.get(e["slug"])
            if t is None and e["slug"] not in DEMO_SLUGS:
                issues.append(f"{c['name']}: 引用不存在的 slug {e['slug']}")
                continue
            if t is None:
                continue
            rev = find_entry(t, c["name"])
            if rev is None:
                issues.append(f"单向：{c['name']} -> {e['slug']}（{e['relation']}）")
            elif rev["relation"] != e["relation"]:
                issues.append(f"类型冲突：{c['name']}->{e['slug']}={e['relation']}，反向={rev['relation']}")
    return issues


def render_block(entries: list[dict]) -> list[str]:
    out = ["related_cases:"]
    for e in entries:
        out.append(f"  - slug: {e['slug']}")
        out.append(f"    relation: {e['relation']}")
        if e["note"]:
            out.append(f"    note: {e['note']}")
    return out


def repair_duplicate_headers(cases: list[dict]) -> int:
    """历史修复脚本曾误插重复 related_cases: 行，这里做幂等清理。"""
    fixed = 0
    for c in cases:
        lines = c["text"].split("\n")
        idx = [i for i, ln in enumerate(lines) if ln.strip() == "related_cases:"]
        if len(idx) <= 1:
            continue
        for i in reversed(idx[:-1]):
            del lines[i]
        c["path"].write_text("\n".join(lines), encoding="utf-8")
        fixed += 1
    return fixed


def apply_fix(cases: list[dict], desired: dict) -> int:
    changed = 0
    for c in cases:
        if not c["name"] or "block" not in c:
            continue
        new_entries = desired.get(c["name"], [])
        old = c["entries"]
        same = (len(old) == len(new_entries) and all(
            a["slug"] == b["slug"] and a["relation"] == b["relation"] and a["note"] == b["note"]
            for a, b in zip(old, new_entries)))
        if same:
            continue
        start, end = c["block"]
        lines = c["lines"]
        fm_end = None
        for i in range(start, len(lines)):
            if lines[i].strip() == "---":
                fm_end = i
                break
        if fm_end is None:
            continue
        # block 行号是 frontmatter 内相对行号，需换算到全文
        abs_start = c["fm_start"] + start
        abs_end = c["fm_start"] + end
        lines2 = lines[:abs_start] + render_block(new_entries) + lines[abs_end:]
        c["path"].write_text("\n".join(lines2), encoding="utf-8")
        changed += 1
    return changed


def render_graph(cases: list[dict], desired: dict) -> str:
    sm = slug_map(cases)
    nodes = []
    for c in sorted(cases, key=lambda x: (FOLDER_ORDER.get(x["path"].parent.name, 9), x["path"].name)):
        if not c["name"]:
            continue
        node_id = c["name"].upper().replace("-", "_")
        label = c["path"].stem.replace("_完整案例", "").replace("_", "/")
        nodes.append((c["path"].parent.name, node_id, label))
    pairs = {}
    for name, entries in desired.items():
        for e in entries:
            if e["slug"] not in sm:
                continue
            key = frozenset({name, e["slug"]})
            pairs[key] = e["relation"]
    lines = ["graph TD"]
    last_folder = None
    for folder, node_id, label in nodes:
        if folder != last_folder:
            lines.append(f"    %% ===== {folder} =====")
            last_folder = folder
        lines.append(f"    {node_id}[{label}]")
    for t in TYPE_ORDER:
        edge = {"composes-with": "==>", "contrasts-with": "-.->", "depends-on": "-->"}[t]
        items = [(tuple(sorted(k)), typ) for k, typ in pairs.items() if typ == t]
        if not items:
            continue
        lines.append(f"    %% ===== {t} =====")
        for (a, b), _ in sorted(items):
            lines.append(f"    {a.upper().replace('-', '_')} {edge} {b.upper().replace('-', '_')}")
    return "\n".join(lines)


def write_graph(cases: list[dict], desired: dict) -> None:
    text = GRAPH_FILE.read_text(encoding="utf-8")
    lines = text.split("\n")
    graph = render_graph(cases, desired)
    # 1) 替换"## 全文关系图"到下一个"## "之间的内容
    start = next(i for i, ln in enumerate(lines) if ln.strip() == "## 全文关系图")
    nxt = None
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            nxt = i
            break
    if nxt is None:
        nxt = len(lines)
    block = ["## 全文关系图", "", "```mermaid", graph, "```", "", "---", "", ""]
    lines = lines[:start] + block + lines[nxt:]

    # 2) 生成"全部案例关联一览（自动生成）"
    detail = ["## 全部案例关联一览（自动生成）", "",
              "> 由 `tools/check_case_relations.py --write-graph` 从各案例 frontmatter 自动生成；"
              "手工精选版见上节“重点案例关联详情”。", ""]
    for c in sorted(cases, key=lambda x: (FOLDER_ORDER.get(x["path"].parent.name, 9), x["path"].name)):
        if not c["name"]:
            continue
        detail.append(f"### {c['path'].stem.replace('_完整案例', '')}")
        detail.append("")
        detail.append("| 关联案例 | 关系 | 说明 |")
        detail.append("|----------|------|------|")
        for e in desired.get(c["name"], []):
            target = next((x for x in cases if x["name"] == e["slug"]), None)
            tname = target["path"].stem.replace("_完整案例", "") if target else e["slug"]
            detail.append(f"| {tname} | {e['relation']} | {e['note'] or '—'} |")
        detail.append("")
    detail.append("")
    # 替换已有自动区，或插到"跨类型类比索引"前
    existing = next((i for i, ln in enumerate(lines) if ln.strip() == "## 全部案例关联一览（自动生成）"), None)
    if existing is not None:
        nxt = None
        for i in range(existing + 1, len(lines)):
            if lines[i].startswith("## "):
                nxt = i
                break
        if nxt is None:
            nxt = len(lines)
        lines = lines[:existing] + detail + lines[nxt:]
    else:
        anchor = next((i for i, ln in enumerate(lines) if ln.strip() == "## 跨类型类比索引"), None)
        if anchor is None:
            lines = lines + detail
        else:
            lines = lines[:anchor] + detail + ["---", ""] + lines[anchor:]
    GRAPH_FILE.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="案例关联关系检查/修复/关系图生成")
    parser.add_argument("--fix", action="store_true", help="写回补全/统一后的 frontmatter")
    parser.add_argument("--write-graph", action="store_true", help="重新生成关系图与自动关联表")
    args = parser.parse_args()
    cases = load_cases()
    issues = check(cases)
    print(f"案例数：{len(cases)}，检查问题：{len(issues)}")
    for s in issues[:40]:
        print(" -", s)
    if args.fix:
        dups = repair_duplicate_headers(cases)
        if dups:
            print(f"已清理重复 related_cases 行：{dups} 个文件")
            cases = load_cases()
        desired = desired_entries(cases)
        changed = apply_fix(cases, desired)
        print(f"已修复并写回 {changed} 个案例文件")
        cases = load_cases()
        print(f"修复后问题：{len(check(cases))}")
    if args.write_graph:
        desired = desired_entries(cases)
        write_graph(cases, desired)
        print(f"已重新生成：{GRAPH_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
