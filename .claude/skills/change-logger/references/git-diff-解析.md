# Git Diff 解析指南

## Git Diff 输出格式

### 基本结构

```diff
diff --git a/path/to/file.csv b/path/to/file.csv
index abc123..def456 100644
--- a/path/to/file.csv
+++ b/path/to/file.csv
@@ -4,3 +4,3 @@
 unchanged line
-old line
+new line
 unchanged line
```

### 各部分说明

| 部分 | 格式 | 含义 |
|------|------|------|
| diff 头 | `diff --git a/... b/...` | 对比的文件路径 |
| index | `index abc123..def456 100644` | Git 对象 hash 和文件模式 |
| 文件标记 | `--- a/...` 和 `+++ b/...` | 旧文件和新文件 |
| hunk 头 | `@@ -4,3 +4,3 @@` | 变更块的位置 |
| 变更内容 | ` ` / `-` / `+` 开头 | 未变更/删除/新增 |

## Hunk 头解析

格式：`@@ -旧起始行,旧行数 +新起始行,新行数 @@`

**示例**：
```diff
@@ -4,3 +4,3 @@
```

- `-4,3`：旧文件从第4行开始，共3行
- `+4,3`：新文件从第4行开始，共3行

**计算实际行号**：
- CSV 文件第1行是表头
- 数据从第2行开始
- 实际数据行号 = hunk 起始行号 - 1

## CSV 文件 Diff 解析

### 场景1：字段值修改

```diff
@@ -8,1 +8,1 @@
-meso_001,Painter,顾恺之,,,,,"{""birth"": ""580"", ""death"": ""640""}",period_tang,,《续画品》,卷一,原文
+meso_001,Painter,顾恺之,,,,,"{""birth"": ""585"", ""death"": ""643""}",period_tang,,《续画品》,卷一,原文
```

**解析步骤**：

1. **识别行号**：第8行（数据行第7行）
2. **分割 CSV**：按逗号分割（注意引号内的逗号）
3. **逐字段对比**：
   ```python
   old_fields = parse_csv_line(old_line)
   new_fields = parse_csv_line(new_line)
   
   for i, (old, new) in enumerate(zip(old_fields, new_fields)):
       if old != new:
           field_name = header[i]
           print(f"字段 {field_name}: {old} → {new}")
   ```
4. **输出结果**：
   - 字段：`birth_death`
   - 修改前：`{"birth": "580", "death": "640"}`
   - 修改后：`{"birth": "585", "death": "643"}`

### 场景2：字段名修改（表头变更）

```diff
@@ -1,1 +1,1 @@
-person_id,primary_role,name,source.chapter,source_text
+person_id,primary_role,name,source_chapter,source_text
```

**解析步骤**：

1. **识别为表头**：行号为1
2. **对比字段名**：
   ```python
   old_headers = old_line.split(',')
   new_headers = new_line.split(',')
   
   for i, (old, new) in enumerate(zip(old_headers, new_headers)):
       if old != new:
           print(f"字段名修改: {old} → {new}")
   ```
3. **输出结果**：
   - 原字段名：`source.chapter`
   - 新字段名：`source_chapter`
   - 影响：全部数据行

### 场景3：多行修改

```diff
@@ -4,3 +4,3 @@
 meso_001,Painter,顾恺之,,,,,"{""birth"": ""580"", ""death"": ""640""}",period_tang,,续画品,卷一,原文
-meso_002,Painter,陆探微,,,,,"{""birth"": null, ""death"": ""485""}",period_southern,,《续画品》,卷一,原文
-meso_003,Painter,张僧繇,,,,,"{""birth"": ""480"", ""death"": ""550""}",period_southern,,续画品,卷二,原文
+meso_002,Painter,陆探微,,,,,"{""birth"": null, ""death"": ""485""}",period_southern,,《续画品》,卷一,原文
+meso_003,Painter,张僧繇,,,,,"{""birth"": ""480"", ""death"": ""550""}",period_southern,,《续画品》,卷二,原文
```

**解析步骤**：

1. **识别变更范围**：第5-6行
2. **逐行对比**：
   - 第5行：`source_book` 字段，`续画品` → `《续画品》`
   - 第6行：`source_book` 字段，`续画品` → `《续画品》`
3. **汇总模式**：
   - 修改类型：添加书名号
   - 影响行数：2行
   - 修改字段：`source_book`

## Python 实现示例

### CSV 行解析（处理引号）

```python
import csv
import io

def parse_csv_line(line):
    """解析 CSV 行，正确处理引号内的逗号"""
    reader = csv.reader(io.StringIO(line))
    return next(reader)

# 示例
line = 'meso_001,Painter,顾恺之,,,,,"{""birth"": ""580"", ""death"": ""640""}",period_tang'
fields = parse_csv_line(line)
# fields[7] = '{"birth": "580", "death": "640"}'
```

### Diff 解析器

```python
import re
import subprocess

def parse_git_diff(file_path):
    """解析 git diff 输出"""
    # 执行 git diff
    result = subprocess.run(
        ['git', 'diff', file_path],
        capture_output=True,
        text=True
    )
    
    diff_output = result.stdout
    changes = []
    
    # 解析 hunk
    hunk_pattern = r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@'
    line_pattern = r'^([-+ ])(.*)'
    
    current_hunk = None
    old_line_num = 0
    new_line_num = 0
    
    for line in diff_output.split('\n'):
        # 匹配 hunk 头
        hunk_match = re.match(hunk_pattern, line)
        if hunk_match:
            old_start, old_count, new_start, new_count = map(int, hunk_match.groups())
            current_hunk = {
                'old_start': old_start,
                'new_start': new_start
            }
            old_line_num = old_start
            new_line_num = new_start
            continue
        
        # 匹配变更行
        line_match = re.match(line_pattern, line)
        if line_match and current_hunk:
            prefix, content = line_match.groups()
            
            if prefix == '-':
                # 删除的行
                changes.append({
                    'type': 'delete',
                    'line_num': old_line_num,
                    'content': content
                })
                old_line_num += 1
            elif prefix == '+':
                # 新增的行
                changes.append({
                    'type': 'add',
                    'line_num': new_line_num,
                    'content': content
                })
                new_line_num += 1
            else:
                # 未变更的行
                old_line_num += 1
                new_line_num += 1
    
    return changes
```

### 字段级对比

```python
def compare_csv_lines(old_line, new_line, headers):
    """对比两行 CSV 数据，返回变更的字段"""
    old_fields = parse_csv_line(old_line)
    new_fields = parse_csv_line(new_line)
    
    field_changes = []
    
    for i, (old_val, new_val) in enumerate(zip(old_fields, new_fields)):
        if old_val != new_val:
            field_changes.append({
                'field_name': headers[i],
                'old_value': old_val,
                'new_value': new_val
            })
    
    return field_changes

# 示例
headers = ['person_id', 'primary_role', 'name', 'birth_death', 'period_ref']
old_line = 'meso_001,Painter,顾恺之,"{""birth"": ""580"", ""death"": ""640""}",period_tang'
new_line = 'meso_001,Painter,顾恺之,"{""birth"": ""585"", ""death"": ""643""}",period_tang'

changes = compare_csv_lines(old_line, new_line, headers)
# [{'field_name': 'birth_death', 'old_value': '{"birth": "580", "death": "640"}', 'new_value': '{"birth": "585", "death": "643"}'}]
```

## 完整工作流

```python
def analyze_file_changes(file_path):
    """分析文件的所有变更"""
    # 1. 获取 diff
    changes = parse_git_diff(file_path)
    
    # 2. 读取表头
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        headers = parse_csv_line(f.readline().strip())
    
    # 3. 配对删除和新增行
    modifications = []
    i = 0
    while i < len(changes):
        if i + 1 < len(changes) and \
           changes[i]['type'] == 'delete' and \
           changes[i + 1]['type'] == 'add' and \
           changes[i]['line_num'] == changes[i + 1]['line_num']:
            # 这是一次修改
            old_line = changes[i]['content']
            new_line = changes[i + 1]['content']
            line_num = changes[i]['line_num']
            
            field_changes = compare_csv_lines(old_line, new_line, headers)
            
            modifications.append({
                'line_num': line_num,
                'field_changes': field_changes
            })
            
            i += 2
        else:
            i += 1
    
    return modifications
```

## 特殊情况处理

### 1. 表头变更

```python
def detect_header_change(changes):
    """检测表头是否变更"""
    for i in range(len(changes) - 1):
        if changes[i]['type'] == 'delete' and \
           changes[i + 1]['type'] == 'add' and \
           changes[i]['line_num'] == 1:
            old_headers = parse_csv_line(changes[i]['content'])
            new_headers = parse_csv_line(changes[i + 1]['content'])
            
            header_changes = []
            for j, (old, new) in enumerate(zip(old_headers, new_headers)):
                if old != new:
                    header_changes.append({
                        'position': j,
                        'old_name': old,
                        'new_name': new
                    })
            
            return header_changes
    
    return None
```

### 2. 批量相同修改

```python
def detect_batch_pattern(modifications):
    """检测批量相同模式的修改"""
    if len(modifications) < 5:
        return None
    
    # 检查是否所有修改都是同一字段
    field_names = set()
    for mod in modifications:
        for change in mod['field_changes']:
            field_names.add(change['field_name'])
    
    if len(field_names) == 1:
        field_name = list(field_names)[0]
        
        # 检查修改模式
        patterns = []
        for mod in modifications:
            change = mod['field_changes'][0]
            old = change['old_value']
            new = change['new_value']
            
            # 检测添加书名号模式
            if not old.startswith('《') and new == f'《{old}》':
                patterns.append('add_book_marks')
        
        if len(patterns) == len(modifications) and len(set(patterns)) == 1:
            return {
                'field': field_name,
                'pattern': patterns[0],
                'count': len(modifications)
            }
    
    return None
```

### 3. 未提交的变更

```python
def get_unstaged_changes(file_path):
    """获取未暂存的变更"""
    result = subprocess.run(
        ['git', 'diff', file_path],
        capture_output=True,
        text=True
    )
    return result.stdout

def get_staged_changes(file_path):
    """获取已暂存的变更"""
    result = subprocess.run(
        ['git', 'diff', '--cached', file_path],
        capture_output=True,
        text=True
    )
    return result.stdout
```

## 错误处理

```python
def safe_parse_diff(file_path):
    """安全地解析 diff，处理各种错误情况"""
    try:
        # 检查是否在 Git 仓库中
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return {'error': 'Not a git repository'}
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        # 获取 diff
        changes = parse_git_diff(file_path)
        
        if not changes:
            return {'error': 'No changes detected'}
        
        return {'success': True, 'changes': changes}
        
    except Exception as e:
        return {'error': str(e)}
```

## 性能优化

对于大文件（>1000行）的 diff：

1. **限制上下文行数**：
   ```bash
   git diff -U0 file.csv  # 不显示上下文
   ```

2. **只获取变更统计**：
   ```bash
   git diff --numstat file.csv
   ```

3. **分块处理**：
   ```python
   def process_large_diff(file_path, chunk_size=100):
       """分块处理大文件的 diff"""
       changes = parse_git_diff(file_path)
       
       for i in range(0, len(changes), chunk_size):
           chunk = changes[i:i + chunk_size]
           yield process_chunk(chunk)
   ```
