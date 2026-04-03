# FSE Skills 优化待办清单

## 🔴 Critical（立即修复）

- [ ] **C1 — 新功能不清理旧数据**：`set-mode` 重置 `current_feature` 但不清理 requirements/analysis/contracts/development 等旧数据，第二次跑 `/fse` 时旧数据污染新功能
- [ ] **C2 — 敏感信息泄露**：`auth_value`、`startup_env` 中的密码/token 明文存在 `workspace.json`，且 `.fullstack/` 未加入 `.gitignore`
- [ ] **C3 — Skill 描述被覆盖**：`## Language Requirement` 插在 frontmatter 之后导致 fse、fse-integration 在 skill 列表中显示 "Language Requirement" 而非真正描述

## 🟠 High（近期改进）

- [ ] **H1 — 状态转换无校验**：`set-state` 接受任意合法状态，LLM 出错可从 INIT 直接跳到 COMPLETED
- [ ] **H2 — 开发阶段没跑单测**：只在最后 fse-test 做测试，应在每个 dev wave 后跑项目测试套件
- [ ] **H3 — 崩溃恢复不够**：崩溃后不知道 wave 中哪些 task 完成了哪些没完成，可能重复执行。建议 per-task checkpointing + session-checkpoint 命令
- [ ] **H4 — 合约不可修改**：联调发现合约错误时只能改代码不能改合约，可能浪费 5 轮
- [ ] **H5 — 蓝湖 MCP 硬依赖**：非 lite 模式强制要求蓝湖，但很多团队不用蓝湖。建议改为可选
- [ ] **H6 — 外部分支变更检测**：用户在 FSE 外手动切了 git 分支，系统无感知
- [ ] **H7 — workspace.py 无原子写入**：写入中途崩溃可能损坏 JSON。建议 write-to-temp + os.replace()
- [ ] **H8 — 路径含空格/中文会破**：SKILL.md 模板中的 shell 命令对项目路径未加引号

## 🟡 Medium（值得做）

- [ ] **M1 — 共享内容重复 10 次**：Language Requirement + AskUserQuestion + codeagent-only 规则在每个 skill 中重复，浪费 context。建议提取 `fse-common.md`
- [ ] **M2 — 初始化太啰嗦**：3 个后端项目 = 15 轮交互。建议自动扫描子目录 + 缓存上次配置到 `.fullstack/defaults.json`
- [ ] **M3 — 不支持状态回退**：严格前进，发现需求遗漏不能回到需求阶段。建议增加 `reopen-phase` 命令 + 下游产物标记为 stale
- [ ] **M4 — 不支持部分交付**：不能说"FR-001~003 先发布，FR-004 延后"
- [ ] **M5 — 合约只支持 REST**：GraphQL、WebSocket、gRPC 不覆盖。建议检测接口范式后分派
- [ ] **M6 — Monorepo 不友好**：一个 repo 多个 app 只能注册为一个项目
- [ ] **M7 — 后端服务启动无依赖排序**：service A 依赖 service B，但联调不管顺序
- [ ] **M8 — 报告缺少监控/依赖变更/破坏性变更**等节
- [ ] **M9 — 合并冲突检测**：没在任何阶段检查 feature branch 能否干净合并
- [ ] **M10 — 人工任务阶段没有回滚 SQL**：只在 report 才有，太晚了
- [ ] **M11 — 代码审查逻辑重复 3 次**：fse-dev/fse-integration/fse-test 中 review 逻辑 copy-paste，建议提取 review-cycle 子程序

## 🟢 Nice-to-have

- [ ] **N1 — 多功能并行开发**：同工作区跑两个 feature，需 namespace `.fullstack/features/<feat-id>/`
- [ ] **N2 — session 自动清理**：防止 sessions 数组无限增长
- [ ] **N3 — codeagent 长时间运行进度可视化**：heartbeat 或 live-status.json
- [ ] **N4 — 历史功能学习**：跨 feature 复用经验，追加 `.fullstack/history.jsonl`
- [ ] **N5 — 基于信心度的弹性仪式**：需求明确时压缩前置阶段
- [ ] **N6 — 错误分级增加 WARNING / INFO 级别** + BLOCKING 子分类（SECURITY / CORRECTNESS / CONTRACT）
- [ ] **N7 — 阶段可跳过代替新增模式**：与其加 migration/hotfix/refactor 模式，不如让阶段可选跳过
