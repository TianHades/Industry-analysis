#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest.py — 校验器回归测试（无需第三方依赖）

运行：python tools/tests/selftest.py
覆盖：合格报告应通过；不合格报告应命中指定 P0；改数应触发交叉核对失败；发布模式产物正确。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "validate_report.py"
FIXTURES = ROOT / "tools" / "tests" / "fixtures"
GOOD = FIXTURES / "good_report.md"
BAD = FIXTURES / "bad_report.md"
DATA = FIXTURES / "data"


def run(args: list[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def p0_codes(proc: subprocess.CompletedProcess) -> set[str]:
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return set()
    return {f["code"] for f in data.get("p0", [])}


def main() -> int:
    failures: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="report_selftest_"))

    # 1) 合格报告必须通过（0），且无 P0
    good = run([str(GOOD), "--data-dir", str(DATA), "--json"])
    if good.returncode != 0:
        failures.append(f"good_report 未通过，P0={sorted(p0_codes(good))}")
    else:
        data = json.loads(good.stdout)
        if not data.get("passed"):
            failures.append("good_report 返回 passed=false")

    # 2) 不合格报告必须失败（1），且命中预期规则
    bad = run([str(BAD), "--json"])
    if bad.returncode != 1:
        failures.append("bad_report 未按预期失败")
    expected = {
        "E-META-08", "E-STRUCT-02", "E-STRUCT-06", "E-STRUCT-INDEX",
        "E-MARK-01", "E-MARK-02", "E-VAL-02", "E-VAL-05", "E-VAL-06",
        "E-LIE-01", "E-MATH-GROWTH",
    }
    missing = expected - p0_codes(bad)
    if missing:
        failures.append(f"bad_report 未命中预期规则：{sorted(missing)}")

    # 3) 数值被篡改必须触发交叉核对失败
    tampered = tmp / "good_report.md"
    text = GOOD.read_text(encoding="utf-8").replace("1500.00 | 25.5", "1500.00 | 30.0")
    tampered.write_text(text, encoding="utf-8")
    tam = run([str(tampered), "--data-dir", str(DATA), "--json"])
    if "E-VAL-CROSS" not in p0_codes(tam):
        failures.append("篡改估值后未触发 E-VAL-CROSS")

    # 4) 发布模式：通过 → 生成报告 + check.json，并注入"自动校验"行
    pub = run([str(GOOD), "--data-dir", str(DATA), "--publish-dir", str(tmp)])
    published = tmp / GOOD.name
    check_json = tmp / (GOOD.stem + ".check.json")
    if pub.returncode != 0 or not published.exists() or not check_json.exists():
        failures.append("发布模式未生成报告/check.json")
    else:
        published_text = published.read_text(encoding="utf-8")
        if "自动校验：通过" not in published_text:
            failures.append("发布版缺少“自动校验：通过”行")
        check = json.loads(check_json.read_text(encoding="utf-8"))
        if not check.get("passed"):
            failures.append("check.json 未标记 passed")

    shutil.rmtree(tmp, ignore_errors=True)
    if failures:
        print("SELFTEST FAILED")
        for f in failures:
            print(" -", f)
        return 1
    print("SELFTEST PASSED: good_report 通过；bad_report 命中全部预期规则；篡改可被发现；发布产物正确。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
