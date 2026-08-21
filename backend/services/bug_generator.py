from __future__ import annotations

import pandas as pd

from backend.services.config import KAGGLE_DIR


class BugReportGeneratorService:
    def __init__(self) -> None:
        self.issue_path = KAGGLE_DIR / "github_issues.csv"

    def load_issue_samples(self, limit: int = 50) -> list[dict]:
        try:
            df = pd.read_csv(self.issue_path, nrows=limit, encoding_errors="ignore")
            return df.fillna("").to_dict(orient="records")
        except FileNotFoundError:
            return [] # Fail gracefully if the CSV isn't downloaded yet

    def generate_reports(self, repository_name: str, defect_predictions: list[dict], test_results: dict, analysis: dict) -> list[dict]:
        issue_samples = self.load_issue_samples(limit=20)
        reports = []
        
        for prediction in defect_predictions[:25]:
            if prediction["defect_probability"] < 0.4:
                continue
                
            # 1. Look up the real file context using the row_index!
            file_index = prediction["row_index"]
            file_info = analysis["files"][file_index]
            real_file_path = file_info["path"]
            language = file_info["language"]

            severity = "critical" if prediction["defect_probability"] >= 0.8 else "high" if prediction["defect_probability"] >= 0.6 else "medium"
            template = issue_samples[file_index % max(len(issue_samples), 1)] if issue_samples else {}
            
            # 2. Inject the real data into the report
            reports.append(
                {
                    "title": f"High complexity & potential defect hotspot in `{real_file_path}`",
                    "severity": severity,
                    "steps_to_reproduce": [
                        f"Open the {language} file located at `{real_file_path}`.",
                        f"Review the {file_info['function_count']} functions for complex logic branches.",
                        "Run related automated tests and inspect recent git changes to this file.",
                        "Exercise error handling and boundary input scenarios."
                    ],
                    "suggested_fix": f"Prioritize refactoring complex branches in {real_file_path}. Add defensive tests for edge cases and validate dependency interactions.",
                    "evidence": {
                        "defect_probability": round(prediction["defect_probability"], 2),
                        "file_complexity": file_info["complexity"],
                        "test_gaps": len(test_results.get("missing_edge_cases", [])),
                        "related_issue_title": template.get("issue_title", "N/A"),
                    },
                }
            )
        return reports