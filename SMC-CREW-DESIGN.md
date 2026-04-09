# SMC-Crew 设计文档

## 核心理念

AI-native 公司模式：一个完全自主运转的团队，角色包括 SMC-PM、SMC-Expert-A、SMC-Expert-B、SMC-Developer、SMC-CodeReviewer、SMC-StrategyReviewer、SMC-RiskManager、SMC-DataKeeper。每个角色独立成长，共享 board.md 作为唯一事实来源。

## 角色设计

### SMC-PM (Coordinator)
**核心职责**：管流程和决策，不写代码。

**自成长技能**：
- 阶段推进判断（什么时候进下一步，什么时候回滚）
- 资源配置（每个阶段分配多少资源）
- 版本管理（v1→v2→v3 的衔接协议）
- 知识压缩触发（什么时候该压缩 knowledge bases）

**产出**：compass.md、board.md、evolution-log.md

**压缩触发**：> 60行时精简，保留核心规则 + 最新状态 + 决策摘要

---

### SMC-Expert-A (SMC Strategy Expert) — model: claude
**核心职责**：提出交易策略，评判策略好不好。

**自成长技能**：
- 策略提案（参数级别，不是模糊方向）
- 策略评审（判断代码实现是否符合策略意图）
- 死路识别（这个策略方向是不是已经死路了）
- 理论更新（发现新理论/新数据时更新知识库）

**产出**：knowledge/expert-a.md、consultations/

**压缩触发**：> 400行时摘录关键结论，删除已验证的细节

---

### SMC-Expert-B (Quant Engineering Expert) — model: codex
**核心职责**：评判工程上能不能做，backtest 可不可信。

**自成长技能**：
- 架构设计（模块怎么拆、接口怎么定义）
- Backtest 审计（检测 bias：look-ahead、survivorship，检测 slippage/fees 是否合理）
- 性能评估（回测要多久，优化方向在哪）
- 工程反模式（哪些实现方式在实盘会出问题）

**产出**：knowledge/expert-b.md、consultations/

**压缩触发**：> 400行时摘录关键结论，删除已验证的细节

---

### SMC-Developer
**核心职责**：只写代码，不做决策。

**自成长技能**：
- 代码模式库（哪些 pattern 在回测里有效、在实盘里稳定）
- 测试设计（为每个功能写测试用例，覆盖边界情况）
- Bug 根因分析（出错了不只是修，要记录为什么错）
- 重构能力（在不破坏功能的前提下简化代码）

**产出**：knowledge/developer.md、tests/

**压缩触发**：> 250行时精简，保留 Bug 模式 + 有效 pattern，删除具体案例

---

### SMC-CodeReviewer
**核心职责**：代码质量守门员。

**自成长技能**：
- 失败模式库（见过的 bug 类型、见过的策略失败原因）
- 回归测试追踪（每次修改影响了哪些测试结果）
- 代码味道识别（哪里有 complexity 过高的风险）

**产出**：verification/code-review.md

**压缩触发**：> 300行时摘录关键结论

---

### SMC-StrategyReviewer
**核心职责**：策略逻辑守门员。

**自成长技能**：
- 策略一致性检查（代码实现是否和 spec 一致）
- 参数合理性检查（止损距离、手数、止盈/止损比）
- 策略失效模式识别

**产出**：verification/strategy-review.md

**压缩触发**：> 300行时摘录关键结论

---

### SMC-RiskManager
**核心职责**：风险管理，止盈止损校验。

**自成长技能**：
- Pre-trade Validation（每次生成交易信号后校验）：
  - 止损距离 × 手数 ≤ $5
  - 止盈/止损比 ≥ 1.5
  - 手续费估算已计入
  - Killzone 允许交易
- 资金曲线监控（最大回撤是否超标）
- 异常风险事件记录

**产出**：risk-patterns.md、risk-events.md

**压缩触发**：> 200行时摘录风险事件摘要 + 阈值，删除详细案例

---

### SMC-DataKeeper
**核心职责**：回测数据管理，参数热力图，版本对比。

**自成长技能**：
- 维护 backtest-results.jsonl（每次回测结果）
- 维护 param-heatmap.json（参数组合效果表）
- 版本对比报告生成（v1 vs v2 vs v3）
- 下一轮优化的数据依据

**产出**：backtest-results.jsonl、param-heatmap.json、archive/vN/

**压缩触发**：不压缩，只追加，定期归档旧版本数据到 archive/

---

## 完整角色清单

```
SMC-PM             — 协调者，流程管理，版本推进
SMC-Expert-A       — SMC策略专家（claude模型）
SMC-Expert-B       — 量化工程专家（codex模型）
SMC-Developer      — 代码实现
SMC-CodeReviewer   — 代码质量审计
SMC-StrategyReviewer — 策略逻辑审计
SMC-RiskManager    — 风险管理，止盈止损校验
SMC-DataKeeper     — 回测数据管理，参数热力图，版本对比
```

---

## 版本管理

### 宪法文件 smc-constitution.md
核心原则永不违背：
- $5 max loss 是铁律
- 回测胜率 < 40% 或盈亏比 < 1.2 的方向直接放弃
- 专家分歧 > 3次无果 → HARDWARE_BLOCK
- 代码变更必须通过 CodeReviewer
- 策略变更必须通过 StrategyReviewer

### 版本切换协议
- 每个大版本结束后，相关文件归档到 `archive/vN/`
- v(N+1) 开始前，DataKeeper 生成版本对比报告
- PM 读取对比报告，决定下一版本的优化方向

---

## 待讨论

- [ ] Expert 可以是多个吗？（用户说可以用多个模型）
- [ ] SMC-Speaker 是否需要独立角色？（翻译/整理专家输出给 PM）
- [ ] Archive 机制具体怎么实施？

---

## 状态

**设计阶段**，等待用户确认后开始写各个 skill。
