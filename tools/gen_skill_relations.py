#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gen_skill_relations.py — 从 14 个顶层技能的 frontmatter 生成关系元数据清单

用途：
  --check  统计并检查关系声明（默认；存在多类型声明时退出码 1）
  --write  把“关系元数据全量清单（自动生成）”写入 INDEX.md
  --fix    一次性迁移：按方案 A（每个技能对只保留一种关系）清理历史多类型声明

说明：
  - 顶层 INDEX 的“关系明细”是编排视角的 18 条核心关系（手工维护）；
  - 本脚本输出 frontmatter 的完整声明（去重到技能对），用于发现双向/多类型声明；
  - 方案 A 规则：depends-on > composes-with > contrasts-with；depends-on 只保留“依赖方→被依赖方”一条，
    反向的 composes-with 声明删除；composes-with 与 contrasts-with 冲突时保留 composes-with。
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "INDEX.md"
TYPE_ORDER = {"depends-on": 0, "composes-with": 1, "contrasts-with": 2}
SECTION_TITLE = "## 关系元数据全量清单（自动生成）"
REL_RE = re.compile(r"^\s*(?:-\s+)?(depends-on|composes-with|contrasts-with):\s*\[(.*)\]\s*$")

# 方案 A 的一次性迁移清单（9 对多类型声明）
CANONICAL_REMOVALS: dict[str, set[tuple[str, str]]] = {
    "industry-lifecycle-anchoring": {
        ("composes-with", t) for t in (
            "business-model-feasibility", "market-size-estimation", "moat-analysis",
            "competitive-landscape-analysis", "capacity-cycle-judgment", "lifecycle-valuation-map",
        )
    },
    "hypothesis-driven-research": {("composes-with", "industry-analysis-orchestrator")},
    "identity-oriented-output": {("composes-with", "industry-analysis-orchestrator")},
    "moat-analysis": {("contrasts-with", "competitive-landscape-analysis")},
    "competitive-landscape-analysis": {("contrasts-with", "moat-analysis")},
}


def parse_skill(path: Path) -> tuple[str | None, list[tuple[str, str]]]:
    lines = path.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].strip() != "---":
        return None, []
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None, []
    fm = lines[1:end]
    name = None
    for ln in fm:
        m = re.match(r"^name:\s*(\S+)", ln)
        if m:
            name = m.group(1).strip()
            break
    rel_i = next((i for i, ln in enumerate(fm) if ln.strip() == "related_skills:"), None)
    if rel_i is None or not name:
        return name, []
    block = []
    for ln in fm[rel_i + 1:]:
        if ln.strip() == "" or ln.startswith(" "):
            block.append(ln)
        else:
            break
    text = "\n".join(block)
    decls = []
    for m in re.finditer(r"(depends-on|composes-with|contrasts-with):\s*\[([^\]]*)\]", text):
        typ = m.group(1)
        for t in [x.strip() for x in m.group(2).split(",") if x.strip()]:
            decls.append((typ, t))
    return name, decls


def _iter_skill_paths():
    for p in sorted(ROOT.glob("*/SKILL.md")):
        if "historical-review" in p.parts:
            continue
        yield p


def _split_rel(block: list[str]) -> tuple[dict, list[str], bool]:
    mapping: dict[str, list[str]] = {}
    order: list[str] = []
    pattern_b = any(
        re.match(r"^  - (depends-on|composes-with|contrasts-with):", ln)
        for ln in block[1:] if ln.strip()
    )
    for ln in block:
        m = REL_RE.match(ln)
        if not m:
            continue
        typ, inner = m.group(1), m.group(2)
        if typ not in mapping:
            mapping[typ] = []
            order.append(typ)
        for t in [x.strip() for x in inner.split(",") if x.strip()]:
            if t not in mapping[typ]:
                mapping[typ].append(t)
    return mapping, order, pattern_b


def _render_rel(mapping: dict, order: list[str], pattern_b: bool) -> list[str]:
    out = []
    if pattern_b:
        for typ in order:
            out.append(f"  - {typ}: [{', '.join(mapping.get(typ, []))}]")
    else:
        first = True
        for typ in order:
            prefix = "  - " if first else "    "
            out.append(f"{prefix}{typ}: [{', '.join(mapping.get(typ, []))}]")
            first = False
    return out


def apply_fix() -> list[str]:
    """按方案 A 清理多类型声明（幂等；只改 frontmatter related_skills 块）。"""
    changed = []
    for path in _iter_skill_paths():
        lines = path.read_text(encoding="utf-8").split("\n")
        if not lines or lines[0].strip() != "---":
            continue
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is None:
            continue
        rel_i = next((i for i in range(1, end) if lines[i].strip() == "related_skills:"), None)
        if rel_i is None:
            continue
        j = rel_i + 1
        while j < len(lines) and (lines[j].strip() == "" or lines[j].startswith(" ")):
            j += 1
        block = lines[rel_i + 1:j]
        mapping, order, pattern_b = _split_rel(block)
        removals = CANONICAL_REMOVALS.get(path.parent.name, set())
        if not removals:
            continue
        new_mapping = {t: [x for x in mapping.get(t, []) if (t, x) not in removals] for t in order}
        if new_mapping == mapping:
            continue
        new_block = _render_rel(new_mapping, order, pattern_b)
        path.write_text("\n".join(lines[:rel_i + 1] + new_block + lines[j:]), encoding="utf-8")
        changed.append(path.parent.name)
    return changed


def load() -> tuple[dict, list[tuple[str, str, str]]]:
    skills = {}
    decls = []
    for p in sorted(ROOT.glob("*/SKILL.md")):
        if "historical-review" in p.parts:
            continue
        name, ds = parse_skill(p)
        if not name:
            continue
        skills[name] = p
        for typ, dst in ds:
            decls.append((name, typ, dst))
    return skills, decls


def build_pairs(decls: list[tuple[str, str, str]]) -> dict:
    pairs: dict[frozenset, list[tuple[str, str, str]]] = {}
    for src, typ, dst in decls:
        pairs.setdefault(frozenset({src, dst}), []).append((src, typ, dst))
    return pairs


def stats(skills: dict, decls: list, pairs: dict) -> dict:
    multi = [k for k, v in pairs.items() if len({t for _, t, _ in v}) > 1]
    bi = [k for k, v in pairs.items()
          if len({(src, dst) for src, _, dst in v}) > 1 or len({(dst, src) for src, _, dst in v}) > 1]
    return {
        "skills": len(skills),
        "declarations": len(decls),
        "pairs": len(pairs),
        "multi_type_pairs": len(multi),
        "bidirectional_pairs": len(bi),
        "multi_list": multi,
        "bi_list": bi,
    }


def render_section(skills: dict, decls: list, pairs: dict) -> str:
    st = stats(skills, decls, pairs)
    lines = [SECTION_TITLE, "",
             f"> 由 `tools/gen_skill_relations.py --write` 从 {st['skills']} 个技能 frontmatter 自动生成；"
             f"与上表“关系明细（编排视角）”互补，不要手工编辑本段。", "",
             f"**统计**：声明 {st['declarations']} 条 → 去重 {st['pairs']} 对；"
             f"其中多类型对 {st['multi_type_pairs']} 个、双向声明对 {st['bidirectional_pairs']} 个。", "",
             "| # | 技能 A | 关系（声明类型） | 技能 B | 声明方向 |",
             "|---|--------|------------------|--------|----------|"]
    rows = sorted(pairs.items(), key=lambda kv: (
        min(TYPE_ORDER.get(t, 9) for _, t, _ in kv[1]),
        sorted(kv[0])[0],
    ))
    for i, (key, entries) in enumerate(rows, 1):
        names = sorted(key)
        types = sorted({t for _, t, _ in entries}, key=lambda x: TYPE_ORDER.get(x, 9))
        # 含 depends-on 时，把依赖方放在 A 列（方向即“A 依赖 B”）
        if "depends-on" in types:
            dep_entry = next(((s, d) for s, t, d in entries if t == "depends-on"), None)
            if dep_entry:
                a, b = dep_entry
            else:
                a, b = names
        else:
            a, b = names
        direction = "；".join(f"{src} --{t}--> {dst}" for src, t, dst in entries)
        lines.append(f"| {i} | {a} | {' + '.join(types)} | {b} | {direction} |")
    lines.append("")
    return "\n".join(lines)


def write_section(text: str) -> str:
    if SECTION_TITLE in text:
        start = text.index(SECTION_TITLE)
        nxt = text.find("\n## ", start + len(SECTION_TITLE))
        end = nxt + 1 if nxt != -1 else len(text)
        return text[:start] + text[end:]
    anchor = text.find("\n## 推荐学习顺序")
    if anchor == -1:
        return text + "\n\n" + SECTION_TITLE + "\n"
    return text[:anchor] + "\n" + text[anchor:]


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 INDEX 关系元数据清单")
    parser.add_argument("--write", action="store_true", help="写入 INDEX.md")
    parser.add_argument("--fix", action="store_true", help="一次性迁移：按方案 A 清理多类型声明")
    args = parser.parse_args()
    if args.fix:
        changed = apply_fix()
        print(f"已规范化 {len(changed)} 个技能：{', '.join(changed) if changed else '无（已幂等）'}")
    skills, decls = load()
    pairs = build_pairs(decls)
    st = stats(skills, decls, pairs)
    print(f"技能数：{st['skills']}；声明 {st['declarations']} 条；去重 {st['pairs']} 对；"
          f"多类型 {st['multi_type_pairs']} 对；双向 {st['bidirectional_pairs']} 对")
    if st["multi_list"]:
        print("多类型对：")
        for k in st["multi_list"]:
            print(" -", " / ".join(sorted(k)), "：", "、".join(sorted({t for _, t, _ in pairs[k]})))
    if args.write:
        text = INDEX.read_text(encoding="utf-8")
        # 先删除旧自动段（若有），再在“推荐学习顺序”前插入
        if SECTION_TITLE in text:
            start = text.index(SECTION_TITLE)
            nxt = text.find("\n## ", start + len(SECTION_TITLE))
            end = nxt + 1 if nxt != -1 else len(text)
            text = text[:start] + text[end:]
        section = render_section(skills, decls, pairs)
        anchor = text.find("\n## 推荐学习顺序")
        if anchor == -1:
            text = text.rstrip() + "\n\n" + section + "\n"
        else:
            text = text[:anchor] + "\n" + section + "\n" + text[anchor:]
        INDEX.write_text(text, encoding="utf-8")
        print("已写入 INDEX.md")
    if not args.write and not args.fix and st["multi_type_pairs"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
