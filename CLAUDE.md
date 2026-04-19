# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

中国人物画知识图谱项目：将古代画史文献转化为结构化知识图谱，采用 M3 三层框架（宏观-中观-微观）构建系统性知识表达。

**核心原则**：
- 所有数据必须可追溯到原始文献（书名、章节、原文）
- 采用混合范式：规则 + LLM + 人工抽检
- 支持增量更新和质量迭代

## 技能管理规范

**重要：所有项目相关的技能必须创建在本项目的 `.claude/skills/` 目录下。**

**技能存储位置**：
- **项目级技能**（必须）：`.claude/skills/[技能名]/`
- **全局级技能**（可选备份）：`~/.claude/skills/[技能名]/`

**技能创建规则**：
1. 所有新技能必须首先创建在项目的 `.claude/skills/` 目录
2. 技能必须遵循 Claude Code 标准格式（YAML frontmatter + 渐进式披露）
3. 技能目录结构：
   ```
   .claude/skills/[技能名]/
   ├── SKILL.md          # 主文档（<500 行）
   ├── references/       # 详细文档
   ├── scripts/          # 可执行脚本
   ├── examples/         # 示例文件
   └── evals/            # 测试用例
   ```
4. 禁止在项目根目录或其他位置创建技能目录（如 `05-技能库/` 等）

**现有技能**：
- `extraction-reviewer`：数据质量审查技能
- `change-logger`：变更日志记录技能

## 数据结构规范

**规范文档位置**：`01-元知识/中国人物画知识图谱数据结构v1_4.md`

### M3 三层框架

- **M1 宏观层**：时序本体、空间地理本体、图像志题材分类
- **M2 中观层**：历史人物核心表、履历与时空轨迹、社会关系实例  
- **M3 微观层**：作品实体表、文献著录与品评

每部文献抽取后生成 8 个 CSV 文件（M1.1-M1.3, M2.1-M2.3, M3.1-M3.2）。

### 溯源字段规范（所有表必须遵守）

| 字段 | 必填性 | 格式规范 |
|------|--------|----------|
| `source_book` | 必填 | 使用书名号《》，如《历代名画记》 |
| `source_chapter` | 强烈推荐 | 格式：卷次·章节名，如"卷一·顾野王" |
| `source_text` | 推荐 | 保留原文标点，使用""标注引文 |
| `source_page` | 可选 | 如"第12页"、"四库本卷三" |

### ID 命名规范

- **时序本体**：`period_` 前缀（如 `period_tang`）
- **空间地理**：`loc_` 前缀（如 `loc_changan`）
- **图像志**：`icon_` 前缀（如 `icon_portrait`）
- **人物**：`meso_` 前缀（如 `meso_gu_kaizhi`）
- **履历**：`cv_` 前缀（如 `cv_001`）
- **关系**：`rel_` 前缀（如 `rel_001`）
- **作品**：`micro_` 前缀（如 `micro_luoshen_fu`）
- **文献**：`lit_` 前缀（如 `lit_001`）

### 枚举值约束

**人物角色** (`primary_role`)：
- Painter, Critic, Collector, Calligrapher, Scholar, Patron, Other

**作品状态** (`status`)：
- Extant（存世）, Lost（佚失）, Attributed（传）, Copy（摹本）, Unknown

**作品材质** (`support`)：
- Silk（绢本）, Paper（纸本）, Wall（壁画）, Wood（木板）, Other, Unknown

**关系类型** (`relation_type`)：
- Teacher, Student, Friend, Colleague, Spouse, Parent, Child, Sibling, Other

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
数据审查与修订
    ↓
04-审查与修订/[文献名]/修订数据/*.csv
```

## 数据质量审查

### 使用 extraction-reviewer 技能

**技能位置**：
- 项目级：`.claude/skills/extraction-reviewer/`（推荐）
- 全局级：`~/.claude/skills/extraction-reviewer/`

**触发方式**：
- 用户要求"审查"、"检查"、"验证"抽取数据
- 提到数据完整性、准确性、健康程度
- 提到字段缺失、格式错误、外键检查等数据质量问题

**审查脚本**：
```bash
# 审查单个文件
python .claude/skills/extraction-reviewer/scripts/reviewer.py \
  --file 03-初步抽取/[文献名]/[表名].csv \
  --output-dir 04-审查与修订/[文献名]

# 审查整个目录
python .claude/skills/extraction-reviewer/scripts/reviewer.py \
  --dir 03-初步抽取/[文献名] \
  --output-dir 04-审查与修订/[文献名]
```

**输出结构**：
```
04-审查与修订/
└── [文献名]/
    ├── 报告/
    │   ├── 审查报告_[时间戳].md          # 人类可读报告
    │   └── 问题清单_[时间戳].csv         # 可筛选问题列表
    ├── 修订数据/
    │   └── [原文件名]_修订版_[时间戳].csv  # 自动修复后的数据
    └── 统计/
        └── 统计数据_[时间戳].json        # 质量统计
```

## 变更日志记录

### 使用 change-logger 技能

**技能位置**：
- 项目级：`.claude/skills/change-logger/`（推荐）
- 全局级：`~/.claude/skills/change-logger/`

**触发方式**：
- 自动触发：每次使用 extraction-reviewer 修复数据后自动记录
- 手动触发：用户要求"记录修改"、"写入日志"、"记录变更"
- 检测到文件修改、数据修订、CSV 更新时

**日志脚本**：
```bash
# 手动记录变更
python .claude/skills/change-logger/scripts/logger.py \
  --files 04-审查与修订/[文献名]/修订数据/[文件名].csv \
  --reason "修改原因说明" \
  --original-file 03-初步抽取/[文献名]/[原文件名].csv \
  --report-file 04-审查与修订/[文献名]/报告/审查报告_[时间戳].md
```

**输出结构**：
```
99-日志文档/
└── [年月]/
    └── 变更日志_[日期].md
```

**日志内容**：
- 修改人（Git 用户名 + 邮箱）
- 修改时间（精确到秒）
- 修改类型（自动修复 / 手动修订）
- 影响范围（文件路径、修改行数、字段数）
- 修改内容详情（字段级对比，使用 git diff）
- 修改原因
- 相关文件（审查报告、问题清单、Git commit）

**与 extraction-reviewer 集成**：
- extraction-reviewer 完成数据修订后自动调用 change-logger
- 变更日志路径会写入审查报告
- 支持追溯每次修订的完整历史

### 常见数据质量问题

1. **字段名错误**：
   - `source.chapter` → `source_chapter`
   - `originalsource_sentence` → `source_text`

2. **格式不规范**：
   - 书名缺少书名号：`历代名画记` → `《历代名画记》`
   - ID 前缀错误：`work_001` → `micro_work_001`

3. **必填字段为空**：
   - `source_book` 为空
   - `person_id` 为空

4. **枚举值错误**：
   - `status: 存世` → 应为 `Extant`
   - `primary_role: 画家` → 应为 `Painter`

### CSV 文件处理注意事项

**编码**：所有 CSV 文件使用 UTF-8-BOM 编码
```python
df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False)
```

**索引处理**：防止第一列被误认为索引
```python
# 始终使用 index_col=False
df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False)
```

**行号计算**：CSV 行号 = DataFrame 索引 + 2（表头占1行）
```python
if isinstance(idx, tuple):
    row_num = int(idx[0]) + 2  # 多级索引
else:
    row_num = int(idx) + 2      # 单级索引
```

## 技能体系

### 元技能层（01-元知识/shiji-skills/00-META-*.md）

从史记项目迁移的通用方法论技能：
- 反思闭环、迭代工作流、冷启动方法
- 柳叶刀方法（问题分层拆解）
- 知识压缩、标注体系设计
- 质量控制、数据融合、Agent提示词工程

### 管线技能层（01-元知识/shiji-skills/SKILL_*.md）

10 个阶段的数据处理技能：
- SKILL_00：管线总览
- SKILL_01：古籍校勘（统一书名、卷次、标点、异体字）
- SKILL_02：结构分析（卷-条-段切分）
- SKILL_03：实体构建（人物、地名、题材识别）
- SKILL_04：事件构建（生平轨迹提取）
- SKILL_05：关系构建（人物关系、作品关系）
- SKILL_06：本体构造（映射到 M1/M2/M3）
- SKILL_07：逻辑推理（断代推断、消歧）
- SKILL_08：知识库管驭（质量量化）
- SKILL_09：应用构造（检索、可视化）

**技能索引**：`01-元知识/shiji-skills/INDEX.md`

## 文件组织规范

### 目录结构

```
中国人物画知识图谱/
├── 01-元知识/                    # 规范与技能
│   ├── shiji-skills/             # 技能库（104个文件）
│   └── 中国人物画知识图谱数据结构v1_4.md
├── 02-原始文档/                  # 原始文本（10部文献）
├── 03-初步抽取/                  # 结构化数据
│   └── [文献名]/                 # 每部文献一个子目录
│       ├── M1.1_时序本体.csv
│       ├── M1.2_空间地理本体.csv
│       ├── M1.3_图像志题材分类.csv
│       ├── M2.1_历史人物核心表.csv
│       ├── M2.2_履历与时空轨迹.csv
│       ├── M2.3_社会关系实例.csv
│       ├── M3.1_作品实体表.csv
│       └── M3.2_文献著录与品评.csv
└── 04-审查与修订/                # 质量控制输出
    └── [文献名]/
        ├── 报告/
        ├── 修订数据/
        └── 统计/
└── 99-日志文档/                  # 变更日志
    └── [年月]/
        └── 变更日志_[日期].md
```

### 文件命名规范

**CSV 文件**：
- 格式：`M[层级].[序号]_[表名]_[文献名].csv` 或 `M[层级].[序号]_[表名]（[文献名]）.csv`
- 示例：`M2.1_历史人物核心表_古画品录.csv`

**修订版文件**：
- 格式：`[原文件名]_修订版_[时间戳].csv`
- 示例：`M2.1_历史人物核心表_修订版_20260419_165338.csv`

**报告文件**：
- 格式：`审查报告_[时间戳].md` 或 `问题清单_[时间戳].csv`

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

## 外键关联关系

跨表引用必须保证完整性：

- `M2.2_履历与时空轨迹.person_ref` → `M2.1_历史人物核心表.person_id`
- `M2.3_社会关系实例.source_id/target_id` → `M2.1_历史人物核心表.person_id`
- `M3.1_作品实体表.creator_ref` → `M2.1_历史人物核心表.person_id`
- `M3.1_作品实体表.period_ref` → `M1.1_时序本体.period_id`
- `M3.1_作品实体表.icon_ref` → `M1.3_图像志题材分类.icon_id`
- `M3.2_文献著录与品评.target_ref` → `M3.1_作品实体表.work_id` 或 `M2.1_历史人物核心表.person_id`
- `M3.2_文献著录与品评.author_ref` → `M2.1_历史人物核心表.person_id`

## 数据处理最佳实践

1. **始终先读取规范文档**：确保理解字段定义和格式要求
2. **使用 extraction-reviewer 技能**：自动化质量检查
3. **保留原始数据**：修订后的数据保存到新文件，不覆盖原文件
4. **自动记录变更**：使用 change-logger 记录所有修订操作
5. **人工复核**：自动修复后仍需人工检查严重问题
6. **增量更新**：支持对已抽取数据的迭代改进

## 常用命令

### 数据审查
```bash
# 审查单个文件
python .claude/skills/extraction-reviewer/scripts/reviewer.py \
  --file 03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv \
  --output-dir 04-审查与修订/古画品录

# 审查整个文献目录
python .claude/skills/extraction-reviewer/scripts/reviewer.py \
  --dir 03-初步抽取/古画品录 \
  --output-dir 04-审查与修订/古画品录
```

### 变更日志
```bash
# 手动记录变更
python .claude/skills/change-logger/scripts/logger.py \
  --files 04-审查与修订/古画品录/修订数据/M2.1_历史人物_修订版.csv \
  --reason "手动修正人物生卒年份" \
  --original-file 03-初步抽取/古画品录/M2.1_历史人物.csv

# 查看今天的变更日志
cat 99-日志文档/$(date +%Y-%m)/变更日志_$(date +%Y-%m-%d).md
```

### 查看数据统计
```bash
# 统计某部文献的记录数
wc -l 03-初步抽取/历代名画记/*.csv

# 查看字段覆盖率
head -1 03-初步抽取/历代名画记/M2.1_历史人物核心表.csv
```

### 检查数据格式
```bash
# 检查编码
file -I 03-初步抽取/古画品录/*.csv

# 检查书名号格式
grep -n "source_book" 03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv | head -5
```

## 项目状态

- **数据结构版本**：M3 Framework v1.6
- **已完成文献**：10部（初步抽取）
- **总记录数**：约 2041 条（仅《历代名画记》）
- **最后更新**：2026-04-19
