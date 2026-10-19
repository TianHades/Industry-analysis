#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ci_check.py — 工程一键回归检查（提交前 / 发布前运行）

覆盖：
  1. Markdown 相对链接
  2. 22 个技能的结构（14 顶层 + 8 历史层：name、RI-A1-A2-E-B）
  3. 校验器回归自测（tools/tests/selftest.py）
  4. 已发布报告机器校验（output/*.md）
  5. 案例关系一致性（tools/check_case_relations.py）
  6. 案例 14 维标准化漂移（tools/normalize_case_vectors.py dry-run 应 0 改动）
   并跑 tools/report_to_14dim.py --selftest（已发布报告 14/14 维）

用法：python tools/ci_check.py
退出码：0=全部通过；1=存在失败项
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable


def run(args: list[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [PY, *args], cwd=str(ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env,
    )


def check_links() -> tuple[bool, str]:
    broken = []
    md_files = [p for p in ROOT.rglob("*.md") if ".git" not in p.parts]
    for f in md_files:
        text = f.read_text(encoding="utf-8")
        for m in re.finditer(r"\]\(([^)\r\n]+)\)", text):
            target = m.group(1).strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1].strip()
            if not target or re.match(r"^(https?:|mailto:|#)", target) or re.match(r"^[A-Za-z]:", target):
                continue
            rel = target.split("#")[0].split("?")[0]
            if not rel:
                continue
            try:
                rel = __import__("urllib.parse", fromlist=["unquote"]).unquote(rel)
            except Exception:
                pass
            if not (f.parent / rel).exists():
                broken.append(f"{f.relative_to(ROOT)} -> {target}")
    ok = not broken
    msg = f"{len(md_files)} 个 md，断链 {len(broken)}"
    if broken:
        msg += "\n" + "\n".join("   " + b for b in broken[:10])
    return ok, msg


def check_skills() -> tuple[bool, str]:
    bad = []
    skills = [p for p in ROOT.glob("*/SKILL.md") if "historical-review" not in p.parts]
    skills += [p for p in (ROOT / "historical-review" / "分析技能层").glob("*/SKILL.md")]
    for p in sorted(skills):
        lines = p.read_text(encoding="utf-8").split("\n")
        if not lines or lines[0].strip() != "---":
            bad.append(f"{p.parent.name}: 无 frontmatter")
            continue
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        fm = "\n".join(lines[1:end or 0])
        m = re.search(r"(?m)^name:\s*(\S+)", fm)
        if not m:
            bad.append(f"{p.parent.name}: 缺 name")
        elif m.group(1) != p.parent.name:
            bad.append(f"{p.parent.name}: name={m.group(1)} 与目录不符")
        for sec in ("R", "I", "A1", "A2", "E", "B"):
            if not re.search(rf"(?m)^## {sec}\b", "\n".join(lines)):
                bad.append(f"{p.parent.name}: 缺 {sec} 段")
    ok = not bad
    return ok, f"{len(skills)} 个技能，问题 {len(bad)}" + ("\n" + "\n".join("   " + b for b in bad[:10]) if bad else "")


def check_reports() -> tuple[bool, str]:
    all_md = sorted((ROOT / "output").glob("*.md"))
    reports = [r for r in all_md if "schema: report-v3" in r.read_text(encoding="utf-8")[:2000]]
    skipped = len(all_md) - len(reports)
    if not reports:
        return True, "无 report-v3 已发布报告（跳过）"
    failures = []
    data_dir = ROOT / "output" / "_data"
    for r in reports:
        args = ["tools/validate_report.py", str(r), "--json"]
        if data_dir.exists():
            args += ["--data-dir", str(data_dir)]
        proc = run(args)
        try:
            result = __import__("json").loads(proc.stdout)
        except Exception:
            failures.append(f"{r.name}: 校验输出不可解析")
            continue
        if not result.get("passed"):
            failures.append(f"{r.name}: P0={len(result.get('p0', []))}")
    ok = not failures
    msg = f"{len(reports)} 份 report-v3 报告（跳过 {skipped} 个非报告文档）"
    if failures:
        msg += "\n" + "\n".join("   " + x for x in failures)
    return ok, msg


def check_cases() -> tuple[bool, str]:
    proc = run(["tools/check_case_relations.py"])
    rel_ok = proc.returncode == 0 and "检查问题：0" in proc.stdout
    proc2 = run(["tools/normalize_case_vectors.py"])
    norm_ok = proc2.returncode == 0 and "本次改动 0 个" in proc2.stdout and "异常案例：0 个" in proc2.stdout
    proc3 = run(["tools/case_match.py", "--query", "tools/examples/白酒-14dim.json", "--top", "1"])
    match_ok = proc3.returncode == 0 and "案例数 22" in proc3.stdout
    proc4 = run(["tools/report_to_14dim.py", "--selftest"])
    extract_ok = proc4.returncode == 0 and "SELFTEST PASSED" in proc4.stdout
    msg = (f"关系 {'OK' if rel_ok else 'FAIL'}；14 维 {'OK' if norm_ok else 'FAIL'}；"
           f"14 维匹配 {'OK' if match_ok else 'FAIL'}；报告→14维 {'OK' if extract_ok else 'FAIL'}")
    return rel_ok and norm_ok and match_ok and extract_ok, msg


def check_selftest() -> tuple[bool, str]:
    proc = run(["tools/tests/selftest.py"])
    ok = proc.returncode == 0 and "SELFTEST PASSED" in proc.stdout
    return ok, "PASS" if ok else (proc.stdout.strip() or proc.stderr.strip())[:500]


def check_skill_relations() -> tuple[bool, str]:
    proc = run(["tools/gen_skill_relations.py"])
    ok = proc.returncode == 0 and "多类型 0 对" in proc.stdout
    if ok:
        return True, "多类型声明 0 对（方案 A）"
    return False, (proc.stdout.strip() or proc.stderr.strip())[:500]


def main() -> int:
    checks = [
        ("链接检查", check_links),
        ("技能结构（22）", check_skills),
        ("技能关系一致性", check_skill_relations),
        ("校验器自测", check_selftest),
        ("已发布报告校验", check_reports),
        ("案例库一致性", check_cases),
    ]
    failed = 0
    print("=== ci_check ===")
    for name, fn in checks:
        try:
            ok, msg = fn()
        except Exception as exc:  # noqa: BLE001
            ok, msg = False, f"异常：{exc}"
        failed += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}")
    print(f"\n结果：{'PASS' if failed == 0 else 'FAIL'}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
