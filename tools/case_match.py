#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""case_match.py — 用 14 维特征向量做“当前行业 ↔ 历史案例”匹配（historical-stage-benchmarking 的半自动实现）

输入：
  --query  当前行业的 14 维向量 JSON（dim 1-14；无数据的维度可写 "N/A"）
输出：
  控制台 Top-N 匹配表；可选 --json-out 保存明细，--md-out 保存表格片段

说明：
  - 案例侧数据来自 historical-review/行业案例档案库 的“四、可对比特征向量”表（2026-10 已标准化为单值）；
  - 这是相似度辅助，不是结论：仍需按 HBS 技能执行“像→不像→像”的人工/专业判断；
  - 数据缺口（N/A）不参与该维度打分；可比维度 <10 时给出警告。
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "historical-review" / "行业案例档案库"

STAGES = ["导入期", "成长期", "成熟期", "下行早期", "下行晚期", "出清期", "重生期", "衰退期"]
CYCLE = ["扩产中", "收缩中", "底部稳定", "刚出清"]
TREND = {"↑上升": 1, "↓下降": -1, "→平稳": 0}
LEVELS = {"极高": 4, "高": 3, "中": 2, "低": 1}
COST = {"强": 3, "中": 2, "弱": 1}
BETA = {"顺周期高Beta": 0, "顺周期低Beta": 1, "逆周期": 2, "穿越周期": 3}
BETA_SIM = {(0, 1): 0.4, (1, 3): 0.6, (0, 3): 0.2, (2, 3): 0.3, (0, 2): 0.3, (1, 2): 0.3}
EFFECT = ["重大拐点", "加速器", "短暂冲击后恢复", "影响有限"]


def checked_only(text: str) -> str:
    """若值单元格是 [x] 选项列表，取已勾选项；否则原样返回。"""
    picked = re.findall(r"\[x\]\s*([^\[\]]+)", text)
    return " ".join(picked) if picked else text


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_num(text: str, pct: bool = False):
    t = text.replace("−", "-").replace("–", "-").replace("~", "").replace("约", " ")
    if pct:
        # 先处理区间（如 65-70% / 10-25%），避免把区间连字符误读为负号
        m_range = re.search(r"(-?\d+(?:\.\d+)?)\s*[-]\s*(\d+(?:\.\d+)?)\s*%", t)
        if m_range:
            return (float(m_range.group(1)) + float(m_range.group(2))) / 2
        m = re.search(r"(-?\d+(?:\.\d+)?)\s*%", t)
        return float(m.group(1)) if m else None
    m = re.search(r"(-?\d+(?:\.\d+)?)", t)
    return float(m.group(1)) if m else None


def parse_stage(text: str) -> list[str]:
    found = []
    for s in STAGES:
        if s in text:
            found.append(s)
    return found


def parse_cycle(text: str):
    for c in CYCLE:
        if c in text:
            return c
    return None


def parse_trend(text: str):
    t = checked_only(text)
    for k, v in TREND.items():
        if k in t:
            return v
    if "上升" in t:
        return 1
    if "下降" in t:
        return -1
    if "平稳" in t:
        return 0
    return None


def parse_level(text: str, mapping=LEVELS):
    t = checked_only(text)
    for k, v in mapping.items():
        if k in t:
            return v
    return None


def parse_effect(text: str):
    t = checked_only(text)
    for i, e in enumerate(EFFECT):
        if e in t:
            return i
    return None


def parse_beta(text: str):
    t = checked_only(text)
    for k, v in BETA.items():
        if k in t:
            return v
    return None


def load_cases() -> list[dict]:
    out = []
    for p in sorted(CASE_DIR.rglob("*_完整案例.md")):
        lines = p.read_text(encoding="utf-8").split("\n")
        start = next((i for i, ln in enumerate(lines) if re.match(r"^\|\s*\*\*1\.", ln)), None)
        if start is None:
            continue
        header = split_row(lines[start - 2])
        rows = []
        j = start
        while j < len(lines) and lines[j].strip().startswith("|"):
            cells = split_row(lines[j])
            m = re.match(r"^\*\*(\d+)\.", cells[0])
            if m and len(cells) >= 3:
                rows.append({"dim": int(m.group(1)), "value": cells[1], "note": cells[2]})
            j += 1
        slug = None
        for ln in lines[1:40]:
            m = re.match(r"^name:\s*(\S+)", ln)
            if m:
                slug = m.group(1)
                break
        out.append({"path": p, "name": p.stem.replace("_完整案例", ""), "slug": slug,
                    "model": p.parent.name, "rows": {r["dim"]: r for r in rows}})
    return out


def sim_stage(q: str, c: str) -> float | None:
    qs = parse_stage(q)
    cs = parse_stage(c)
    if not qs or not cs:
        return None
    best = 0.0
    for a in qs:
        for b in cs:
            ia, ib = STAGES.index(a), STAGES.index(b)
            d = abs(ia - ib)
            best = max(best, 1.0 if d == 0 else (0.5 if d == 1 else 0.0))
    return best


def sim_cycle(q: str, c: str) -> float | None:
    a, b = parse_cycle(q), parse_cycle(c)
    if a is None or b is None:
        return None
    d = abs(CYCLE.index(a) - CYCLE.index(b))
    return 1.0 if d == 0 else (0.5 if d == 1 else 0.0)


def sim_trend(q: str, c: str) -> float | None:
    a, b = parse_trend(q), parse_trend(c)
    if a is None or b is None:
        return None
    if a == b:
        return 1.0
    if a == 0 or b == 0:
        return 0.5
    return 0.0


def sim_level(q: str, c: str, mapping=LEVELS) -> float | None:
    a, b = parse_level(q, mapping), parse_level(c, mapping)
    if a is None or b is None:
        return None
    return 1.0 - abs(a - b) / (max(mapping.values()) - min(mapping.values()))


def sim_effect(q: str, c: str) -> float | None:
    a, b = parse_effect(q), parse_effect(c)
    if a is None or b is None:
        return None
    return 1.0 if a == b else (0.5 if abs(a - b) == 1 else 0.0)


def sim_beta(q: str, c: str) -> float | None:
    a, b = parse_beta(q), parse_beta(c)
    if a is None or b is None:
        return None
    if a == b:
        return 1.0
    return BETA_SIM.get(tuple(sorted((a, b))), 0.0)


def sim_num(q: float | None, c: float | None, scale: float) -> float | None:
    if q is None or c is None:
        return None
    return max(0.0, 1.0 - min(1.0, abs(q - c) / scale))


def compare(query: dict, case: dict) -> tuple[float, int, dict]:
    q = query["vector"]
    detail = {}
    skipped = []
    for d in range(1, 15):
        qv = str(q.get(str(d), "")).strip()
        row = case["rows"].get(d)
        if not qv or qv.upper() == "N/A" or row is None:
            skipped.append(d)
            continue
        cv = row["value"]
        s = None
        if d == 1:
            s = sim_stage(qv, cv)
        elif d == 2:
            s = sim_cycle(qv, cv)
        elif d == 3:
            if "未获取" in cv or "未获取" in qv:
                s = None
            else:
                qn, cn = parse_num(qv, pct=True), parse_num(cv, pct=True)
                s = sim_num(qn, cn, max(abs(qn or 0), 30))
        elif d == 4:
            qn, cn = parse_num(qv, pct=True), parse_num(cv, pct=True)
            if qn is not None and cn is not None and (qn >= 0) != (cn >= 0):
                s = 0.15
            else:
                s = sim_num(qn, cn, max(abs(qn or 0), abs(cn or 0), 5))
        elif d == 5:
            # 案例侧只有部分给出“分位”，PE 区间等口径不参与匹配
            if "分位" in cv:
                s = sim_num(parse_num(qv, pct=True), parse_num(cv, pct=True), 100)
        elif d == 6:
            s = sim_trend(qv, cv)
        elif d in (7, 8, 11):
            s = sim_level(qv, cv)
        elif d == 9:
            s = sim_level(qv, cv, COST)
        elif d == 10:
            s = sim_num(parse_num(qv), parse_num(cv), 10)
        elif d in (12, 13):
            s = sim_effect(qv, cv)
        else:
            s = sim_beta(qv, cv)
        if s is None:
            skipped.append(d)
            continue
        detail[d] = {"query": qv, "case": cv, "score": s}
    if not detail:
        return 0.0, 0, {}
    mean = sum(v["score"] for v in detail.values()) / len(detail)
    coverage = len(detail) / 14.0
    total = mean * (0.7 + 0.3 * coverage)
    detail["_skipped"] = skipped
    return total, len(detail), detail


def main() -> int:
    ap = argparse.ArgumentParser(description="14 维特征向量案例匹配")
    ap.add_argument("--query", required=True, help="14 维向量 JSON 路径")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--json-out", help="匹配明细 JSON 输出路径")
    args = ap.parse_args()
    query = json.loads(Path(args.query).read_text(encoding="utf-8"))
    cases = load_cases()
    results = []
    for c in cases:
        score, n, detail = compare(query, c)
        results.append({"name": c["name"], "slug": c["slug"], "model": c["model"],
                        "score": round(score, 3), "dims": n, "detail": detail})
    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"查询：{query.get('industry', '?')}；案例数 {len(cases)}；Top {args.top}")
    header = "| # | 案例 | 模式 | 得分 | 可比维度 |"
    print(header)
    print("|---|------|------|------|----------|")
    for i, r in enumerate(results[:args.top], 1):
        print(f"| {i} | {r['name']} | {r['model']} | {r['score']:.3f} | {r['dims']} |")
    print("\nTop1 维度明细：")
    top = results[0]
    for d in sorted(k for k in top["detail"] if isinstance(k, int)):
        v = top["detail"][d]
        print(f"  {d:>2}: 当前={v['query']} | 案例={v['case']} | 相似度={v['score']:.2f}")
    print(f"  跳过维度（案例侧无同口径数据）：{top['detail'].get('_skipped', [])}")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(
            {"query": query, "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n明细已写入：{args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
