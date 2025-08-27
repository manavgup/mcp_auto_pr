#!/usr/bin/env python3
"""LibCST-based code analyzer for MCP Auto PR refactoring insights.

This tool analyzes the codebase to identify:
- Duplicate code patterns
- Common imports and dependencies
- Class and function similarities
- Configuration patterns
- Refactoring opportunities

Usage:
    python scripts/code_analyzer.py [--output-format json|markdown] [--detailed]
"""

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import libcst as cst
    # from libcst import matchers as m  # TODO: Add matchers functionality if needed
except ImportError:
    print("Error: libcst not installed. Install with: pip install libcst")
    sys.exit(1)


@dataclass
class DuplicatePattern:
    """Represents a duplicate code pattern."""

    pattern_type: str
    pattern_hash: str
    files: list[str]
    line_ranges: list[tuple[int, int]]
    content_sample: str
    similarity_score: float


@dataclass
class ImportAnalysis:
    """Import usage analysis."""

    module: str
    imported_items: list[str]
    files: list[str]
    usage_count: int
    is_standard_library: bool
    is_third_party: bool


@dataclass
class FunctionSignature:
    """Function signature for similarity analysis."""

    name: str
    file: str
    line_number: int
    parameters: list[str]
    return_annotation: str | None
    decorators: list[str]
    body_hash: str


@dataclass
class ClassSignature:
    """Class signature for similarity analysis."""

    name: str
    file: str
    line_number: int
    base_classes: list[str]
    methods: list[str]
    decorators: list[str]
    body_hash: str


@dataclass
class AnalysisResult:
    """Complete analysis result."""

    duplicate_patterns: list[DuplicatePattern]
    import_analysis: list[ImportAnalysis]
    function_signatures: list[FunctionSignature]
    class_signatures: list[ClassSignature]
    summary: dict[str, Any]


class CodeAnalyzer(cst.CSTVisitor):
    """LibCST visitor for code analysis."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports: list[tuple[str, list[str]]] = []
        self.functions: list[FunctionSignature] = []
        self.classes: list[ClassSignature] = []
        self.current_line = 1
        self.source_lines: list[str] = []

    def visit_Import(self, node: cst.Import) -> None:
        """Visit import statements."""
        for name in node.names:
            if isinstance(name, cst.ImportAlias):
                module = self._get_dotted_name(name.name)
                self.imports.append((module, []))

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Visit from...import statements."""
        if node.module:
            module = self._get_dotted_name(node.module)
            if isinstance(node.names, cst.ImportStar):
                imported_items = ["*"]
            elif isinstance(node.names, list):
                imported_items = []
                for name in node.names:
                    if isinstance(name, cst.ImportAlias):
                        imported_items.append(self._get_name(name.name))
            else:
                imported_items = []
            self.imports.append((module, imported_items))

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        """Visit function definitions."""
        name = node.name.value

        # Extract parameters
        parameters = []
        if node.params:
            for param in node.params.params:
                parameters.append(param.name.value)

        # Extract return annotation
        return_annotation = None
        if node.returns:
            return_annotation = self._get_annotation_string(node.returns.annotation)

        # Extract decorators
        decorators = []
        for decorator in node.decorators:
            decorators.append(self._get_decorator_name(decorator.decorator))

        # Create body hash
        body_hash = self._hash_node(node.body)

        self.functions.append(
            FunctionSignature(
                name=name,
                file=self.file_path,
                line_number=self.current_line,
                parameters=parameters,
                return_annotation=return_annotation,
                decorators=decorators,
                body_hash=body_hash,
            )
        )

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        """Visit class definitions."""
        name = node.name.value

        # Extract base classes
        base_classes = []
        if node.bases:
            for base in node.bases:
                if isinstance(base, cst.Arg):
                    base_classes.append(self._get_name(base.value))

        # Extract methods
        methods = []
        for item in node.body.body:
            if isinstance(item, cst.SimpleStatementLine):
                continue
            elif isinstance(item, cst.FunctionDef):
                methods.append(item.name.value)

        # Extract decorators
        decorators = []
        for decorator in node.decorators:
            decorators.append(self._get_decorator_name(decorator.decorator))

        # Create body hash
        body_hash = self._hash_node(node.body)

        self.classes.append(
            ClassSignature(
                name=name,
                file=self.file_path,
                line_number=self.current_line,
                base_classes=base_classes,
                methods=methods,
                decorators=decorators,
                body_hash=body_hash,
            )
        )

    def _get_dotted_name(self, node: cst.CSTNode) -> str:
        """Extract dotted name from AST node."""
        if isinstance(node, cst.Name):
            return node.value
        elif isinstance(node, cst.Attribute):
            return f"{self._get_dotted_name(node.value)}.{node.attr.value}"
        return "unknown"

    def _get_name(self, node: cst.CSTNode) -> str:
        """Extract simple name from AST node."""
        if isinstance(node, cst.Name):
            return node.value
        return "unknown"

    def _get_annotation_string(self, node: cst.CSTNode) -> str:
        """Convert annotation node to string."""
        if isinstance(node, cst.Name):
            return node.value
        elif isinstance(node, cst.Attribute):
            return self._get_dotted_name(node)
        return "unknown"

    def _get_decorator_name(self, node: cst.CSTNode) -> str:
        """Extract decorator name."""
        if isinstance(node, cst.Name):
            return node.value
        elif isinstance(node, cst.Attribute):
            return self._get_dotted_name(node)
        elif isinstance(node, cst.Call):
            return self._get_name(node.func)
        return "unknown"

    def _hash_node(self, node: cst.CSTNode) -> str:
        """Create hash of node content."""
        try:
            content = cst.Module([]).code_for_node(node)
            return hashlib.md5(content.encode()).hexdigest()[:12]
        except Exception:
            # Fallback to string representation
            return hashlib.md5(str(node).encode()).hexdigest()[:12]


class RefactoringAnalyzer:
    """Main analyzer orchestrating the analysis."""

    def __init__(self, src_dir: Path):
        self.src_dir = src_dir
        self.all_imports: list[tuple[str, str, list[str]]] = []  # (file, module, items)
        self.all_functions: list[FunctionSignature] = []
        self.all_classes: list[ClassSignature] = []

    def analyze(self) -> AnalysisResult:
        """Run complete analysis."""
        print(f"🔍 Analyzing code in {self.src_dir}")

        # Find all Python files
        python_files = list(self.src_dir.rglob("*.py"))
        print(f"📁 Found {len(python_files)} Python files")

        # Analyze each file
        for file_path in python_files:
            if self._should_skip_file(file_path):
                continue

            try:
                self._analyze_file(file_path)
            except Exception as e:
                print(f"⚠️  Warning: Failed to analyze {file_path}: {e}")

        # Generate insights
        duplicate_patterns = self._find_duplicate_patterns()
        import_analysis = self._analyze_imports()
        summary = self._generate_summary()

        return AnalysisResult(
            duplicate_patterns=duplicate_patterns,
            import_analysis=import_analysis,
            function_signatures=self.all_functions,
            class_signatures=self.all_classes,
            summary=summary,
        )

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__",
            ".pyc",
            "test_",
            "tests/",
            ".git/",
            "build/",
            "dist/",
            ".tox/",
            ".venv/",
            "venv/",
        ]

        path_str = str(file_path)
        return any(pattern in path_str for pattern in skip_patterns)

    def _analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            # Parse with LibCST
            tree = cst.parse_module(source)

            # Create analyzer visitor
            analyzer = CodeAnalyzer(str(file_path.relative_to(self.src_dir)))
            analyzer.source_lines = source.splitlines()

            # Visit the tree
            tree.visit(analyzer)

            # Collect results
            for module, items in analyzer.imports:
                self.all_imports.append((analyzer.file_path, module, items))

            self.all_functions.extend(analyzer.functions)
            self.all_classes.extend(analyzer.classes)

        except Exception as e:
            print(f"❌ Error analyzing {file_path}: {e}")

    def _find_duplicate_patterns(self) -> list[DuplicatePattern]:
        """Find duplicate code patterns."""
        patterns = []

        # Find duplicate functions by body hash
        function_hashes = defaultdict(list)
        for func in self.all_functions:
            function_hashes[func.body_hash].append(func)

        for hash_key, funcs in function_hashes.items():
            if len(funcs) > 1:
                # Check if functions have similar signatures too
                names = [f.name for f in funcs]
                if len(set(names)) == 1:  # Same function name
                    patterns.append(
                        DuplicatePattern(
                            pattern_type="identical_function",
                            pattern_hash=hash_key,
                            files=[f.file for f in funcs],
                            line_ranges=[(f.line_number, f.line_number + 10) for f in funcs],
                            content_sample=f"Function: {funcs[0].name}({', '.join(funcs[0].parameters)})",
                            similarity_score=1.0,
                        )
                    )

        # Find duplicate classes by body hash
        class_hashes = defaultdict(list)
        for cls in self.all_classes:
            class_hashes[cls.body_hash].append(cls)

        for hash_key, classes in class_hashes.items():
            if len(classes) > 1:
                patterns.append(
                    DuplicatePattern(
                        pattern_type="identical_class",
                        pattern_hash=hash_key,
                        files=[c.file for c in classes],
                        line_ranges=[(c.line_number, c.line_number + 20) for c in classes],
                        content_sample=f"Class: {classes[0].name}",
                        similarity_score=1.0,
                    )
                )

        # Find similar function signatures
        signature_groups = defaultdict(list)
        for func in self.all_functions:
            # Group by name and parameter count
            sig_key = (func.name, len(func.parameters))
            signature_groups[sig_key].append(func)

        for (name, param_count), funcs in signature_groups.items():
            if len(funcs) > 1 and len({f.file for f in funcs}) > 1:
                # Functions with same name/signature in different files
                patterns.append(
                    DuplicatePattern(
                        pattern_type="similar_function_signature",
                        pattern_hash=f"{name}_{param_count}",
                        files=[f.file for f in funcs],
                        line_ranges=[(f.line_number, f.line_number + 5) for f in funcs],
                        content_sample=f"Function: {name}({param_count} params)",
                        similarity_score=0.8,
                    )
                )

        return patterns

    def _analyze_imports(self) -> list[ImportAnalysis]:
        """Analyze import patterns."""
        import_counter = defaultdict(lambda: defaultdict(list))

        # Group imports by module
        for file_path, module, items in self.all_imports:
            import_counter[module]["files"].append(file_path)
            import_counter[module]["items"].extend(items)

        analysis = []
        for module, data in import_counter.items():
            files = list(set(data["files"]))
            items = list(set(data["items"]))

            # Determine library type
            is_standard = self._is_standard_library(module)
            is_third_party = not is_standard and not self._is_local_module(module)

            analysis.append(
                ImportAnalysis(
                    module=module,
                    imported_items=items,
                    files=files,
                    usage_count=len(files),
                    is_standard_library=is_standard,
                    is_third_party=is_third_party,
                )
            )

        # Sort by usage count
        analysis.sort(key=lambda x: x.usage_count, reverse=True)
        return analysis

    def _is_standard_library(self, module: str) -> bool:
        """Check if module is from standard library."""
        stdlib_modules = {
            "os",
            "sys",
            "json",
            "logging",
            "argparse",
            "asyncio",
            "traceback",
            "pathlib",
            "typing",
            "dataclasses",
            "collections",
            "itertools",
            "functools",
            "contextlib",
            "hashlib",
            "uuid",
            "datetime",
            "time",
            "re",
            "math",
            "random",
            "string",
            "io",
            "shutil",
            "subprocess",
        }
        return module.split(".")[0] in stdlib_modules

    def _is_local_module(self, module: str) -> bool:
        """Check if module is local to the project."""
        local_prefixes = ["shared", "mcp_local_repo_analyzer", "mcp_pr_recommender"]
        return any(module.startswith(prefix) for prefix in local_prefixes)

    def _generate_summary(self) -> dict[str, Any]:
        """Generate analysis summary."""
        total_files = len({f.file for f in self.all_functions + self.all_classes})

        # Count duplicates
        duplicate_functions = len(
            [p for p in self._find_duplicate_patterns() if p.pattern_type == "identical_function"]
        )
        duplicate_classes = len([p for p in self._find_duplicate_patterns() if p.pattern_type == "identical_class"])

        # Import statistics
        import_stats = self._analyze_imports()
        most_common_imports = import_stats[:10]

        # Function statistics
        function_names = [f.name for f in self.all_functions]
        common_function_names = Counter(function_names).most_common(10)

        return {
            "total_files_analyzed": total_files,
            "total_functions": len(self.all_functions),
            "total_classes": len(self.all_classes),
            "total_imports": len(self.all_imports),
            "duplicate_functions": duplicate_functions,
            "duplicate_classes": duplicate_classes,
            "most_common_imports": [
                {"module": imp.module, "usage_count": imp.usage_count} for imp in most_common_imports
            ],
            "common_function_names": [{"name": name, "count": count} for name, count in common_function_names],
            "refactoring_opportunities": self._identify_refactoring_opportunities(),
        }

    def _identify_refactoring_opportunities(self) -> list[dict[str, Any]]:
        """Identify specific refactoring opportunities."""
        opportunities = []

        # Duplicate imports that could be consolidated
        imports = self._analyze_imports()
        high_usage_imports = [imp for imp in imports if imp.usage_count >= 3]

        if high_usage_imports:
            opportunities.append(
                {
                    "type": "consolidate_imports",
                    "description": f"Consider consolidating {len(high_usage_imports)} commonly used imports",
                    "impact": "medium",
                    "files_affected": sum(len(imp.files) for imp in high_usage_imports[:5]),
                }
            )

        # Functions with identical implementations
        duplicate_patterns = self._find_duplicate_patterns()
        identical_functions = [p for p in duplicate_patterns if p.pattern_type == "identical_function"]

        if identical_functions:
            opportunities.append(
                {
                    "type": "extract_common_functions",
                    "description": f"Extract {len(identical_functions)} duplicate functions to shared utilities",
                    "impact": "high",
                    "files_affected": sum(len(p.files) for p in identical_functions),
                }
            )

        # Classes with similar structure
        identical_classes = [p for p in duplicate_patterns if p.pattern_type == "identical_class"]

        if identical_classes:
            opportunities.append(
                {
                    "type": "create_base_classes",
                    "description": f"Create base classes for {len(identical_classes)} duplicate class patterns",
                    "impact": "high",
                    "files_affected": sum(len(p.files) for p in identical_classes),
                }
            )

        # Configuration patterns
        config_functions = [f for f in self.all_functions if "config" in f.name.lower() or "setting" in f.name.lower()]
        if len(config_functions) > 3:
            opportunities.append(
                {
                    "type": "unified_configuration",
                    "description": f"Unify {len(config_functions)} configuration-related functions",
                    "impact": "medium",
                    "files_affected": len({f.file for f in config_functions}),
                }
            )

        return opportunities


def format_markdown_report(result: AnalysisResult) -> str:
    """Format analysis result as markdown report."""
    report = ["# MCP Auto PR Code Analysis Report\n"]

    # Summary
    report.append("## 📊 Summary\n")
    summary = result.summary
    report.append(f"- **Files Analyzed**: {summary['total_files_analyzed']}")
    report.append(f"- **Functions Found**: {summary['total_functions']}")
    report.append(f"- **Classes Found**: {summary['total_classes']}")
    report.append(f"- **Import Statements**: {summary['total_imports']}")
    report.append(f"- **Duplicate Functions**: {summary['duplicate_functions']}")
    report.append(f"- **Duplicate Classes**: {summary['duplicate_classes']}\n")

    # Refactoring Opportunities
    report.append("## 🔧 Refactoring Opportunities\n")
    for opp in summary.get("refactoring_opportunities", []):
        impact_emoji = {"high": "🚨", "medium": "🔶", "low": "🔹"}.get(opp["impact"], "•")
        report.append(f"{impact_emoji} **{opp['type'].replace('_', ' ').title()}**")
        report.append(f"  - {opp['description']}")
        report.append(f"  - Files affected: {opp['files_affected']}\n")

    # Duplicate Patterns
    if result.duplicate_patterns:
        report.append("## 🔄 Duplicate Code Patterns\n")
        for pattern in result.duplicate_patterns:
            report.append(f"### {pattern.pattern_type.replace('_', ' ').title()}")
            report.append(f"- **Files**: {', '.join(pattern.files)}")
            report.append(f"- **Pattern**: {pattern.content_sample}")
            report.append(f"- **Similarity**: {pattern.similarity_score:.1%}\n")

    # Import Analysis
    report.append("## 📦 Import Analysis\n")
    report.append("### Most Common Imports\n")
    for imp in result.summary.get("most_common_imports", [])[:10]:
        report.append(f"- `{imp['module']}` (used in {imp['usage_count']} files)")

    # Common Function Names
    report.append("\n### Common Function Names\n")
    for func in result.summary.get("common_function_names", [])[:10]:
        report.append(f"- `{func['name']}` (appears {func['count']} times)")

    report.append("\n---\n*Report generated by LibCST Code Analyzer*")

    return "\n".join(report)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Analyze MCP Auto PR codebase for refactoring opportunities")
    parser.add_argument("--src-dir", type=Path, default=Path("src"), help="Source directory to analyze (default: src)")
    parser.add_argument("--output", type=Path, help="Output file path (default: stdout)")
    parser.add_argument(
        "--format", choices=["json", "markdown"], default="markdown", help="Output format (default: markdown)"
    )
    parser.add_argument("--detailed", action="store_true", help="Include detailed function and class signatures")

    args = parser.parse_args()

    if not args.src_dir.exists():
        print(f"❌ Source directory {args.src_dir} not found")
        sys.exit(1)

    # Run analysis
    analyzer = RefactoringAnalyzer(args.src_dir)
    result = analyzer.analyze()

    # Format output
    if args.format == "json":
        output = json.dumps(asdict(result), indent=2, default=str)
    else:
        output = format_markdown_report(result)

    # Write output
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"✅ Analysis complete. Report saved to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
