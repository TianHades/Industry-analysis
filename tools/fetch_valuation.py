#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_valuation.py — 行业核心标的实时估值取数（腾讯行情为主，东财/百度兜底）

用法（需 requests；akshare 仅作兜底）：
  python tools/fetch_valuation.py --industry 白酒 --targets tools/targets/白酒.json --date 2026-10-16
  python tools/fetch_valuation.py --industry 电力 --codes 600900:长江电力,600406:国电南瑞

输出：output/_data/{industry}-valuation-{YYYYMMDD}.json（schema=valuation-v1）
报告估值表必须引用该文件，并由 tools/validate_report.py 逐值交叉核对。

数据源策略（自动降级，JSON 中记录实际来源）：
  1) 腾讯行情 qt.gtimg.cn（批量、稳定；含 最新价/涨跌幅/成交额/PE-TTM/PB/总市值/数据时间）
  2) 东财 push2 quote（兜底；PE 为动态口径，会标注）
  3) AkShare 百度源 stock_zh_valuation_baidu（总市值/市净率兜底）
环境：脚本已设 NO_PROXY='*'；数据日期优先取行情返回的时间戳（周末=最后交易日）。

退出码：0=成功（≥1 条行情）；2=参数/依赖/全部失败
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTDIR = REPO_ROOT / "output" / "_data"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Referer": "https://finance.sina.com.cn",
}


def parse_targets(args) -> list[dict]:
    targets: list[dict] = []
    if args.targets:
        data = json.loads(Path(args.targets).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("targets", [])
        for it in data:
            targets.append({
                "code": str(it.get("code", "")).strip().zfill(6),
                "name": str(it.get("name", "")).strip(),
                "segment": str(it.get("segment", "")).strip(),
            })
    if args.codes:
        for part in args.codes.split(","):
            fields = [x.strip() for x in part.split(":")]
            if not fields or not fields[0]:
                continue
            targets.append({
                "code": fields[0].zfill(6),
                "name": fields[1] if len(fields) > 1 else "",
                "segment": fields[2] if len(fields) > 2 else "",
            })
    seen, uniq = set(), []
    for t in targets:
        if t["code"] and t["code"] not in seen:
            seen.add(t["code"])
            uniq.append(t)
    return uniq


def prefixed(code: str) -> str:
    if code.startswith("6"):
        return "sh" + code
    if code.startswith(("4", "8")):
        return "bj" + code
    return "sz" + code


def to_float(v):
    try:
        if v is None:
            return None
        s = str(v).strip().replace(",", "").replace("−", "-")
        if s in {"", "-", "--", "None", "nan", "NaN"}:
            return None
        return float(s)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ sources
def fetch_tencent(codes: list[str], errors: list[str]) -> tuple[dict, str | None]:
    """腾讯行情：一次批量取全部。返回 {code: {...}}, data_date"""
    import requests

    out: dict = {}
    data_date = None
    try:
        q = ",".join(prefixed(c) for c in codes)
        r = requests.get(f"https://qt.gtimg.cn/q={q}", headers=UA, timeout=15)
        r.encoding = "gbk"
        for line in r.text.splitlines():
            m = re.search(r'v_(\w+)="(.*)";?', line)
            if not m:
                continue
            f = m.group(2).split("~")
            if len(f) < 47 or not f[2]:
                continue
            code = f[2].zfill(6)
            ts = f[30] if len(f) > 30 else ""
            if len(ts) >= 8 and data_date is None:
                data_date = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}"
            out[code] = {
                "price": to_float(f[3]),
                "chg_pct": to_float(f[32]),
                "amount": to_float(f[37]) if len(f) > 37 else None,
                "pe_ttm": to_float(f[39]) if len(f) > 39 else None,
                "mktcap": to_float(f[45]) if len(f) > 45 else None,
                "pb": to_float(f[46]) if len(f) > 46 else None,
                "div_yield": None,
                "quote_time": ts,
                "source": "tencent:qt.gtimg.cn",
            }
    except Exception as exc:
        errors.append(f"tencent: {exc}")
    return out, data_date


def fetch_eastmoney(code: str, errors: list[str]) -> dict | None:
    """东财 push2 quote 兜底（PE 为动态口径，字段 f162/100）。"""
    import requests

    try:
        secid = ("1." if code.startswith("6") else "0.") + code
        params = {"secid": secid, "fields": "f43,f57,f58,f116,f162,f167"}
        r = requests.get("https://push2.eastmoney.com/api/qt/stock/get",
                         params=params, headers=UA, timeout=15)
        d = (r.json() or {}).get("data") or {}
        if not d:
            return None
        price = to_float(d.get("f43"))
        if price is not None and price > 10000:
            price = price / 100.0
        return {
            "price": price,
            "chg_pct": None,
            "amount": None,
            "pe_ttm": (to_float(d.get("f162")) / 100.0) if to_float(d.get("f162")) else None,
            "pb": (to_float(d.get("f167")) / 100.0) if to_float(d.get("f167")) else None,
            "mktcap": (to_float(d.get("f116")) / 1e8) if to_float(d.get("f116")) else None,
            "div_yield": None,
            "quote_time": "",
            "source": "eastmoney:push2(PE为动态口径)",
        }
    except Exception as exc:
        errors.append(f"eastmoney {code}: {exc}")
        return None


def fetch_baidu(code: str, errors: list[str]) -> dict:
    """AkShare 百度源兜底：总市值/市净率。"""
    out: dict = {}
    try:
        import akshare as ak
    except Exception as exc:
        errors.append(f"baidu: akshare 不可用（{exc}）")
        return out
    for indicator, key in (("总市值", "mktcap"), ("市净率", "pb")):
        try:
            df = ak.stock_zh_valuation_baidu(symbol=code, indicator=indicator, period="近一年")
            if df is not None and len(df) > 0:
                out[key] = to_float(df.iloc[-1].get("value", df.iloc[-1].iloc[-1]))
        except Exception as exc:
            errors.append(f"baidu {code} {indicator}: {exc}")
    if out:
        out["source"] = "baidu:akshare"
    return out


# ------------------------------------------------------------------ main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="行业估值取数（腾讯行情为主，东财/百度兜底）")
    parser.add_argument("--industry", required=True, help="行业名称（输出文件名与 JSON 字段）")
    parser.add_argument("--targets", help="标的 JSON 文件：[{code,name,segment}]")
    parser.add_argument("--codes", help="逗号分隔 code:name[:segment]")
    parser.add_argument("--outdir", default=str(DEFAULT_OUTDIR), help="输出目录（默认 output/_data）")
    parser.add_argument("--date", help="数据日期 YYYY-MM-DD（默认取行情时间戳；周末为最后交易日）")
    args = parser.parse_args(argv)

    targets = parse_targets(args)
    if not targets:
        print("[ERROR] 未提供标的：用 --targets 或 --codes", file=sys.stderr)
        return 2
    os.environ["NO_PROXY"] = "*"
    errors: list[str] = []

    # 1) 腾讯批量
    quotes, data_date = fetch_tencent([t["code"] for t in targets], errors)
    # 2) 缺失字段的标的用东财/百度兜底
    for t in targets:
        code = t["code"]
        item = quotes.get(code)
        if item is None or item.get("pe_ttm") is None or item.get("pb") is None:
            em = fetch_eastmoney(code, errors)
            if em:
                if item is None:
                    quotes[code] = em
                    item = em
                else:
                    for k in ("pe_ttm", "pb", "mktcap", "price"):
                        if item.get(k) is None and em.get(k) is not None:
                            item[k] = em[k]
                    item["source"] = item.get("source", "") + "+" + em["source"]
        item = quotes.get(code)
        if item is not None and item.get("pb") is None:
            bd = fetch_baidu(code, errors)
            for k in ("pb", "mktcap"):
                if item.get(k) is None and bd.get(k) is not None:
                    item[k] = bd[k]
            if bd:
                item["source"] = item.get("source", "") + "+" + bd["source"]

    date_str = args.date or data_date or datetime.now().strftime("%Y-%m-%d")
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"[ERROR] --date 格式应为 YYYY-MM-DD：{date_str}", file=sys.stderr)
        return 2

    items = []
    for t in targets:
        q = quotes.get(t["code"], {})
        items.append({
            "code": t["code"],
            "name": t["name"],
            "segment": t["segment"],
            "price": q.get("price"),
            "chg_pct": q.get("chg_pct"),
            "amount": q.get("amount"),
            "pe_ttm": q.get("pe_ttm"),
            "pb": q.get("pb"),
            "mktcap": q.get("mktcap"),
            "div_yield": q.get("div_yield"),
            "quote_time": q.get("quote_time"),
            "sources": [s for s in str(q.get("source", "")).split("+") if s],
        })
        flag = "OK " if q.get("price") is not None else "MISS"
        print(f"[{flag}] {t['code']} {t['name']:<8} price={q.get('price')} "
              f"PE={q.get('pe_ttm')} PB={q.get('pb')} mktcap={q.get('mktcap')}")

    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = REPO_ROOT / outdir
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f"{args.industry}-valuation-{date_str.replace('-', '')}.json"
    payload = {
        "schema": "valuation-v1",
        "industry": args.industry,
        "fetched_at": date_str,
        "fetched_at_iso": datetime.now().astimezone().isoformat(timespec="seconds"),
        "quote_data_date": data_date,
        "currency": "CNY",
        "source": "tencent:qt.gtimg.cn（主）+ eastmoney:push2 / baidu:akshare（兜底）",
        "items": items,
        "errors": errors,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ok = sum(1 for it in items if it["price"] is not None)
    print(f"\n已写入：{out_path}")
    print(f"行情 {ok}/{len(items)} 条，错误 {len(errors)} 条")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
