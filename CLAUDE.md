# CLAUDE.md

本文档为 Claude Code 提供项目工作指南。

## 项目概述

**中国人物画知识图谱**：将古代画史文献转化为结构化知识图谱，采用 M3 三层框架（宏观-中观-微观）构建系统性知识表达。

**核心原则**：
- 所有数据必须可追溯到原始文献（书名、章节、原文）
- 采用混合范式：规则 + LLM + 人工抽检
- 支持增量更新和质量迭代

## 技能系统

项目技能存储在 `.claude/skills/` 目录，遵循渐进式披露原则（主文档 <300 行）。

### extraction-reviewer
**用途**：数据质量审查与自动修复  
**触发**：用户提到"审查"、"检查"、"验证"、"数据质量"等关键词  
**输出**：审查报告、问题清单、修订数据、统计数据

详细文档：[.claude/skills/extraction-reviewer/SKILL.md](.claude/skills/extraction-reviewer/SKILL.md)

### change-logger
**用途**：自动记录数据修订操作  
**触发**：extraction-reviewer 修复数据后自动触发，或检测到文件修改  
**输出**：变更日志（按年月组织）

详细文档：[.claude/skills/change-logger/SKILL.md](.claude/skills/change-logger/SKILL.md)

### 技能协作流程

```
用户请求审查数据
    ↓
extraction-reviewer 执行审查
    ↓
生成修订数据
    ↓
change-logger 自动触发
    ↓
记录变更日志
```

## 数据结构

**规范文档**：[01-元知识/中国人物画知识图谱数据结构v1_4.md](01-元知识/中国人物画知识图谱数据结构v1_4.md)

### M3 三层框架

- **M1 宏观层**：时序本体、空间地理本体、图像志题材分类
- **M2 中观层**：历史人物核心表、履历与时空轨迹、社会关系实例  
- **M3 微观层**：作品实体表、文献著录与品评

每部文献抽取后生成 8 个 CSV 文件（M1.1-M1.3, M2.1-M2.3, M3.1-M3.2）。

### 核心规范速查

**溯源字段**（所有表必填）：
- `source_book`：《书名》格式
- `source_chapter`：卷次·章节名
- `source_text`：原文引用

**ID 前缀**：
- 人物 `meso_`、作品 `micro_`、时序 `period_`、地理 `loc_`、图像志 `icon_`

**枚举值**：
- 角色：Painter, Critic, Collector, Calligrapher, Scholar, Patron, Other
- 状态：Extant, Lost, Attributed, Copy, Unknown
- 材质：Silk, Paper, Wall, Wood, Other, Unknown

详细规范见：[.claude/references/data-schema.md](.claude/references/data-schema.md)

## 数据处理工作流

```
02-原始文档/*.txt
    ↓
文本校勘与规范化
    ↓
结构切分（卷-条-段）
    ↓
实体抽取（人物、地名、作品）
    ↓
事件识别（履历、创作、交游）
    ↓
关系构建（师承、鉴藏、著录）
    ↓
本体映射（M1/M2/M3表格）
    ↓
质量控制与推理验证
    ↓
03-初步抽取/[文献名]/*.csv
    ↓
数据审查与修订（extraction-reviewer）
    ↓
04-审查与修订/[文献名]/修订数据/*.csv
    ↓
变更日志记录（change-logger）
    ↓
04-审查与修订/变更日志/[年月]/
```

## 数据质量控制

### 常见问题类型

1. **字段名错误**：`source.chapter` → `source_chapter`
2. **格式不规范**：缺少书名号、ID 前缀错误
3. **必填字段为空**：`source_book`、`person_id` 等
4. **枚举值错误**：中文值 → 英文标准值

详细问题分类见：[.claude/references/quality-issues.md](.claude/references/quality-issues.md)

### CSV 处理规范

- **编码**：UTF-8-BOM
- **索引**：始终使用 `index_col=False`
- **行号**：CSV 行号 = DataFrame 索引 + 2

详细规范见：[.claude/references/csv-handling.md](.claude/references/csv-handling.md)

## 文件组织

### 目录结构

```
中国人物画知识图谱/
├── .claude/
│   ├── skills/                    # 项目技能
│   │   ├── extraction-reviewer/
│   │   └── change-logger/
│   └── references/                # 详细文档
│       ├── data-schema.md
│       ├── quality-issues.md
│       ├── csv-handling.md
│       ├── foreign-keys.md
│       └── examples.md
├── 01-元知识/                     # 规范文档
│   └── 中国人物画知识图谱数据结构v1_4.md
├── 02-原始文档/                   # 原始文本（10部文献）
├── 03-初步抽取/                   # 结构化数据
│   └── [文献名]/                  # 每部文献一个子目录
│       ├── M1.1_时序本体.csv
│       ├── M1.2_空间地理本体.csv
│       ├── M1.3_图像志题材分类.csv
│       ├── M2.1_历史人物核心表.csv
│       ├── M2.2_履历与时空轨迹.csv
│       ├── M2.3_社会关系实例.csv
│       ├── M3.1_作品实体表.csv
│       └── M3.2_文献著录与品评.csv
└── 04-审查与修订/                 # 质量控制输出
    ├── [文献名]/
    │   ├── 报告/
    │   ├── 修订数据/
    │   └── 统计/
    └── 变更日志/
        └── [年月]/
```

### 文件命名规范

**CSV 文件**：
- 格式：`M[层级].[序号]_[表名]_[文献名].csv`
- 示例：`M2.1_历史人物核心表_古画品录.csv`

**修订版文件**：
- 格式：`[原文件名]_修订版_[时间戳].csv`
- 示例：`M2.1_历史人物核心表_修订版_20260419_165338.csv`

## 外键关联关系

跨表引用必须保证完整性：

- `M2.2.person_ref` → `M2.1.person_id`
- `M2.3.source_id/target_id` → `M2.1.person_id`
- `M3.1.creator_ref` → `M2.1.person_id`
- `M3.1.period_ref` → `M1.1.period_id`
- `M3.1.icon_ref` → `M1.3.icon_id`
- `M3.2.target_ref` → `M3.1.work_id` 或 `M2.1.person_id`
- `M3.2.author_ref` → `M2.1.person_id`

详细关系图见：[.claude/references/foreign-keys.md](.claude/references/foreign-keys.md)

## 已处理文献

当前工作区已完成初步抽取的 10 部文献：
1. 《历代名画记》（唐·张彦远）- 2041条记录
2. 《古画品录》（南朝·谢赫）
3. 《续画品》（唐·李嗣真）
4. 《续画品录》（唐·李嗣真）
5. 《贞观公私画史》（唐·裴孝源）
6. 《唐朝名画录》（唐·朱景玄）
7. 《笔法记》（唐·荆浩）
8. 《后画录》（唐·朱景玄）
9. 《圣朝名画评》（北宋·刘道醇）
10. 《益州名画录》（北宋·黄休复）

## 最佳实践

1. **始终先读取规范文档**：确保理解字段定义和格式要求
2. **使用 extraction-reviewer 技能**：自动化质量检查
3. **保留原始数据**：修订后的数据保存到新文件，不覆盖原文件
4. **自动记录变更**：change-logger 会自动追踪所有修订操作
5. **人工复核**：自动修复后仍需人工检查严重问题
6. **增量更新**：支持对已抽取数据的迭代改进

## 常用命令速查

```bash
# 审查单个文件
/extraction-reviewer --file 03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv

# 审查整个文献目录
/extraction-reviewer --dir 03-初步抽取/古画品录

# 统计记录数
wc -l 03-初步抽取/历代名画记/*.csv

# 检查编码
file -I 03-初步抽取/古画品录/*.csv
```

详细命令参考见：[.claude/references/examples.md](.claude/references/examples.md)

## 项目状态

- **数据结构版本**：M3 Framework v1.6
- **已完成文献**：10部（初步抽取）
- **总记录数**：约 2041 条（仅《历代名画记》）
- **最后更新**：2026-04-19
