#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抽取结果审查器
审查中国人物画知识图谱抽取结果的数据质量
"""

import os
import sys
import json
import re
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pandas as pd

# 导入规范解析器
from schema_parser import SchemaParser


class ExtractionReviewer:
    """抽取结果审查器"""

    def __init__(self, schema_path: str = None):
        self.parser = SchemaParser()
        self.issues = []  # 问题列表
        self.stats = {}   # 统计信息
        self.fixes = []   # 修复记录

    def review_file(self, file_path: str) -> Dict[str, Any]:
        """审查单个文件"""
        print(f"\n正在审查: {file_path}")

        # 读取 CSV 文件，不使用第一列作为索引
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig', index_col=False)
        except Exception as e:
            return {
                "file": file_path,
                "error": f"文件读取失败: {str(e)}",
                "issues": [],
                "stats": {},
                "record_count": 0
            }

        # 推断表类型
        filename = os.path.basename(file_path)
        table_type = self.parser.infer_table_type(filename)
        schema = self.parser.get_schema(table_type)

        print(f"  表类型: {schema['table_name']}")
        print(f"  记录数: {len(df)}")

        # 执行各项检查
        file_issues = []
        file_issues.extend(self._check_field_names(df, schema, file_path))
        file_issues.extend(self._check_completeness(df, schema, file_path))
        file_issues.extend(self._check_formats(df, schema, file_path))

        # 统计信息
        file_stats = self._calculate_stats(df, schema)

        return {
            "file": file_path,
            "table_type": table_type,
            "table_name": schema['table_name'],
            "record_count": len(df),
            "issues": file_issues,
            "stats": file_stats,
            "dataframe": df  # 保留 DataFrame 用于后续修复
        }

    def _check_field_names(self, df: pd.DataFrame, schema: Dict, file_path: str) -> List[Dict]:
        """检查字段名是否正确"""
        issues = []
        columns = df.columns.tolist()

        # 检查常见的字段名错误
        field_name_fixes = {
            "source.chapter": "source_chapter",
            "source_chapter.": "source_chapter",
            "originalsource_sentence": "source_text",
            "source_sentence": "source_text",
            "original_text": "source_text"
        }

        for wrong_name, correct_name in field_name_fixes.items():
            if wrong_name in columns:
                issues.append({
                    "file": file_path,
                    "row": None,
                    "field": wrong_name,
                    "issue_type": "字段名错误",
                    "severity": "警告",
                    "current_value": wrong_name,
                    "suggested_value": correct_name,
                    "auto_fixed": True,  # 字段名错误可以自动修复
                    "description": f"字段名应为 {correct_name}"
                })

        return issues

    def _check_completeness(self, df: pd.DataFrame, schema: Dict, file_path: str) -> List[Dict]:
        """检查数据完整性"""
        issues = []

        # 检查必填字段
        for field in schema['required_fields']:
            if field not in df.columns:
                issues.append({
                    "file": file_path,
                    "row": None,
                    "field": field,
                    "issue_type": "必填字段缺失",
                    "severity": "严重",
                    "current_value": None,
                    "suggested_value": None,
                    "auto_fixed": False,
                    "description": f"表中缺少必填字段: {field}"
                })
            else:
                # 检查字段中的空值
                null_rows = df[df[field].isna() | (df[field] == '')]
                for idx in null_rows.index:
                    # 处理可能的多级索引
                    if isinstance(idx, tuple):
                        row_num = int(idx[0]) + 2
                    else:
                        row_num = int(idx) + 2
                    issues.append({
                        "file": file_path,
                        "row": row_num,
                        "field": field,
                        "issue_type": "必填字段为空",
                        "severity": "严重",
                        "current_value": "",
                        "suggested_value": None,
                        "auto_fixed": False,
                        "description": f"必填字段 {field} 为空"
                    })

        # 检查推荐字段
        for field in schema['recommended_fields']:
            if field in df.columns:
                null_rows = df[df[field].isna() | (df[field] == '')]
                if len(null_rows) > len(df) * 0.5:  # 超过50%为空
                    issues.append({
                        "file": file_path,
                        "row": None,
                        "field": field,
                        "issue_type": "推荐字段缺失率高",
                        "severity": "警告",
                        "current_value": None,
                        "suggested_value": None,
                        "auto_fixed": False,
                        "description": f"推荐字段 {field} 缺失率 {len(null_rows)/len(df)*100:.1f}%"
                    })

        return issues

    def _check_formats(self, df: pd.DataFrame, schema: Dict, file_path: str) -> List[Dict]:
        """检查格式规范"""
        issues = []

        for field, format_spec in schema.get('field_formats', {}).items():
            if field not in df.columns:
                continue

            # 检查正则表达式模式
            if 'pattern' in format_spec:
                pattern = format_spec['pattern']
                for idx, value in df[field].items():
                    if pd.isna(value) or value == '':
                        continue

                    value_str = str(value)
                    if not re.match(pattern, value_str):
                        # 尝试自动修复
                        fixed_value, can_fix = self._try_fix_format(field, value_str, pattern)

                        # 处理可能的多级索引
                        if isinstance(idx, tuple):
                            row_num = int(idx[0]) + 2
                        else:
                            row_num = int(idx) + 2
                        issues.append({
                            "file": file_path,
                            "row": row_num,
                            "field": field,
                            "issue_type": "格式不规范",
                            "severity": "警告",
                            "current_value": value_str,
                            "suggested_value": fixed_value if can_fix else None,
                            "auto_fixed": can_fix,
                            "description": f"{field} 格式不符合规范"
                        })

            # 检查枚举值
            if 'enum' in format_spec:
                allowed_values = format_spec['enum']
                for idx, value in df[field].items():
                    if pd.isna(value) or value == '':
                        continue

                    if value not in allowed_values:
                        # 处理可能的多级索引
                        if isinstance(idx, tuple):
                            row_num = int(idx[0]) + 2
                        else:
                            row_num = int(idx) + 2
                        issues.append({
                            "file": file_path,
                            "row": row_num,
                            "field": field,
                            "issue_type": "枚举值错误",
                            "severity": "警告",
                            "current_value": value,
                            "suggested_value": None,
                            "auto_fixed": False,
                            "description": f"{field} 的值 '{value}' 不在允许范围内: {allowed_values}"
                        })

        return issues

    def _try_fix_format(self, field: str, value: str, pattern: str) -> Tuple[str, bool]:
        """尝试自动修复格式问题"""
        # 修复书名格式
        if field == "source_book" and pattern == r"^《.*》$":
            fixed = value.strip()
            # 移除可能存在的引号
            fixed = fixed.strip('"').strip("'")
            # 只有在没有书名号时才添加
            if not (fixed.startswith('《') and fixed.endswith('》')):
                if not fixed.startswith('《'):
                    fixed = '《' + fixed
                if not fixed.endswith('》'):
                    fixed = fixed + '》'
            return fixed, True

        # 修复 ID 前缀
        if field == "person_id" and pattern == r"^meso_":
            if not value.startswith('meso_'):
                return 'meso_' + value, True

        if field == "work_id" and pattern == r"^micro_":
            if not value.startswith('micro_'):
                return 'micro_' + value, True

        if field == "period_id" and pattern == r"^period_":
            if not value.startswith('period_'):
                return 'period_' + value, True

        if field == "location_id" and pattern == r"^loc_":
            if not value.startswith('loc_'):
                return 'loc_' + value, True

        return value, False

    def _calculate_stats(self, df: pd.DataFrame, schema: Dict) -> Dict[str, Any]:
        """计算统计信息"""
        stats = {
            "record_count": len(df),
            "field_coverage": {}
        }

        # 计算字段覆盖率
        for field in df.columns:
            non_null_count = df[field].notna().sum()
            non_empty_count = (df[field].notna() & (df[field] != '')).sum()
            stats["field_coverage"][field] = {
                "non_null": non_null_count,
                "non_empty": non_empty_count,
                "coverage_rate": non_empty_count / len(df) if len(df) > 0 else 0
            }

        # 计算必填字段完整率
        required_complete = 0
        for field in schema['required_fields']:
            if field in df.columns:
                if stats["field_coverage"][field]["coverage_rate"] == 1.0:
                    required_complete += 1

        stats["required_completeness"] = required_complete / len(schema['required_fields']) if schema['required_fields'] else 1.0

        # 计算推荐字段完整率
        recommended_complete = 0
        for field in schema['recommended_fields']:
            if field in df.columns:
                if stats["field_coverage"][field]["coverage_rate"] >= 0.8:
                    recommended_complete += 1

        stats["recommended_completeness"] = recommended_complete / len(schema['recommended_fields']) if schema['recommended_fields'] else 1.0

        return stats

    def auto_fix(self, review_result: Dict) -> pd.DataFrame:
        """自动修复可修复的问题"""
        df = review_result['dataframe'].copy()
        file_path = review_result['file']

        # 首先处理字段名修复
        field_renames = {}
        for issue in review_result['issues']:
            if issue['issue_type'] == '字段名错误' and issue['suggested_value']:
                field = issue['field']
                if field in df.columns and issue['suggested_value'] not in df.columns:
                    field_renames[field] = issue['suggested_value']
                    self.fixes.append({
                        "file": file_path,
                        "type": "字段名修复",
                        "from": field,
                        "to": issue['suggested_value']
                    })

        if field_renames:
            df.rename(columns=field_renames, inplace=True)

        # 然后处理字段值修复
        for issue in review_result['issues']:
            if issue['issue_type'] != '字段名错误' and issue.get('auto_fixed') and issue['suggested_value'] is not None:
                field = issue['field']
                row = issue['row']

                if row and field in df.columns:
                    df.at[row - 2, field] = issue['suggested_value']
                    self.fixes.append({
                        "file": file_path,
                        "row": row,
                        "field": field,
                        "type": "格式修复",
                        "from": issue['current_value'],
                        "to": issue['suggested_value']
                    })

        return df

    def generate_report(self, results: List[Dict], output_dir: str):
        """生成审查报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 创建输出目录
        report_dir = os.path.join(output_dir, "报告")
        revised_dir = os.path.join(output_dir, "修订数据")
        stats_dir = os.path.join(output_dir, "统计")

        os.makedirs(report_dir, exist_ok=True)
        os.makedirs(revised_dir, exist_ok=True)
        os.makedirs(stats_dir, exist_ok=True)

        # 生成 Markdown 报告
        report_path = os.path.join(report_dir, f"审查报告_{timestamp}.md")
        self._generate_markdown_report(results, report_path, timestamp)

        # 生成 CSV 问题清单
        issues_path = os.path.join(report_dir, f"问题清单_{timestamp}.csv")
        self._generate_issues_csv(results, issues_path)

        # 生成 JSON 统计
        stats_path = os.path.join(stats_dir, f"数据质量统计_{timestamp}.json")
        self._generate_stats_json(results, stats_path, timestamp)

        # 保存修订后的数据
        modified_files = []
        original_files = []
        for result in results:
            if result.get('dataframe') is not None:
                df_fixed = self.auto_fix(result)
                filename = os.path.basename(result['file'])
                name_without_ext = os.path.splitext(filename)[0]
                revised_path = os.path.join(revised_dir, f"{name_without_ext}_修订版_{timestamp}.csv")
                df_fixed.to_csv(revised_path, index=False, encoding='utf-8-sig')
                modified_files.append(revised_path)
                original_files.append(result['file'])

        print(f"\n✅ 审查完成！")
        print(f"\n📁 生成文件：")
        print(f"  - 审查报告: {report_path}")
        print(f"  - 问题清单: {issues_path}")
        print(f"  - 质量统计: {stats_path}")
        print(f"  - 修订数据: {revised_dir}/ ({len(results)} 个文件)")

        # 调用 change-logger 记录变更
        if modified_files and len(self.fixes) > 0:
            self._call_change_logger(
                modified_files=modified_files,
                original_files=original_files,
                report_file=report_path,
                issue_list_file=issues_path
            )

    def _generate_markdown_report(self, results: List[Dict], output_path: str, timestamp: str):
        """生成 Markdown 格式的审查报告"""
        # 统计摘要
        total_files = len(results)
        total_records = sum(r['record_count'] for r in results)
        all_issues = [issue for r in results for issue in r['issues']]
        severe_issues = [i for i in all_issues if i['severity'] == '严重']
        warning_issues = [i for i in all_issues if i['severity'] == '警告']
        auto_fixed = [i for i in all_issues if i.get('auto_fixed', False)]

        report = f"""# 中国人物画知识图谱抽取结果审查报告

**审查时间**：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**数据结构规范版本**：v1.4

## 一、审查摘要

- 审查文件总数：{total_files} 个
- 数据记录总数：{total_records} 条
- 发现问题总数：{len(all_issues)} 个
  - 严重问题（必须修复）：{len(severe_issues)} 个
  - 警告问题（建议修复）：{len(warning_issues)} 个
- 自动修复问题数：{len(auto_fixed)} 个
- 需人工处理问题数：{len(all_issues) - len(auto_fixed)} 个

## 二、数据质量统计

### 2.1 字段完整性统计

| 表名 | 总记录数 | 必填字段完整率 | 推荐字段完整率 |
|------|---------|--------------|--------------|
"""

        for result in results:
            table_name = result.get('table_name', '未知')
            record_count = result['record_count']
            req_complete = result['stats'].get('required_completeness', 0) * 100
            rec_complete = result['stats'].get('recommended_completeness', 0) * 100
            report += f"| {table_name} | {record_count} | {req_complete:.1f}% | {rec_complete:.1f}% |\n"

        report += "\n### 2.2 字段覆盖率详情\n\n"

        for result in results:
            if 'error' in result:
                continue
            report += f"**{result.get('table_name', '未知')}**：\n"
            field_coverage = result.get('stats', {}).get('field_coverage', {})
            for field, coverage in field_coverage.items():
                rate = coverage['coverage_rate'] * 100
                status = "✅" if rate == 100 else ("⚠️" if rate >= 50 else "❌")
                report += f"- {field}: {rate:.1f}% {status}\n"
            report += "\n"

        report += "## 三、问题清单\n\n"
        report += "### 3.1 严重问题（必须修复）\n\n"

        # 按问题类型分组
        severe_by_type = {}
        for issue in severe_issues:
            issue_type = issue['issue_type']
            if issue_type not in severe_by_type:
                severe_by_type[issue_type] = []
            severe_by_type[issue_type].append(issue)

        for issue_type, issues in severe_by_type.items():
            report += f"#### 问题类型：{issue_type}\n\n"
            report += "| 文件 | 行号 | 字段 | 问题描述 |\n"
            report += "|------|------|------|----------|\n"
            for issue in issues[:20]:  # 最多显示20个
                filename = os.path.basename(issue['file'])
                row = issue['row'] if issue['row'] else '-'
                report += f"| {filename} | {row} | {issue['field']} | {issue['description']} |\n"
            if len(issues) > 20:
                report += f"\n*（还有 {len(issues) - 20} 个类似问题未显示）*\n"
            report += "\n"

        report += "### 3.2 警告问题（建议修复）\n\n"

        # 按问题类型分组
        warning_by_type = {}
        for issue in warning_issues:
            issue_type = issue['issue_type']
            if issue_type not in warning_by_type:
                warning_by_type[issue_type] = []
            warning_by_type[issue_type].append(issue)

        for issue_type, issues in warning_by_type.items():
            report += f"#### 问题类型：{issue_type}\n\n"
            report += "| 文件 | 行号 | 字段 | 当前值 | 建议值 | 状态 |\n"
            report += "|------|------|------|--------|--------|------|\n"
            for issue in issues[:20]:
                filename = os.path.basename(issue['file'])
                row = issue['row'] if issue['row'] else '-'
                current = str(issue['current_value'])[:30] if issue['current_value'] else '-'
                suggested = str(issue['suggested_value'])[:30] if issue['suggested_value'] else '-'
                status = "✅ 已自动修复" if issue.get('auto_fixed') else "⚠️ 需人工处理"
                report += f"| {filename} | {row} | {issue['field']} | {current} | {suggested} | {status} |\n"
            if len(issues) > 20:
                report += f"\n*（还有 {len(issues) - 20} 个类似问题未显示）*\n"
            report += "\n"

        report += "## 四、修复建议\n\n"
        report += f"### 4.1 已自动修复的问题\n\n"
        report += f"- 格式修复：{len([f for f in self.fixes if f['type'] == '格式修复'])} 处\n"
        report += f"- 字段名修复：{len([f for f in self.fixes if f['type'] == '字段名修复'])} 处\n\n"

        report += "### 4.2 需要人工处理的问题\n\n"
        manual_issues = [i for i in all_issues if not i.get('auto_fixed', False)]
        if manual_issues:
            report += "请查看问题清单 CSV 文件，筛选需要人工处理的问题。\n\n"

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

    def _generate_issues_csv(self, results: List[Dict], output_path: str):
        """生成 CSV 格式的问题清单"""
        all_issues = []
        for result in results:
            for issue in result['issues']:
                all_issues.append({
                    "文件名": os.path.basename(issue['file']),
                    "行号": issue['row'] if issue['row'] else '',
                    "字段名": issue['field'],
                    "问题类型": issue['issue_type'],
                    "严重程度": issue['severity'],
                    "当前值": issue['current_value'] if issue['current_value'] else '',
                    "建议值": issue['suggested_value'] if issue['suggested_value'] else '',
                    "是否已修复": "是" if issue.get('auto_fixed') else "否",
                    "问题描述": issue['description']
                })

        df = pd.DataFrame(all_issues)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

    def _generate_stats_json(self, results: List[Dict], output_path: str, timestamp: str):
        """生成 JSON 格式的统计信息"""
        all_issues = [issue for r in results for issue in r['issues']]
        severe_issues = [i for i in all_issues if i['severity'] == '严重']
        warning_issues = [i for i in all_issues if i['severity'] == '警告']
        auto_fixed = [i for i in all_issues if i.get('auto_fixed', False)]

        stats = {
            "审查时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "审查范围": [r['file'] for r in results],
            "统计摘要": {
                "文件总数": len(results),
                "记录总数": sum(r['record_count'] for r in results),
                "问题总数": len(all_issues),
                "严重问题": len(severe_issues),
                "警告问题": len(warning_issues),
                "自动修复": len(auto_fixed),
                "需人工处理": len(all_issues) - len(auto_fixed)
            },
            "表级统计": {}
        }

        for result in results:
            if 'error' in result:
                continue
            table_name = result.get('table_name', '未知')
            field_coverage = result.get('stats', {}).get('field_coverage', {})
            stats["表级统计"][table_name] = {
                "记录数": result['record_count'],
                "必填字段完整率": result.get('stats', {}).get('required_completeness', 0),
                "推荐字段完整率": result.get('stats', {}).get('recommended_completeness', 0),
                "字段覆盖率": {
                    field: coverage['coverage_rate']
                    for field, coverage in field_coverage.items()
                }
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

    def _call_change_logger(self, modified_files: List[str], original_files: List[str],
                           report_file: str, issue_list_file: str):
        """调用 change-logger 记录变更"""
        try:
            # 构建修改原因
            fix_types = {}
            for fix in self.fixes:
                fix_type = fix['type']
                fix_types[fix_type] = fix_types.get(fix_type, 0) + 1

            reason_parts = []
            for fix_type, count in fix_types.items():
                reason_parts.append(f"{fix_type}（{count}处）")

            reason = f"extraction-reviewer 自动修复：{', '.join(reason_parts)}"

            # 获取 change-logger 脚本路径
            current_dir = Path(__file__).parent
            skills_dir = current_dir.parent.parent
            logger_script = skills_dir / 'change-logger' / 'scripts' / 'logger.py'

            if not logger_script.exists():
                print(f"\n⚠️ 未找到 change-logger 脚本: {logger_script}")
                return

            # 构建命令
            cmd = [
                sys.executable,
                str(logger_script),
                '--files', *modified_files,
                '--reason', reason,
                '--report-file', report_file,
                '--issue-list-file', issue_list_file
            ]

            # 添加原始文件参数（如果只有一个文件）
            if len(original_files) == 1:
                cmd.extend(['--original-file', original_files[0]])

            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"\n📝 变更日志已记录")
                # 提取日志文件路径
                for line in result.stdout.split('\n'):
                    if '变更日志已记录到' in line:
                        print(f"  {line.strip()}")
            else:
                print(f"\n⚠️ 变更日志记录失败: {result.stderr}")

        except Exception as e:
            print(f"\n⚠️ 调用 change-logger 失败: {e}")


def main():
    parser = argparse.ArgumentParser(description='审查中国人物画知识图谱抽取结果')
    parser.add_argument('--file', help='要审查的单个文件路径')
    parser.add_argument('--dir', help='要审查的目录路径')
    parser.add_argument('--output-dir', default='04-审查与修订', help='输出目录')

    args = parser.parse_args()

    reviewer = ExtractionReviewer()
    results = []

    if args.file:
        # 审查单个文件
        result = reviewer.review_file(args.file)
        results.append(result)
    elif args.dir:
        # 审查目录下所有 CSV 文件
        for root, dirs, files in os.walk(args.dir):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    result = reviewer.review_file(file_path)
                    results.append(result)
    else:
        print("错误：请指定 --file 或 --dir 参数")
        sys.exit(1)

    # 生成报告
    reviewer.generate_report(results, args.output_dir)


if __name__ == "__main__":
    main()
