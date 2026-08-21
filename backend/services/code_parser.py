from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
}


@dataclass
class FileAnalysis:
    path: str
    language: str
    loc: int
    complexity: int
    function_count: int
    dependency_count: int
    dependencies: list[str]
    test_file: bool


class CodeAnalyzerService:
    def analyze_repository(self, repo_path: Path) -> dict:
        files = list(self._source_files(repo_path))
        analyses = [self._analyze_file(path, repo_path) for path in files]
        return {
            "repository": str(repo_path),
            "file_count": len(analyses),
            "languages": self._language_breakdown(analyses),
            "summary": {
                "total_loc": sum(item.loc for item in analyses),
                "total_functions": sum(item.function_count for item in analyses),
                "avg_complexity": round(sum(item.complexity for item in analyses) / max(len(analyses), 1), 2),
                "test_file_count": sum(1 for item in analyses if item.test_file),
            },
            "files": [item.__dict__ for item in analyses],
        }

    def features_for_prediction(self, analysis: dict) -> list[dict]:
        return [
            {
                "loc": file_info["loc"],
                "v_g": file_info["complexity"],
                "branchcount": file_info["complexity"],
                "locode": max(file_info["loc"] - 2, 0),
                "uniq_op": file_info["dependency_count"],
                "total_op": file_info["function_count"] + file_info["dependency_count"],
                "total_opnd": file_info["loc"],
            }
            for file_info in analysis["files"]
        ]

    def _source_files(self, repo_path: Path) -> Iterable[Path]:
        for path in repo_path.rglob("*"):
            if path.suffix.lower() in SUPPORTED_EXTENSIONS and path.is_file():
                yield path

    def _language_breakdown(self, analyses: list[FileAnalysis]) -> dict[str, int]:
        breakdown: dict[str, int] = {}
        for item in analyses:
            breakdown[item.language] = breakdown.get(item.language, 0) + 1
        return breakdown

    def _analyze_file(self, file_path: Path, root: Path) -> FileAnalysis:
        language = SUPPORTED_EXTENSIONS[file_path.suffix.lower()]
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        loc = sum(1 for line in text.splitlines() if line.strip())
        test_file = self._is_test_file(file_path)

        if language == "python":
            complexity, function_count, dependencies = self._analyze_python(text)
        elif language in {"javascript", "typescript"}:
            complexity, function_count, dependencies = self._analyze_javascript_family(text)
        else:
            complexity, function_count, dependencies = self._analyze_java(text)

        return FileAnalysis(
            path=str(file_path.relative_to(root)),
            language=language,
            loc=loc,
            complexity=complexity,
            function_count=function_count,
            dependency_count=len(dependencies),
            dependencies=dependencies,
            test_file=test_file,
        )

    def _analyze_python(self, text: str) -> tuple[int, int, list[str]]:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return 1, 0, []
        function_count = sum(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) for node in ast.walk(tree))
        complexity = 1 + sum(isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.BoolOp)) for node in ast.walk(tree))
        dependencies = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                dependencies.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                dependencies.append(node.module)
        return complexity, function_count, sorted(set(dependencies))

    def _analyze_javascript_family(self, text: str) -> tuple[int, int, list[str]]:
        dependencies = re.findall(r"(?:import .* from ['\"]([^'\"]+)['\"]|require\(['\"]([^'\"]+)['\"]\))", text)
        flattened_dependencies = sorted({item for pair in dependencies for item in pair if item})
        function_count = len(re.findall(r"\bfunction\b|=>", text))
        complexity = 1 + len(re.findall(r"\bif\b|\bfor\b|\bwhile\b|\bcase\b|\bcatch\b|\?\s*", text))
        return complexity, function_count, flattened_dependencies

    def _analyze_java(self, text: str) -> tuple[int, int, list[str]]:
        dependencies = sorted(set(re.findall(r"import\s+([\w\.]+);", text)))
        function_count = len(re.findall(r"(public|private|protected)\s+[\w<>\[\]]+\s+\w+\s*\(", text))
        complexity = 1 + len(re.findall(r"\bif\b|\bfor\b|\bwhile\b|\bcase\b|\bcatch\b|\?", text))
        return complexity, function_count, dependencies

    def _is_test_file(self, path: Path) -> bool:
        name = path.name.lower()
        return any(marker in str(path).lower() for marker in ("test", "tests", "spec")) or name.endswith(
            (".test.js", ".spec.js", ".test.ts", ".spec.ts")
        )