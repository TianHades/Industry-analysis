# 行业快速分析 Skill

基于《如何快速了解一个行业》（肖璟著）方法论构建的 Claude Code 技能库，通过模块化、系统化的框架输出身份导向的行业分析报告。

## 架构特点

本技能库采用 **模块化微核架构**：13 个独立子技能 + 4 个共享参考文件，通过 `industry-analysis-orchestrator` 统一调度。

每个子技能遵循 **RI-A1-A2-E-B** 六段结构：
- **R**（原文引用）：书中关键段落
- **I**（方法论骨架）：核心框架的精炼表达
- **A1**（书中的应用）：2-3个书中案例
- **A2**（触发场景）：何时激活 + 语言信号
- **E**（可执行步骤）：3-5步 + 完成标准 + 判停条件
- **B**（边界）：不适用场景 / 失败模式 / 作者盲点 / 邻近方法区分

## 快速开始

### 使用

直接说"帮我分析XX行业"，orchestrator 会自动调度全部子技能，完成：

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
| `reference/output-template.md` | 完整报告输出模板 |
| `reference/search-specs.md` | 搜索工具链、Google操作符、按阶段定向搜索指引 |
| `reference/data-annotation-standards.md` | 数据标注格式、时效校验规则、冲突仲裁规则 |
| `reference/methodology-catalog.md` | 方法速查卡片、核心概念定义 |
| `BOOK_OVERVIEW.md` | 对原著的系统批判（作者局限、立场盲点、未证明假设） |
| `INDEX.md` | 技能全景图、关系图、学习路径 |

## 示例报告

查看 [output/](output/) 目录获取分析报告示例。

## 方法论来源

基于《如何快速了解一个行业》（肖璟著，2025年人民邮电出版社）的系统化研究框架。

## 免责声明

本 Skill 生成的内容基于公开信息整理分析，仅供行业研究参考，不构成任何投资建议。投资有风险，决策需谨慎。
