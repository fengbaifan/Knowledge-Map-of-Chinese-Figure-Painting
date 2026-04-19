---
name: meta-incremental-data-update
description: 增量式数据更新策略,保留已有数据成果,通过合并/覆盖机制避免重复劳动和数据丢失。适用于多轮AI推理、多数据源融合、版本演化等场景,确保数据持续积累而非被覆盖。
---

# 元技能（草稿）: 增量式数据更新 — 数据持续积累的工程策略

---

## 一、核心思想

> **"数据是资产,每次更新应该是增长而非替换"**

**增量式数据更新**（Incremental Data Update）是指在数据演化过程中,通过智能合并策略保留已有成果,只更新变化部分,避免全量重建导致的数据丢失和重复劳动。

### 核心洞察

```
传统全量更新方式:
  旧数据(V1) → 新数据(V2) → 完全替换 → 旧数据丢失

问题:
  - AI Agent第一轮推理的1000条结果被第二轮的800条覆盖
  - 人工校正的100条数据在自动化流程中被重置
  - 多数据源(MD/JSON/CSV)同步时优先级不明
  - 无法追溯数据的历史版本

增量更新方式:
  旧数据(V1) + 新数据(V2) → 智能合并 → 增量数据(V1+V2)

优势:
  - 保留所有轮次的推理成果
  - 保护人工校正数据
  - 多源数据按优先级合并
  - 版本历史完整可追溯
```

---

## 二、核心模式

### 模式1: 键值合并（Key-based Merge）

#### 适用场景
结构化数据（JSON/CSV），有唯一键（如ID/名称）

#### 合并策略

```python
# 核心逻辑：按唯一键合并，冲突时根据策略选择
old_dict = {item[key]: item for item in old_data}
new_dict = {item[key]: item for item in new_data}

merged = {}
# 保留旧数据 + 新数据覆盖/合并
for k in old_dict:
    merged[k] = new_dict[k] if k in new_dict else old_dict[k]  # prefer_new策略
# 添加新记录
for k in new_dict:
    if k not in merged:
        merged[k] = new_dict[k]
```

**三种策略**:
- `prefer_new`: 冲突时新数据优先
- `prefer_old`: 冲突时旧数据优先
- `merge_fields`: 字段级合并（新字段非空则更新）

#### 本项目实例：姓氏数据合并

**场景**:
- 旧JSON: 2053人姓氏数据（AI推理v1.0）
- 新MD文件: 616人详细姓氏记录（人工校正+AI推理v2.1）
- 目标: 合并为2095人完整数据

**合并逻辑**:
```python
# kg/entities/scripts/update_xingshi_from_md.py
old_json = load_json('xingshi.json')  # 2053人
new_md = parse_markdown('xingshi_reasoning/*.md')  # 616人

# 优先级：MD文件（人工审查）> 旧JSON（AI推理）
merged = {}
merged.update({p['name']: p for p in old_json})    # 基础数据
merged.update({p['name']: p for p in new_md})      # MD覆盖

# 结果：2095人（2053 - 616重复 + 616 + 42新增）
```

**结果**:
- MD文件: 616人
- 旧JSON: 2053人
- 合并后: 2095人（+42人新增）

**commit**: [f341729f](https://github.com/baojie/shiji-kb/commit/f341729f)

---

### 模式2: 时间戳优先（Timestamp-based Priority）

#### 适用场景
需要追踪数据更新时间，优先使用最新数据

#### 合并策略

```python
# 核心逻辑：比较时间戳，保留最新版本
for item in old_data + new_data:
    k = item[key]
    ts = item.get('_timestamp', '1970-01-01')
    if k not in merged or ts > merged[k]['_timestamp']:
        merged[k] = item
```

#### 本项目实例：事件索引增量更新

```python
# 只处理变化的章节（基于git diff）
modified_chapters = get_modified_chapters()
new_events = extract_events(modified_chapters)

# 合并：新事件覆盖旧事件
merged = {e['id']: e for e in existing_events}
merged.update({e['id']: e for e in new_events})

# 输出示例：
# 已有事件: 3150
# 新提取: 35（3个章节）
# 最终: 3185
```

---

### 模式3: 多源优先级合并（Multi-source Priority Merge）

#### 适用场景
同一数据有多个来源，需要按优先级合并

#### 优先级定义

```python
SOURCE_PRIORITY = {
    'human_verified': 100,      # 人工验证：最高优先级
    'ai_high_confidence': 80,   # AI高置信度
    'ai_medium_confidence': 60,
    'auto_extracted': 20,       # 自动提取：最低优先级
}

# 核心逻辑：按优先级排序，高优先级覆盖低优先级
sources.sort(key=lambda s: s['priority'], reverse=True)
for source in sources:
    for item in source['data']:
        if item[key] not in merged or source['priority'] > merged[item[key]]['_priority']:
            merged[item[key]] = {**item, '_source': source['name'], '_priority': source['priority']}
```

#### 本项目实例：姓氏推理多轮合并

```python
# 六轮推理结果按优先级合并
sources = [
    {'name': 'R1_直接记载', 'data': ..., 'priority': 100},  # 原文明确
    {'name': 'R6_深度反思', 'data': ..., 'priority': 80},   # 反思修正
    {'name': 'R2_邦国推理', 'data': ..., 'priority': 80},
    {'name': 'R3_氏族推理', 'data': ..., 'priority': 80},
    {'name': 'R5_父子传播', 'data': ..., 'priority': 60},   # 中等置信度
]

merged = merge_multi_source(sources, key='name')

# 姓氏来源统计:
#   R1_直接记载: 856人
#   R2_邦国推理: 412人
#   R3_氏族推理: 389人
#   R5_父子传播: 276人
#   R6_深度反思: 162人
```

---

### 模式4: 字段级增量更新（Field-level Incremental Update）

#### 适用场景
只更新特定字段，其他字段保留旧值

#### 合并策略

```python
# 核心逻辑：只更新指定字段，其他字段保留
for update in updates:
    k = update[key]
    if k in old_dict:
        for field in update_fields:
            if field in update and update[field] is not None:
                old_dict[k][field] = update[field]
```

#### 本项目实例：实体属性增量补充

```python
# 只更新生卒年字段，保留其他字段
entities = load_json('entity_index.json')
lifespan_updates = load_json('person_lifespans.json')

updated = update_fields(
    old_data=entities,
    updates=lifespan_updates,
    update_fields=['birth_year', 'death_year', 'lifespan_reasoning']
)

# 实体总数: 5000
# 更新数: 864
```

---

## 三、数据源优先级管理

### 3.1 优先级定义原则

```python
PRIORITY_RULES = {
    # 人工验证 > AI推理
    'human_verified': 100,
    'ai_inferred': 50,

    # 原文明确 > 推理结论
    'text_explicit': 100,
    'reasoning_based': 50,

    # 新版本 > 旧版本（同等质量下）
    'v2.0': 60,
    'v1.0': 50,

    # 高置信度 > 低置信度
    'confidence_high': 80,
    'confidence_medium': 60,
    'confidence_low': 40,

    # 详细记录 > 简单标记
    'detailed_record': 70,
    'simple_tag': 50,
}
```

### 3.2 冲突解决策略

**策略矩阵**:

| 旧数据来源 | 新数据来源 | 解决策略 | 示例 |
|-----------|-----------|---------|------|
| 人工验证 | AI推理 | **保留旧数据** | 人工校正不被AI覆盖 |
| AI推理v1 | AI推理v2 | **使用新数据** | 版本迭代 |
| 原文明确 | 推理结论 | **保留旧数据** | 原文为准 |
| 高置信度 | 低置信度 | **保留旧数据** | 质量优先 |
| 简单标记 | 详细记录 | **使用新数据** | 信息量优先 |
| 空值 | 任何值 | **使用新数据** | 填充空白 |

### 3.3 冲突日志记录

```python
# 检测并记录冲突字段
conflicts = []
for k in old_dict:
    if k in new_dict:
        conflict_fields = [f for f in old_dict[k] if old_dict[k][f] != new_dict[k].get(f)]
        if conflict_fields:
            conflicts.append({'key': k, 'fields': conflict_fields, 'resolution': 'prefer_new'})

# 保存冲突日志
save_json('logs/merge_conflicts.json', conflicts)
```

---

## 四、典型应用场景

### 场景1: AI多轮推理结果合并

**问题**:
- AI第一轮推理2000条结果
- 第二轮优化提示词后推理1800条（部分人物未覆盖）
- 如何保留两轮的并集？

**解决方案**:
```python
# 合并两轮推理结果
round1_data = load_json('xingshi_round1.json')  # 2000条
round2_data = load_json('xingshi_round2.json')  # 1800条

merged = merge_by_key(
    old_data=round1_data,
    new_data=round2_data,
    key='name',
    strategy='prefer_new'  # 重复的用第二轮结果
)

# 结果: 2200条（2000 - 1800重复 + 1800 + 200仅在R1的）
```

---

### 场景2: 人工校正保护

**问题**:
- 自动化流程每次运行会重新生成JSON
- 人工校正的100条数据在下次运行时被覆盖

**解决方案**:
```python
# 加载人工校正数据（优先级100）
human_verified = load_json('xingshi_human_verified.json')

# 加载自动推理数据（优先级50）
auto_inferred = load_json('xingshi_auto.json')

# 多源合并（人工数据优先）
merged = merge_multi_source([
    {'name': 'human', 'data': human_verified, 'priority': 100},
    {'name': 'auto', 'data': auto_inferred, 'priority': 50}
])

save_json('xingshi_final.json', merged)
```

---

### 场景3: 跨文件格式同步

**问题**:
- MD文件: 详细记录（人工编辑）
- JSON文件: 结构化数据（自动生成）
- 如何保持一致性？

**解决方案**:
```python
# MD为主，JSON为辅
md_data = parse_markdown_files('xingshi_reasoning/*.md')
json_data = load_json('xingshi.json')

merged = merge_multi_source([
    {'name': 'md', 'data': md_data, 'priority': 100},
    {'name': 'json', 'data': json_data, 'priority': 50}
])

save_json('xingshi_merged.json', merged)
```

**脚本**: `update_xingshi_from_md.py`

---

### 场景4: 增量发布

**问题**:
- 11个表格JSON文件（总计650KB）
- 只有2个文件修改，如何避免全量复制？

**解决方案**:
```python
# scripts/publish_tables_data.py
# 基于文件修改时间判断是否需要复制
for source_file in source_dir.glob('*.json'):
    target_file = target_dir / source_file.name

    if target_file.exists() and source_file.stat().st_mtime <= target_file.stat().st_mtime:
        print(f"⏭️  跳过: {source_file.name}")
        continue

    shutil.copy2(source_file, target_file)
    print(f"✅ 发布: {source_file.name}")

# 输出: 已发布2个, 跳过9个
```

**commit**: [f78bfc38](https://github.com/baojie/shiji-kb/commit/f78bfc38)

---

## 五、核心优势

### 5.1 数据持续积累

```
传统方式: V1(1000) → V2(800) → V3(900)
  最终只有900条

增量方式: V1(1000) → V1+V2(1200) → V1+V2+V3(1500)
  数据持续增长
```

### 5.2 保护人工劳动

```
人工校正100条 → 自动化流程运行 → 人工校正被保留
```

### 5.3 多源数据融合

```
源A(高质量,少量) + 源B(低质量,大量) → 融合后(高质量,大量)
```

### 5.4 可追溯性

```
每条数据记录:
  - 来源（哪个文件/哪一轮推理）
  - 时间戳
  - 优先级
  - 覆盖历史
```

---

## 六、与其他元技能的关系

### 关联元技能

- **← META-02 (迭代工作流)**: 增量更新是迭代工作流的数据层实现
- **← META-15 (批量反思管线)**: 多轮反思的结果需要增量合并
- **→ META-12 (数据融合)**: 增量更新是数据融合的前提
- **→ META-19 (建设逻辑留痕)**: 合并日志是建设逻辑的一部分

### 协同使用

**典型工作流**:
```
1. 批量反思管线 (META-15) → 多轮推理结果
   ↓
2. 增量式数据更新 (META-16) → 合并所有轮次
   ↓
3. 建设逻辑留痕 (META-19) → 记录合并决策
   ↓
4. 数据融合 (META-12) → 跨源融合
```

---

## 七、反模式（Anti-patterns）

### 反模式1: 盲目全量替换

**错误做法**:
```python
# ❌ 每次运行直接覆盖
new_data = ai_inference()
save_json('data.json', new_data)  # 旧数据丢失
```

**正确做法**:
```python
# ✅ 增量合并
old_data = load_json('data.json')
new_data = ai_inference()
merged = merge_by_key(old_data, new_data)
save_json('data.json', merged)
```

---

### 反模式2: 无优先级定义

**错误做法**:
```python
# ❌ 随机覆盖
for source in sources:
    data.update(source)  # 后来的覆盖先来的
```

**正确做法**:
```python
# ✅ 明确优先级
sources_with_priority = [
    {'data': human_verified, 'priority': 100},
    {'data': ai_inferred, 'priority': 50}
]
merged = merge_multi_source(sources_with_priority)
```

---

### 反模式3: 缺少冲突日志

**错误做法**:
```python
# ❌ 静默覆盖，无法追溯
merged[key] = new_value  # 旧值丢失
```

**正确做法**:
```python
# ✅ 记录冲突
if key in merged and merged[key] != new_value:
    log_conflict(key, old=merged[key], new=new_value)
merged[key] = new_value
```

---

### 反模式4: 忽略数据版本

**错误做法**:
```python
# ❌ 所有数据混在一起，无法区分来源
save_json('data.json', merged_data)
```

**正确做法**:
```python
# ✅ 记录数据版本和来源
for item in merged_data:
    item['_version'] = 'v2.1'
    item['_source'] = 'xingshi_reasoning_r6'
    item['_updated_at'] = datetime.now().isoformat()
save_json('data.json', merged_data)
```

---

## 八、本项目应用总结

### 应用实例统计

| 数据类型 | 旧数据量 | 新数据量 | 合并后 | 增量 | commit链接 |
|---------|---------|---------|--------|------|-----------|
| **姓氏数据** | 2053人 | 616人(MD) | 2095人 | +42 | [f341729f](https://github.com/baojie/shiji-kb/commit/f341729f) |
| **寿命推理** | 0 | 864行(新增) | 864行 | +864 | [f341729f](https://github.com/baojie/shiji-kb/commit/f341729f) |
| **表格数据** | 11个表 | 2个修改 | 11个表 | 增量发布 | [f78bfc38](https://github.com/baojie/shiji-kb/commit/f78bfc38) |

### 核心脚本

| 脚本 | 功能 | 位置 |
|-----|------|------|
| `update_xingshi_from_md.py` | 姓氏MD+JSON合并 | `kg/entities/scripts/` |
| `publish_tables_data.py` | 表格数据增量发布 | `scripts/` |
| `publish_xingshi_data.py` | 姓氏数据自动化发布 | `scripts/` |
| `export_events_incremental.py` | 事件索引增量导出 | `kg/events/scripts/` |

---

## 九、迁移指南

### 迁移到其他项目

**步骤1: 识别数据源**
- 列出所有数据来源（文件/API/数据库）
- 定义优先级顺序

**步骤2: 定义唯一键**
- 确定数据的唯一标识（ID/名称/复合键）
- 确保键的稳定性（不随时间变化）

**步骤3: 选择合并模式**
- 键值合并：结构化数据
- 时间戳优先：需要版本控制
- 多源优先级：多数据源
- 字段级更新：部分字段更新

**步骤4: 实现合并逻辑**
```python
# 通用合并模板
def merge_data(old_path, new_path, output_path, strategy='merge'):
    old_data = load_data(old_path)
    new_data = load_data(new_path)

    if strategy == 'merge':
        merged = merge_by_key(old_data, new_data)
    elif strategy == 'priority':
        merged = merge_multi_source([
            {'data': old_data, 'priority': 50},
            {'data': new_data, 'priority': 100}
        ])

    save_data(output_path, merged)
```

**步骤5: 记录合并日志**
- 冲突日志
- 覆盖历史
- 来源追溯

---

## 十、进一步阅读

### 相关文档

- `kg/entities/data/lifespan_reasoning_process.md`: 寿命推理过程（986行）
- `SKILL_07b_姓氏推理.md`: 姓氏推理R1-R14规则
- `scripts/publish_tables_data.py`: 表格数据增量发布脚本

### 相关commit

- [f341729f](https://github.com/baojie/shiji-kb/commit/f341729f): 新增寿命推理过程文档和姓氏转换脚本
- [f78bfc38](https://github.com/baojie/shiji-kb/commit/f78bfc38): 新增十表交互式数据查看器
- [4a4255bf](https://github.com/baojie/shiji-kb/commit/4a4255bf): 姓氏推理首轮完成（覆盖2053/3630人物）

---

**创建日期**: 2026-03-26
**版本**: v1.0
**作者**: 基于《史记》知识库项目实践总结
