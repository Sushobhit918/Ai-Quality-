from __future__ import annotations

from pathlib import Path


class TestIntelligenceService:
    def analyze(self, repo_path: Path, file_analysis: dict) -> dict:
        test_files = [file_info for file_info in file_analysis["files"] if file_info["test_file"]]
        source_files = [file_info for file_info in file_analysis["files"] if not file_info["test_file"]]
        coverage_estimate = min(100.0, round((len(test_files) / max(len(source_files), 1)) * 100, 2))

        failed_tests = []
        missing_edge_cases = []
        for test_file in test_files[:50]:
            text = (repo_path / test_file["path"]).read_text(encoding="utf-8", errors="ignore")
            if "todo" in text.lower() or "skip" in text.lower():
                failed_tests.append(
                    {
                        "file": test_file["path"],
                        "reason": "Skipped or TODO tests detected; this often hides unstable behavior.",
                    }
                )
            if "error" not in text.lower() and "exception" not in text.lower():
                missing_edge_cases.append(
                    {
                        "file": test_file["path"],
                        "gap": "Missing explicit negative-path or exception assertions.",
                    }
                )

        framework_counts = {
            "jest": sum(item["path"].endswith((".test.js", ".spec.js", ".test.ts", ".spec.ts")) for item in test_files),
            "pytest": sum(item["path"].endswith(".py") for item in test_files),
            "junit": sum(item["path"].endswith(".java") for item in test_files),
        }

        return {
            "coverage_estimate": coverage_estimate,
            "framework_counts": framework_counts,
            "test_files": test_files[:100],
            "failed_tests": failed_tests,
            "missing_edge_cases": missing_edge_cases[:25],
        }
