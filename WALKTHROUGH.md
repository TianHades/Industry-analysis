# Industry-analysis 全工程 Walkthrough

> **这是什么**：一份「带读式」工程导览 + 验收记录——按真实链路把工程从头到尾走一遍，并记录本次实际运行结果。
> **生成时间**：2026-10-19（版本 v1）
> **适用读者**：第一次接触本工程的人、未来的维护者、需要验收交付物的人。
> **怎么验证这份文档**：按文末「一键验收」运行 `python tools/ci_check.py`，应输出 6 项 PASS；本文所有命令均在 2026-10-19 实际执行过。

---

## 0. 30 秒看懂

- **一句话**：这是一个「行业分析技能库 + 报告生产流水线 + 历史案例对照层」，用 Markdown 技能（SOP）驱动 AI 产出**可机器校验**的行业研究报告，并可选做历史阶段对照。
- **核心链路**：选行业 → 取数（估值 JSON）→ 写报告草稿 → `validate_report.py` 机器门禁（P0=0）→ 发布到 `output/` + `check.json` →（可选）14 维向量匹配历史案例。
- **当前产物**：3 份通过校验的行业报告（白酒/保险/电力）、3 份历史对照（白酒/电力实质对标；保险判停）、22 个标准化案例、4 个行业取数模板。
- **一键体检**：`python tools/ci_check.py` → `结果：PASS`。

---

## 1. 这是什么 / 不是什么

### 是

| 角色 | 说明 |
|------|------|
| 方法论技能库 | 14 个顶层分析技能 + 1 个编排器，按 RI-A1-A2-E-B 六段结构写成 SOP（Markdown），AI 读取后执行 |
| 报告生产流水线 | 契约（report-v3）+ 取数（JSON 可追溯）+ 机器校验（P0 门禁）+ 发布产物（报告 + check.json） |
| 历史案例对照层 | `historical-review/`：8 个历史分析技能 + 22 个行业案例（14 维标准化向量）+ 3 个对比示范，半自动调用 |
| 回归工程 | `tools/ci_check.py` 一键检查链接/技能结构/关系/校验器/已发布报告/案例一致性 |

### 不是

- **不是自动投研系统**：没有定时任务、没有数据库、不自动调用历史对照（v2.2.0 起刻意保持半自动，由人或 agent 显式发起）；
- **不保证结论正确**：机器只保证「结构完整、数据可追溯、数值一致、口径规则成立」，**不保证商业判断为真**；🔴 缺口需人工补；
- **不构成投资建议**：所有报告均为 AI 研究草稿 + 机器校验产物。

---

## 2. 目录地图

| 路径 | 内容 | 入库 |
|------|------|------|
| `industry-analysis-orchestrator/` | 编排器：调用流程、阶段权重、报告契约、PEST 修正环 | ✅ |
| 其余 13 个顶层技能目录 | 定义/生命周期/时空对标/市场规模/商业模式/护城河/竞争/产能/估值/PEST/景气/身份输出/假设验证 | ✅ |
| `historical-review/分析技能层/` | 8 个历史对照技能（已标【历史对照层】触发标签）+ candidates/verified 目录 | ✅ |
| `historical-review/行业案例档案库/` | 22 个完整案例（周期制造 11 + 品牌消费 7 + 技术迭代 4）、案例模板、关系图 | ✅ |
| `historical-review/行业对比示范/` | 3 份对比示范（周期/技术/品牌消费） | ✅ |
| `reference/` | 报告契约 `output-template.md`、数据标注规范、方法论目录、搜索规范、历史对照交接文档 | ✅ |
| `output/` | 3 份已发布报告 + `*.check.json` + 3 份历史对照（供阅读/交付） | ✅ |
| `tools/` | 取数、校验、CI、匹配、案例维护脚本 + 测试 + 示例向量 + 4 行业取数模板 | ✅ |
| `output/_drafts/`、`output/_data/` | 草稿与取数 JSON（中间产物） | ❌ gitignore |
| `如何快速了解一个行业.epub` | 原著电子书（12.9 MB，仅供查证，不参与流水线） | 本地保留 |

**技能注册**：`.claude/settings.json` 注册 `["*/", "historical-review/分析技能层/*/"]`，共 22 个技能可被发现。

---

## 3. 端到端 SOP（以「电力」报告为例，真实命令）

### 3.1 准备

```bash
# 校验器/CI 只需 Python 3.8+（DSH 内置 Python 即可）
# 取数脚本需要 requests/akshare（本机系统 Python 3.10 已装）
pip install -r tools/requirements.txt   # 首次
```

### 3.2 取数（估值 JSON，可追溯）

```bash
python tools/fetch_valuation.py --industry 电力 --targets tools/targets/电力.json
```

输出：`output/_data/电力-valuation-20261019.json`（schema=`valuation-v1`，7 只标的，记录数据源、行情时间戳、错误数）。
要点：数据日期默认取行情时间戳；`--date` 与行情时间不一致会报错（防止把盘中价标成历史日期）。

### 3.3 写草稿

在 `output/_drafts/` 写 `{行业}行业-行业分析报告（投资者版）.md`：
- 报告头 YAML metadata（schema/report-v3、industry、identity、generated_at、data_cutoff、valuation_fetch_date、lifecycle_stage、penetration、evidence_files）；
- 8 个大节 + 14 个固定模块（定义/产业链/生命周期/核心假设/时空对标/商业模式/市场规模/护城河/竞争/产能库存/估值/PEST/景气/第二曲线）；
- 估值表 ≥5 只标的，数值必须来自取数 JSON；
- 数据搜索/网页抓取工具**以运行时实际可用为准**：Chrome MCP（`browse`/`extract`）或内置 `web_search`/`web_fetch`，规范见 `reference/search-specs.md`。

### 3.4 机器校验（P0 门禁）

```bash
python tools/validate_report.py "output/_drafts/电力行业-行业分析报告（投资者版）.md" \
    --data-dir output/_data --json
```

- 退出码 0=通过（可含 P1 警告）、1=存在 P0、2=用法错误；
- P0：结构/metadata/日期/估值表/数值交叉核对/🟢 预测词/假设与验证表/第二曲线范围等硬性规则；
- P1：需要人工复核的警告（如 PE 中位数复算偏差、占比合计异常）。

### 3.5 发布

```bash
python tools/validate_report.py "output/_drafts/电力行业-行业分析报告（投资者版）.md" \
    --data-dir output/_data --publish-dir output
```

产物：`output/电力行业-行业分析报告（投资者版）.md` + `.check.json`（`passed: true`），并在报告「数据时效性与质量说明」注入"自动校验：通过"行。

### 3.6 历史对照（可选，半自动）

```bash
python tools/case_match.py --query tools/examples/电力-14dim.json --top 5
```

流程：报告 → 14 维向量 JSON（`tools/examples/`）→ 与 22 个案例匹配 → 按 HBS 技能「像→不像→像」人工复核 → 产出 `output/历史对照-{行业}-{日期}.md`。
已实测三种分支：白酒（实质对标）、电力（部分相似/驱动不同）、保险（诚实判停：无好对标）。

### 3.7 提交前一键回归

```bash
python tools/ci_check.py
```

---

## 4. 关键契约（改报告/改工具前必读）

### 4.1 report-v3（`reference/output-template.md`）

- **14 个固定模块**，顺序固定；缺模块/顺序错 = P0；
- **metadata 必填**：`schema: report-v3`、industry、identity、generated_at、data_cutoff、valuation_fetch_date、template_version、orchestrator_version、lifecycle_stage、penetration、evidence_files；
- **估值表**：投资者版 ≥5 只；单元格不得出现"待补/未获取"；`获取时间` 必须等于 `valuation_fetch_date`；数值与 `evidence_files` 的 JSON **逐值一致**（价/PE/PB/市值容差比对）；PE/PB 非正数应标"亏损"/"—"（校验器 E-VAL-10）；正文"合计总市值"须与估值表求和一致（校验器 W-MATH-MCAP）；
- **符号规则**：🟢 实际数据（行内禁预测词）、🟡 预测（必须带 4 位年份）、🟠 历史、🔴 不确定、🔍 推断、🔒 需人工、⏳ 待验证；
- **数据时效**：行业数据默认年度、估值数据为取数日快照；盘中/午间快照必须在表前注明，不得称"收盘"。

### 4.2 14 维案例向量（`historical-review/行业案例档案库/`）

- 每个案例「四、可对比特征向量」为 **14 维、单值**；
- 双时点/子行业差异写入备注（`【阶段变体：…】`），单值维度只勾选一个（其余写"该维另标注"）；
- 维护脚本：`tools/normalize_case_vectors.py --apply --single-select`（应保持 0 改动）；
- 关系：`tools/check_case_relations.py --fix --write-graph`（当前 0 问题，关系图由脚本生成）。

### 4.3 技能关系（方案 A）

- 14 个顶层技能 frontmatter 的 `related_skills`：**每对技能只保留一种关系**；`depends-on` 方向为"依赖方→被依赖方"；冲突优先级 `depends-on > composes-with > contrasts-with`；
- `tools/gen_skill_relations.py` 检查多类型声明（应 0 对），`--fix` 幂等迁移，`--write` 更新 INDEX 自动段；
- INDEX「关系明细（编排视角，17 条）」是手工维护的调度视图，自动段是 frontmatter 的完整元数据视图，两者互补。

---

## 5. 产物清单与状态

### 5.1 已发布报告（均 P0=0 / P1=0）

| 报告 | 行业路径 | 状态 |
|------|----------|------|
| [白酒行业（投资者版）](output/白酒行业-行业分析报告（投资者版）.md) | 成熟期/消费 | ✅ 44.9 KB；check.json passed |
| [保险行业（投资者版）](output/保险行业-行业分析报告（投资者版）.md) | 成长期后段/金融 | ✅ 24.9 KB；check.json passed |
| [电力行业（投资者版）](output/电力行业-行业分析报告（投资者版）.md) | 成熟期/公用事业 | ✅ 28.6 KB；check.json passed |

### 5.2 历史对照（半自动）

| 对照 | 结论 |
|------|------|
| [白酒行业历史对照](output/历史对照-白酒-20261019.md) | 候选家电 2016-18 / 白酒自身 2012-15；结论"像底部结构、不像复苏确认" |
| [电力行业历史对照](output/历史对照-电力-20261019.md) | 候选电力自身 2012-15 / 银行 2016-18；结论"修复+重估叠加，非周期复刻" |
| [保险行业历史对照](output/历史对照-保险-20261019.md) | **判停**：14 维仅 9 维可比、无对应案例，明确"历史上没有很好的对标" |

### 5.3 工具箱

| 工具 | 用途 |
|------|------|
| `tools/fetch_valuation.py` | 估值取数（腾讯行情主，东财/百度兜底），输出 valuation-v1 JSON |
| `tools/validate_report.py` | report-v3 机器校验 + 发布 + check.json |
| `tools/ci_check.py` | 一键回归（6 项） |
| `tools/case_match.py` | 14 维向量 × 22 案例匹配 |
| `tools/normalize_case_vectors.py` | 案例 14 维标准化 |
| `tools/check_case_relations.py` | 案例关系检查/修复/关系图生成 |
| `tools/gen_skill_relations.py` | 技能关系元数据检查/迁移/INDEX 生成 |
| `tools/tests/selftest.py` | 校验器 4 场景回归测试 |

取数模板：`tools/targets/` 下 4 个行业（白酒/保险/电力/银行）；示例向量：`tools/examples/` 下 3 个（白酒/电力/保险）。

### 5.4 案例库

- 22 个完整案例：周期制造型 11、品牌消费型 7、技术迭代型 4；
- 14 维全部单值、关系检查 0 问题；
- `案例关联关系图.md` 由脚本生成（Mermaid + 全部案例关联一览）；
- 3 份对比示范（周期/技术/品牌消费）。

---

## 6. 一键验收：`ci_check` 六项

```bash
python tools/ci_check.py
```

| 检查项 | 验什么 | 期望 |
|--------|--------|------|
| 链接检查 | 全部 Markdown 相对链接 | 断链 0 |
| 技能结构（22） | 14+8 个 SKILL.md 的 name 与 RI-A1-A2-E-B 六段 | 问题 0 |
| 技能关系一致性 | frontmatter 多类型声明 | 0 对（方案 A） |
| 校验器自测 | good/bad fixture、篡改检测、发布产物 | SELFTEST PASSED |
| 已发布报告校验 | `output/*.md` 中 report-v3 文档逐个跑 P0 校验 | 3 份通过 |
| 案例库一致性 | 22 案例关系 0 问题、14 维 0 漂移、匹配可运行 | OK |

**本次验证记录（2026-10-19）**：

```
[PASS] 链接检查: 81 个 md，断链 0
[PASS] 技能结构（22）: 22 个技能，问题 0
[PASS] 技能关系一致性: 多类型声明 0 对（方案 A）
[PASS] 校验器自测: PASS
[PASS] 已发布报告校验: 3 份 report-v3 报告（跳过 3 个非报告文档）
[PASS] 案例库一致性: 关系 OK；14 维 OK；14 维匹配 OK

结果：PASS
```

（含本文档；本次实际 81 个 md、断链 0。）

---

## 7. 演进史（为什么现在是这样）

| 阶段 | 内容 |
|------|------|
| 模块化解耦（2026-06） | ~1200 行 SKILL.md → 14 个独立子技能 + 4 个参考文件；RI-A1-A2-E-B 六段结构 |
| 历史层收编（2026-10-18） | 独立工程 StockReview 迁入 `historical-review/`（8 技能 + 22 案例 + 3 示范），路径改工程内相对路径，8 技能注册，调用方式维持半自动 |
| 报告契约 v3 + 机器门禁（2026-10-18） | 固定 14 模块与 metadata；新增 `validate_report.py`（P0 门禁）与 `fetch_valuation.py`；移除 8 份旧报告；orchestrator 升至 3.0.0 |
| 试点报告（2026-10-18/19） | 白酒（44.9 KB，2025 年报/2026H1 数据）、保险（金融/非制造业路径）、电力（公用事业/重资产路径） |
| 历史层一致性（2026-10-19） | 案例 14 维标准化（16→14、双列时点→单值基准、多选收敛）；关系补全 17 条反向并统一 3 对冲突；关系图脚本生成；引文边界重标；双层触发标签 |
| 工程化收尾（2026-10-19） | `ci_check.py` 一键回归；`gen_skill_relations.py` 关系清单；targets 扩至 4 行业；清理 `_archive` 备份（约 52 MB） |
| 历史对照实测（2026-10-19） | 白酒（实质对标）、电力（部分相似）、保险（判停）三种 HBS 分支落地 |
| 关系裁决（2026-10-19） | 9 对多类型声明收敛为单类型（52→42 条声明、多类型 9→0） |
| 全量审视修复（2026-10-19） | 修复电力报告合计总市值算术错误；搜索规范改为运行时自适应（Chrome MCP / 内置工具）；校正模板模块 7 深度规则、orchestrator 失效引用、README/交接文档旧备份路径；校验器新增 PE 非正数与合计总市值检查；3 份报告 metadata 统一 3.0.0 并重新发布 |
| Walkthrough（2026-10-19） | 本文档 + 全链路验收 |

关键提交（最新在前）：`77282c9` 保险对照 → `d1d342c` 关系裁决 → `ebeddb6` 电力对照 → `fdd593e` 电力报告 → `7221718` 白酒对照 → `c75dcf6` P2 收尾。

---

## 8. 已知局限与风险（重要）

| # | 局限 | 影响 | 处理建议 |
|---|------|------|----------|
| 1 | **历史对照是半自动**：orchestrator 不自动调用历史层 | 需要人工记得触发 | 在报告末尾/交接文档明确"是否已做对照" |
| 2 | **保险无对应历史案例**，14 维仅 9 维可比 | 保险对照只能判停 | 补"保险版扩展维度"（PEV/NBV/代理人/久期缺口） |
| 3 | 案例数据截至 **2020 年**（原书 2021 出版） | 2020 后结构性变化无完整周期数据 | 对照时明确"可比性折扣" |
| 4 | TAM/SAM/SOM、CR5、周期性强度等含 🔍 估算 | 不能当披露数据用 | 报告中已标 🔍，需外部数据校验 |
| 5 | 估值取数依赖腾讯行情，且电力/保险为**盘中快照** | 非收盘价，时点敏感 | 报告中注明时点；收盘后可重取 |
| 6 | PEV、股息率、分主体 CR5、CAPEX/折旧等数据缺口 | 估值判断偏方向性 | 报告质量说明已列 🔴 |
| 7 | 8 份旧版报告已删除，未按新契约重做 | 只剩 3 份新报告 | 如需覆盖更多行业，按 SOP 续做 |
| 8 | 机器校验不保证商业结论正确 | 可能存在"合规但错误" | 发布前仍需人工/专业复核 |
| 9 | 技能关系"编排视角 17 条"为手工维护 | 与自动元数据段并存 | 已在 INDEX 说明两者关系；改关系时先跑 `gen_skill_relations.py` |
| 10 | 历史对照结论依赖 14 维框架 | 金融/服务业适配不足 | 见第 2 条；必要时扩展维度框架 |
| 11 | 搜索/抓取工具随运行时变化（Chrome MCP vs 内置 `web_search`/`web_fetch`） | 执行细节可能不同 | 规范已改为自适应；以当前运行时可用工具为准 |

---

## 9. 下一步建议

1. **银行行业报告（第四份）**：案例库有银行完整案例（已被电力/保险对照用作风格参照），可形成"报告 + 对照"闭环；
2. **保险版扩展维度**：把 PEV/NBV/新业务价值率/代理人产能/分红险占比/投资收益率/久期缺口纳入"金融业变体"，再跑一次保险对照；
3. **更多行业覆盖**：按现有 SOP 继续产出（每个行业约 30–60 分钟）；
4. **可选工程升级**：报告归档/版本管理、行情源冗余、港股/美股取数扩展。

---

## 10. 附录

### 10.1 命令速查

| 目的 | 命令 |
|------|------|
| 取数 | `python tools/fetch_valuation.py --industry {行业} --targets tools/targets/{行业}.json` |
| 校验（不发布） | `python tools/validate_report.py "output/_drafts/{报告}.md" --data-dir output/_data --json` |
| 校验并发布 | `python tools/validate_report.py "output/_drafts/{报告}.md" --data-dir output/_data --publish-dir output` |
| 一键回归 | `python tools/ci_check.py` |
| 历史对照 | `python tools/case_match.py --query tools/examples/{行业}-14dim.json --top 5` |
| 校验器自测 | `python tools/tests/selftest.py` |
| 案例标准化 | `python tools/normalize_case_vectors.py --apply --single-select` |
| 案例关系图 | `python tools/check_case_relations.py --fix --write-graph` |
| 技能关系 | `python tools/gen_skill_relations.py`（检查）/ `--write`（更新 INDEX）/ `--fix`（迁移） |

### 10.2 术语表

| 术语 | 含义 |
|------|------|
| report-v3 | 当前报告契约：8 大节 + 14 固定模块 + YAML metadata + 符号/估值表规则 |
| P0 / P1 | P0=阻断发布的结构/数据错误；P1=需人工复核的警告 |
| TAM/SAM/SOM | 理论天花板 / 当前可服务市场 / 可获得市场 |
| 14 维向量 | 案例库的标准特征向量（阶段/产能/CR3/需求/估值/盈利/政策/供给/成本/周期/海外/2008/2016/Beta） |
| HBS | `historical-stage-benchmarking`：像→不像→像 的历史对照技能 |
| 判停 | HBS 分支：找不到相似驱动力时诚实告知"没有好对标"，不强行匹配 |
| 方案 A | 技能关系规范化规则：每对技能只保留一种关系，`depends-on > composes-with > contrasts-with` |

### 10.3 本次 walkthrough 验证清单

- [x] `ci_check.py` 6 项 PASS
- [x] 3 份报告 check.json 均 `passed: true`
- [x] 3 份历史对照文件存在、链接可达
- [x] 22 个案例 14 维单值、关系 0 问题
- [x] 技能关系多类型 0 对
- [x] 全库 81 个 Markdown、0 断链
