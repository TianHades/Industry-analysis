# tools/ — 报告产出工具

本目录承载「报告契约 v3」的两项机器化能力：**取数**与**校验**。

## 1. 取数：fetch_valuation.py

```bash
# 用装有 akshare 的 Python（本机为系统 Python 3.10）
python tools/fetch_valuation.py --industry 白酒 --targets tools/targets/白酒.json --date 2026-10-16
```

- 输出 `output/_data/{industry}-valuation-{YYYYMMDD}.json`（schema=`valuation-v1`）。
- 数据日期默认取**行情接口返回的时间戳**（周末/节假日即最后交易日）；`--date` 传入的日期若与行情时间戳不一致，脚本会报错退出，防止把盘中/最新价标成历史日期（确需覆盖加 `--allow-date-mismatch`）。
- 依赖：`pip install -r tools/requirements.txt`；必须 `NO_PROXY='*'`（脚本已内置），使用腾讯行情为主、东财/百度兜底。
- 报告估值表必须引用该 JSON；`validate_report.py` 会逐值比对（防手抄/换算错）。

## 2. 校验：validate_report.py

```bash
python tools/validate_report.py "output/_drafts/白酒行业-行业分析报告（投资者版）.md" \
    --data-dir output/_data --publish-dir output
```

- 规则来源：`reference/output-template.md`（v3.0）。
- 退出码：`0` 通过（可含 P1 警告）；`1` 存在 P0 失败；`2` 用法错误。
- 通过且指定 `--publish-dir` 时：复制到 `output/`，并写 `{报告名}.check.json`，同时向「数据时效性与质量说明」注入“自动校验：通过”行。
- 失败时按 P0 逐条修复；P1 警告须在质量说明中回应或修复。

## 3. 回归测试

```bash
python tools/tests/selftest.py
```

覆盖：合格报告通过；不合格报告命中全部预期规则；篡改估值触发交叉核对失败；发布产物正确。

## 4. 报告目录约定

| 目录 | 内容 | 是否入库 |
|------|------|----------|
| `output/_drafts/` | 草稿（未过校验） | 否（gitignore） |
| `output/_data/` | 取数 JSON 与事实 JSON（数据追溯用） | 否（gitignore） |
| `output/*.md` + `*.check.json` | 已发布报告与校验结果 | 是 |

## 5. 环境说明

- 取数依赖 akshare：本机系统 Python 3.10 已安装；DSH 内置 Python 无 akshare。
- 校验器仅用标准库，任意 Python 3.8+ 可跑。

## 6. 跨行业验证记录

| 行业 | 阶段 / 类型 | 验证路径 | 暴露并已修复的问题 |
|------|-------------|----------|--------------------|
| 白酒 | 成熟期 / 消费 | 首次端到端：取数 → 草稿 → 校验 → 发布 | 取数源以腾讯行情为主；TAM/SAM/SOM 口径按契约修正 |
| 保险 | 成长期后段 / 金融 | 非制造业（模块 10“不适用+理由”）、成长期模块 14 可选、金融 PE/PB 口径、午间快照 | ① 校验器在多行业取数文件共存时会按文件名盲选（已改为按 industry + fetched_at 选择）；② 取数器可能把盘中价标成历史日期（已加 `--date` 一致性守卫）；③ 盘中快照表述（契约已补规则） |

> 后续行业验证时，优先检查：阶段分支（模块 10/14）、估值口径（非 PE 行业）、数据快照时点、跨行业数据文件选择。
