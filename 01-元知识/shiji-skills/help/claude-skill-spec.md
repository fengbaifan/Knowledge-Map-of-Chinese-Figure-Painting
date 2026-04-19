# Claude Skill 构造规范

> 本规范面向项目中所有 skill 的设计者，目标是构造出触发准确、执行可靠、易于维护的 skill。

---

## 一、什么是 Skill

Skill 是一份结构化的指令包，放置在 Claude 的上下文中，指导 Claude 在特定任务场景下如何工作。Claude 通过阅读 `available_skills` 列表中每个 skill 的 **名称 + 描述**，决定是否加载该 skill 的完整内容。

Skill 解决的核心问题：
- **触发**：Claude 什么时候应该用这个 skill？
- **执行**：Claude 拿到 skill 后应该做什么、怎么做？
- **输出**：交付物的格式和质量标准是什么？

---

## 二、目录结构

```
skill-name/
├── SKILL.md              # 必须，主指令文件
└── resources/            # 可选，按需加载的附属资源
    ├── scripts/          # 可执行脚本（确定性/重复性操作）
    ├── references/       # 参考文档（按需读入上下文）
    └── assets/           # 模板、字体、图标等静态文件
```

**命名规则**：skill 目录名与 `SKILL.md` frontmatter 中的 `name` 字段保持一致，使用小写 kebab-case，如 `pdf-export`、`shiji-parser`。

---

## 三、SKILL.md 结构

### 3.1 Frontmatter（必须）

```yaml
---
name: skill-name
description: |
  一到两句话说明这个 skill 做什么、什么时候触发。
  要略显"主动"——明确列出应当触发的典型场景，
  以防 Claude 在该用时犹豫不决。
---
```

**Description 写作要点：**

| 要素 | 说明 |
|------|------|
| **做什么** | 一句话概括 skill 的核心能力 |
| **什么时候用** | 列举典型触发场景（用户短语、文件类型、任务类型） |
| **主动性** | 加一句"遇到 X/Y/Z 情况，务必使用本 skill" |
| **长度** | 100 词以内，越精准越好 |

**反例（过于被动）：**
```
处理 PDF 文件的工具。
```

**正例（主动明确）：**
```
用于读取、提取、合并、拆分或创建 PDF 文件。
只要用户提到 .pdf 文件、需要导出为 PDF、或要对 PDF 执行任何操作，
都应使用本 skill，即使用户未明确说"用 PDF skill"。
```

---

### 3.2 正文（SKILL.md body）

正文是 Claude 加载 skill 后读到的核心指令。**目标长度 < 500 行**。

推荐结构如下（根据实际情况取舍）：

```markdown
# Skill 名称

## 概述（可选）
一句话补充说明，澄清 description 未覆盖的边界。

## 前置条件（可选）
- 依赖工具：bash、python 3.x、某 npm 包……
- 需要的输入：文件路径、API key 等

## 核心流程
Step-by-step 的执行指令。用祈使句（imperative）。

## 输出格式
明确规定交付物的结构、文件名、编码等。

## 边界情况处理
列出已知的特殊情况及对应处理方式。

## 示例（可选）
Input / Output 对照，帮助 Claude 理解期望结果。

## 参考资源（可选）
指向 resources/ 目录下的文件，说明何时去读。
```

---

## 四、三级加载模型

Skill 内容分三级，按需加载，避免撑大上下文：

```
Level 1 — Metadata（始终在上下文）
  name + description，约 100 词
  ↓ 触发后
Level 2 — SKILL.md 正文（skill 触发时载入）
  核心流程指令，< 500 行
  ↓ 执行时按需
Level 3 — resources/ 附属文件（执行中按需读取）
  脚本直接执行，参考文档按需 view，无大小限制
```

**关键原则**：
- 正文接近 500 行时，将详细内容迁移到 `resources/references/`，并在正文中用明确指针说明何时去读
- 大型参考文件（> 300 行）必须加目录
- 脚本优于内联代码：确定性步骤写成可执行脚本，避免 Claude 每次重新生成

---

## 五、写作风格规范

### 5.1 指令语气

- **用祈使句**：`读取文件` `提取表格` `保存到 outputs/`
- **避免委婉**：不写"可以考虑"、"可能需要"，直接说"必须"或"应该"
- **解释原因**：说明为什么某步骤重要，而不只是"必须这样做"。Claude 理解原因后执行更准确

### 5.2 输出格式定义

用固定模板定义输出，减少歧义：

```markdown
## 输出格式
ALWAYS 使用以下结构：

# [标题]
## 摘要
## 主体内容
## 结论
```

### 5.3 示例模式

```markdown
## 示例

**示例 1**
输入：用户上传了一份扫描版合同 PDF
输出：提取出的文本保存至 /mnt/user-data/outputs/contract.txt，
      并在对话中汇报页数、语言、是否含表格
```

### 5.4 "最少意外"原则

Skill 的实际行为应与 description 描述完全一致，不能出现用户没有预期的副作用（如静默删除文件、发送网络请求等）。

---

## 六、resources/ 目录规范

### scripts/
- 每个脚本完成一项明确任务
- 顶部注释说明：用途、输入参数、输出
- 优先用 Python（环境稳定）；需要 npm 包时在 SKILL.md 中声明依赖

### references/
- 文件名语义明确：`aws.md`、`error-codes.md`、`api-schema.json`
- 超过 300 行的文件加目录
- 在 SKILL.md 中明确说明"当遇到 X 情况时，读取 `references/X.md`"

### assets/
- 模板文件（.docx、.pptx 等）放这里
- 文件名加版本号或日期后缀，如 `report-template-v2.docx`

### 多变体组织模式

当 skill 支持多个框架/平台时：

```
cloud-deploy/
├── SKILL.md        # 流程概述 + 选择逻辑
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

SKILL.md 中写明选择逻辑："根据用户指定的平台，读取对应的 references/xxx.md"。

---

## 七、触发优化

Skill 的触发完全依赖 description。触发失败的主要原因：

1. **描述太宽泛**：没有列出具体的触发词/场景
2. **描述太保守**：没有"主动推荐"自己
3. **与其他 skill 重叠**：边界模糊导致 Claude 选错

**触发 checklist：**

- [ ] Description 包含用户可能说的关键短语（如"Word 文档"、"合并 PDF"）
- [ ] Description 说明了文件类型（如`.docx`、`.xlsx`）
- [ ] Description 有一句主动推荐："遇到 X 情况，务必使用本 skill"
- [ ] 与其他 skill 的边界在 description 中有区分（可选，边界不清晰时加）

---

## 八、安全与合规

- Skill 不得包含恶意代码、漏洞利用代码或任何可能危害系统的内容
- Skill 的实际行为必须与其 description 一致，不得误导用户
- 涉及文件操作时，明确说明读写路径（用户上传文件在 `/mnt/user-data/uploads/`，输出文件放 `/mnt/user-data/outputs/`）
- 涉及网络请求时，在 description 和正文中均需声明

---

## 九、快速自检清单

在提交一个新 skill 前，过一遍：

**结构**
- [ ] `SKILL.md` 存在且有 YAML frontmatter
- [ ] `name` 与目录名一致
- [ ] `description` 在 100 词以内
- [ ] 正文 < 500 行（超出则迁移到 references/）

**触发**
- [ ] Description 列出了典型触发场景
- [ ] Description 包含主动推荐语句
- [ ] 与现有 skill 无明显重叠或边界已说清

**执行**
- [ ] 所有步骤用祈使句
- [ ] 输出格式明确定义
- [ ] 边界情况有处理说明
- [ ] resources/ 中的文件有明确的读取时机说明

**质量**
- [ ] 用 2-3 个真实用户提示测试过
- [ ] 执行结果符合预期

---

## 十、最小可用 Skill 模板

```markdown
---
name: my-skill
description: |
  [一句话：这个 skill 做什么]。
  [一句话：适用场景列举，如"当用户提到 X、Y、Z 时"]。
  遇到上述情况，务必使用本 skill。
---

# My Skill

## 流程

1. [步骤一]
2. [步骤二]
3. 将结果保存到 `/mnt/user-data/outputs/`

## 输出格式

[描述交付物结构]

## 注意事项

- [已知边界情况一]
- [已知边界情况二]
```

---

*本规范基于 Anthropic skill-creator 官方实践整理，适用于本项目所有自定义 skill 的设计与审查。*
