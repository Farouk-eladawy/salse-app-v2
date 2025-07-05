#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project File Dependency Analyzer
يحلل ملفات المشروع ويرسم شجرة الاستدعاءات والاعتماديات
"""

import os
import ast
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict, deque
import argparse


class ProjectAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.files_info = {}
        self.dependencies = defaultdict(set)
        self.reverse_dependencies = defaultdict(set)
        self.external_imports = defaultdict(set)

    def find_python_files(self) -> List[Path]:
        """البحث عن جميع ملفات Python في المشروع"""
        python_files = []
        for file_path in self.project_root.rglob("*.py"):
            if not any(part.startswith('.') for part in file_path.parts):
                python_files.append(file_path)
        return python_files

    def get_relative_module_name(self, file_path: Path) -> str:
        """تحويل مسار الملف إلى اسم وحدة نسبي"""
        relative_path = file_path.relative_to(self.project_root)
        module_parts = list(relative_path.parts[:-1])  # المجلدات
        filename = relative_path.stem

        if filename != "__init__":
            module_parts.append(filename)

        return ".".join(module_parts) if module_parts else filename

    def parse_imports(self, file_content: str, current_module: str) -> Tuple[Set[str], Set[str]]:
        """استخراج الاستدعاءات من محتوى الملف"""
        local_imports = set()
        external_imports = set()

        try:
            tree = ast.parse(file_content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        if self.is_local_import(module_name):
                            local_imports.add(module_name)
                        else:
                            external_imports.add(module_name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module
                        if node.level > 0:  # relative import
                            # معالجة الاستدعاءات النسبية
                            resolved_module = self.resolve_relative_import(
                                current_module, module_name, node.level
                            )
                            if resolved_module:
                                local_imports.add(resolved_module)
                        else:
                            if self.is_local_import(module_name):
                                local_imports.add(module_name)
                            else:
                                external_imports.add(module_name)

        except SyntaxError as e:
            print(f"خطأ في تحليل الملف {current_module}: {e}")

        return local_imports, external_imports

    def is_local_import(self, module_name: str) -> bool:
        """تحديد ما إذا كان الاستدعاء محلي أم خارجي"""
        # قائمة بالمكتبات الخارجية الشائعة
        external_modules = {
            'os', 'sys', 'json', 'ast', 're', 'pathlib', 'typing',
            'collections', 'datetime', 'time', 'logging', 'sqlite3',
            'tkinter', 'threading', 'asyncio', 'urllib', 'http',
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'requests',
            'flask', 'django', 'fastapi', 'aiohttp', 'sqlalchemy',
            'pytest', 'unittest', 'mock', 'cryptography', 'PIL',
            'cv2', 'tensorflow', 'torch', 'sklearn', 'scipy'
        }

        # التحقق من الجذر الأول للوحدة
        root_module = module_name.split('.')[0]

        # إذا كان في قائمة المكتبات الخارجية
        if root_module in external_modules:
            return False

        # التحقق من وجود الملف في المشروع
        possible_paths = [
            self.project_root / f"{module_name.replace('.', '/')}.py",
            self.project_root / f"{module_name.replace('.', '/')}/__init__.py"
        ]

        return any(path.exists() for path in possible_paths)

    def resolve_relative_import(self, current_module: str, import_module: str, level: int) -> str:
        """حل الاستدعاءات النسبية"""
        if not current_module:
            return None

        current_parts = current_module.split('.')

        # إزالة المستويات بناءً على عدد النقاط
        for _ in range(level):
            if current_parts:
                current_parts.pop()

        if import_module:
            return '.'.join(current_parts + [import_module])
        else:
            return '.'.join(current_parts) if current_parts else None

    def analyze_file(self, file_path: Path):
        """تحليل ملف واحد"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            module_name = self.get_relative_module_name(file_path)
            local_imports, external_imports = self.parse_imports(content, module_name)

            # تخزين معلومات الملف
            self.files_info[module_name] = {
                'path': str(file_path),
                'size': len(content),
                'lines': len(content.splitlines()),
                'local_imports': list(local_imports),
                'external_imports': list(external_imports)
            }

            # إضافة الاعتماديات
            for imported_module in local_imports:
                self.dependencies[module_name].add(imported_module)
                self.reverse_dependencies[imported_module].add(module_name)

            self.external_imports[module_name] = external_imports

        except Exception as e:
            print(f"خطأ في تحليل الملف {file_path}: {e}")

    def analyze_project(self):
        """تحليل المشروع كاملاً"""
        print("🔍 البحث عن ملفات Python...")
        python_files = self.find_python_files()
        print(f"تم العثور على {len(python_files)} ملف Python")

        print("📖 تحليل الملفات...")
        for file_path in python_files:
            self.analyze_file(file_path)

        print(f"✅ تم تحليل {len(self.files_info)} ملف بنجاح")

    def generate_dependency_tree(self, module: str, visited: Set[str] = None, depth: int = 0) -> str:
        """إنشاء شجرة الاعتماديات لوحدة معينة"""
        if visited is None:
            visited = set()

        if module in visited:
            return "  " * depth + f"├── {module} (دائري)\n"

        visited.add(module)
        tree = "  " * depth + f"├── {module}\n"

        if module in self.dependencies:
            deps = sorted(self.dependencies[module])
            for i, dep in enumerate(deps):
                if i == len(deps) - 1:
                    tree += "  " * (depth + 1) + f"└── {dep}\n"
                else:
                    tree += "  " * (depth + 1) + f"├── {dep}\n"

                if dep in self.dependencies and depth < 3:  # تحديد العمق لتجنب التعقيد
                    tree += self.generate_dependency_tree(dep, visited.copy(), depth + 2)

        return tree

    def find_circular_dependencies(self) -> List[List[str]]:
        """البحث عن الاعتماديات الدائرية"""
        circles = []
        visited = set()

        def dfs(node, path, rec_stack):
            if node in rec_stack:
                # وجدنا دائرة
                circle_start = path.index(node)
                circle = path[circle_start:] + [node]
                circles.append(circle)
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.dependencies.get(node, []):
                dfs(neighbor, path, rec_stack)

            path.pop()
            rec_stack.remove(node)

        for module in self.files_info:
            if module not in visited:
                dfs(module, [], set())

        return circles

    def get_most_imported_modules(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """الحصول على أكثر الوحدات استدعاءً"""
        import_counts = {}
        for module, deps in self.reverse_dependencies.items():
            import_counts[module] = len(deps)

        return sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def get_most_importing_modules(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """الحصول على الوحدات التي تستدعي أكثر وحدات أخرى"""
        import_counts = {}
        for module, deps in self.dependencies.items():
            import_counts[module] = len(deps)

        return sorted(import_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def generate_report(self) -> str:
        """إنشاء تقرير شامل"""
        report = []
        report.append("=" * 60)
        report.append("📊 تقرير تحليل المشروع")
        report.append("=" * 60)
        report.append("")

        # إحصائيات عامة
        report.append("📈 الإحصائيات العامة:")
        report.append(f"  • عدد الملفات: {len(self.files_info)}")
        total_lines = sum(info['lines'] for info in self.files_info.values())
        report.append(f"  • إجمالي الأسطر: {total_lines:,}")
        total_size = sum(info['size'] for info in self.files_info.values())
        report.append(f"  • إجمالي الحجم: {total_size:,} حرف")
        report.append("")

        # أكثر الوحدات استدعاءً
        report.append("🔗 أكثر الوحدات استدعاءً:")
        most_imported = self.get_most_imported_modules()
        for module, count in most_imported:
            report.append(f"  • {module}: {count} استدعاء")
        report.append("")

        # الوحدات التي تستدعي أكثر وحدات
        report.append("📤 الوحدات التي تستدعي أكثر وحدات:")
        most_importing = self.get_most_importing_modules()
        for module, count in most_importing:
            report.append(f"  • {module}: يستدعي {count} وحدة")
        report.append("")

        # البحث عن الاعتماديات الدائرية
        circles = self.find_circular_dependencies()
        if circles:
            report.append("⚠️  اعتماديات دائرية تم العثور عليها:")
            for i, circle in enumerate(circles, 1):
                report.append(f"  {i}. {' → '.join(circle)}")
        else:
            report.append("✅ لا توجد اعتماديات دائرية")
        report.append("")

        # شجرة الاعتماديات للملف الرئيسي
        if "app" in self.files_info:
            report.append("🌳 شجرة اعتماديات الملف الرئيسي (app):")
            report.append(self.generate_dependency_tree("app"))

        return "\n".join(report)

    def save_detailed_analysis(self, output_file: str = "project_analysis.json"):
        """حفظ التحليل المفصل في ملف JSON"""
        analysis_data = {
            "files": self.files_info,
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "reverse_dependencies": {k: list(v) for k, v in self.reverse_dependencies.items()},
            "external_imports": {k: list(v) for k, v in self.external_imports.items()},
            "statistics": {
                "total_files": len(self.files_info),
                "total_lines": sum(info['lines'] for info in self.files_info.values()),
                "total_size": sum(info['size'] for info in self.files_info.values()),
                "circular_dependencies": self.find_circular_dependencies(),
                "most_imported": self.get_most_imported_modules(),
                "most_importing": self.get_most_importing_modules()
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=2)

        print(f"💾 تم حفظ التحليل المفصل في: {output_file}")

    def generate_graphviz_dot(self, output_file: str = "dependency_graph.dot"):
        """إنشاء ملف Graphviz لرسم الشجرة بصرياً"""
        dot_content = ["digraph ProjectDependencies {"]
        dot_content.append("  rankdir=TB;")
        dot_content.append("  node [shape=box, style=filled, fillcolor=lightblue];")
        dot_content.append("")

        # إضافة العقد
        for module in self.files_info:
            # تنسيق اسم العقدة
            clean_name = module.replace(".", "_")
            display_name = module.split(".")[-1] if "." in module else module

            # تحديد اللون بناءً على نوع الملف
            if "controller" in module:
                color = "lightcoral"
            elif "view" in module:
                color = "lightgreen"
            elif "core" in module:
                color = "lightyellow"
            elif "util" in module:
                color = "lightgray"
            else:
                color = "lightblue"

            dot_content.append(f'  {clean_name} [label="{display_name}", fillcolor={color}];')

        dot_content.append("")

        # إضافة الاتصالات
        for module, deps in self.dependencies.items():
            clean_module = module.replace(".", "_")
            for dep in deps:
                clean_dep = dep.replace(".", "_")
                dot_content.append(f"  {clean_module} -> {clean_dep};")

        dot_content.append("}")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(dot_content))

        print(f"📊 تم إنشاء ملف Graphviz: {output_file}")
        print("لرسم الشجرة، استخدم الأمر: dot -Tpng dependency_graph.dot -o dependency_graph.png")


def main():
    parser = argparse.ArgumentParser(description="تحليل اعتماديات ملفات المشروع")
    parser.add_argument("project_path", nargs="?", default=".",
                       help="مسار المشروع (افتراضي: المجلد الحالي)")
    parser.add_argument("--output", "-o", default="project_analysis",
                       help="اسم ملف الإخراج (بدون امتداد)")
    parser.add_argument("--graphviz", action="store_true",
                       help="إنشاء ملف Graphviz للرسم البصري")

    args = parser.parse_args()

    # التحقق من وجود المشروع
    if not os.path.exists(args.project_path):
        print(f"❌ المسار غير موجود: {args.project_path}")
        return

    print(f"🚀 بدء تحليل المشروع في: {os.path.abspath(args.project_path)}")
    print("-" * 50)

    # إنشاء المحلل
    analyzer = ProjectAnalyzer(args.project_path)

    # تحليل المشروع
    analyzer.analyze_project()

    # إنشاء التقرير
    report = analyzer.generate_report()
    print(report)

    # حفظ التحليل المفصل
    json_file = f"{args.output}.json"
    analyzer.save_detailed_analysis(json_file)

    # حفظ التقرير النصي
    txt_file = f"{args.output}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📄 تم حفظ التقرير في: {txt_file}")

    # إنشاء ملف Graphviz إذا طُلب
    if args.graphviz:
        dot_file = f"{args.output}.dot"
        analyzer.generate_graphviz_dot(dot_file)


if __name__ == "__main__":
    main()
