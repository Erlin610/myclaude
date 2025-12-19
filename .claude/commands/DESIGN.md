# init-project-command 设计改进

## 核心改进

### 1. 智能项目类型检测（而非硬编码角色）

**之前**:
```yaml
# 所有项目都生成这4个命令
- pm.md
- ux.md
- dev.md
- test.md
```

**现在**:
```yaml
# 根据项目类型动态推荐角色
Software项目 → product-manager, ux-designer, developer, qa-engineer
Marketing项目 → marketing-strategist, copywriter, designer, data-analyst
Video项目 → scriptwriter, director, video-editor, operations-manager
Content项目 → content-strategist, writer, seo-specialist, editor
Research项目 → research-lead, data-scientist, analyst, report-writer
```

### 2. 命令文件全英文，输出内容全中文

**文件命名规范**:
```bash
# ✅ 正确
.claude/commands/marketing-strategist.md
.claude/commands/video-editor.md
.claude/commands/content-strategist.md

# ❌ 错误
.claude/commands/市场策略师.md
.claude/commands/剪辑师.md
```

**Prompt规范**:
```markdown
---
description: Marketing Strategist mode for campaign strategy
---

You are a top-tier Marketing Strategist.

## Your Context
...

## Communication Requirements

**CRITICAL**: You MUST communicate with the user in Chinese (中文).
- All your outputs, questions, and responses must be in Chinese
- Technical terms can use English when appropriate
- Code and documentation follow project conventions

## Responsibilities
...
```

### 3. 项目类型检测逻辑

**关键词映射**:
```python
project_type_keywords = {
    "Software Development": [
        "技术栈", "API", "数据库", "用户故事", "前端", "后端",
        "架构", "代码", "开发", "测试"
    ],
    "Marketing Campaign": [
        "推广", "营销", "用户增长", "转化率", "ROI", "广告",
        "文案", "品牌", "市场"
    ],
    "Video Production": [
        "脚本", "拍摄", "剪辑", "视频", "镜头", "导演",
        "后期", "短视频", "发布"
    ],
    "Content Creation": [
        "文章", "内容", "SEO", "公众号", "博客", "编辑",
        "写作", "发布"
    ],
    "Research/Analysis": [
        "研究", "数据分析", "调研", "报告", "研报", "分析", "洞察"
    ]
}
```

### 4. 角色模板库设计

每个角色类型都有预定义的模板，包含：
- 角色职责描述
- 典型输入/输出
- 工作流程
- 与其他角色的协作关系

示例：

```yaml
marketing-strategist:
  name_en: "Marketing Strategist"
  name_zh: "市场策略师"
  description_en: "Analyze market, define target audience, create marketing strategy"
  description_zh: "分析市场，定义目标受众，制定营销策略"
  input: "Project brief, market data"
  output: "docs/marketing-strategy.md"
  next_roles: ["copywriter", "designer"]
  prompt_template: |
    You are a top-tier Marketing Strategist.

    ## Your Context
    Working on **{project_name}** project. Reference `.claude/project.yaml`.

    ## Responsibilities
    - Market analysis: Identify target market segments
    - Audience research: Define ideal customer profiles
    - Strategy formulation: Create actionable marketing plans
    - KPI definition: Set measurable success metrics

    ## Communication Requirements
    **CRITICAL**: You MUST communicate with the user in Chinese (中文).

    ## Workflow
    1. Ask clarifying questions about target market
    2. Analyze competitive landscape
    3. Define audience segments and personas
    4. Create marketing strategy document
    5. Define KPIs and success metrics

    ## Output Format
    Generate `docs/marketing-strategy.md`:
    ```markdown
    # 营销策略文档

    ## 目标市场分析
    ...

    ## 受众画像
    ...

    ## 营销策略
    ...

    ## 关键指标 (KPIs)
    ...
    ```

    ## Next Step
    After strategy is confirmed: `/copywriter`
```

### 5. 工作流编排

根据角色依赖关系自动生成工作流：

**Software项目工作流**:
```
product-manager → ux-designer → developer → qa-engineer
```

**Marketing项目工作流**:
```
marketing-strategist → copywriter → designer → data-analyst
                    ↘              ↗
```

**Video项目工作流**:
```
scriptwriter → director → video-editor → operations-manager
```

### 6. 用户确认流程

**问题1: 项目类型确认**
```
检测到的项目类型：营销推广项目
推荐团队角色：市场策略师、文案策划、设计师、数据分析师

是否正确？
- 确认，类型正确
- 需要修改项目类型
```

**问题2: 角色调整**
```
当前推荐的角色：
1. 市场策略师 (marketing-strategist) - 分析市场，制定策略
2. 文案策划 (copywriter) - 编写营销文案
3. 设计师 (designer) - 设计视觉资产
4. 数据分析师 (data-analyst) - 追踪指标，优化策略

是否需要调整？
- 确认，角色配置合适
- 需要添加角色
- 需要删除某些角色
```

## 实现状态

### ✅ 已完成
1. 核心逻辑设计
2. 项目类型检测关键词映射
3. 5种项目类型的角色推荐
4. 命令文件命名规范（英文kebab-case）
5. Prompt语言规范（英文prompt，中文输出）

### 🚧 待完成（需要补充）
1. 每个角色的完整prompt模板（目前是框架）
2. 角色之间的依赖关系定义
3. 工作流自动编排逻辑
4. 特殊项目类型的角色自定义

## 使用示例

### 案例1: 短视频制作项目

```bash
/init-project-command ~/projects/douyin-content
```

**AI分析**:
```
项目文档包含关键词: 脚本、短视频、剪辑、发布、运营
检测到项目类型: Video Production
推荐团队角色: scriptwriter, director, video-editor, operations-manager
```

**生成的命令**:
```
.claude/commands/scriptwriter.md        (英文prompt，中文输出)
.claude/commands/director.md
.claude/commands/video-editor.md
.claude/commands/operations-manager.md
.claude/commands/workflow.md
```

**工作流**:
```
/scriptwriter → 编写脚本 → docs/script.md
↓
/director → 制定拍摄计划 → docs/shooting-plan.md
↓
/video-editor → 剪辑制作 → videos/final-output.mp4
↓
/operations-manager → 发布和运营 → docs/distribution-report.md
```

### 案例2: 市场推广项目

```bash
/init-project-command ~/projects/product-launch
```

**AI分析**:
```
项目文档包含关键词: 推广、营销、用户增长、转化率、ROI
检测到项目类型: Marketing Campaign
推荐团队角色: marketing-strategist, copywriter, designer, data-analyst
```

**生成的命令**:
```
.claude/commands/marketing-strategist.md
.claude/commands/copywriter.md
.claude/commands/designer.md
.claude/commands/data-analyst.md
.claude/commands/workflow.md
```

## 下一步改进建议

### 短期（必须）
1. **补充完整的角色模板**: 为每个角色编写完整的prompt模板
2. **测试项目类型检测**: 用真实项目文档测试准确率
3. **优化用户确认流程**: 简化交互，减少问题数量

### 中期（重要）
1. **支持混合项目类型**: 例如"软件+营销"项目
2. **允许自定义角色**: 用户可以添加项目特有的角色
3. **工作流可视化**: 生成Mermaid图展示角色协作关系

### 长期（增强）
1. **角色模板市场**: 社区贡献角色模板
2. **项目类型学习**: 根据用户反馈优化检测算法
3. **多语言支持**: 支持其他语言的prompt和输出

## 关键设计决策

### 为什么命令文件用英文？
1. **一致性**: 代码库、API、工具链通常用英文
2. **可维护性**: 英文文件名在所有系统上兼容性更好
3. **可读性**: kebab-case命名清晰易读

### 为什么prompt用英文但输出用中文？
1. **Prompt质量**: 英文prompt更容易编写和维护，AI理解更准确
2. **用户体验**: 中文用户希望看到中文输出
3. **灵活性**: 在prompt中明确要求输出语言，可随时调整

### 为什么不硬编码角色？
1. **通用性**: 不同项目需要不同的团队结构
2. **准确性**: 强制PM/UX/Dev/Test对非软件项目没有意义
3. **可扩展性**: 新项目类型可以轻松添加新角色

---

**总结**: 新版本是一个真正智能的项目初始化工具，能根据项目特点推荐合适的团队角色，而不是强制使用固定的工作流。
