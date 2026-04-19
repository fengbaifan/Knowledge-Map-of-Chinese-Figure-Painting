#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
变更日志记录器

自动记录项目中的数据修订操作，使用 Git diff 对比变更，
生成包含修改人、时间、具体变更内容的详细日志。
"""

import argparse
import subprocess
import csv
import io
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class GitDiffParser:
    """Git diff 解析器"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.headers = self._read_headers()

    def _read_headers(self) -> List[str]:
        """读取 CSV 文件表头"""
        try:
            with open(self.file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                return next(reader)
        except:
            return []

    def parse_csv_line(self, line: str) -> List[str]:
        """解析 CSV 行，正确处理引号内的逗号"""
        reader = csv.reader(io.StringIO(line))
        try:
            return next(reader)
        except:
            return []

    def get_diff(self) -> str:
        """获取文件的 git diff 输出"""
        try:
            result = subprocess.run(
                ['git', 'diff', self.file_path],
                capture_output=True,
                text=True,
                cwd=Path(self.file_path).parent
            )
            return result.stdout
        except Exception as e:
            print(f"⚠️ 获取 git diff 失败：{e}")
            return ""

    def parse_diff(self) -> List[Dict]:
        """解析 diff 输出，返回变更列表"""
        diff_output = self.get_diff()

        if not diff_output:
            return []

        changes = []
        hunk_pattern = r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@'

        lines = diff_output.split('\n')
        current_line_num = 0

        for i, line in enumerate(lines):
            # 匹配 hunk 头
            hunk_match = re.match(hunk_pattern, line)
            if hunk_match:
                old_start, old_count, new_start, new_count = map(int, hunk_match.groups())
                current_line_num = new_start
                continue

            # 匹配变更行
            if line.startswith('-') and not line.startswith('---'):
                # 删除的行
                old_line = line[1:]
                # 查找对应的新增行
                if i + 1 < len(lines) and lines[i + 1].startswith('+'):
                    new_line = lines[i + 1][1:]

                    # 对比字段
                    field_changes = self._compare_lines(old_line, new_line)

                    if field_changes:
                        changes.append({
                            'line_num': current_line_num,
                            'field_changes': field_changes
                        })

                current_line_num += 1
            elif line.startswith('+') and not line.startswith('+++'):
                current_line_num += 1
            elif not line.startswith('-') and not line.startswith('+'):
                current_line_num += 1

        return changes

    def _compare_lines(self, old_line: str, new_line: str) -> List[Dict]:
        """对比两行 CSV 数据，返回变更的字段"""
        old_fields = self.parse_csv_line(old_line)
        new_fields = self.parse_csv_line(new_line)

        if not old_fields or not new_fields:
            return []

        field_changes = []

        for i, (old_val, new_val) in enumerate(zip(old_fields, new_fields)):
            if old_val != new_val and i < len(self.headers):
                field_changes.append({
                    'field_name': self.headers[i],
                    'old_value': old_val,
                    'new_value': new_val
                })

        return field_changes


class ChangeLogger:
    """变更日志记录器"""

    def __init__(self, log_dir: str = "99-日志文档"):
        self.log_dir = Path(log_dir)
        self.git_user = self._get_git_user()
        self.git_email = self._get_git_email()

    def _get_git_user(self) -> str:
        """获取 Git 用户名"""
        try:
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() or "Unknown User"
        except:
            return "Unknown User"

    def _get_git_email(self) -> str:
        """获取 Git 邮箱"""
        try:
            result = subprocess.run(
                ['git', 'config', 'user.email'],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() or ""
        except:
            return ""

    def _get_log_file_path(self) -> Path:
        """获取今天的日志文件路径"""
        now = datetime.now()
        year_month = now.strftime('%Y-%m')
        date_str = now.strftime('%Y-%m-%d')

        log_subdir = self.log_dir / year_month
        log_subdir.mkdir(parents=True, exist_ok=True)

        return log_subdir / f"变更日志_{date_str}.md"

    def _read_existing_log(self, log_file: Path) -> Tuple[str, int]:
        """读取已存在的日志文件，返回内容和当前记录数"""
        if not log_file.exists():
            return "", 0

        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 统计已有记录数
        record_count = len(re.findall(r'## \[\d{2}:\d{2}:\d{2}\]', content))

        return content, record_count

    def _create_log_header(self, date_str: str) -> str:
        """创建日志文件头部"""
        now = datetime.now()
        return f"""# 变更日志 - {date_str}

**创建时间**：{now.strftime('%Y-%m-%d %H:%M:%S')}
**最后更新**：{now.strftime('%Y-%m-%d %H:%M:%S')}
**修订次数**：1 次
**涉及文件**：待更新
**修改行数**：待更新

本文件记录 {date_str} 的所有数据修订操作。

---

"""

    def _format_change_record(
        self,
        record_num: int,
        modified_files: List[str],
        reason: str,
        changes: Dict[str, List[Dict]],
        original_file: Optional[str] = None,
        report_file: Optional[str] = None,
        issue_list_file: Optional[str] = None
    ) -> str:
        """格式化变更记录"""
        now = datetime.now()
        time_str = now.strftime('%H:%M:%S')
        datetime_str = now.strftime('%Y-%m-%d %H:%M:%S')

        # 统计总修改行数和字段数
        total_lines = sum(len(file_changes) for file_changes in changes.values())
        all_fields = set()
        for file_changes in changes.values():
            for change in file_changes:
                for field_change in change['field_changes']:
                    all_fields.add(field_change['field_name'])

        # 构建记录
        record = f"""## [{time_str}] 数据修订记录 #{record_num}

**修改人**：{self.git_user}"""

        if self.git_email:
            record += f" <{self.git_email}>"

        record += f"""
**修改时间**：{datetime_str}
**修改类型**：数据修订（自动修复）
**触发来源**：extraction-reviewer

### 影响范围

"""

        # 列出所有修改的文件
        for file_path in modified_files:
            file_changes = changes.get(file_path, [])
            record += f"- **文件路径**：`{file_path}`\n"
            if original_file:
                record += f"- **原始文件**：`{original_file}`\n"
            record += f"- **修改行数**：{len(file_changes)} 行\n"
            record += f"- **修改字段数**：{len(all_fields)} 个字段\n\n"

        record += "### 修改内容详情\n\n"

        # 详细列出每个文件的变更
        for file_path in modified_files:
            file_changes = changes.get(file_path, [])

            if not file_changes:
                record += f"**{Path(file_path).name}**：无字段级变更检测到\n\n"
                continue

            # 按行号列出变更
            for change in file_changes[:20]:  # 最多显示前20行
                line_num = change['line_num']
                record += f"**第 {line_num} 行**：\n"

                for field_change in change['field_changes']:
                    field_name = field_change['field_name']
                    old_val = field_change['old_value']
                    new_val = field_change['new_value']

                    record += f"- 字段：`{field_name}`\n"
                    record += f"- 修改前：`{old_val}`\n"
                    record += f"- 修改后：`{new_val}`\n"
                    record += f"- 原因：{self._infer_reason(old_val, new_val)}\n\n"

            if len(file_changes) > 20:
                record += f"*（还有 {len(file_changes) - 20} 行变更未显示）*\n\n"

        record += f"### 修改原因\n\n{reason}\n\n"

        # 相关文件
        record += "### 相关文件\n\n"
        if report_file:
            record += f"- 审查报告：`{report_file}`\n"
        if issue_list_file:
            record += f"- 问题清单：`{issue_list_file}`\n"

        # 尝试获取 Git commit hash
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                commit_hash = result.stdout.strip()[:7]
                record += f"- Git commit：`{commit_hash}`\n"
        except:
            pass

        record += "\n---\n\n"

        return record

    def _infer_reason(self, old_val: str, new_val: str) -> str:
        """推断修改原因"""
        if not old_val.startswith('《') and new_val.startswith('《') and new_val.endswith('》'):
            return "书名格式不规范，添加书名号"
        elif old_val.startswith('"') and not new_val.startswith('"'):
            return "移除多余引号"
        elif '.' in old_val and '_' in new_val:
            return "字段名格式修正"
        else:
            return "数据修正"

    def log_changes(
        self,
        modified_files: List[str],
        reason: str,
        original_file: Optional[str] = None,
        report_file: Optional[str] = None,
        issue_list_file: Optional[str] = None
    ) -> Dict:
        """记录变更到日志文件"""
        try:
            # 获取日志文件路径
            log_file = self._get_log_file_path()

            # 读取已存在的日志
            existing_content, record_count = self._read_existing_log(log_file)

            # 解析每个文件的变更
            changes = {}
            for file_path in modified_files:
                if Path(file_path).exists() and file_path.endswith('.csv'):
                    parser = GitDiffParser(file_path)
                    file_changes = parser.parse_diff()
                    changes[file_path] = file_changes

            # 创建新记录
            new_record = self._format_change_record(
                record_num=record_count + 1,
                modified_files=modified_files,
                reason=reason,
                changes=changes,
                original_file=original_file,
                report_file=report_file,
                issue_list_file=issue_list_file
            )

            # 写入日志文件
            if existing_content:
                # 追加到已有文件
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(new_record)
            else:
                # 创建新文件
                date_str = datetime.now().strftime('%Y-%m-%d')
                header = self._create_log_header(date_str)
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(header)
                    f.write(new_record)

            return {
                'success': True,
                'log_file': str(log_file),
                'record_num': record_count + 1
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def main():
    parser = argparse.ArgumentParser(description='记录数据修订变更到日志')
    parser.add_argument('--files', nargs='+', required=True, help='修改的文件路径列表')
    parser.add_argument('--reason', required=True, help='修改原因')
    parser.add_argument('--original-file', help='原始文件路径')
    parser.add_argument('--report-file', help='审查报告路径')
    parser.add_argument('--issue-list-file', help='问题清单路径')
    parser.add_argument('--log-dir', default='99-日志文档', help='日志目录')

    args = parser.parse_args()

    logger = ChangeLogger(log_dir=args.log_dir)

    result = logger.log_changes(
        modified_files=args.files,
        reason=args.reason,
        original_file=args.original_file,
        report_file=args.report_file,
        issue_list_file=args.issue_list_file
    )

    if result['success']:
        print(f"✅ 变更日志已记录到：{result['log_file']}")
        print(f"   记录编号：#{result['record_num']}")
    else:
        print(f"❌ 变更日志记录失败：{result['error']}")
        exit(1)


if __name__ == '__main__':
    main()
