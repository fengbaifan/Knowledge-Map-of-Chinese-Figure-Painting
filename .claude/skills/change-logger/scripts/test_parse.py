#!/usr/bin/env python3
"""测试 parse_diff 方法"""

import subprocess
from pathlib import Path

# 测试文件路径
original = "/Users/a1234/Desktop/中国人物画知识图谱/03-初步抽取/续画品/2.1_历史人物核心表.csv"
modified = "/Users/a1234/Desktop/中国人物画知识图谱/04-审查与修订/续画品/修订数据/2.1_历史人物核心表_修订版_20260419_181820.csv"

# 获取 diff
result = subprocess.run(
    ['git', 'diff', '--no-index', original, modified],
    capture_output=True,
    text=True
)

diff_output = result.stdout
print(f"Diff 输出长度: {len(diff_output)} 字符")
print("\n前 2000 字符:")
print(diff_output[:2000])
print("\n" + "="*80)

# 测试 hunk 匹配
import re
hunk_pattern = r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@'
lines = diff_output.split('\n')

print(f"\n总行数: {len(lines)}")

hunk_count = 0
change_pairs = 0

for i, line in enumerate(lines):
    hunk_match = re.match(hunk_pattern, line)
    if hunk_match:
        hunk_count += 1
        print(f"\nHunk {hunk_count}: {line}")
        old_start, old_count, new_start, new_count = map(int, hunk_match.groups())
        print(f"  旧文件: 从第 {old_start} 行开始，共 {old_count} 行")
        print(f"  新文件: 从第 {new_start} 行开始，共 {new_count} 行")

    # 查找 - 和 + 配对
    if line.startswith('-') and not line.startswith('---'):
        if i + 1 < len(lines) and lines[i + 1].startswith('+') and not lines[i + 1].startswith('+++'):
            change_pairs += 1
            if change_pairs <= 3:  # 只打印前3对
                print(f"\n变更对 {change_pairs} (行 {i}):")
                print(f"  旧: {line[:100]}")
                print(f"  新: {lines[i + 1][:100]}")

print(f"\n\n统计:")
print(f"  找到 {hunk_count} 个 hunk")
print(f"  找到 {change_pairs} 对变更行")
