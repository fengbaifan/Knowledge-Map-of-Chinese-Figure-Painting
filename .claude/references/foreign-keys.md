# 外键关联关系详解

本文档详细说明中国人物画知识图谱中的外键关联关系。

## 关系图总览

```
M1.1 时序本体 (period_id)
    ↓
M2.1 历史人物 (person_id) ← M1.2 空间地理 (loc_id)
    ↓                          ↓
    ├─→ M2.2 履历 (person_ref)
    ├─→ M2.3 关系 (source_id, target_id)
    └─→ M3.1 作品 (creator_ref) ← M1.1 时序 (period_ref)
            ↓                      ← M1.3 图像志 (icon_ref)
        M3.2 文献 (target_ref, author_ref)
```

## 详细关联关系

### 1. M2.2 履历 → M2.1 人物

**外键字段**：`M2.2.person_ref`  
**引用字段**：`M2.1.person_id`  
**关系类型**：多对一（一个人物可有多条履历）  
**必填性**：必填

**示例**：
```csv
# M2.1_历史人物核心表.csv
person_id,person_name,primary_role
meso_gu_kaizhi,顾恺之,Painter

# M2.2_履历与时空轨迹.csv
cv_id,person_ref,event_type,event_year
cv_001,meso_gu_kaizhi,Birth,344
cv_002,meso_gu_kaizhi,Career,364
```

**验证规则**：
- `person_ref` 必须存在于 `M2.1.person_id` 中
- `person_ref` 不能为空
- `person_ref` 必须使用 `meso_` 前缀

### 2. M2.3 关系 → M2.1 人物

**外键字段**：`M2.3.source_id`, `M2.3.target_id`  
**引用字段**：`M2.1.person_id`  
**关系类型**：多对多（人物之间的关系）  
**必填性**：必填

**示例**：
```csv
# M2.1_历史人物核心表.csv
person_id,person_name
meso_gu_kaizhi,顾恺之
meso_lu_tanwei,陆探微

# M2.3_社会关系实例.csv
rel_id,source_id,target_id,relation_type
rel_001,meso_gu_kaizhi,meso_lu_tanwei,Friend
```

**验证规则**：
- `source_id` 和 `target_id` 必须存在于 `M2.1.person_id` 中
- `source_id` 和 `target_id` 不能相同（避免自引用）
- 必须使用 `meso_` 前缀

### 3. M3.1 作品 → M2.1 人物

**外键字段**：`M3.1.creator_ref`  
**引用字段**：`M2.1.person_id`  
**关系类型**：多对一（一个人物可创作多件作品）  
**必填性**：强烈推荐（除非作者不详）

**示例**：
```csv
# M2.1_历史人物核心表.csv
person_id,person_name
meso_gu_kaizhi,顾恺之

# M3.1_作品实体表.csv
work_id,work_title,creator_ref
micro_luoshen_fu,洛神赋图,meso_gu_kaizhi
```

**验证规则**：
- `creator_ref` 应存在于 `M2.1.person_id` 中
- 作者不详时可为空或使用 `Unknown`
- 必须使用 `meso_` 前缀

### 4. M3.1 作品 → M1.1 时序

**外键字段**：`M3.1.period_ref`  
**引用字段**：`M1.1.period_id`  
**关系类型**：多对一（一个时期有多件作品）  
**必填性**：推荐

**示例**：
```csv
# M1.1_时序本体.csv
period_id,period_name,start_year,end_year
period_eastern_jin,东晋,317,420

# M3.1_作品实体表.csv
work_id,work_title,period_ref
micro_luoshen_fu,洛神赋图,period_eastern_jin
```

**验证规则**：
- `period_ref` 应存在于 `M1.1.period_id` 中
- 必须使用 `period_` 前缀

### 5. M3.1 作品 → M1.3 图像志

**外键字段**：`M3.1.icon_ref`  
**引用字段**：`M1.3.icon_id`  
**关系类型**：多对一（一个题材有多件作品）  
**必填性**：推荐

**示例**：
```csv
# M1.3_图像志题材分类.csv
icon_id,icon_name,icon_category
icon_portrait,人物画,Figure

# M3.1_作品实体表.csv
work_id,work_title,icon_ref
micro_luoshen_fu,洛神赋图,icon_portrait
```

**验证规则**：
- `icon_ref` 应存在于 `M1.3.icon_id` 中
- 必须使用 `icon_` 前缀

### 6. M3.2 文献 → M3.1 作品 或 M2.1 人物

**外键字段**：`M3.2.target_ref`  
**引用字段**：`M3.1.work_id` 或 `M2.1.person_id`  
**关系类型**：多对一（一个对象可有多条文献著录）  
**必填性**：必填

**示例**：
```csv
# M3.1_作品实体表.csv
work_id,work_title
micro_luoshen_fu,洛神赋图

# M2.1_历史人物核心表.csv
person_id,person_name
meso_gu_kaizhi,顾恺之

# M3.2_文献著录与品评.csv
lit_id,target_ref,target_type,content
lit_001,micro_luoshen_fu,Work,"洛神赋图，顾恺之所作"
lit_002,meso_gu_kaizhi,Person,"顾恺之，字长康"
```

**验证规则**：
- 当 `target_type = Work` 时，`target_ref` 必须存在于 `M3.1.work_id` 中
- 当 `target_type = Person` 时，`target_ref` 必须存在于 `M2.1.person_id` 中
- 必须使用正确的前缀（`micro_` 或 `meso_`）

### 7. M3.2 文献 → M2.1 人物（作者）

**外键字段**：`M3.2.author_ref`  
**引用字段**：`M2.1.person_id`  
**关系类型**：多对一（一个作者可写多条文献）  
**必填性**：推荐

**示例**：
```csv
# M2.1_历史人物核心表.csv
person_id,person_name
meso_zhang_yanyuan,张彦远

# M3.2_文献著录与品评.csv
lit_id,author_ref,content
lit_001,meso_zhang_yanyuan,"顾恺之，字长康"
```

**验证规则**：
- `author_ref` 应存在于 `M2.1.person_id` 中
- 作者不详时可为空
- 必须使用 `meso_` 前缀

## 外键检查 SQL 示例

虽然我们使用 CSV 文件，但可以用类似 SQL 的逻辑检查外键完整性：

### 检查 M2.2 → M2.1

```python
# 检查 M2.2 中的 person_ref 是否都存在于 M2.1 中
invalid_refs = df_m22[~df_m22['person_ref'].isin(df_m21['person_id'])]
```

### 检查 M3.1 → M2.1

```python
# 检查 M3.1 中的 creator_ref 是否都存在于 M2.1 中
# 排除空值
valid_creators = df_m31[df_m31['creator_ref'].notna()]
invalid_refs = valid_creators[~valid_creators['creator_ref'].isin(df_m21['person_id'])]
```

### 检查 M3.2 → M3.1 或 M2.1

```python
# 检查 M3.2 中的 target_ref
for idx, row in df_m32.iterrows():
    target_ref = row['target_ref']
    target_type = row['target_type']
    
    if target_type == 'Work':
        if target_ref not in df_m31['work_id'].values:
            print(f"行 {idx+2}: target_ref {target_ref} 不存在于 M3.1")
    elif target_type == 'Person':
        if target_ref not in df_m21['person_id'].values:
            print(f"行 {idx+2}: target_ref {target_ref} 不存在于 M2.1")
```

## 外键完整性检查清单

### 必须检查的外键
- [ ] M2.2.person_ref → M2.1.person_id
- [ ] M2.3.source_id → M2.1.person_id
- [ ] M2.3.target_id → M2.1.person_id
- [ ] M3.2.target_ref → M3.1.work_id 或 M2.1.person_id

### 推荐检查的外键
- [ ] M3.1.creator_ref → M2.1.person_id
- [ ] M3.1.period_ref → M1.1.period_id
- [ ] M3.1.icon_ref → M1.3.icon_id
- [ ] M3.2.author_ref → M2.1.person_id

## 外键错误处理策略

### 严重错误（必须修复）
- 必填外键为空
- 外键指向不存在的记录
- 外键前缀错误

**处理方式**：
1. 人工检查原始文献
2. 补充正确的外键值
3. 或标记为需要进一步调查

### 警告（建议修复）
- 推荐外键为空
- 外键值存在但格式不规范

**处理方式**：
1. 尽量补充外键值
2. 规范化外键格式
3. 在备注中说明原因

## 级联操作建议

### 删除操作
- 删除 M2.1 人物记录前，应先检查：
  - M2.2 中是否有引用
  - M2.3 中是否有引用
  - M3.1 中是否有引用
  - M3.2 中是否有引用

### 更新操作
- 更新 M2.1.person_id 时，应同步更新：
  - M2.2.person_ref
  - M2.3.source_id / target_id
  - M3.1.creator_ref
  - M3.2.target_ref / author_ref

## 外键命名规范

### 引用字段命名
- 引用人物：`person_ref`, `creator_ref`, `author_ref`, `source_id`, `target_id`
- 引用作品：`work_ref`, `target_ref`
- 引用时序：`period_ref`
- 引用地理：`location_ref`
- 引用图像志：`icon_ref`

### 命名原则
- 使用 `_ref` 后缀表示外键引用
- 使用 `_id` 后缀表示主键
- 特殊情况（如 source_id, target_id）保持语义清晰
