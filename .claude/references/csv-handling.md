# CSV 文件处理规范

本文档提供 CSV 文件读写的技术规范和最佳实践。

## 编码规范

### UTF-8-BOM 编码

**要求**：所有 CSV 文件必须使用 UTF-8-BOM 编码

**原因**：
- 支持中文字符
- BOM 标记帮助 Excel 正确识别编码
- 避免乱码问题

**Python 读取**：
```python
import pandas as pd

df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False)
```

**Python 写入**：
```python
df.to_csv(file_path, encoding='utf-8-sig', index=False)
```

**检查编码**：
```bash
file -I file.csv
# 输出应包含：charset=utf-8
```

**转换编码**：
```bash
iconv -f GBK -t UTF-8 input.csv > output.csv
```

## 索引处理规范

### 防止第一列被误认为索引

**问题**：pandas 默认可能将第一列作为索引，导致数据错位

**解决方案**：始终使用 `index_col=False`

```python
# 正确做法
df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False)

# 错误做法（可能导致第一列丢失）
df = pd.read_csv(file_path, encoding='utf-8-sig')
```

### 写入时不保存索引

```python
# 正确做法
df.to_csv(file_path, encoding='utf-8-sig', index=False)

# 错误做法（会多出一列无意义的索引）
df.to_csv(file_path, encoding='utf-8-sig')
```

## 行号计算规范

### CSV 行号与 DataFrame 索引的关系

**规则**：CSV 行号 = DataFrame 索引 + 2

**原因**：
- CSV 第 1 行是表头
- DataFrame 索引从 0 开始
- 因此 DataFrame 索引 0 对应 CSV 第 2 行

**单级索引**：
```python
# DataFrame 索引 0 → CSV 行号 2
# DataFrame 索引 1 → CSV 行号 3
row_num = int(idx) + 2
```

**多级索引**：
```python
# 多级索引取第一个元素
if isinstance(idx, tuple):
    row_num = int(idx[0]) + 2
else:
    row_num = int(idx) + 2
```

**示例**：
```python
import pandas as pd

df = pd.read_csv('data.csv', encoding='utf-8-sig', index_col=False)

# 遍历 DataFrame 并输出 CSV 行号
for idx, row in df.iterrows():
    csv_row_num = int(idx) + 2
    print(f"CSV 行号: {csv_row_num}, 数据: {row['person_name']}")
```

## 字段名规范

### 命名规则

- 使用小写字母和下划线
- 不使用点号、连字符、空格
- 不使用中文字符

**正确**：
```
person_id, source_book, source_chapter, birth_year
```

**错误**：
```
person.id, source-book, source chapter, 人物ID
```

### 读取时处理字段名

```python
# 读取后清理字段名
df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False)
df.columns = df.columns.str.strip()  # 去除空格
df.columns = df.columns.str.lower()  # 转小写（可选）
```

## 特殊字符处理

### 逗号处理

**问题**：字段内容包含逗号会破坏 CSV 结构

**解决方案**：使用双引号包裹

```python
# pandas 自动处理
df.to_csv(file_path, encoding='utf-8-sig', index=False, quoting=csv.QUOTE_MINIMAL)
```

**手动处理**：
```python
import csv

# 所有字段都加引号
df.to_csv(file_path, encoding='utf-8-sig', index=False, quoting=csv.QUOTE_ALL)

# 只对包含特殊字符的字段加引号
df.to_csv(file_path, encoding='utf-8-sig', index=False, quoting=csv.QUOTE_MINIMAL)
```

### 换行符处理

**问题**：字段内容包含换行符

**解决方案**：
```python
# pandas 自动处理，字段会被双引号包裹
df.to_csv(file_path, encoding='utf-8-sig', index=False)

# 读取时保持换行符
df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False, keep_default_na=False)
```

### 引号处理

**问题**：字段内容包含双引号

**解决方案**：双引号转义为两个双引号

```python
# pandas 自动处理
# 原始内容：He said "hello"
# CSV 中存储：He said ""hello""
```

## 空值处理

### 空值表示

**标准**：使用空字符串或不填写

**不推荐**：
- `NULL`
- `None`
- `N/A`
- `#N/A`

**读取时处理空值**：
```python
# 保持空字符串为空字符串，不转换为 NaN
df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False, keep_default_na=False)

# 或者指定哪些值视为 NaN
df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False, na_values=['NULL', 'N/A'])
```

**写入时处理空值**：
```python
# 将 NaN 写为空字符串
df.to_csv(file_path, encoding='utf-8-sig', index=False, na_rep='')
```

## 数据类型处理

### 字符串类型

**问题**：数字 ID 可能被识别为数值类型，导致前导零丢失

**解决方案**：指定列类型为字符串

```python
# 读取时指定类型
df = pd.read_csv(
    file_path, 
    encoding='utf-8-sig', 
    index_col=False,
    dtype={'person_id': str, 'work_id': str}
)

# 或读取后转换
df['person_id'] = df['person_id'].astype(str)
```

### 日期类型

```python
# 读取时解析日期
df = pd.read_csv(
    file_path, 
    encoding='utf-8-sig', 
    index_col=False,
    parse_dates=['birth_date', 'death_date']
)
```

### 布尔类型

```python
# 读取时转换布尔值
df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False)
df['is_verified'] = df['is_verified'].map({'TRUE': True, 'FALSE': False, '1': True, '0': False})
```

## 大文件处理

### 分块读取

```python
# 分块读取大文件
chunk_size = 1000
for chunk in pd.read_csv(file_path, encoding='utf-8-sig', index_col=False, chunksize=chunk_size):
    process_chunk(chunk)
```

### 只读取需要的列

```python
# 只读取指定列
df = pd.read_csv(
    file_path, 
    encoding='utf-8-sig', 
    index_col=False,
    usecols=['person_id', 'person_name', 'source_book']
)
```

## 错误处理

### 读取错误处理

```python
import pandas as pd

try:
    df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False)
except FileNotFoundError:
    print(f"文件不存在: {file_path}")
except pd.errors.EmptyDataError:
    print(f"文件为空: {file_path}")
except pd.errors.ParserError:
    print(f"文件格式错误: {file_path}")
except Exception as e:
    print(f"读取文件时发生错误: {e}")
```

### 写入错误处理

```python
try:
    df.to_csv(file_path, encoding='utf-8-sig', index=False)
except PermissionError:
    print(f"没有写入权限: {file_path}")
except Exception as e:
    print(f"写入文件时发生错误: {e}")
```

## 完整示例

### 读取 CSV 文件

```python
import pandas as pd

def read_csv_safe(file_path):
    """安全读取 CSV 文件"""
    try:
        df = pd.read_csv(
            file_path,
            encoding='utf-8-sig',  # UTF-8-BOM 编码
            index_col=False,       # 不使用第一列作为索引
            keep_default_na=False, # 保持空字符串
            dtype=str              # 所有列读取为字符串（可选）
        )
        
        # 清理字段名
        df.columns = df.columns.str.strip()
        
        return df
    except Exception as e:
        print(f"读取文件失败: {file_path}, 错误: {e}")
        return None
```

### 写入 CSV 文件

```python
def write_csv_safe(df, file_path):
    """安全写入 CSV 文件"""
    try:
        df.to_csv(
            file_path,
            encoding='utf-8-sig',  # UTF-8-BOM 编码
            index=False,           # 不写入索引列
            na_rep='',             # NaN 写为空字符串
            quoting=csv.QUOTE_MINIMAL  # 最小引号策略
        )
        print(f"文件写入成功: {file_path}")
        return True
    except Exception as e:
        print(f"写入文件失败: {file_path}, 错误: {e}")
        return False
```

### 遍历并报告行号

```python
def process_csv_with_row_numbers(file_path):
    """处理 CSV 并报告行号"""
    df = read_csv_safe(file_path)
    if df is None:
        return
    
    issues = []
    
    for idx, row in df.iterrows():
        csv_row_num = int(idx) + 2  # CSV 行号
        
        # 检查必填字段
        if pd.isna(row['source_book']) or row['source_book'] == '':
            issues.append({
                'file': file_path,
                'row': csv_row_num,
                'field': 'source_book',
                'issue': '必填字段为空'
            })
    
    return issues
```

## 最佳实践清单

- [ ] 使用 UTF-8-BOM 编码
- [ ] 读取时使用 `index_col=False`
- [ ] 写入时使用 `index=False`
- [ ] 行号计算：DataFrame 索引 + 2
- [ ] 字段名使用下划线分隔
- [ ] 处理特殊字符（逗号、换行、引号）
- [ ] 正确处理空值
- [ ] 指定数据类型（避免类型推断错误）
- [ ] 添加错误处理
- [ ] 大文件使用分块读取
