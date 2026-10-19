#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report_to_14dim.py — 从 report-v3 行业报告抽取 14 维历史对照向量（草稿）。

定位：把“报告 → 14 维向量”从纯人工填写，降为“脚本生成草稿 + 人工复核”。
     - 可自动抽取：生命周期、产能位置、CR3、需求增速、估值分位、政策/海外敏感度、
       供给刚性、成本传导、Beta 等有明确表述的维度；
     - 需人工复核：周期性强度（合成分）、部分定性判断、N/A 与子行业差异；
     - 输出 `review_required` 清单，配合 `--strict` 可作为发布前检查。

用法：
    python tools/report_to_14dim.py --report "output/电力行业-行业分析报告（投资者版）.md"
    python tools/report_to_14dim.py --report <report> --out tools/examples/电力-14dim.auto.json
    python tools/report_to_14dim.py --report <report> --compare tools/examples/电力-14dim.json
    python tools/report_to_14dim.py --selftest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

MODULE_RE = re.compile(r"^###\s+(\d{1,2})\.\s+(.+?)\s*$", re.M)
STAGES = ["导入期", "成长期", "成熟期", "下行早期", "下行晚期", "出清期", "重生期", "衰退期"]


def _clean(text: str, limit: int = 80) -> str:
    text = re.sub(r"[*_`#>]", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _frontmatter(text: str) -> dict[str, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    meta: dict[str, str] = {}
    if not m:
        return meta
    for line in m.group(1).split("\n"):
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta


def _modules(text: str) -> dict[int, str]:
    matches = list(MODULE_RE.finditer(text))
    out: dict[int, str] = {}
    for i, m in enumerate(matches):
        n = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[n] = text[start:end]
    return out


def _section(modules: dict[int, str], *nums: int) -> str:
    return "\n".join(modules.get(n, "") for n in nums)


def _sentence_with(text: str, kw: str, limit: int = 70) -> str:
    for seg in re.split(r"[。；\n]", text):
        if kw in seg:
            return _clean(seg, limit)
    return _clean(text, limit)


def _stage(raw: str) -> str:
    raw = raw or ""
    # 先匹配更长的词，避免“下行早期/晚期”被“下行”截断
    for s in ["下行早期", "下行晚期", "出清期", "重生期", "导入期", "成长期", "成熟期", "衰退期"]:
        if s in raw:
            return s
    for s in STAGES:
        if s in raw:
            return s
    return ""


def _dim1(meta: dict[str, str], mods: dict[int, str]) -> tuple[str, str, bool]:
    raw = meta.get("lifecycle_stage", "")
    source = "报告 metadata lifecycle_stage"
    if not raw:
        m = re.search(r"(导入期|成长期|成熟期|下行早期|下行晚期|出清期|重生期|衰退期)", mods.get(3, ""))
        raw = m.group(1) if m else ""
        source = "报告模块 3"
    stage = _stage(raw)
    if not stage:
        return "N/A（无法从 metadata/模块 3 识别生命周期阶段）", source, True
    if stage in raw and raw != stage:
        return f"{stage}（报告标注：{_clean(raw, 40)}）", source, False
    return stage, source, False


def _dim2(mods: dict[int, str]) -> tuple[str, str, bool]:
    text = _section(mods, 2, 10)
    if re.search(r"无传统产能周期|不适用|无产能周期|轻资产", text):
        return "N/A（无传统产能周期）", "报告模块 2/10", False
    candidates = [
        ("供不应求", ["供不应求"]),
        ("扩产中", ["扩产中", "逆势扩张", "装机高增", "新能源扩张", "产能扩张", "仍在扩产"]),
        ("产能激增", ["产能激增", "供给过剩风险上升"]),
        ("刚出清", ["刚出清"]),
        ("产能出清", ["产能出清", "出清"]),
        ("底部稳定", ["底部稳定"]),
        ("收缩中", ["收缩中"]),
        ("格局改善", ["格局改善"]),
    ]
    for label, kws in candidates:
        for kw in kws:
            if kw in text:
                ev = _sentence_with(text, kw, 70)
                return f"{label}（{ev}）", f"报告模块 2/10（{kw}）", False
    return "N/A（未识别到产能周期位置）", "报告模块 2/10", True


def _dim3(mods: dict[int, str]) -> tuple[str, str, bool]:
    text = mods.get(9, "")
    # 严格执行 CR3 口径：子行业 CR3（火电/财险/光伏等）不能冒充全行业 CR3
    sub_labels = r"(火电|水电|核电|风电|光伏|财险|财产险|寿险|人身险|硅料|硅片|组件|电池|乘用车|整车|零部件|白电|空调|冰洗)"
    full = None
    for m in re.finditer(r"CR3\s*[≈约=]?\s*(\d{1,3}(?:\.\d+)?)\s*%?(?:\s*[-–~]\s*(\d{1,3}(?:\.\d+)?))?\s*%", text):
        prefix = text[max(0, m.start() - 14):m.start()]
        if not re.search(sub_labels, prefix):
            full = m
            break
    if full:
        if full.group(2):
            return f"CR3≈{full.group(1)}%-{full.group(2)}%", "报告模块 9", False
        return f"CR3≈{full.group(1)}%", "报告模块 9", False
    m5 = re.search(r"CR5\s*[（(]?[^0-9%\n]{0,80}?(\d{1,3}(?:\.\d+)?)\s*%?(?:\s*[-–~]\s*(\d{1,3}(?:\.\d+)?))?\s*%", text)
    if m5:
        span = f"{m5.group(1)}%-{m5.group(2)}%" if m5.group(2) else f"{m5.group(1)}%"
        return f"CR3 未获取（CR5≈{span}）", "报告模块 9（仅有 CR5 或仅子行业 CR3）", True
    m10 = re.search(r"CR10\s*[（(]?[^0-9%\n]{0,20}?(\d{1,3}(?:\.\d+)?)\s*%", text)
    if m10:
        return f"CR3 未获取（CR10≈{m10.group(1)}%）", "报告模块 9（仅有 CR10）", True
    return "CR3 未获取（报告未给出集中度数值）", "报告模块 9", True


def _dim4(mods: dict[int, str]) -> tuple[str, str, bool]:
    text = _section(mods, 3, 7)
    demand_kw = r"(用电量|需求量?|销量|产量|行业收入|保费|营收|收入)"
    candidates: list[tuple[str, str]] = []
    for seg in re.split(r"[。；\n]", text):
        if not re.search(demand_kw, seg):
            continue
        nums = re.findall(r"([+-]?\d{1,3}(?:\.\d+)?)\s*%", seg)
        for n in nums:
            candidates.append((n, _clean(seg, 80)))
    if candidates:
        # 优先取带符号/小数、且落在“2025/同比/增长”语境里的值；
        # 排除保险深度/密度/渗透率等“率”值，避免把 4.3% 当保费增速。
        def score(c: tuple[str, str]) -> tuple[int, int]:
            v, ev = c
            s = 0
            if "同比" in ev: s += 3
            if "增长" in ev: s += 2
            if "2025" in ev: s += 1
            if v.startswith(("+", "-")): s += 1
            if "." in v: s += 1
            if re.search(r"深度|密度|渗透率|占比", ev): s -= 3
            return (s, -len(ev))
        v, ev = sorted(candidates, key=score, reverse=True)[0]
        if not v.startswith(("+", "-")):
            v = "+" + v
        # 同一报告里“产量/收入/用电量”等多口径并存，或取到“年均”值时，必须人工确认
        needs_review = len({x[0] for x in candidates}) > 1 or bool(re.search(r"年均|十四五年均", ev))
        return f"{v}%（{ev}）", "报告模块 3/7", needs_review
    return "N/A（报告未给出需求量增速）", "报告模块 3/7", True


def _dim5(mods: dict[int, str], text: str, industry: str) -> tuple[str, str, bool]:
    # 优先模块 11；报告有时只在“核心发现/摘要”里给分位
    candidates: list[tuple[str, str, str]] = []
    for src, blob in (("报告模块 11", mods.get(11, "")), ("报告全文", text)):
        for m in re.finditer(r"(PE|PB)[^。；\n]{0,40}?(\d{1,3}(?:\.\d+)?)\s*%\s*分位", blob):
            candidates.append((f"{m.group(1)} {m.group(2)}%分位", src, blob[max(0, m.start() - 30):m.start()]))
        for m in re.finditer(r"(\d{1,3}(?:\.\d+)?)\s*%\s*分位", blob):
            candidates.append((f"{m.group(1)}%分位", src, blob[max(0, m.start() - 30):m.start()]))
    if candidates:
        # 同一报告可能同时引用“行业 PE 分位”和“本行业 PE 分位”，优先取上下文含本行业名的
        chosen = next((c for c in candidates if industry and industry in c[2]), candidates[0])
        review = len({c[0] for c in candidates}) > 1
        return chosen[0], chosen[1], review
    if re.search(r"未取|未获取|N/A|不适用", mods.get(11, "")):
        return "N/A（未取历史分位）", "报告模块 11", False
    return "N/A（未取历史分位）", "报告模块 11", True


def _dim6(mods: dict[int, str], text: str) -> tuple[str, str, bool]:
    # 优先看执行摘要/核心发现/全文里的利润同比数字
    m = re.search(r"(?:归母净利|净利润|净利|利润)[^。；\n]{0,40}?同比[^。；\n]{0,12}?([+-]?\d{1,3}(?:\.\d+)?)\s*%", text)
    if not m:
        m = re.search(r"(?:归母净利|净利润|净利|利润)[^。；\n]{0,30}?([+-]?\d{1,3}(?:\.\d+)?)\s*%", text)
    if m:
        v = m.group(1)
        if v.startswith("-"):
            return "↓下降", "报告摘要/核心发现（利润同比为负）", False
        if v.startswith("+"):
            return "↑上升", "报告摘要/核心发现（利润同比为正）", False
    section = mods.get(6, "")
    if re.search(r"分化", section):
        return "→平稳（结构分化）", "报告模块 6", False
    if re.search(r"[↑]|上升|改善|修复|回升|增长", section):
        return "↑上升", "报告模块 6", False
    if re.search(r"[↓]|下降|下滑|承压|恶化|亏损", section):
        return "↓下降", "报告模块 6", False
    if re.search(r"平稳|稳定|持平", section):
        return "→平稳", "报告模块 6", False
    return "→平稳（🔍 待复核）", "报告模块 6", True


def _dim7(mods: dict[int, str], text: str) -> tuple[str, str, bool]:
    section = mods.get(12, "")
    m = re.search(r"政策敏感度[^。；\n]{0,20}?(极高|高|中|低)", text)
    if m:
        return m.group(1), "报告全文（政策敏感度）", False
    m = re.search(r"(?:P\s*政治|政策敏感度)[^。；\n]{0,60}?(极高|高|中|低)", section)
    if m:
        return m.group(1), "报告模块 12（P 政治）", False
    p_row = ""
    for line in section.split("\n"):
        if "P 政治" in line or "**P" in line:
            p_row += line
    blob = p_row or section
    if re.search(r"(牌照|管制|强监管|核心变量|清零|准入|配额)", blob):
        return "极高（🔍 依模块 12 推断）", "报告模块 12（P 政治）", True
    if "政策" in blob or len(p_row) > 20:
        return "高（🔍 依模块 12 推断）", "报告模块 12（P 政治）", True
    return "中（🔍 待复核）", "报告模块 12", True


def _dim8(mods: dict[int, str]) -> tuple[str, str, bool]:
    text = _section(mods, 2, 10)
    if re.search(r"结论[:：]\s*不适用|无传统产能周期|无产能周期|不存在传统意义的?产能|轻资产", text):
        return "N/A（无传统产能周期）", "报告模块 2/10", False
    m = re.search(r"(极高|高|中|低)\s*[（(](\d{1,2}(?:\.\d+)?)\s*[-–~]\s*(\d{1,2}(?:\.\d+)?)\s*年", text)
    if m:
        return f"{m.group(1)}（{m.group(2)}-{m.group(3)}年）", "报告模块 2/10", False
    # 只把 1-2 位数字的“x-y 年”当作工期，避免把 2028-2030 的年份当年数
    m2 = re.search(r"(?<!\d)(\d{1,2}(?:\.\d+)?)\s*[-–~]\s*(\d{1,2}(?:\.\d+)?)\s*年", text)
    if m2:
        lo, hi = float(m2.group(1)), float(m2.group(2))
        avg = (lo + hi) / 2
        level = "极高" if avg > 5 else "高" if avg >= 3 else "中" if avg >= 1 else "低"
        durations = re.findall(r"(?<!\d)(\d{1,2}(?:\.\d+)?)\s*[-–~]\s*(\d{1,2}(?:\.\d+)?)\s*年", text)
        needs_review = len(set(durations)) > 1
        return f"{level}（{m2.group(1)}-{m2.group(2)}年）", "报告模块 2/10（按投产/储存周期映射）", needs_review
    return "中（🔍 待复核）", "报告模块 2/10", True


def _dim9(mods: dict[int, str], text: str) -> tuple[str, str, bool]:
    section = _section(mods, 6) + "\n" + text[:6000]
    if re.search(r"价格接受者|成本传导(不畅|弱|差)", section):
        return "弱（价格接受者）", "报告模块 6", False
    if re.search(r"(无|没有|缺乏|不具备|较弱).{0,6}定价权", section):
        return "弱（无定价权）", "报告模块 6", False
    if re.search(r"品牌定价权|定价权|提价能力|提价贡献", section):
        return "强（品牌定价权/提价能力）", "报告模块 6", False
    if re.search(r"部分传导|成本传导[^。；\n]{0,10}(中|部分)|电价传导|受管制|受监管|市场化传导", section):
        return "中（受管制/部分传导）", "报告模块 6", False
    return "中（🔍 待复核）", "报告模块 6", True


def _dim10(mods: dict[int, str], text: str) -> tuple[str, str, bool]:
    explicit = re.search(r"周期性强度[^0-9]{0,10}(\d{1,2})\s*(?:/10|分)", text)
    if explicit:
        return f"{explicit.group(1)}", "报告模块 6/10（报告明示）", False
    section = _section(mods, 3, 6, 10) + "\n" + text[:3000]
    score = 3
    reasons = ["基础 3"]
    loss_text = _section(mods, 6, 10)
    if re.search(r"全行业亏损|全面亏损|大面积亏损|巨亏", loss_text):
        score += 2; reasons.append("全行业亏损 +2")
    if re.search(r"资本开支|CAPEX", section) and re.search(r"骤降|波动|扩张|收缩", section):
        score += 1; reasons.append("CAPEX 波动 +1")
    if re.search(r"煤价|猪价|运价|价格周期|大宗商品|硅料价格|提价", section):
        score += 1; reasons.append("价格周期 +1")
    if re.search(r"产能周期|扩产|出清", section):
        score += 1; reasons.append("产能周期 +1")
    if re.search(r"投资端|权益|投资收益", section) and re.search(r"波动|弹性", section):
        score += 1; reasons.append("投资端波动 +1")
    if re.search(r"公用事业|稳定现金流|高股息|刚需", section):
        score -= 1; reasons.append("公用事业/刚需 -1")
    score = max(1, min(10, score))
    return f"{score}（🔍 自动合成：{'；'.join(reasons)}）", "报告模块 3/6/10（合成）", True


def _dim11(mods: dict[int, str], text: str) -> tuple[str, str, bool]:
    section = mods.get(12, "")
    m = re.search(r"(?:E\s*经济|海外|出口|汇率|全球|外资)[^。；\n]{0,40}?(极高|高|中|低)", section)
    if m:
        return m.group(1), "报告模块 12（E 经济/海外）", False
    if re.search(r"影响有限|内需为主|以内需|几乎无影响", section + "\n" + text[:2000]):
        return "低（内需为主）", "报告模块 12", False
    if re.search(r"出口|海外收入|外资|北向|汇率|全球", section + "\n" + text[:3000]):
        return "中（🔍 依模块 12 推断）", "报告模块 12", True
    return "低（🔍 待复核）", "报告模块 12", True


def _dim_effect(report: str, year: str) -> tuple[str, str, bool]:
    m = re.search(rf"{year}[^。；\n]{{0,30}}(重大拐点|加速器|短暂冲击|影响有限|不适用)", report)
    if m:
        return m.group(1), f"报告提及 {year}（{m.group(1)}）", False
    return "N/A（当前行业无对应事件）", f"报告未给出 {year} 的可量化效应", False


def _dim14(mods: dict[int, str], text: str) -> tuple[str, str, bool]:
    section = _section(mods, 3, 11) + "\n" + text[:6000]
    for kw in ["顺周期高Beta", "顺周期低Beta", "逆周期", "穿越周期"]:
        if kw in section:
            return kw, "报告模块 3/11", False
    if re.search(r"高Beta|高 Beta|权益弹性|高弹性", section):
        return "顺周期高Beta（🔍 依表述映射）", "报告模块 3/11", True
    if re.search(r"投资端|权益", section) and re.search(r"波动|弹性", section):
        return "顺周期高Beta（🔍 依投资端表述推断）", "报告模块 3/11", True
    if re.search(r"低Beta|低 Beta|防御属性|弱相关", section):
        return "顺周期低Beta（🔍 依表述映射）", "报告模块 3/11", True
    return "顺周期低Beta（🔍 待复核）", "报告模块 3/11", True


def extract_report(report_path: str | Path) -> dict:
    path = Path(report_path)
    text = path.read_text(encoding="utf-8")
    meta = _frontmatter(text)
    mods = _modules(text)
    industry = meta.get("industry") or path.name.replace("行业-行业分析报告（投资者版）.md", "")
    as_of = meta.get("data_cutoff") or meta.get("generated_at") or date.today().isoformat()

    results: dict[int, tuple[str, str, bool]] = {}
    results[1] = _dim1(meta, mods)
    results[2] = _dim2(mods)
    results[3] = _dim3(mods)
    results[4] = _dim4(mods)
    results[5] = _dim5(mods, text, industry)
    results[6] = _dim6(mods, text)
    results[7] = _dim7(mods, text)
    results[8] = _dim8(mods)
    results[9] = _dim9(mods, text)
    results[10] = _dim10(mods, text)
    results[11] = _dim11(mods, text)
    results[12] = _dim_effect(text, "2008")
    results[13] = _dim_effect(text, "2016")
    results[14] = _dim14(mods, text)

    vector = {str(k): v[0] for k, v in results.items()}
    sources = {str(k): v[1] for k, v in results.items()}
    review = [str(k) for k, v in results.items() if v[2]]
    gaps = []
    if meta.get("schema") != "report-v3":
        gaps.append("报告 metadata 缺少 schema=report-v3；抽取结果仅供起草参考")
    if not mods:
        gaps.append("未识别到 `### N.` 模块标题（报告不符合 report-v3 结构）")
    for k in review:
        gaps.append(f"第{k}维：{sources[str(k)]}（{vector[str(k)]}）")
    return {
        "industry": industry,
        "as_of": as_of,
        "report": str(path).replace("\\", "/"),
        "generated_by": "tools/report_to_14dim.py（草稿，需人工复核标 🔍 的维度）",
        "vector": vector,
        "sources": sources,
        "gaps": gaps,
        "review_required": review,
    }


def _default_out(payload: dict) -> Path:
    day = (payload.get("as_of") or date.today().isoformat()).replace("-", "")[:8]
    industry = payload.get("industry") or "unknown"
    return Path("output/_data") / f"{industry}-14dim-{day}.json"


def print_summary(payload: dict) -> None:
    print(f"行业：{payload['industry']}；报告：{payload['report']}")
    print(f"14 维草稿（{len(payload['vector'])}/14）：")
    for k in range(1, 15):
        flag = "🔍" if str(k) in payload["review_required"] else "✅"
        print(f"  {flag} {k:>2}. {payload['vector'][str(k)]}")


def main() -> int:
    ap = argparse.ArgumentParser(description="从 report-v3 报告抽取 14 维历史对照向量（草稿）")
    ap.add_argument("--report", help="报告 .md 路径")
    ap.add_argument("--out", help="输出 JSON；默认 output/_data/{行业}-14dim-{date}.json")
    ap.add_argument("--json", action="store_true", help="打印完整 JSON")
    ap.add_argument("--strict", action="store_true", help="存在待复核维度时退出码 2")
    ap.add_argument("--compare", help="与已有向量 JSON 对比，打印逐维差异")
    ap.add_argument("--force", action="store_true", help="允许覆盖已存在的 --out 文件")
    ap.add_argument("--selftest", action="store_true", help="对全部已发布报告做抽取自测")
    args = ap.parse_args()

    if args.selftest:
        reports = sorted(Path("output").glob("*行业-行业分析报告（投资者版）.md"))
        if not reports:
            print("SELFTEST FAILED: output/ 下未找到已发布报告")
            return 1
        for r in reports:
            payload = extract_report(r)
            if len(payload["vector"]) != 14 or len(payload["sources"]) != 14:
                print(f"SELFTEST FAILED: {r.name} 维度不完整")
                return 1
            if any(not v.strip() for v in payload["vector"].values()):
                print(f"SELFTEST FAILED: {r.name} 存在空向量值")
                return 1
            if not payload["vector"]["3"].startswith("CR3"):
                print(f"SELFTEST FAILED: {r.name} 第 3 维不符合 CR3 口径：{payload['vector']['3']}")
                return 1
        print(f"SELFTEST PASSED: {len(reports)} 份报告均抽取 14/14 维")
        return 0

    if not args.report:
        ap.error("--report 必填（或使用 --selftest）")
    if not Path(args.report).exists():
        print(f"ERROR: 报告不存在：{args.report}")
        return 2

    payload = extract_report(args.report)
    failures = [k for k in range(1, 15) if not payload["vector"].get(str(k))]
    if failures:
        print(f"ERROR: 维度缺失 {failures}")
        return 1

    if args.compare:
        old = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        old_vec = old.get("vector", {})
        print(f"=== 与 {args.compare} 对比 ===")
        for k in range(1, 15):
            a = old_vec.get(str(k), "")
            b = payload["vector"][str(k)]
            if a == b:
                print(f"  {k:>2}. 相同：{a}")
            else:
                print(f"  {k:>2}. 旧：{a}")
                print(f"      新：{b}（{payload['sources'][str(k)]}）")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_summary(payload)

    out = Path(args.out) if args.out else _default_out(payload)
    if out.exists() and not args.force:
        print(f"\n未写入：{out} 已存在（加 --force 覆盖）")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n已写入：{out}")

    if payload["review_required"]:
        print(f"待复核维度：{','.join(payload['review_required'])}（见 gaps）")
    if args.strict and payload["review_required"]:
        print("STRICT: 存在待复核维度，未通过")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
