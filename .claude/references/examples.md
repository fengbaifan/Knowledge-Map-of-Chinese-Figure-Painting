# 使用示例

本文档提供中国人物画知识图谱项目的常用命令和操作示例。

## 数据审查示例

### 使用 extraction-reviewer 技能

#### 审查单个文件
```bash
# 方式 1：使用技能命令
/extraction-reviewer --file 03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv

# 方式 2：直接运行脚本（如果技能提供）
python .claude/skills/extraction-reviewer/scripts/reviewer.py \
  --file 03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv \
  --output-dir 04-审查与修订/古画品录
```

#### 审查整个文献目录
```bash
# 审查某部文献的所有 CSV 文件
/extraction-reviewer --dir 03-初步抽取/古画品录

# 或使用脚本
python .claude/skills/extraction-reviewer/scripts/reviewer.py \
  --dir 03-初步抽取/古画品录 \
  --output-dir 04-审查与修订/古画品录
```

#### 审查多个文献
```bash
# 批量审查
for dir in 03-初步抽取/*/; do
  dirname=$(basename "$dir")
  echo "审查 $dirname"
  /extraction-reviewer --dir "$dir"
done
```

### 查看审查报告

```bash
# 查看最新的审查报告
ls -lt 04-审查与修订/古画品录/报告/ | head -5

# 查看报告内容
cat 04-审查与修订/古画品录/报告/审查报告_20260419_165338.md

# 查看问题清单（CSV 格式，可用 Excel 打开）
open 04-审查与修订/古画品录/报告/问题清单_20260419_165338.csv
```

## 变更日志示例

### 使用 change-logger 技能

#### 自动记录（extraction-reviewer 触发）
```bash
# extraction-reviewer 完成后会自动调用 change-logger
# 无需手动操作
```

#### 手动记录变更
```bash
# 记录单个文件的修改
python .claude/skills/change-logger/scripts/logger.py \
  --files 04-审查与修订/古画品录/修订数据/M2.1_历史人物_修订版_20260419.csv \
  --reason "手动修正人物生卒年份" \
  --original-file 03-初步抽取/古画品录/M2.1_历史人物.csv

# 记录多个文件的修改
python .claude/skills/change-logger/scripts/logger.py \
  --files 04-审查与修订/古画品录/修订数据/*.csv \
  --reason "批量修复书名格式" \
  --original-file 03-初步抽取/古画品录/
```

### 查看变更日志

```bash
# 查看今天的变更日志
cat 04-审查与修订/变更日志/$(date +%Y-%m)/变更日志_$(date +%Y-%m-%d).md

# 查看本月所有变更
ls -l 04-审查与修订/变更日志/$(date +%Y-%m)/

# 搜索特定文件的变更历史
grep "M2.1_历史人物" 04-审查与修订/变更日志/2026-04/*.md
```

## 数据统计示例

### 统计记录数

```bash
# 统计某部文献的总记录数
wc -l 03-初步抽取/历代名画记/*.csv

# 统计所有文献的记录数
for dir in 03-初步抽取/*/; do
  dirname=$(basename "$dir")
  count=$(wc -l "$dir"/*.csv | tail -1 | awk '{print $1}')
  echo "$dirname: $count 行"
done
```

### 查看字段覆盖率

```bash
# 查看表头
head -1 03-初步抽取/历代名画记/M2.1_历史人物核心表.csv

# 统计某字段的非空值数量
awk -F',' 'NR>1 && $3!="" {count++} END {print count}' \
  03-初步抽取/历代名画记/M2.1_历史人物核心表.csv
```

### 查看统计数据

```bash
# 查看审查统计（JSON 格式）
cat 04-审查与修订/古画品录/统计/统计数据_20260419_165338.json

# 使用 jq 格式化输出
jq '.' 04-审查与修订/古画品录/统计/统计数据_20260419_165338.json
```

## 数据格式检查示例

### 检查文件编码

```bash
# 检查单个文件编码
file -I 03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv

# 批量检查编码
for file in 03-初步抽取/古画品录/*.csv; do
  echo "$file:"
  file -I "$file"
done
```

### 检查书名格式

```bash
# 检查 source_book 字段是否有书名号
grep -n "source_book" 03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv | head -5

# 查找缺少书名号的记录
awk -F',' 'NR>1 && $4!~/《.*》/ {print NR": "$4}' \
  03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv
```

### 检查 ID 前缀

```bash
# 检查 person_id 是否都有 meso_ 前缀
awk -F',' 'NR>1 && $1!~/^meso_/ {print NR": "$1}' \
  03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv

# 检查 work_id 是否都有 micro_ 前缀
awk -F',' 'NR>1 && $1!~/^micro_/ {print NR": "$1}' \
  03-初步抽取/古画品录/M3.1_作品实体表_古画品录.csv
```

## 数据备份示例

### 备份原始数据

```bash
# 备份整个抽取目录
tar -czf backup_$(date +%Y%m%d).tar.gz 03-初步抽取/

# 备份单个文献
tar -czf 古画品录_backup_$(date +%Y%m%d).tar.gz 03-初步抽取/古画品录/
```

### 恢复备份

```bash
# 恢复备份
tar -xzf backup_20260419.tar.gz

# 恢复到指定目录
tar -xzf backup_20260419.tar.gz -C /path/to/restore/
```

## Git 操作示例

### 提交修订数据

```bash
# 查看修改状态
git status

# 添加修订数据
git add 04-审查与修订/古画品录/修订数据/

# 提交
git commit -m "修订古画品录数据：修复书名格式和ID前缀"

# 推送到远程
git push origin main
```

### 查看修改历史

```bash
# 查看某个文件的修改历史
git log --follow 03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv

# 查看具体修改内容
git diff HEAD~1 03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv
```

## Python 脚本示例

### 读取 CSV 文件

```python
import pandas as pd

# 读取 CSV 文件
df = pd.read_csv(
    '03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv',
    encoding='utf-8-sig',
    index_col=False
)

# 查看基本信息
print(f"总记录数: {len(df)}")
print(f"字段列表: {df.columns.tolist()}")
print(f"前5条记录:\n{df.head()}")
```

### 检查数据质量

```python
import pandas as pd

df = pd.read_csv(
    '03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv',
    encoding='utf-8-sig',
    index_col=False
)

# 检查必填字段
required_fields = ['source_book', 'person_id', 'person_name']
for field in required_fields:
    null_count = df[field].isna().sum()
    empty_count = (df[field] == '').sum()
    print(f"{field}: {null_count} 个空值, {empty_count} 个空字符串")

# 检查书名格式
no_brackets = df[~df['source_book'].str.contains('《.*》', na=False)]
print(f"缺少书名号的记录数: {len(no_brackets)}")

# 检查 ID 前缀
wrong_prefix = df[~df['person_id'].str.startswith('meso_', na=False)]
print(f"ID 前缀错误的记录数: {len(wrong_prefix)}")
```

### 批量修复数据

```python
import pandas as pd

df = pd.read_csv(
    '03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv',
    encoding='utf-8-sig',
    index_col=False
)

# 修复书名格式
df['source_book'] = df['source_book'].apply(
    lambda x: f"《{x}》" if not pd.isna(x) and not x.startswith('《') else x
)

# 修复 ID 前缀
df['person_id'] = df['person_id'].apply(
    lambda x: f"meso_{x}" if not pd.isna(x) and not x.startswith('meso_') else x
)

# 保存修订数据
df.to_csv(
    '04-审查与修订/古画品录/修订数据/M2.1_历史人物_修订版.csv',
    encoding='utf-8-sig',
    index=False
)

print("数据修复完成")
```

## 常用查询示例

### 查找特定人物

```bash
# 在所有文件中查找"顾恺之"
grep -r "顾恺之" 03-初步抽取/

# 查找特定 person_id
grep "meso_gu_kaizhi" 03-初步抽取/*/M2.*.csv
```

### 统计人物数量

```bash
# 统计某部文献的人物数量
wc -l 03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv

# 统计所有文献的人物总数
cat 03-初步抽取/*/M2.1_*.csv | wc -l
```

### 查找重复记录

```python
import pandas as pd

df = pd.read_csv(
    '03-初步抽取/古画品录/M2.1_历史人物_古画品录.csv',
    encoding='utf-8-sig',
    index_col=False
)

# 查找重复的 person_id
duplicates = df[df.duplicated(subset=['person_id'], keep=False)]
print(f"重复的 person_id 数量: {len(duplicates)}")
print(duplicates[['person_id', 'person_name']])
```

## 项目维护示例

### 清理临时文件

```bash
# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 清理 macOS 文件
find . -name ".DS_Store" -delete
```

### 更新文档

```bash
# 更新 CLAUDE.md
vim CLAUDE.md

# 更新数据结构规范
vim 01-元知识/中国人物画知识图谱数据结构v1_4.md

# 提交文档更新
git add CLAUDE.md 01-元知识/
git commit -m "更新项目文档"
```

### 生成项目报告

```bash
# 统计项目进度
echo "=== 项目统计 ==="
echo "已处理文献数: $(ls -d 03-初步抽取/*/ | wc -l)"
echo "总记录数: $(cat 03-初步抽取/*/M*.csv | wc -l)"
echo "审查报告数: $(find 04-审查与修订 -name "审查报告_*.md" | wc -l)"
echo "变更日志数: $(find 04-审查与修订/变更日志 -name "*.md" | wc -l)"
```
