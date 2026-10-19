#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_report.py — 行业分析报告机器校验器（report-v3 契约）

用法：
  python tools/validate_report.py output/_drafts/白酒行业-行业分析报告（投资者版）.md
  python tools/validate_report.py <draft.md> --data-dir output/_data
  python tools/validate_report.py <draft.md> --data-dir output/_data --publish-dir output
  python tools/validate_report.py <draft.md> --json

规则来源：reference/output-template.md（v3.0）
退出码：0 = 通过（可含 P1 警告）；1 = 存在 P0 失败；2 = 用法/解析错误
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

SCHEMA = "report-v3"
TEMPLATE_MAJOR = 3
VALIDATOR_VERSION = "3.0.0"
REPO_ROOT = Path(__file__).resolve().parents[1]

IDENTITIES = {"投资者", "创业者", "求职者", "学生", "学生/研究者", "路人"}
STAGES = {"导入期", "成长期", "成熟期", "衰退期"}
MIN_VALUATION_CODES = {"投资者": 5}

# (编号, 标题关键词)
MODULES = [
    (1, "行业定义"),
    (2, "产业链"),
    (3, "生命周期"),
    (4, "假设"),
    (5, "时空对标"),
    (6, "商业模式"),
    (7, "市场规模"),
    (8, "护城河"),
    (9, "竞争格局"),
    (10, "产能"),
    (11, "估值"),
    (12, "PEST"),
    (13, "景气"),
    (14, "第二曲线"),
]
TOP_SECTIONS = [
    ("执行摘要", True),
    ("核心结论", True),
    ("AI 已完成的分析", True),
    ("建议下一步行动", True),
    ("可继续深入的研究方向", False),
    ("完整信源列表", True),
    ("数据时效性与质量说明", True),
    ("免责声明", True),
]
FORECAST_WORDS = ["预测", "预计", "预期", "估算", "目标价", "目标市值"]
PLACEHOLDERS = ["待补", "未获取", "获取失败", "待查", "暂无"]

Finding = dict


class Result:
    def __init__(self) -> None:
        self.p0: list[Finding] = []
        self.p1: list[Finding] = []

    def fail(self, code: str, msg: str, line: int | None = None) -> None:
        self.p0.append({"code": code, "msg": msg, "line": line})

    def warn(self, code: str, msg: str, line: int | None = None) -> None:
        self.p1.append({"code": code, "msg": msg, "line": line})

    @property
    def passed(self) -> bool:
        return not self.p0


# ---------------------------------------------------------------- parsing
def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split("\n")


def parse_scalar(v: str):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse_frontmatter(lines: list[str]) -> tuple[dict, int]:
    if not lines or lines[0].strip() != "---":
        return {}, 0
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, 0
    meta: dict = {}
    key = None
    for ln in lines[1:end]:
        if not ln.strip():
            continue
        m_list = re.match(r"^\s+-\s+(.*)$", ln)
        if m_list and key:
            if not isinstance(meta.get(key), list):
                meta[key] = []
            meta[key].append(parse_scalar(m_list.group(1)))
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", ln)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            meta[key] = [] if val == "" else parse_scalar(val)
    return meta, end + 1


def split_sections(lines: list[str]) -> list[dict]:
    idx = [i for i, ln in enumerate(lines) if re.match(r"^##\s+", ln)]
    secs = []
    for k, i in enumerate(idx):
        end = idx[k + 1] if k + 1 < len(idx) else len(lines)
        secs.append({"title": re.sub(r"^##\s+", "", lines[i]).strip(), "start": i, "end": end})
    return secs


def find_section(secs: list[dict], keyword: str) -> dict | None:
    for s in secs:
        if keyword in s["title"]:
            return s
    return None


def split_modules(lines: list[str], sec: dict) -> list[dict]:
    idx = [i for i in range(sec["start"], sec["end"]) if re.match(r"^###\s+\d+\.", lines[i])]
    mods = []
    for k, i in enumerate(idx):
        end = idx[k + 1] if k + 1 < len(idx) else sec["end"]
        m = re.match(r"^###\s+(\d+)\.\s*(.*)$", lines[i])
        mods.append(
            {
                "num": int(m.group(1)),
                "title": m.group(2).strip(),
                "start": i,
                "end": end,
                "text": "\n".join(lines[i + 1:end]),
            }
        )
    return mods


def iter_tables(lines: list[str], start: int, end: int) -> list[dict]:
    tables = []
    i = start
    while i < end:
        if lines[i].strip().startswith("|"):
            sep = i + 1
            if sep < end and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[sep]):
                header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows = []
                j = sep + 1
                while j < end and lines[j].strip().startswith("|"):
                    cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                    rows.append({"line": j + 1, "cells": cells})
                    j += 1
                tables.append({"header": header, "rows": rows})
                i = j
                continue
        i += 1
    return tables


# ---------------------------------------------------------------- values
NUM_RE = re.compile(r"[-−]?\d+(?:\.\d+)?")


def as_num(cell: str) -> float | None:
    if cell is None:
        return None
    s = str(cell).strip().replace(",", "").replace("−", "-")
    if s in {"", "—", "-", "–", "亏损", "不适用", "N/A", "n/a", "无"}:
        return None
    m = NUM_RE.search(s)
    if not m:
        return None
    v = float(m.group(0).replace("−", "-"))
    if "万亿" in s:
        v *= 10000
    elif "万" in s and "亿" not in s:
        v *= 0.0001
    return v


def as_pct(cell: str) -> float | None:
    m = re.search(r"([-−+]?\d+(?:\.\d+)?)\s*%", str(cell))
    return float(m.group(1).replace("−", "-")) if m else None


def parse_date(v) -> date | None:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", str(v).strip().strip("\"'"))
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None


def col_index(header: list[str], keys: list[str]) -> int | None:
    for i, h in enumerate(header):
        for k in keys:
            if k.lower() in h.lower():
                return i
    return None


def norm_code(cell: str) -> str | None:
    m = re.search(r"\b(\d{5})\.HK\b", str(cell))
    if m:
        return m.group(1)
    m = re.search(r"\b(\d{6})\b", str(cell))
    return m.group(1) if m else None


def section_text(lines: list[str], sec: dict | None) -> str:
    if not sec:
        return ""
    return "\n".join(lines[sec["start"]: sec["end"]])


# ---------------------------------------------------------------- checks
def check_meta(res: Result, meta: dict, lines: list[str]) -> dict:
    out = {"stage": "", "identity": "", "valuation_date": None, "data_cutoff": None}
    required = ["schema", "industry", "identity", "generated_at", "data_cutoff",
                "template_version", "orchestrator_version", "lifecycle_stage"]
    for k in required:
        if not meta.get(k):
            res.fail("E-META-01", f"报告头缺少字段：{k}")
    schema = str(meta.get("schema", ""))
    if not schema.startswith(SCHEMA):
        res.fail("E-META-02", f"schema 应为 {SCHEMA}，实际：{schema or '缺失'}")
    identity = str(meta.get("identity", "")).strip()
    out["identity"] = identity
    if identity and identity not in IDENTITIES:
        res.fail("E-META-03", f"identity 非法：{identity}（可选：{'/'.join(sorted(IDENTITIES))}）")
    stage = str(meta.get("lifecycle_stage", "")).strip()
    out["stage"] = stage
    if stage and stage not in STAGES:
        res.fail("E-META-04", f"lifecycle_stage 非法：{stage}")
    gen = parse_date(meta.get("generated_at", ""))
    cut = parse_date(meta.get("data_cutoff", ""))
    out["data_cutoff"] = cut
    if meta.get("generated_at") and gen is None:
        res.fail("E-META-05", "generated_at 不是合法日期（YYYY-MM-DD）")
    if meta.get("data_cutoff") and cut is None:
        res.fail("E-META-06", "data_cutoff 不是合法日期（YYYY-MM-DD）")
    if gen and cut and cut > gen:
        res.fail("E-META-07", f"data_cutoff（{cut}）晚于 generated_at（{gen}）")
    if identity == "投资者":
        vf = parse_date(meta.get("valuation_fetch_date", ""))
        out["valuation_date"] = vf
        if not meta.get("valuation_fetch_date"):
            res.fail("E-META-08", "投资者版缺少 valuation_fetch_date")
        elif vf is None:
            res.fail("E-META-09", "valuation_fetch_date 不是合法日期")
        elif cut and vf != cut:
            res.fail("E-META-10", f"valuation_fetch_date（{vf}）必须等于 data_cutoff（{cut}）")
    tv = str(meta.get("template_version", ""))
    m = re.match(r"^(\d+)", tv)
    if not m or int(m.group(1)) < TEMPLATE_MAJOR:
        res.fail("E-META-11", f"template_version 必须 >= 3.0，实际：{tv or '缺失'}")
    ov = str(meta.get("orchestrator_version", ""))
    m = re.match(r"^(\d+)", ov)
    if not m or int(m.group(1)) < 3:
        res.warn("W-META-01", f"orchestrator_version 建议 >= 3.0，实际：{ov or '缺失'}")
    ev = meta.get("evidence_files") or []
    if not isinstance(ev, list):
        ev = [ev]
    if not ev:
        res.warn("W-EVID-01", "报告头未列 evidence_files（数据不可追溯）")
    for p in ev:
        target = REPO_ROOT / str(p)
        if not target.exists():
            res.fail("E-EVID-02", f"evidence_files 指向的文件不存在：{p}")
    return out


def check_structure(res: Result, lines: list[str], secs: list[dict]) -> tuple[dict | None, list[dict]]:
    for kw, mandatory in TOP_SECTIONS:
        if find_section(secs, kw) is None:
            (res.fail if mandatory else res.warn)("E-STRUCT-01", f"缺少一级章节：{kw}")
    ai = find_section(secs, "AI 已完成的分析")
    if ai is None:
        return None, []
    mods = split_modules(lines, ai)
    by_num = {m["num"]: m for m in mods}
    if len(mods) != 14:
        res.fail("E-STRUCT-02", f"AI 已完成的分析应有 14 个编号模块，实际 {len(mods)} 个：{sorted(by_num)}")
    prev = 0
    for m in mods:
        if m["num"] <= prev:
            res.fail("E-STRUCT-03", f"模块编号未严格递增：{m['num']}（上一模块 {prev}）", m["start"] + 1)
        prev = max(prev, m["num"])
        if 1 <= m["num"] <= 14:
            kw = dict(MODULES)[m["num"]]
            if kw not in m["title"]:
                res.fail("E-STRUCT-04", f"模块 {m['num']} 标题应包含「{kw}」，实际：{m['title']}", m["start"] + 1)
    for num, kw in MODULES:
        if num not in by_num:
            res.fail("E-STRUCT-05", f"缺少模块 {num}. {kw}")
    core = find_section(secs, "核心结论")
    if core:
        t = section_text(lines, core)
        if "机会点" not in t:
            res.fail("E-STRUCT-06", "「对{身份}的核心结论」缺少「机会点」子节")
        if "风险" not in t:
            res.warn("W-STRUCT-01", "「对{身份}的核心结论」缺少「风险提示」子节")
    return ai, mods


def check_modules(res: Result, mods: list[dict], meta: dict, identity: str, stage: str,
                  lines: list[str], data_dir: Path | None) -> None:
    by_num = {m["num"]: m for m in mods}
    m = by_num.get(2)
    if m:
        t = m["text"]
        if len(t.strip()) < 80 or "上游" not in t or ("中游" not in t and "下游" not in t):
            res.fail("E-MOD-02", "模块 2 产业链结构须含上游/中游/下游并实质展开", m["start"] + 1)
    m = by_num.get(3)
    if m and "渗透率" not in m["text"]:
        res.warn("W-MOD-03", "模块 3 未提及渗透率（无法定位生命周期时须说明原因）", m["start"] + 1)
    m = by_num.get(4)
    if m:
        rows = sum(len(tb["rows"]) for tb in iter_tables(lines, m["start"], m["end"]))
        if "验证" not in m["text"] or "证伪" not in m["text"] or rows < 3:
            res.fail("E-MOD-04", "模块 4 须含 ≥3 条假设，每条含验证指标与证伪条件（表格）", m["start"] + 1)
    m = by_num.get(5)
    if m and ("时间对标" not in m["text"] or "空间对标" not in m["text"]):
        res.fail("E-MOD-05", "模块 5 须至少含 1 个时间对标与 1 个空间对标", m["start"] + 1)
    m = by_num.get(7)
    if m and not all(k in m["text"] for k in ("TAM", "SAM", "SOM")):
        res.fail("E-MOD-07", "模块 7 须含 TAM / SAM / SOM 三口径", m["start"] + 1)
    m = by_num.get(9)
    if m:
        if not re.search(r"CR\s*[358]", m["text"]):
            res.fail("E-MOD-09", "模块 9 须含 CR3/CR5/CR8 集中度", m["start"] + 1)
        if "利润" not in m["text"]:
            res.warn("W-MOD-09", "模块 9 未包含产业链利润分配", m["start"] + 1)
    m = by_num.get(10)
    if m:
        t = m["text"].strip()
        if stage in {"成熟期", "衰退期"}:
            if "不适用" in t and len(t) < 150:
                res.fail("E-MOD-10", "模块 10 写“不适用”时必须给出 ≥30 字理由", m["start"] + 1)
            elif len(t) < 120:
                res.fail("E-MOD-10", "模块 10 产能/库存周期分析过于简略（成熟期/衰退期必须实质展开）", m["start"] + 1)
        elif len(t) < 60 and "不适用" not in t:
            res.warn("W-MOD-10", "模块 10 未分析且未声明“不适用”", m["start"] + 1)
    m = by_num.get(11)
    if m:
        if "PE" not in m["text"] and "PB" not in m["text"]:
            res.fail("E-MOD-11", "模块 11 须给出估值方法（PE/PB/PS 等）", m["start"] + 1)
        check_valuation(res, m, lines, meta, identity, data_dir)
    m = by_num.get(12)
    if m:
        for kw in ("政治", "经济", "社会", "技术"):
            if kw not in m["text"]:
                res.fail("E-MOD-12", f"模块 12 PEST 缺少维度：{kw}", m["start"] + 1)
    m = by_num.get(13)
    if m:
        rows = sum(len(tb["rows"]) for tb in iter_tables(lines, m["start"], m["end"]))
        if "验证" not in m["text"] or "证伪" not in m["text"] or rows < 3:
            res.fail("E-MOD-13", "模块 13 须含 3–5 个指标及验证/证伪条件（表格）", m["start"] + 1)
    m = by_num.get(14)
    if m:
        t = m["text"].strip()
        if stage == "成熟期" and (len(t) < 200 or (len(t) < 250 and "不适用" in t)):
            res.fail("E-MOD-14", "成熟期行业模块 14 第二曲线须实质论证（不能只写不适用）", m["start"] + 1)
        elif stage == "衰退期" and len(t) < 100:
            res.fail("E-MOD-14", "衰退期行业模块 14 须论证第二曲线或写“不适用 + 理由”", m["start"] + 1)
        elif stage in {"导入期", "成长期"} and len(t) < 60 and "不适用" not in t:
            res.warn("W-MOD-14", "导入/成长期行业第二曲线可写“不适用 + 理由”或简要结论", m["start"] + 1)


def load_valuation_file(data_dir: Path | None, meta: dict) -> tuple[dict | None, Path | None]:
    """按报告 industry 选择对应取数 JSON（多行业共存时不能按文件名排序盲取）。"""

    def _load(path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8")), path
        except Exception:
            return None, path

    industry = str(meta.get("industry", "")).strip()
    if data_dir:
        d = Path(data_dir)
        groups = []
        if industry:
            groups.append(sorted(d.glob(f"{industry}-valuation-*.json")))
        groups.append(sorted(d.glob("*valuation*.json")))
        for cands in groups:
            if not cands:
                continue
            best = None
            for p in cands:
                data, _ = _load(p)
                if data is None:
                    continue
                if industry and str(data.get("industry", "")).strip() not in {"", industry}:
                    continue
                key = str(data.get("fetched_at", ""))
                if best is None or key > best[0]:
                    best = (key, data, p)
            if best:
                return best[1], best[2]
    ev = meta.get("evidence_files") or []
    if isinstance(ev, list):
        for p in ev:
            if "valuation" in str(p) and (REPO_ROOT / str(p)).exists():
                data, path = _load(REPO_ROOT / str(p))
                if data is not None:
                    return data, path
                return None, path
    return None, None


def check_valuation(res: Result, mod: dict, lines: list[str], meta: dict, identity: str,
                    data_dir: Path | None) -> None:
    tables = iter_tables(lines, mod["start"], mod["end"])
    table = None
    for tb in tables:
        if col_index(tb["header"], ["代码"]) is not None:
            table = tb
            break
    if table is None:
        res.fail("E-VAL-01", "模块 11 未找到含“代码”列的估值表", mod["start"] + 1)
        return
    h = table["header"]
    ci = col_index(h, ["代码"])
    pe_i = col_index(h, ["PE"])
    pb_i = col_index(h, ["PB"])
    mc_i = col_index(h, ["市值"])
    price_i = col_index(h, ["最新价", "价格", "股价"])
    src_i = col_index(h, ["数据来源", "来源"])
    time_i = col_index(h, ["获取时间", "数据时间", "时间"])
    min_codes = MIN_VALUATION_CODES.get(identity, 3)
    val_date = parse_date(meta.get("valuation_fetch_date") or meta.get("data_cutoff") or "")
    codes = []
    valid_rows = 0
    for row in table["rows"]:
        cells = row["cells"]
        cell = lambda i: cells[i] if i is not None and i < len(cells) else ""
        code = norm_code(cell(ci))
        if code:
            codes.append(code)
        bad = [p for p in PLACEHOLDERS if p in (cell(pe_i) + cell(pb_i) + cell(mc_i))]
        if bad:
            res.fail("E-VAL-02", f"估值表出现占位符「{bad[0]}」（{code or '未知标的'}）：取不到应标“亏损”或“—”并说明", row["line"])
            continue
        pe_cell, pb_cell = cell(pe_i), cell(pb_i)
        has_value = as_num(pe_cell) is not None or "亏损" in pe_cell or as_num(pb_cell) is not None
        if has_value:
            valid_rows += 1
        else:
            res.warn("W-VAL-01", f"估值行缺少有效 PE/PB（{code or '未知标的'}）", row["line"])
        if time_i is not None:
            td = parse_date(cell(time_i))
            if td is None:
                res.fail("E-VAL-03", f"获取时间不可解析（{code or '未知标的'}）", row["line"])
            elif val_date and td != val_date:
                res.fail("E-VAL-04", f"获取时间 {td} ≠ valuation_fetch_date {val_date}（{code or '未知标的'}）", row["line"])
        elif identity == "投资者":
            res.fail("E-VAL-05", "投资者版估值表缺少“获取时间”列", row["line"])
        if src_i is not None and not cell(src_i).strip():
            res.warn("W-VAL-02", f"估值行缺少数据来源（{code or '未知标的'}）", row["line"])
    if len(set(codes)) < min_codes:
        res.fail("E-VAL-06", f"{identity}版估值表有效标的数 {len(set(codes))} < 要求 {min_codes}")
    if valid_rows < min_codes:
        res.fail("E-VAL-07", f"估值表有效估值行 {valid_rows} < 要求 {min_codes}（PE/PB 至少一项有数值或标“亏损”）")
    # 交叉核对取数 JSON
    data, data_path = load_valuation_file(data_dir, meta)
    if data is None:
        if identity == "投资者":
            res.warn("W-VAL-03", "未找到估值取数 JSON，跳过数值交叉核对（数据不可追溯）")
        return
    fetched = parse_date(data.get("fetched_at", ""))
    if val_date and fetched and fetched != val_date:
        res.fail("E-VAL-08", f"取数 JSON fetched_at（{fetched}）≠ valuation_fetch_date（{val_date}）：{data_path}")
    index = {}
    for it in data.get("items", []):
        code = norm_code(str(it.get("code", "")))
        if code:
            index[code] = it
    for row in table["rows"]:
        cells = row["cells"]
        cell = lambda i: cells[i] if i is not None and i < len(cells) else ""
        code = norm_code(cell(ci))
        if not code:
            continue
        it = index.get(code)
        if it is None:
            res.fail("E-VAL-09", f"标的 {code} 不在取数 JSON 中（{data_path.name}）", row["line"])
            continue
        for label, ci2, key, tol in (("PE", pe_i, "pe_ttm", 0.03), ("PB", pb_i, "pb", 0.03),
                                     ("市值", mc_i, "mktcap", 0.015), ("最新价", price_i, "price", 0.005)):
            rv = as_num(cell(ci2))
            jv = it.get(key)
            if rv is None or jv is None:
                continue
            try:
                jv = float(jv)
            except (TypeError, ValueError):
                continue
            if abs(rv - jv) > max(tol * abs(jv), 0.05):
                res.fail("E-VAL-CROSS", f"{code} {label} 报告值 {rv} 与取数 JSON {jv} 不一致", row["line"])


def check_markers(res: Result, lines: list[str], secs: list[dict]) -> None:
    for i, line in enumerate(lines, 1):
        if any(k in line for k in ("符号说明", "符号定义", "符号：")):
            continue
        if "🟢" in line:
            for w in FORECAST_WORDS:
                if w in line:
                    res.fail("E-MARK-01", f"🟢 行内出现预测词「{w}」（实际数据不得用于预测）", i)
                    break
        if "🟡" in line and not re.search(r"(?:19|20)\d{2}", line):
            res.fail("E-MARK-02", "🟡 预测数据未标注年份", i)
    quality = find_section(secs, "数据时效性与质量说明")
    if quality:
        t = section_text(lines, quality)
        claims = any(k in t for k in ("含文件编号", "包含文件编号", "含文号", "包含文号"))
        if claims and not re.search(r"〔\d{4}〕", "\n".join(lines)):
            res.fail("E-LIE-01", "质量说明声称含文件编号，但全文没有 〔YYYY〕 文号")
    for s in secs:
        if re.search(r"修订记录|更新日志|版本记录|核实修订", s["title"]):
            res.warn("W-BODY-REVLOG", f"正文含修订/版本类章节：{s['title']}", s["start"] + 1)
    if "价值判断" not in "\n".join(lines):
        res.warn("W-JUDGE-01", "全文未出现“价值判断”标注，事实/价值判断未区分")


def check_arithmetic(res: Result, lines: list[str]) -> None:
    all_tables = []
    # 扫描全文表格
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("|"):
            sep = i + 1
            if sep < len(lines) and re.match(r"^\s*\|[\s:\-|]+\|\s*$", lines[sep]):
                header = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows = []
                j = sep + 1
                while j < len(lines) and lines[j].strip().startswith("|"):
                    rows.append({"line": j + 1, "cells": [c.strip() for c in lines[j].strip().strip("|").split("|")]})
                    j += 1
                all_tables.append({"header": header, "rows": rows})
                i = j
                continue
        i += 1
    for tb in all_tables:
        h = tb["header"]
        gi = None
        for k, hc in enumerate(h):
            if ("增速" in hc or "同比" in hc or "增长率" in hc) and "CAGR" not in hc and "复合" not in hc:
                gi = k
                break
        if gi is None:
            continue
        year_cols = []
        for k in range(gi):
            my = re.search(r"(20\d{2})", h[k])
            if my:
                year_cols.append((k, int(my.group(1))))
        for row in tb["rows"]:
            cells = row["cells"]
            if gi >= len(cells):
                continue
            stated = as_pct(cells[gi])
            if stated is None:
                continue
            if len(year_cols) >= 2:
                (pa, ya), (pb_, yb) = year_cols[0], year_cols[1]
                prev_k, cur_k = (pa, pb_) if ya < yb else (pb_, pa)
                if max(prev_k, cur_k) < len(cells):
                    pv, cv = as_num(cells[prev_k]), as_num(cells[cur_k])
                    if pv not in (None, 0) and cv is not None:
                        calc = (cv - pv) / abs(pv) * 100
                        tol = max(2.0, 0.08 * abs(stated))
                        if abs(calc - stated) > tol:
                            res.fail("E-MATH-GROWTH",
                                     f"增速与表内两期数值不符：表中 {stated:+.1f}%，按 {ya}->{yb} 计算 {calc:+.1f}%",
                                     row["line"])
                        continue
            nums = []
            for k in range(gi - 1, -1, -1):
                if k < len(cells):
                    v = as_num(cells[k])
                    if v is not None:
                        nums.append(v)
                if len(nums) == 2:
                    break
            if len(nums) < 2:
                continue
            cur, prev = nums[0], nums[1]
            if prev == 0:
                continue
            calc = (cur - prev) / abs(prev) * 100
            calc_swapped = (prev - cur) / abs(cur) * 100 if cur else None
            tol = max(1.0, 0.06 * abs(stated))
            ok1 = abs(calc - stated) <= tol
            ok2 = calc_swapped is not None and abs(calc_swapped - stated) <= tol
            if ok1 or ok2:
                continue
            same_sign_a = (calc > 0) == (stated > 0)
            same_sign_b = calc_swapped is not None and (calc_swapped > 0) == (stated > 0)
            if not same_sign_a and not same_sign_b and abs(calc) > 1:
                res.fail("E-MATH-GROWTH",
                         f"增速与相邻数值方向相反：表中 {stated:+.1f}%，按数值计算 {calc:+.1f}%（列序/口径请核对）",
                         row["line"])
            else:
                res.warn("W-MATH-GROWTH",
                         f"增速与相邻数值不自洽：表中 {stated:+.1f}%，按数值计算 {calc:+.1f}%（可能是口径问题）",
                         row["line"])
        # 占比合计检查（warning）
        for k, hc in enumerate(h):
            if "占比" in hc or "份额" in hc:
                pcts = [as_pct(r["cells"][k]) for r in tb["rows"] if k < len(r["cells"])]
                vals = [v for v in pcts if v is not None]
                if len(vals) >= 2 and not (95 <= sum(vals) <= 105):
                    res.warn("W-MATH-SUM", f"「{hc}」列合计 {sum(vals):.1f}%（请确认是否为全集）", tb["rows"][0]["line"])
                break
    # PE 中位数复算（模块 11 内；“中位数约 X 倍”才算声明，避免“PE 中位数、7 家市值”误报）
    for idx, line in enumerate(lines):
        if "PE" in line and "中位数" in line:
            m = re.search(r"中位数[^0-9]{0,10}(\d+(?:\.\d+)?)\s*倍", line)
            if not m:
                continue
            stated = float(m.group(1))
            pe_vals = []
            for tb in all_tables:
                h = tb["header"]
                pi = col_index(h, ["PE"])
                if pi is None:
                    continue
                start_line = tb["rows"][0]["line"] if tb["rows"] else 0
                if abs(start_line - (idx + 1)) < 200:
                    for row in tb["rows"]:
                        if pi < len(row["cells"]):
                            v = as_num(row["cells"][pi])
                            if v is not None and v > 0:
                                pe_vals.append(v)
            if len(pe_vals) >= 3:
                pe_vals.sort()
                n = len(pe_vals)
                median = pe_vals[n // 2] if n % 2 else (pe_vals[n // 2 - 1] + pe_vals[n // 2]) / 2
                if abs(stated - median) > max(10.0, 0.10 * abs(median)):
                    res.warn("W-MATH-MEDIAN",
                             f"文中 PE 中位数约 {stated:g}，表内非负 PE 复算中位数 {median:g}（请复核）", idx + 1)


def check_signal(res: Result, lines: list[str], identity: str) -> None:
    if identity != "投资者":
        return
    pat = re.compile(r"(中证|国证|申万|沪深|创业板指|板块|指数)[^\n]{0,60}?([-+−]\d+(?:\.\d+)?%|\d+\.\d+%)")
    if not pat.search("\n".join(lines)):
        res.fail("E-STRUCT-INDEX", "投资者版缺少行业指数/板块涨跌幅信号（如“国证绿色电力指数近一年 +15.28%”）")


# ---------------------------------------------------------------- publish
def inject_validation_line(text: str, line: str) -> str:
    lines = text.split("\n")
    out = [ln for ln in lines if not ln.startswith("> 自动校验：")]
    try:
        start = next(i for i, ln in enumerate(out) if "数据时效性与质量说明" in ln)
    except StopIteration:
        return "\n".join(out + ["", line, ""])
    end = len(out)
    for j in range(start + 1, len(out)):
        if re.match(r"^##\s", out[j]):
            end = j
            break
    payload = out[:end] + ["", line, ""] + out[end:]
    return "\n".join(payload)


def publish(draft: Path, publish_dir: Path, meta: dict, res: Result) -> Path:
    publish_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
    stem = draft.stem
    check_path = publish_dir / f"{stem}.check.json"
    line = f"> 自动校验：通过（{SCHEMA} / validator {VALIDATOR_VERSION}，{stamp}；详见 {check_path.name}）"
    text = inject_validation_line(draft.read_text(encoding="utf-8"), line)
    out_path = publish_dir / draft.name
    out_path.write_text(text, encoding="utf-8")
    check = {
        "schema": "check-v1",
        "validator_version": VALIDATOR_VERSION,
        "report": str(out_path.name),
        "industry": meta.get("industry"),
        "identity": meta.get("identity"),
        "passed": res.passed,
        "p0": res.p0,
        "p1": res.p1,
        "checked_at": stamp,
        "template_version": meta.get("template_version"),
        "orchestrator_version": meta.get("orchestrator_version"),
    }
    check_path.write_text(json.dumps(check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return check_path


# ---------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="行业分析报告 report-v3 机器校验器")
    parser.add_argument("draft", help="草稿 Markdown 路径")
    parser.add_argument("--data-dir", help="估值取数 JSON 目录（如 output/_data）")
    parser.add_argument("--publish-dir", help="校验通过后发布到该目录（如 output）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = parser.parse_args(argv)

    draft = Path(args.draft)
    if not draft.exists():
        print(f"[ERROR] 文件不存在：{draft}", file=sys.stderr)
        return 2
    lines = read_lines(draft)
    meta, _ = parse_frontmatter(lines)
    secs = split_sections(lines)
    res = Result()

    info = check_meta(res, meta, lines)
    ai, mods = check_structure(res, lines, secs)
    if ai and mods:
        check_modules(res, mods, meta, info["identity"], info["stage"], lines,
                      Path(args.data_dir) if args.data_dir else None)
    check_markers(res, lines, secs)
    check_arithmetic(res, lines)
    check_signal(res, lines, info["identity"])

    report = {
        "file": str(draft),
        "schema": SCHEMA,
        "validator_version": VALIDATOR_VERSION,
        "passed": res.passed,
        "p0": res.p0,
        "p1": res.p1,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for f in res.p0:
            loc = f" L{f['line']}" if f.get("line") else ""
            print(f"[P0]{loc} {f['code']}: {f['msg']}")
        for f in res.p1:
            loc = f" L{f['line']}" if f.get("line") else ""
            print(f"[P1]{loc} {f['code']}: {f['msg']}")
        print(f"\n结果：P0={len(res.p0)}  P1={len(res.p1)}  -> {'通过' if res.passed else '不通过'}")

    if res.passed and args.publish_dir:
        check_path = publish(draft, Path(args.publish_dir), meta, res)
        print(f"已发布：{Path(args.publish_dir) / draft.name}")
        print(f"校验结果：{check_path}")
    return 0 if res.passed else 1


if __name__ == "__main__":
    sys.exit(main())
