# 如何做历史对照（historical-review 层）

> **定位**：本工程（Industry-analysis）现在包含**两层技能**——顶层 14 个技能负责当期行业分析；`historical-review/` 层负责历史对照。本文是两层之间的**交接说明**，不是可触发的 skill。
>
> **调用方式：维持半自动。** orchestrator 流水线**不自动调用** historical-review 层：本工程职责到"产出一份带齐关键指标的行业分析报告"为止；需要历史对照时，由用户显式提出，再按本文的 14 维特征向量契约，在同一工程内调用 `historical-review/分析技能层/historical-stage-benchmarking` 等原生技能。这样既避免方法论双份维护，也避免"对照"被自动流程当成必选项。
>
> **沿革**：`historical-review/` 原为独立工程 `D:\workspace\01-投研主链\StockReview`，2026-10-18 收编进本工程；目录内部结构未重排，相对链接全部自动保持有效。原目录完整备份于 `D:\workspace\01-投研主链\_archive\20261018_StockReview_backup`，原著 epub（50.45 MB）未随迁。

---

## 工作流

```
本工程 (Industry-analysis)
①  orchestrator 产出 output/{行业}-行业分析报告（投资者版）.md
        ↓  按 14 维契约从报告章节摘取特征（无需切换工程目录）
②  显式调用 historical-review/分析技能层/historical-stage-benchmarking
        ↓
③  "像→不像→像"三段对照 + 情景推演 → 输出完整投资报告
```

1. 在本工程跑完 orchestrator，得到 `output/{行业名称}-行业分析报告（投资者版）.md`
2. **不需要切换 workspace**：直接在本工程内显式触发 historical-review 层技能（8 个技能均已注册进 `.claude/settings.json`，但不在 orchestrator 的自动调用链里）
3. 对照结论用于投资判断；原报告不回写，保持产出时点的快照

---

## historical-review 层可用的技能

| 技能 | 路径 | 用途 |
|------|------|------|
| **historical-stage-benchmarking**（核心） | `historical-review/分析技能层/historical-stage-benchmarking/SKILL.md` | "像→不像→像"三段历史对照的完整方法论——把当前行业对标到 22 个案例库中最相似的历史阶段 |
| industry-stage-locator | `historical-review/分析技能层/industry-stage-locator/SKILL.md` | 用渗透率/增速/政策信号定位行业生命周期阶段（对照的参照系锚点） |
| capacity-cycle-positioning | `historical-review/分析技能层/capacity-cycle-positioning/SKILL.md` | 产能四阶段模型，判断供需格局和盈利拐点 |
| leader-moat-assessment | `historical-review/分析技能层/leader-moat-assessment/SKILL.md` | 龙头护城河与估值溢价合理性 |
| bull-bear-signal-system | `historical-review/分析技能层/bull-bear-signal-system/SKILL.md` | 水牛 vs 业绩牛、戴维斯双击/双杀判断（对照的"可能性边界"验证） |
| policy-driver-assessment | `historical-review/分析技能层/policy-driver-assessment/SKILL.md` | 政策节奏与投资时钟 |
| industry-replay-methodology | `historical-review/分析技能层/industry-replay-methodology/SKILL.md` | 复盘 SOP 元能力 |
| external-shock-transmission | `historical-review/分析技能层/external-shock-transmission/SKILL.md` | 外部冲击三层传导管道 |

**案例数据**：22 个行业完整档案在 `historical-review/行业案例档案库/`，对照演示在 `historical-review/行业对比示范/`，统一框架见 `historical-review/行业生命周期全景框架_蒸馏笔记.md`。技能依赖图与学习顺序见 [`historical-review/分析技能层/INDEX.md`](../historical-review/分析技能层/INDEX.md)。

> 对照方法论的**完整步骤、判停条件、失败模式**全部以上方 historical-review 原生技能为准，本工程不复述，避免双份漂移。

---

## 交接契约：14 维特征向量映射表 ★

这是本说明**唯一**承载的增量价值——告诉你在调用 historical-review 层前，**从本工程报告的哪些章节带走哪些指标**，对应历史案例档案的哪些字段。历史对照技能假设你已知道该输入什么特征；这张表就是那个"该输入什么"的清单。

| # | 特征维度 | 本工程报告中的来源模块（report-v3） | historical-review 案例对应字段 |
|---|---------|----------------------|------------------------|
| 1 | 生命周期阶段 | 模块 3「产业生命周期判断」 | 生命周期阶段（8 选 1） |
| 2 | 产能周期位置 | 模块 10「产能周期与库存周期」 | 产能周期位置 |
| 3 | CR3 集中度 | 模块 9「竞争格局与利润分配」 | 行业集中度 CR3 |
| 4 | 需求量增速 | 模块 7「市场规模测算」或模块 3 | 需求量增速 YoY |
| 5 | 估值分位数 | 模块 11「估值逻辑」 | 估值分位数（5 年） |
| 6 | 盈利趋势方向 | 模块 13「景气度跟踪与验证方案」 | 盈利趋势方向 |
| 7 | 政策敏感度 | 模块 12「PEST 外部驱动 → P 政治」 | 政策敏感度 |
| 8 | 供给刚性程度 | 模块 10「产能周期与库存周期」 | 供给刚性程度 |
| 9 | 成本传导能力 | 模块 9「竞争格局与利润分配」或模块 8「护城河分析」 | 成本传导能力 |
| 10 | 周期性强度 | 模块 3 + 模块 10（见下方合成法） | 周期性强度（1-10） |
| 11 | 海外因素敏感度 | 模块 12「PEST → P 政治/E 经济」 | 海外因素敏感度 |
| 12 | 2008 年效应 | N/A（当前行业无需填写） | 2008 年效应 |
| 13 | 2016 年效应 | N/A（当前行业无需填写） | 2016 年效应 |
| 14 | Beta 特征 | 模块 12「PEST → E 经济」 | Beta 特征 |

> 模块编号来自 `reference/output-template.md`（report-v3，14 个固定模块）；模板升级时以模块名称为准。
> 报告必须通过 `tools/validate_report.py`（P0=0）且 `{报告名}.check.json` 为 `passed`，才可作为历史对照输入。

### 维度 10「周期性强度」合成法（报告未直接给出 1-10 评分时）

本工程报告通常不直接给出"周期性强度 1-10"，需按以下规则合成，再 clamp 到 1-10：

- (a) 行业是否属于周期制造型？是 → 起始 5 分，否 → 起始 2 分
- (b) 近 3 年营收增速标准差 > 15%？(+2)
- (c) CAPEX/折旧比波动 > 50%？(+2)
- (d) 历史上出现过全行业亏损？(+1)

---

## 交接前的自检

切换到历史对照前，确认报告已带齐：

- [ ] 上表 14 维中**至少 10 维**有明确取值（不足 7 维 → 先回本工程补全基本面，再做对照）
- [ ] 报告已通过 `tools/validate_report.py`（P0=0），`{报告名}.check.json` 为 `passed`
- [ ] 每维数据标注了来源章节和置信度
- [ ] 行业**不属于**"极度新兴、无任何历史参照"类别（否则在 historical-review 里诚实告知"没有好的对标"，不强行匹配）

---

## 已知的局限（沿用 historical-review 层原生技能的边界）

- 案例数据截至 **2020 年**（原书出版于 2018/2021），2020 年后的结构性变化（双碳、AI、人口拐点、中美脱钩）在案例库中无完整周期数据
- 案例以 **A 股**为主，对港股/美股直接适用性有限
- 历史对照针对**中长期阶段判断**（季度以上），不适用于日度/周度交易

> 这些边界的权威表述以 [`historical-stage-benchmarking` 的 B 节](../historical-review/分析技能层/historical-stage-benchmarking/SKILL.md) 为准。

---

## 变更记录

- 2026-06-16（v2.2.0）：移除 Phase 3.5 自动调用，桥接 skill 降级为本文档
- 2026-10-18：原独立工程 StockReview 收编为本工程 `historical-review/` 层，路径改为工程内相对路径，调用方式维持半自动
- 2026-10-18（report-v3）：映射表改为按模块名引用（模块 3/7/9/10/11/12/13），报告须先通过机器校验
