---
name: change-logger
description: 自动记录项目中的所有数据修订操作，生成详细的变更日志。当检测到文件修改、数据修订、CSV更新时自动触发。也应在用户提到以下情况时使用：记录修改、写入日志、变更历史、修订记录、追踪变更、审计日志。特别重要：每次使用 extraction-reviewer 修复数据后必须自动触发此技能记录变更。即使用户没有明确说"记录"，只要有文件被修改就应该使用此技能。
---

# 变更日志记录器

## 目标

自动追踪和记录项目中的所有数据修订操作，使用 Git diff 对比变更，生成包含修改人、时间、具体变更内容的详细日志。

## 核心原则

1. **自动触发**：检测到文件修订后自动记录，无需用户手动触发
2. **字段级追踪**：记录 CSV 文件中具体哪些行、哪些字段被修改
3. **完整溯源**：记录修改人（Git 用户）、修改时间、修改原因
4. **结构化存储**：按年月组织日志，便于检索和审计

## 工作流程

### 第一步：检测变更

监听以下触发条件：
- extraction-reviewer 生成修订数据后
- 用户手动修改 CSV/JSON 文件后
- 用户明确要求"记录这次修改"

### 第二步：获取修改人信息

从 Git 配置读取用户信息：
```bash
git config user.name
git config user.email
```

如果不在 Git 仓库中，使用系统用户名。

### 第三步：对比变更内容

使用 `git diff` 对比文件变更：
```bash
# 对比工作区与暂存区
git diff <file_path>

# 对比特定提交
git diff <commit1> <commit2> <file_path>
```

对于 CSV 文件，解析 diff 输出提取：
- 修改的行号
- 修改的字段名
- 修改前的值
- 修改后的值

详细解析规则见：[references/git-diff-解析.md](references/git-diff-解析.md)

### 第四步：生成变更日志

创建日志文件：
```
99-日志文档/
└── [年月]/
    └── 变更日志_[日期].md
```

日志格式见：[references/日志格式规范.md](references/日志格式规范.md)

### 第五步：追加到日志文件

如果当天的日志文件已存在，追加新记录；否则创建新文件。

## 使用方法

### 方式一：自动触发（推荐）

在 extraction-reviewer 完成数据修订后自动调用：
```python
# 在 reviewer.py 中集成
from change_logger import log_changes

# 修订完成后
log_changes(
    modified_files=["04-审查与修订/古画品录/修订数据/M2.1_历史人物_修订版_20260419.csv"],
    reason="extraction-reviewer 自动修复：字段名错误、书名格式"
)
```

### 方式二：手动触发

用户明确要求时：
```bash
python .claude/skills/change-logger/scripts/logger.py \
  --files 03-初步抽取/古画品录/M2.1_历史人物.csv \
  --reason "手动修正人物生卒年份"
```

## 日志输出示例

示例见：[examples/变更日志示例.md](examples/变更日志示例.md)

## 与 extraction-reviewer 集成

extraction-reviewer 在生成修订数据后，自动调用 change-logger：

1. 读取审查报告中的修复项
2. 提取修改的文件列表
3. 调用 logger.py 生成变更日志
4. 将日志路径写入审查报告

集成方式见：[references/集成指南.md](references/集成指南.md)

## 扩展阅读

- [日志格式规范](references/日志格式规范.md) - 变更日志的结构说明
- [Git Diff 解析](references/git-diff-解析.md) - 如何解析 Git diff 输出
- [集成指南](references/集成指南.md) - 与其他技能集成的方法

## 技术实现

核心脚本：
- `scripts/logger.py` - 主日志记录逻辑
- `scripts/diff_parser.py` - Git diff 解析器

依赖：subprocess, datetime, pathlib, re

Git 要求：项目必须是 Git 仓库
