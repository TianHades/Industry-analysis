# tools/ — 报告产出工具

本目录承载「报告契约 v3」的两项机器化能力：**取数**与**校验**。

## 1. 取数：fetch_valuation.py

```bash
# 用装有 akshare 的 Python（本机为系统 Python 3.10）；默认取行情返回的日期
python tools/fetch_valuation.py --industry 白酒 --targets tools/targets/白酒.json

# 如需固定历史日期：--date 2026-10-16（仅当行情源返回的日期与之一致时才允许）
```

- 输出 `output/_data/{industry}-valuation-{YYYYMMDD}.json`（schema=`valuation-v1`）。
- 数据日期默认取**行情接口返回的时间戳**（周末/节假日即最后交易日）；`--date` 与行情时间戳不一致、或行情源未返回时间戳时，脚本会报错退出，防止把盘中/最新价标成历史日期（确需覆盖加 `--allow-date-mismatch`）。
- PE/PB 非正数（亏损/资不抵债）会归一为 `null`，原值保留在 `pe_ttm_raw` / `pb_raw`；报告估值表应标"亏损"或"—"并说明，不得手写 0/负数。
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
- 关键规则补充：估值表 PE/PB 非正数应标"亏损"/"—"（E-VAL-10）；正文"合计总市值"须与估值表求和一致（W-MATH-MCAP）；批量/草稿校验建议不带 `--publish-dir`（发布是独立步骤）。

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
| 电力 | 成熟期 / 公用事业 | 重资产公用事业路径：装机/利用小时/容量电价、7 标的估值、盘中快照 | PE 中位数误报（“PE 中位数、7 家总市值”被解析为 7）——校验器已收紧为“中位数…倍”才参与复算 |

> 后续行业验证时，优先检查：阶段分支（模块 10/14）、估值口径（非 PE 行业）、数据快照时点、跨行业数据文件选择。

## 7. 案例库维护工具

| 脚本 | 作用 |
|------|------|
| `tools/normalize_case_vectors.py` | 14 维特征向量标准化：16 维→14 维（补充维度移出）、双列时点→单值基准+阶段变体、单值维度多选收敛；`--apply --single-select` 写入 |
| `tools/check_case_relations.py` | 案例关系一致性检查/修复/关系图生成：引用缺失、单向关系、类型冲突；`--fix` 补全并统一，`--write-graph` 重新生成 `案例关联关系图.md`（Mermaid + 全部案例关联一览） |
| `tools/case_match.py` | 用 14 维向量做“当前行业 ↔ 历史案例”匹配（HBS 半自动初筛）：`--query tools/examples/电力-14dim.json --top 5`；可加 `--json-out` 保存明细。示例向量：`tools/examples/白酒-14dim.json`、`tools/examples/电力-14dim.json`、`tools/examples/保险-14dim.json`（可比维度 <10 时应走判停分支） |

> 约定：案例 frontmatter 的 `name:` 即 slug；3 份对比示范为外部目标（不入案例关系图）。当前状态：22 个案例 14 维单值、关系检查 0 问题。示例查询向量与实测报告：`tools/examples/白酒-14dim.json`、`output/历史对照-白酒-20261019.md`。

## 8. 技能关系与一键回归

| 脚本 | 作用 |
|------|------|
| `tools/gen_skill_relations.py` | 从 14 个技能 frontmatter 生成关系元数据清单（42 条声明 → 33 对，多类型 0/双向 9）；`--write` 更新 INDEX 自动段；`--fix` 按方案 A 幂等清理多类型声明（存在多类型时默认退出码 1） |
| `tools/ci_check.py` | 一键回归：链接检查、22 技能结构、技能关系一致性、校验器自测、已发布报告校验、案例库一致性；提交前运行 |

```bash
python tools/ci_check.py     # 期望输出：结果：PASS
```

## 9. 取数标的模板（tools/targets/）

| 文件 | 覆盖 |
|------|------|
| `白酒.json` | 贵州茅台/五粮液/泸州老窖/山西汾酒/洋河/古井 |
| `保险.json` | 中国平安/中国人寿/中国太保/新华保险/中国人保 |
| `电力.json` | 长江电力/国电南瑞/华能国际/中国核电/三峡能源/国投电力/华电国际 |
| `银行.json` | 招商/工商/建设/农业/中国银行/宁波/兴业 |

> 新增行业时复制一份 `targets/{行业}.json`；行业名需与报告 metadata `industry` 一致（校验器据此选择取数 JSON）。
