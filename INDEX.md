---
title: "行业快速分析技能库索引"
author: 肖璟（原著）+ AI Industry Analyst（技能化）
main_idea: |
  用产业生命周期框架为锚，结合金字塔原理/SCQR/假设驱动法等研究元能力，
  将行业分析拆解为可行性、规模性、防守性、盈利性四个基本面维度，
  叠加估值映射、外部驱动力扫描和景气度追踪，输出身份导向的行业分析报告。
total_skills: 14
generated_at: 2026-10-18
report_contract: v3.0（14 固定模块 + 机器校验门禁）
---

# 《如何快速了解一个行业》技能库

> 基于肖璟《如何快速了解一个行业》方法论，构建的模块化行业研究技能库。
> 采用 RI-A1-A2-E-B 六段结构，每个子技能可独立调用，也可通过 orchestrator 一键调度。

---

## 技能全景

### 🚀 总成入口（1 个）— 从这里开始

| Skill | Slug | 一句话 |
|-------|------|--------|
| **行业分析总成** | `industry-analysis-orchestrator` | 🌟 **统一入口**：输入行业名，自动调度全部子技能，输出结构化分析报告 |

> 💡 **使用方式**: 直接说"帮我分析XX行业"，orchestrator 会按产业生命周期流水线依次调用身份确认→定义→定位→假设→对标→加权分析→估值→外部→景气度→报告输出。

### 元能力（2 个）

| Skill | Slug | 一句话 |
|-------|------|--------|
| 假设驱动研究法 | `hypothesis-driven-research` | "怎么做研究"的底层方法论——金字塔原理/SCQR/DIKW/MECE |
| 时空对标推理法 | `spatial-temporal-benchmarking` | 用过去和他处理解当下和此处——时间对标/空间对标/终局对标 |

### 核心锚定（1 个）

| Skill | Slug | 一句话 |
|-------|------|--------|
| 产业生命周期定位术 | `industry-lifecycle-anchoring` | 用渗透率判断行业阶段，决定"现在该分析什么" |

### 基本面四维（5 个）

| Skill | Slug | 所属阶段 | 一句话 |
|-------|------|----------|--------|
| 商业模式可行性验证 | `business-model-feasibility` | 导入期重点 | 验证"这个模式能不能跑通" |
| 市场规模测算 | `market-size-estimation` | 成长期重点 | 量化"天花板到底有多高" |
| 护城河分析 | `moat-analysis` | 成熟期重点 | 判断"利润能不能守住" |
| 竞争格局分析 | `competitive-landscape-analysis` | 成熟期重点 | 拆解"同行/上下游谁赚得最多" |
| 产能周期判断法 | `capacity-cycle-judgment` | 成熟期(周期场景) | 判断"产能过剩到哪一步了" |

### 估值与外部（3 个）

| Skill | Slug | 适用范围 | 一句话 |
|-------|------|----------|--------|
| 产业生命周期估值地图 | `lifecycle-valuation-map` | 跨阶段 | 根据生命周期阶段选择估值框架 |
| 外部驱动力扫描（PEST+） | `external-force-scanner` | 跨阶段 | 扫描外部变量如何修正基本面判断 |
| 景气度追踪体系 | `prosperity-tracking-system` | 跨阶段 | 用高频指标验证中长期判断 |

### 输入输出（2 个）

| Skill | Slug | 一句话 |
|-------|------|--------|
| 行业定义与边界 | `industry-definition` | 确定分析范围和产业链结构 |
| 身份导向输出 | `identity-oriented-output` | 根据用户身份定制分析方案和叙事结构 |

### 🕰️ 历史对照层（8 个）— 2026-10-18 收编

| 来源 | 路径 | 说明 |
|------|------|------|
| 原独立工程 StockReview | `historical-review/分析技能层/` | 8 个历史对照技能（核心 `historical-stage-benchmarking`）+ 案例数据层（22 个行业档案）+ 3 份对照示范，见 [historical-review/分析技能层/INDEX.md](historical-review/分析技能层/INDEX.md) 与 [MERGE_MANIFESTO.md](historical-review/MERGE_MANIFESTO.md) |

> 调用方式为**半自动**：orchestrator 不自动调用该层；报告产出后，按 [交接文档](reference/如何接入StockReview做历史对照.md) 的 14 维特征向量契约由用户显式触发。该层 8 个技能已注册（连同顶层 14 个共 22 个技能可被发现）。

### 🧰 报告流水线（tools/）

| 工具 | 作用 |
|------|------|
| `tools/fetch_valuation.py` | 估值取数（腾讯行情为主，东财/百度兜底）→ `output/_data/*-valuation-*.json` |
| `tools/validate_report.py` | 报告契约 v3.0 机器校验（P0 门禁）→ 通过后发布 + `*.check.json` |
| `tools/tests/selftest.py` | 校验器回归测试（合格/不合格/篡改/发布四种场景） |

> 报告流程：草稿写 `output/_drafts/` → 取数 JSON → 校验 P0=0 → 发布 `output/`。契约见 [reference/output-template.md](reference/output-template.md)（v3.0），工具说明见 [tools/README.md](tools/README.md)。

---

## 技能关系图

```mermaid
graph LR
    subgraph 元能力
        hypothesis[hypothesis-driven-research]
        benchmark[spatial-temporal-benchmarking]
    end

    subgraph 核心锚定
        lifecycle[industry-lifecycle-anchoring]
    end

    subgraph 基本面四维
        feasibility[business-model-feasibility]
        marketsize[market-size-estimation]
        moat[moat-analysis]
        competitive[competitive-landscape-analysis]
        capacity[capacity-cycle-judgment]
    end

    subgraph 估值与外部
        valuation[lifecycle-valuation-map]
        pest[external-force-scanner]
        prosperity[prosperity-tracking-system]
    end

    subgraph 输入输出
        definition[industry-definition]
        identity[identity-oriented-output]
    end

    subgraph 总装
        orchestrator[industry-analysis-orchestrator]
    end

    %% depends-on (all pointing to lifecycle as the core anchor)
    valuation --> lifecycle
    capacity --> lifecycle
    prosperity --> lifecycle
    feasibility --> lifecycle
    marketsize --> lifecycle
    moat --> lifecycle
    competitive --> lifecycle
    pest --> lifecycle

    %% identity depends-on hypothesis (for SCQR narrative framework)
    identity --> hypothesis

    %% composes-with
    feasibility ===> benchmark
    marketsize ===> benchmark
    moat ===> competitive
    pest ===> benchmark
    prosperity ===> hypothesis
    competitive ===> capacity

    %% orchestrator composes all
    orchestrator ==> identity
    orchestrator ==> definition
    orchestrator ==> lifecycle
    orchestrator ==> hypothesis
    orchestrator ==> benchmark
```

---

## 关系明细（编排视角，17 条）

| # | 源技能 | 关系类型 | 目标技能 | 说明 |
|---|--------|----------|----------|------|
| 1 | lifecycle-valuation-map | depends-on | industry-lifecycle-anchoring | 估值需先知道行业处于哪个阶段 |
| 2 | capacity-cycle-judgment | depends-on | industry-lifecycle-anchoring | 产能周期是成熟期"稳定周期化"的子周期 |
| 3 | prosperity-tracking-system | depends-on | industry-lifecycle-anchoring | 景气度追踪是在已确定的阶段内做验证 |
| 4 | business-model-feasibility | depends-on | industry-lifecycle-anchoring | 只有确定导入期后才启动深度可行性验证 |
| 5 | market-size-estimation | depends-on | industry-lifecycle-anchoring | 成长期才启动完整市场规模测算 |
| 6 | moat-analysis | depends-on | industry-lifecycle-anchoring | 成熟期才启动深度护城河分析 |
| 7 | competitive-landscape-analysis | depends-on | industry-lifecycle-anchoring | 成熟期才启动深度竞争格局分析 |
| 8 | external-force-scanner | depends-on | industry-lifecycle-anchoring | 外部因素对所有阶段都有影响，但分析框架需先明确阶段 |
| 9 | business-model-feasibility | composes-with | spatial-temporal-benchmarking | 时间/空间对标是可行性验证的核心工具 |
| 10 | market-size-estimation | composes-with | spatial-temporal-benchmarking | 终局对标为市场规模测算提供有参照的假设 |
| 11 | moat-analysis | composes-with | competitive-landscape-analysis | 防守性+盈利性构成成熟期二维分析矩阵（单家防守 vs 行业利润分配为对比视角，已在技能 B 段说明） |
| 12 | external-force-scanner | composes-with | spatial-temporal-benchmarking | PEST校验时空对标的"环境可比"前提 |
| 13 | prosperity-tracking-system | composes-with | hypothesis-driven-research | 景气度指标是假设验证步骤的具体实践 |
| 14 | competitive-landscape-analysis | composes-with | capacity-cycle-judgment | 产能周期位置决定竞争格局变化方向 |
| 15 | identity-oriented-output | depends-on | hypothesis-driven-research | SCQR叙事框架是身份输出方案的理论基础 |
| 16 | external-force-scanner | contrasts-with | prosperity-tracking-system | 中长期结构变量 vs 高频交易指标 |
| 17 | hypothesis-driven-research | contrasts-with | spatial-temporal-benchmarking | 演绎验证 vs 类比推理 |

---

## 关系元数据全量清单（自动生成）

> 由 `tools/gen_skill_relations.py --write` 从 14 个技能 frontmatter 自动生成；与上表“关系明细（编排视角）”互补，不要手工编辑本段。

**统计**：声明 42 条 → 去重 33 对；其中多类型对 0 个、双向声明对 9 个。

| # | 技能 A | 关系（声明类型） | 技能 B | 声明方向 |
|---|--------|------------------|--------|----------|
| 1 | business-model-feasibility | depends-on | industry-lifecycle-anchoring | business-model-feasibility --depends-on--> industry-lifecycle-anchoring |
| 2 | capacity-cycle-judgment | depends-on | industry-lifecycle-anchoring | capacity-cycle-judgment --depends-on--> industry-lifecycle-anchoring |
| 3 | competitive-landscape-analysis | depends-on | industry-lifecycle-anchoring | competitive-landscape-analysis --depends-on--> industry-lifecycle-anchoring |
| 4 | external-force-scanner | depends-on | industry-lifecycle-anchoring | external-force-scanner --depends-on--> industry-lifecycle-anchoring |
| 5 | identity-oriented-output | depends-on | hypothesis-driven-research | identity-oriented-output --depends-on--> hypothesis-driven-research |
| 6 | industry-analysis-orchestrator | depends-on | hypothesis-driven-research | industry-analysis-orchestrator --depends-on--> hypothesis-driven-research |
| 7 | industry-analysis-orchestrator | depends-on | identity-oriented-output | industry-analysis-orchestrator --depends-on--> identity-oriented-output |
| 8 | industry-analysis-orchestrator | depends-on | industry-lifecycle-anchoring | industry-analysis-orchestrator --depends-on--> industry-lifecycle-anchoring |
| 9 | lifecycle-valuation-map | depends-on | industry-lifecycle-anchoring | lifecycle-valuation-map --depends-on--> industry-lifecycle-anchoring |
| 10 | market-size-estimation | depends-on | industry-lifecycle-anchoring | market-size-estimation --depends-on--> industry-lifecycle-anchoring |
| 11 | moat-analysis | depends-on | industry-lifecycle-anchoring | moat-analysis --depends-on--> industry-lifecycle-anchoring |
| 12 | prosperity-tracking-system | depends-on | industry-lifecycle-anchoring | prosperity-tracking-system --depends-on--> industry-lifecycle-anchoring |
| 13 | business-model-feasibility | composes-with | spatial-temporal-benchmarking | business-model-feasibility --composes-with--> spatial-temporal-benchmarking；spatial-temporal-benchmarking --composes-with--> business-model-feasibility |
| 14 | business-model-feasibility | composes-with | industry-analysis-orchestrator | industry-analysis-orchestrator --composes-with--> business-model-feasibility |
| 15 | capacity-cycle-judgment | composes-with | competitive-landscape-analysis | capacity-cycle-judgment --composes-with--> competitive-landscape-analysis；competitive-landscape-analysis --composes-with--> capacity-cycle-judgment |
| 16 | capacity-cycle-judgment | composes-with | prosperity-tracking-system | capacity-cycle-judgment --composes-with--> prosperity-tracking-system；prosperity-tracking-system --composes-with--> capacity-cycle-judgment |
| 17 | capacity-cycle-judgment | composes-with | industry-analysis-orchestrator | industry-analysis-orchestrator --composes-with--> capacity-cycle-judgment |
| 18 | competitive-landscape-analysis | composes-with | moat-analysis | competitive-landscape-analysis --composes-with--> moat-analysis；moat-analysis --composes-with--> competitive-landscape-analysis |
| 19 | competitive-landscape-analysis | composes-with | industry-analysis-orchestrator | industry-analysis-orchestrator --composes-with--> competitive-landscape-analysis |
| 20 | competitive-landscape-analysis | composes-with | industry-definition | industry-definition --composes-with--> competitive-landscape-analysis |
| 21 | external-force-scanner | composes-with | spatial-temporal-benchmarking | external-force-scanner --composes-with--> spatial-temporal-benchmarking；spatial-temporal-benchmarking --composes-with--> external-force-scanner |
| 22 | external-force-scanner | composes-with | industry-analysis-orchestrator | industry-analysis-orchestrator --composes-with--> external-force-scanner |
| 23 | hypothesis-driven-research | composes-with | prosperity-tracking-system | hypothesis-driven-research --composes-with--> prosperity-tracking-system；prosperity-tracking-system --composes-with--> hypothesis-driven-research |
| 24 | industry-analysis-orchestrator | composes-with | industry-definition | industry-analysis-orchestrator --composes-with--> industry-definition |
| 25 | industry-analysis-orchestrator | composes-with | spatial-temporal-benchmarking | industry-analysis-orchestrator --composes-with--> spatial-temporal-benchmarking |
| 26 | industry-analysis-orchestrator | composes-with | market-size-estimation | industry-analysis-orchestrator --composes-with--> market-size-estimation |
| 27 | industry-analysis-orchestrator | composes-with | moat-analysis | industry-analysis-orchestrator --composes-with--> moat-analysis |
| 28 | industry-analysis-orchestrator | composes-with | lifecycle-valuation-map | industry-analysis-orchestrator --composes-with--> lifecycle-valuation-map |
| 29 | industry-analysis-orchestrator | composes-with | prosperity-tracking-system | industry-analysis-orchestrator --composes-with--> prosperity-tracking-system |
| 30 | industry-definition | composes-with | industry-lifecycle-anchoring | industry-definition --composes-with--> industry-lifecycle-anchoring |
| 31 | market-size-estimation | composes-with | spatial-temporal-benchmarking | market-size-estimation --composes-with--> spatial-temporal-benchmarking；spatial-temporal-benchmarking --composes-with--> market-size-estimation |
| 32 | external-force-scanner | contrasts-with | prosperity-tracking-system | external-force-scanner --contrasts-with--> prosperity-tracking-system；prosperity-tracking-system --contrasts-with--> external-force-scanner |
| 33 | hypothesis-driven-research | contrasts-with | spatial-temporal-benchmarking | hypothesis-driven-research --contrasts-with--> spatial-temporal-benchmarking；spatial-temporal-benchmarking --contrasts-with--> hypothesis-driven-research |


## 推荐学习顺序

```
第 1 步：hypothesis-driven-research        ← 元能力，无前置依赖
第 2 步：spatial-temporal-benchmarking     ← 推理框架，无前置依赖
第 3 步：industry-lifecycle-anchoring      ← 核心锚，建议先掌握元能力再学
第 4 步：industry-definition               ← 基础能力，无前置依赖
第 5 步：business-model-feasibility        ← 导入期应用
第 6 步：market-size-estimation            ← 成长期应用
第 7 步：moat-analysis                     ← 成熟期（可与第8步并行）
第 8 步：competitive-landscape-analysis    ← 成熟期（可与第7步并行）
第 9 步：capacity-cycle-judgment           ← 成熟期"周期化"场景
第 10 步：lifecycle-valuation-map          ← 需理解四个基本面维度后
第 11 步：external-force-scanner           ← 需理解所有基本面后才能修正判断
第 12 步：prosperity-tracking-system       ← 需理解整个框架后才能做持续验证
第 13 步：identity-oriented-output         ← 需理解SCQR后才能做受众适配
```

---

## 审计轨迹

| 阶段 | 日期 | 内容 | 状态 |
|------|------|------|------|
| 模块化解耦 | 2026-06-10 | 将 ~1200行 SKILL.md 拆解为 14 个独立子技能 + 4 个参考文件 | ✅ 完成 |
| 结构标准化 | 2026-06-10 | 每个子技能完成 RI-A1-A2-E-B 六段结构 | ✅ 完成 |
| 关系建模 | 2026-06-10 | 识别 18 条技能间关系（9 depends-on + 6 composes-with + 3 contrasts-with） | ✅ 完成 |
| 批判整合 | 2026-06-10 | 基于 BOOK_OVERVIEW.md 的系统批判注入每个子技能的 B 字段 | ✅ 完成 |
| StockReview 桥接 | 2026-06-14~16 | 初版 historical-case-matching 桥接 skill → 发现与 StockReview 原生 historical-stage-benchmarking 方法论重复 → 降级为 reference 交接文档（见 reference/如何接入StockReview做历史对照.md） | ✅ 完成 |
| 收编 StockReview | 2026-10-18 | 独立工程 StockReview 整体迁入为 `historical-review/` 历史对照层（8 技能 + 22 案例 + 3 示范），路径改工程内相对路径、8 技能注册，调用方式维持半自动；原著 epub 未随迁 | ✅ 完成 |
| 报告契约 v3 + 机器校验 | 2026-10-18 | 固定 14 模块与报告头 metadata；新增 `tools/validate_report.py`（P0 门禁）与 `tools/fetch_valuation.py`（估值数据可追溯）；移除 8 份旧报告；orchestrator 升至 v3.0.0 | ✅ 完成 |
| 首份 v3 试点报告 | 2026-10-18 | 白酒行业（投资者版）通过 P0=0/P1=0 校验并发布（`output/` 报告 + `.check.json`）；数据缺口以 🔴 标注 | ✅ 完成 |
| 第二份 v3 试点（保险） | 2026-10-19 | 保险行业（投资者版）通过 P0=0/P1=0 校验并发布；验证金融/非制造业与成长期分支；修复校验器多行业取数选择、取数日期一致性守卫 | ✅ 完成 |
| 案例库 14 维标准化 + 关系重建 | 2026-10-19 | 22/22 案例统一 14 维单值（16 维→14、双列时点→基准+变体、多选收敛）；关系检查 0 问题、补全 17 条反向关系、统一 3 对冲突；关系图改为脚本生成 | ✅ 完成 |
| 历史层引文边界 + 双层触发标签 | 2026-10-19 | 教育案例 2021-07 后引文改标“补注（非原书）”；8 个历史层技能 description 首段加【历史对照层】标签，降低与顶层技能触发混淆 | ✅ 完成 |
| 关系元数据清单自动生成 | 2026-10-19 | 新增 `tools/gen_skill_relations.py`：从 14 个技能 frontmatter 生成去重关系清单（52 条声明 → 33 对，含 9 对多类型/17 对双向）；INDEX 增加自动生成段，编排视角 18 条保持不变 | ✅ 完成 |
| P2 工程化收尾 | 2026-10-19 | 新增 `tools/ci_check.py` 一键回归（链接/技能结构/校验器自测/报告/案例）；扩展 targets（电力/银行）；清理 `_archive` 备份（约 52 MB，3 个目录） | ✅ 完成 |
| 历史对照实测（白酒） | 2026-10-19 | 新增 `tools/case_match.py` 与 `tools/examples/白酒-14dim.json`；白酒报告 → 14 维向量 → 22 案例匹配（Top1 家电 0.694）→ 按 HBS“像/不像/像”产出对照报告；ci_check 增加匹配回归并兼容非 report-v3 文档 | ✅ 完成 |
| 第三份 v3 试点（电力） | 2026-10-19 | 电力行业（投资者版）通过 P0=0/P1=0 校验并发布（7 标的，盘中快照）；验证公用事业/重资产路径；修复校验器 PE 中位数误报（“PE 中位数、7 家…”） | ✅ 完成 |
| 历史对照实测（电力） | 2026-10-19 | 电力报告 → 14 维向量 → 22 案例匹配（算法 Top1 汽车为表面相似，已排除；候选：电力自身 2012-2015、银行 2016-2018）→ 按 HBS 三阶段产出对照报告；新增 `tools/examples/电力-14dim.json` | ✅ 完成 |
| 核心技能关系裁决（方案 A） | 2026-10-19 | 9 对多类型声明收敛为单类型（depends-on 保留依赖方→被依赖方；moat/competitive 统一 composes-with）；52→42 条声明、多类型 9→0；编排表 18→17 条、关系统计同步；`gen_skill_relations.py --fix` 支持幂等迁移 | ✅ 完成 |
| 历史对照实测（保险·判停） | 2026-10-19 | 保险报告 → 14 维向量（仅 9 维可比，低于 ≥10 门槛）→ 22 案例匹配（Top 汽车/军工等均为表面相似；银行 #7 仅风格参照）→ 按 HBS 判停条件终止，明确“历史上没有很好的对标”；新增 `tools/examples/保险-14dim.json`，交接文档登记“不适用行业清单” | ✅ 完成 |

### 关系统计

| 关系类型 | 数量 | 说明 |
|----------|------|------|
| depends-on | 9 | 核心锚被8个技能依赖 + identity依赖hypothesis |
| composes-with | 6 | 工具技能被组合使用 |
| contrasts-with | 2 | 代表不同分析路径 |
| **合计** | **17** | 编排视角核心关系（手工维护，用于调度/关系图） |
| **元数据声明** | **42 条 / 去重 33 对** | 来自 14 个技能 frontmatter；方案 A 裁决后多类型声明 0 对、双向声明 9 对，详见“关系元数据全量清单（自动生成）” |

---

### v2.5.0 更新日志（从原有SKILL.md继承）

基于对原著全文的系统审视，此版本补全了此前缺失的关键方法论并修正错误：

**v2.5.0 新增方法论：**
- 🔴 金字塔原理：构建金字塔的四步法、"总结vs提炼"区分、"那又怎样？"深度追问
- 🔴 SCQR叙事框架："空雨湿伞"模型 + 按四种受众调整叙事顺序
- 🟡 专家访谈技巧：能力圈判断、绕开保密协议、启发式追问
- 🟡 研报筛选四法：热度→团队→推荐→内容
- 🟡 搜索引擎高级操作符：site:/filetype:/双引号/减号/通配符
- 🟡 FOMO警示：在未建立深度差前警惕盲目追求广度

**v2.5.0 错误修正：**
- 🔧 修正渗透率阈值与创新扩散理论的机械对应
- 🔧 修正护城河分析要求：从"至少覆盖两种"改为"根据行业特性选择2-3类"
- 🔧 生命周期优先级矩阵加入行业特性例外条款
- 🔧 数据时效规则加入弹性例外条款

**v2.4.0 新增：**
- 🔴 创新扩散理论、产能周期分析、库存周期
- 🟡 货币三种价格、经济发展水平分析、Gartner技术成熟度曲线、创新层级金字塔
- 🟡 DIKW模型、事实判断vs价值判断、信息茧房意识、MECE原则
