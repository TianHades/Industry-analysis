# 行业快速分析 Skill

基于《如何快速了解一个行业》（肖璟著）方法论构建的 Claude Code 技能库，通过模块化、系统化的框架输出身份导向的行业分析报告。

> **默认配置**：未说明身份时按 **投资者版** 输出；叙事默认 **大老板**（R→S→C→Q，结论前置）。明确说"我是创业者/求职者/学生/路人"或指定受众时切换。

## 架构特点

本技能库采用 **模块化微核架构**：13 个独立子技能 + 1 个总成技能 + 5 个共享参考文件，通过 `industry-analysis-orchestrator` 统一调度；另含 2026-10-18 收编的 `historical-review/` 历史对照层（8 个技能 + 22 个案例档案，半自动调用）与 `tools/` 报告流水线（契约校验 + 估值取数）。

> 📖 **第一次接触本工程？** 先读 [WALKTHROUGH.md](WALKTHROUGH.md)——全工程带读 + 一键验收记录（约 10 分钟读完）。

每个子技能遵循 **RI-A1-A2-E-B** 六段结构：
- **R**（原文引用）：书中关键段落
- **I**（方法论骨架）：核心框架的精炼表达
- **A1**（书中的应用）：2-3个书中案例
- **A2**（触发场景）：何时激活 + 语言信号
- **E**（可执行步骤）：3-5步 + 完成标准 + 判停条件
- **B**（边界）：不适用场景 / 失败模式 / 作者盲点 / 邻近方法区分

## 快速开始

### 使用

直接说"帮我分析XX行业"（默认投资者版 / 大老板受众），orchestrator 会自动调度全部子技能，完成：

```
身份确认 → 行业定义 → 生命周期定位 → 假设建立 → 时空对标 →
按阶段加权分析 → 估值判断 → 外部扫描 → 景气追踪 → 报告输出
```

### 独立调用子技能

每个子技能也可独立调用，例如：
- "用护城河分析分析XX行业"
- "帮我判断XX行业处于产业生命周期的哪个阶段"
- "帮我做XX行业的PEST分析"

## 技能全景

| 分类 | 技能 | 说明 |
|------|------|------|
| 🚀 总成 | `industry-analysis-orchestrator` | 统一入口，一键调度 |
| 🧠 元能力 | `hypothesis-driven-research` | 金字塔原理/SCQR/DIKW/MECE |
| 🧠 元能力 | `spatial-temporal-benchmarking` | 时间/空间/终局对标 |
| ⚓ 核心锚 | `industry-lifecycle-anchoring` | 渗透率判断阶段 |
| 📊 基本面 | `business-model-feasibility` | 商业模式可行性（导入期） |
| 📊 基本面 | `market-size-estimation` | TAM/SAM/SOM（成长期） |
| 📊 基本面 | `moat-analysis` | 五类护城河（成熟期） |
| 📊 基本面 | `competitive-landscape-analysis` | CRn+U型演变（成熟期） |
| 📊 基本面 | `capacity-cycle-judgment` | 产能+库存周期（周期场景） |
| 💰 估值 | `lifecycle-valuation-map` | 阶段匹配估值方法 |
| 🌍 外部 | `external-force-scanner` | PEST+经济框架 |
| 📈 验证 | `prosperity-tracking-system` | 高频指标验证 |
| 📝 输入输出 | `industry-definition` | 行业定义与产业链 |
| 📝 输入输出 | `identity-oriented-output` | 身份定制+叙事适配 |

## 共享参考文件

| 文件 | 内容 |
|------|------|
| `reference/output-template.md` | **报告契约 v3.0**：14 固定模块、报告头 metadata、估值表与校验规则 |
| `reference/search-specs.md` | 搜索工具链、Google操作符、按阶段定向搜索指引 |
| `reference/data-annotation-standards.md` | 符号体系、数据标注格式、时效校验规则、冲突仲裁规则 |
| `reference/methodology-catalog.md` | 方法速查卡片、核心概念定义 |
| `reference/如何接入StockReview做历史对照.md` | 报告 → historical-review 层的 14 维交接契约与自检 |
| `BOOK_OVERVIEW.md` | 对原著的系统批判（作者局限、立场盲点、未证明假设） |
| `INDEX.md` | 技能全景图、关系图、学习路径 |

## 历史对照层（historical-review/）

2026-10-18 收编原独立工程 StockReview 为本工程的 `historical-review/` 层，用于报告产出后的"像→不像→像"历史对照。**调用方式维持半自动**：orchestrator 不自动调用该层，需要时由用户显式触发。

| 组成 | 内容 |
|------|------|
| 分析技能层 | 8 个历史对照技能（核心 `historical-stage-benchmarking`），见 [historical-review/分析技能层/INDEX.md](historical-review/分析技能层/INDEX.md) |
| 案例数据层 | 22 个行业完整档案（11 周期制造型 + 4 技术迭代型 + 7 品牌消费型），见 [historical-review/行业案例档案库/README.md](historical-review/行业案例档案库/README.md) |
| 对照演示 | 3 份完整对比示范 + 统一框架 [行业生命周期全景框架_蒸馏笔记.md](historical-review/行业生命周期全景框架_蒸馏笔记.md) |
| 交接契约 | 报告 → 对照的 14 维特征向量映射表，见 [reference/如何接入StockReview做历史对照.md](reference/如何接入StockReview做历史对照.md) |

> 8 个历史对照技能已注册进 `.claude/settings.json`（连同顶层 14 个技能，共 22 个可被发现），但不在 orchestrator 流水线内自动执行。

## 报告流水线工具（tools/）

| 工具 | 作用 |
|------|------|
| [tools/fetch_valuation.py](tools/fetch_valuation.py) | 估值取数（腾讯行情为主，东财/百度兜底）→ `output/_data/*-valuation-*.json` |
| [tools/validate_report.py](tools/validate_report.py) | 报告契约 v3.0 机器校验（P0 门禁）→ 通过后发布 + `*.check.json` |
| [tools/report_to_14dim.py](tools/report_to_14dim.py) | 从 report-v3 报告自动抽取 14 维向量草稿（🔍 维度人工复核） |
| [tools/tests/selftest.py](tools/tests/selftest.py) | 校验器回归测试（合格/不合格/篡改/发布四种场景） |

> 详细用法见 [tools/README.md](tools/README.md)。

## 报告产出（v3.0 流水线）

旧版 8 份行业分析报告已于 2026-10-18 整体移除（经审查存在数据核算与模板偏差，不逐条勘误）；备份曾置于 `_archive\20261018_reports_backup`，已于 2026-10-19 清理。

新报告按 **报告契约 v3.0** 生成，流程如下：

```bash
# 1) 取数（估值，输出 output/_data/{行业}-valuation-{YYYYMMDD}.json）
python tools/fetch_valuation.py --industry 白酒 --targets tools/targets/白酒.json --date 2026-10-16

# 2) 写草稿（output/_drafts/），报告头写全 YAML metadata（见 reference/output-template.md）

# 3) 机器校验（P0 必须为 0）
python tools/validate_report.py "output/_drafts/白酒行业-行业分析报告（投资者版）.md" \
    --data-dir output/_data --publish-dir output

# 4) 产物：output/{报告}.md + output/{报告}.check.json（自动校验行由脚本注入）
```

- 目录约定：`output/_drafts/`（草稿，不入库）、`output/_data/`（取数 JSON，不入库）、`output/*.md + *.check.json`（发布版，入库）。
- 校验器回归测试：`python tools/tests/selftest.py`。
- 提交前一键回归：`python tools/ci_check.py`（链接/22 技能结构/技能关系一致性/校验器自测/已发布报告/案例一致性含报告→14维）。
- 工具说明见 [tools/README.md](tools/README.md)。
- **已发布报告（均通过 P0=0/P1=0 校验）**：
  - [白酒行业（投资者版）](output/白酒行业-行业分析报告（投资者版）.md)（2026-10-18）
  - [保险行业（投资者版）](output/保险行业-行业分析报告（投资者版）.md)（2026-10-19，金融/成长期分支）
  - [电力行业（投资者版）](output/电力行业-行业分析报告（投资者版）.md)（2026-10-19，公用事业/盘中快照）
- **历史对照实测（半自动，orchestrator 不自动调用）**：
  - [白酒行业历史对照（2026-10-19）](output/历史对照-白酒-20261019.md)
  - [电力行业历史对照（2026-10-19）](output/历史对照-电力-20261019.md)
  - [保险行业历史对照（2026-10-19，判停：无好对标）](output/历史对照-保险-20261019.md)

## 方法论来源

基于《如何快速了解一个行业》（肖璟著，2025年人民邮电出版社）的系统化研究框架。

## 免责声明

本 Skill 生成的内容基于公开信息整理分析，仅供行业研究参考，不构成任何投资建议。投资有风险，决策需谨慎。
