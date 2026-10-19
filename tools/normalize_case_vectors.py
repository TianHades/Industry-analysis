#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""normalize_case_vectors.py — 历史案例库 14 维特征向量标准化工具

问题：
  - 3 个案例把特征向量扩成 16 维（多出 15/16 维“补充维度”）；
  - 6 个案例把“本案例的典型值”拆成两列（两个时点），无法做同维相似度计算。
处理：
  - 16 维：15/16 维移出表格，转为“补充维度（不计入 14 维）”说明；
  - 双列时点：保留第一列为基准值，第二列并入备注（前缀【阶段变体：时点】）；
  - 统一表头为 14 维单值三列格式。
用法：
  python tools/normalize_case_vectors.py            # dry-run
  python tools/normalize_case_vectors.py --apply    # 写入
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASE_DIR = ROOT / "historical-review" / "行业案例档案库"
STANDARD_HEADER = "| 特征维度 | 本案例的典型值 | 备注说明 |"
STANDARD_SEP = "|----------|-------------|---------|"
SINGLE_SELECT_DIMS = {6, 7, 8, 9, 11, 12, 13, 14}


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def join_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def paren_label(text: str, fallback: str) -> str:
    m = re.search(r"[（(]([^（）()]{2,30})[）)]", text)
    return m.group(1).strip() if m else fallback


def find_table(lines: list[str]):
    for i, line in enumerate(lines):
        if re.match(r"^\|\s*\*\*1\.", line):
            return i - 2, i - 1, i  # header, separator, first data row
    return None


def table_end(lines: list[str], first_row: int) -> int:
    j = first_row
    while j < len(lines) and lines[j].strip().startswith("|"):
        j += 1
    return j


def normalize(path: Path, apply: bool, single_select: bool = False) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    found = find_table(lines)
    if not found:
        return {"file": path.name, "status": "no-table"}
    h, s, r = found
    end = table_end(lines, r)
    header = split_row(lines[h])
    rows = [(i, split_row(lines[i])) for i in range(r, end)]
    changes = []
    supplement: list[str] = []

    # 1) 双列时点 → 单值基准 + 备注阶段变体
    if len(header) >= 4:
        label1 = paren_label(header[1], "基准时点")
        label2 = paren_label(header[2], "第二时点")
        new_header = f"| 特征维度 | 本案例的典型值（基准） | 备注说明（含阶段变体） |"
        new_rows = []
        for i, cells in rows:
            if len(cells) >= 4:
                dim, v1, v2, remark = cells[0], cells[1], cells[2], cells[3]
                empty = {"", "—", "-", "–", "无", "N/A", "不适用"}
                if v1 in empty and v2 not in empty:
                    new_remark = f"【基准时点：{label2}】" + (remark if remark else "")
                    new_rows.append((i, [dim, v2, new_remark]))
                elif v1 in empty:
                    new_rows.append((i, [dim, v1, remark]))
                else:
                    prefix = f"【阶段变体：{label2}】{v2}" if v2 not in empty else ""
                    new_remark = (prefix + ("；" if prefix and remark else "") + remark) if (prefix or remark) else ""
                    new_rows.append((i, [dim, v1, new_remark]))
            else:
                new_rows.append((i, cells))
        header_line = new_header
        sep_line = STANDARD_SEP
        changes.append(f"双列时点合并为单值（基准 {label1}，变体 {label2}）")
    else:
        header_line = STANDARD_HEADER
        sep_line = STANDARD_SEP
        new_rows = rows

    # 2) 15/16 补充维度 → 表格外说明
    kept = []
    for i, cells in new_rows:
        m = re.match(r"^\|\s*\*\*(\d+)\.", lines[i])
        num = int(m.group(1)) if m else 0
        if num >= 15:
            dim = re.sub(r"^\*\*(\d+)\.\s*", r"\1. ", cells[0].replace("**", "").strip())
            value = cells[1] if len(cells) > 1 else ""
            remark = cells[2] if len(cells) > 2 else ""
            supplement.append(f"- {dim}：{value}" + (f"（{remark}）" if remark else ""))
        else:
            kept.append((i, cells))
    if supplement:
        changes.append(f"15/16 维移出表格（{len(supplement)} 条补充维度）")

    # 3) 单值化：单值维度出现多个 [x] 时，保留第一个为主选，其余写入备注
    if single_select:
        converted = []
        for i, cells in kept:
            m = re.match(r"^\|\s*\*\*(\d+)\.", lines[i])
            dim = int(m.group(1)) if m else 0
            if dim in SINGLE_SELECT_DIMS and len(cells) >= 3:
                options = re.findall(r"(\[x\]|\[ \])\s*([^\[\]]+)", cells[1])
                checked = [text.strip() for mark, text in options if mark == "[x]"]
                if len(checked) > 1:
                    first = checked[0]
                    others = "、".join(checked[1:])
                    new_value = f"[x] {first}"
                    note_prefix = f"该维另标注：{others}"
                    cells = [cells[0], new_value,
                             note_prefix + ("；" + cells[2] if cells[2] else "")]
                    changes.append(f"第{dim}维单值化（主选：{first}）")
            converted.append((i, cells))
        kept = converted

    if not changes and len(kept) == 14:
        return {"file": path.name, "status": "ok"}

    # 重写表格区域
    new_block = [header_line, sep_line] + [join_row(c) for _, c in kept]
    if supplement:
        new_block += ["", "**补充维度（不计入 14 维相似度计算，仅供阅读）**："] + supplement
    lines2 = lines[:h] + new_block + lines[end:]
    if apply:
        path.write_text("\n".join(lines2), encoding="utf-8")
    return {"file": path.name, "status": "updated" if apply else "would-update",
            "changes": changes, "rows": len(kept)}


def check_single_select(path: Path) -> list[str]:
    """检查 6/7/8/9/11/12/13/14 维是否存在 [x] 多选或未选；检查维 3 是否为 CR3 严格口径。"""
    issues = []
    for i, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        m = re.match(r"^\|\s*\*\*(\d+)\.", line)
        if not m:
            continue
        dim = int(m.group(1))
        cells = split_row(line)
        if dim == 3:
            if len(cells) < 2:
                continue
            value = cells[1]
            if "未获取" in value:
                continue
            cm = re.match(
                r"^CR3\s*(?:约|≈|~)?\s*(?:[<>])?\s*(\d+(?:\.\d+)?)\s*%"
                r"(?:\s*[-–~]\s*(\d+(?:\.\d+)?)\s*%)?", value)
            if not cm:
                issues.append(f"  L{i} 第3维缺少合法 CR3 数值")
            elif "%" in value[cm.end():]:
                issues.append(f"  L{i} 第3维 CR3 数值不唯一（子行业差异应移至备注）")
            continue
        if dim not in SINGLE_SELECT_DIMS:
            continue
        if len(cells) < 2:
            continue
        value = cells[1]
        n = value.count("[x]")
        if n != 1:
            issues.append(f"  L{i} 第{m.group(1)}维 [x] 数量={n}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="案例库 14 维特征向量标准化")
    parser.add_argument("--apply", action="store_true", help="写入文件（默认 dry-run）")
    parser.add_argument("--single-select", action="store_true",
                        help="把单值维度的多选 [x] 收敛为主选（第一个），其余写入备注")
    args = parser.parse_args()
    cases = sorted(CASE_DIR.rglob("*_完整案例.md"))
    updated = 0
    for c in cases:
        res = normalize(c, args.apply, args.single_select)
        if res["status"] in {"updated", "would-update"}:
            updated += 1
            print(f"[{res['status']}] {c.name}: {'；'.join(res['changes'])}")
    print(f"\n共 {len(cases)} 个案例，本次改动 {updated} 个（{'已写入' if args.apply else 'dry-run'}）")
    print("\n单值维度检查（[x] 数量 != 1）：")
    bad = 0
    for c in cases:
        issues = check_single_select(c)
        if issues:
            bad += 1
            print(f"- {c.name}")
            print("\n".join(issues))
    print(f"异常案例：{bad} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
