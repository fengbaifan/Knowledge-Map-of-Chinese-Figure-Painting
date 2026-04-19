#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据结构规范解析器
从 Markdown 规范文档中提取表结构定义
"""

import re
import json
from typing import Dict, List, Any


class SchemaParser:
    """解析数据结构规范文档"""

    def __init__(self):
        # 手动维护的表结构定义（基于规范 v1.4）
        self.schemas = {
            "M1.1_时序本体": {
                "table_name": "时序本体 (Temporal Ontology)",
                "required_fields": ["period_id", "name", "time_range", "source_book"],
                "recommended_fields": ["source_chapter", "source_text", "dynastic_info"],
                "optional_fields": ["source_page"],
                "field_formats": {
                    "period_id": {"pattern": r"^period_", "type": "string"},
                    "source_book": {"pattern": r"^《.*》$", "type": "string"},
                    "time_range": {"type": "json_struct"}
                }
            },
            "M1.2_空间地理本体": {
                "table_name": "空间地理本体 (Spatial Ontology)",
                "required_fields": ["location_id", "modern_address", "source_book"],
                "recommended_fields": ["source_chapter", "source_text", "historical_names"],
                "optional_fields": ["coordinates", "source_page"],
                "field_formats": {
                    "location_id": {"pattern": r"^loc_", "type": "string"},
                    "source_book": {"pattern": r"^《.*》$", "type": "string"}
                }
            },
            "M1.3_图像志题材分类": {
                "table_name": "图像志题材分类 (Iconography)",
                "required_fields": ["icon_id", "name_cn", "source_book"],
                "recommended_fields": ["source_chapter", "source_text", "parent_id"],
                "optional_fields": ["name_en", "description", "source_page"],
                "field_formats": {
                    "icon_id": {"pattern": r"^icon_", "type": "string"},
                    "source_book": {"pattern": r"^《.*》$", "type": "string"}
                }
            },
            "M2.1_历史人物": {
                "table_name": "历史人物核心表 (Person)",
                "required_fields": ["person_id", "name", "primary_role", "source_book"],
                "recommended_fields": ["source_chapter", "source_text", "period_ref"],
                "optional_fields": ["courtesy_name", "pseudonym", "other_names", "choronym",
                                   "birth_death", "authority_ids", "source_page"],
                "field_formats": {
                    "person_id": {"pattern": r"^meso_", "type": "string"},
                    "source_book": {"pattern": r"^《.*》$", "type": "string"},
                    "primary_role": {"enum": ["Painter", "Critic", "Collector", "Calligrapher",
                                             "Scholar", "Patron", "Other"]},
                    "birth_death": {"type": "json_struct"}
                }
            },
            "M2.2_履历与时空轨迹": {
                "table_name": "履历与时空轨迹 (CV)",
                "required_fields": ["cv_id", "person_ref", "event_type", "source_book"],
                "recommended_fields": ["source_chapter", "source_text", "time_ref", "location_ref"],
                "optional_fields": ["description", "source_page"],
                "field_formats": {
                    "cv_id": {"pattern": r"^cv_", "type": "string"},
                    "person_ref": {"pattern": r"^meso_", "type": "string"},
                    "source_book": {"pattern": r"^《.*》$", "type": "string"}
                }
            },
            "M2.3_社会关系实例": {
                "table_name": "社会关系实例 (Relation)",
                "required_fields": ["rel_id", "source_id", "target_id", "relation_type", "source_book"],
                "recommended_fields": ["source_chapter", "source_text", "formal_name"],
                "optional_fields": ["time_range", "source_page"],
                "field_formats": {
                    "rel_id": {"pattern": r"^rel_", "type": "string"},
                    "source_id": {"pattern": r"^meso_", "type": "string"},
                    "target_id": {"pattern": r"^meso_", "type": "string"},
                    "source_book": {"pattern": r"^《.*》$", "type": "string"},
                    "relation_type": {"enum": ["Teacher", "Student", "Friend", "Colleague",
                                              "Spouse", "Parent", "Child", "Sibling", "Other"]}
                }
            },
            "M3.1_作品实体表": {
                "table_name": "作品实体表 (Work)",
                "required_fields": ["work_id", "title", "creator_ref", "source_book"],
                "recommended_fields": ["source_chapter", "source_text", "period_ref", "icon_ref"],
                "optional_fields": ["status", "support", "dimensions", "repository", "source_page"],
                "field_formats": {
                    "work_id": {"pattern": r"^micro_", "type": "string"},
                    "creator_ref": {"pattern": r"^meso_", "type": "string"},
                    "source_book": {"pattern": r"^《.*》$", "type": "string"},
                    "status": {"enum": ["Extant", "Lost", "Attributed", "Copy", "Unknown"]},
                    "support": {"enum": ["Silk", "Paper", "Wall", "Wood", "Other", "Unknown"]}
                }
            },
            "M3.2_文献著录与品评": {
                "table_name": "文献著录与品评 (Literature)",
                "required_fields": ["lit_id", "target_ref", "source_book"],
                "recommended_fields": ["source_chapter", "author_ref", "quote"],
                "optional_fields": ["quality_rank", "source_page"],
                "field_formats": {
                    "lit_id": {"pattern": r"^lit_", "type": "string"},
                    "source_book": {"pattern": r"^《.*》$", "type": "string"}
                }
            }
        }

    def get_schema(self, table_name: str) -> Dict[str, Any]:
        """获取指定表的结构定义"""
        # 尝试精确匹配
        if table_name in self.schemas:
            return self.schemas[table_name]

        # 尝试模糊匹配（基于文件名）
        for key, schema in self.schemas.items():
            if key in table_name or table_name in key:
                return schema

        # 未找到，返回空定义
        return {
            "table_name": table_name,
            "required_fields": ["source_book"],
            "recommended_fields": ["source_chapter", "source_text"],
            "optional_fields": [],
            "field_formats": {
                "source_book": {"pattern": r"^《.*》$", "type": "string"}
            }
        }

    def infer_table_type(self, filename: str) -> str:
        """从文件名推断表类型"""
        filename_lower = filename.lower()

        if "时序" in filename or "temporal" in filename_lower or "1.1" in filename or "m1.1" in filename_lower:
            return "M1.1_时序本体"
        elif "空间" in filename or "地理" in filename or "spatial" in filename_lower or "1.2" in filename or "m1.2" in filename_lower:
            return "M1.2_空间地理本体"
        elif "图像志" in filename or "题材" in filename or "iconography" in filename_lower or "1.3" in filename or "m1.3" in filename_lower:
            return "M1.3_图像志题材分类"
        elif "人物" in filename or "person" in filename_lower or "2.1" in filename or "m2.1" in filename_lower:
            return "M2.1_历史人物"
        elif "履历" in filename or "时空轨迹" in filename or "cv" in filename_lower or "2.2" in filename or "m2.2" in filename_lower:
            return "M2.2_履历与时空轨迹"
        elif "社会关系" in filename or "relation" in filename_lower or "2.3" in filename or "m2.3" in filename_lower:
            return "M2.3_社会关系实例"
        elif "作品" in filename or "work" in filename_lower or "3.1" in filename or "m3.1" in filename_lower:
            return "M3.1_作品实体表"
        elif "文献" in filename or "著录" in filename or "品评" in filename or "literature" in filename_lower or "3.2" in filename or "m3.2" in filename_lower:
            return "M3.2_文献著录与品评"
        else:
            return "Unknown"

    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """获取所有表结构定义"""
        return self.schemas


if __name__ == "__main__":
    # 测试
    parser = SchemaParser()

    # 测试文件名推断
    test_files = [
        "M2.1_历史人物_古画品录.csv",
        "2.1_历史人物核心表.csv",
        "M3.1_作品实体表（古画品录）.csv",
        "1.1_时序本体.csv"
    ]

    for filename in test_files:
        table_type = parser.infer_table_type(filename)
        schema = parser.get_schema(table_type)
        print(f"\n文件: {filename}")
        print(f"推断类型: {table_type}")
        print(f"必填字段: {schema['required_fields']}")
