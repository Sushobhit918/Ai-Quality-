from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.services.bug_generator import BugReportGeneratorService
from backend.services.code_parser import CodeAnalyzerService
from backend.services.gemini_service import GeminiService
from backend.services.ml_model import DefectPredictionService
from backend.services.project_store import ProjectStoreService
from backend.services.schemas import AnalyzeRequest, AskAIRequest, SemanticSearchRequest
from backend.services.semantic_search import SemanticSearchService
from backend.services.test_intelligence import TestIntelligenceService

router = APIRouter()
code_analyzer = CodeAnalyzerService()
ml_service = DefectPredictionService()
test_service = TestIntelligenceService()
bug_service = BugReportGeneratorService()
gemini_service = GeminiService()
project_store = ProjectStoreService()
semantic_search = SemanticSearchService()


def _resolve_project_path(project_path: str) -> Path:
    # 1. Check if the user passed a GitHub/Git URL instead of a local path
    if project_path.startswith("http://") or project_path.startswith("https://"):
        try:
            # Create a secure temporary directory
            temp_dir = tempfile.mkdtemp(prefix="ai_testing_app_")
            
            # Use your system's git to clone the repository into the temp folder
            subprocess.run(
                ["git", "clone","--depth", "1", project_path, temp_dir], 
                check=True, 
                capture_output=True
            )
            return Path(temp_dir)
            
        except subprocess.CalledProcessError as e:
            # If the clone fails (e.g., private repo or typo), return a helpful error
            error_msg = e.stderr.decode('utf-8') if e.stderr else "Unknown Git error"
            raise HTTPException(status_code=400, detail=f"Failed to clone repository: {error_msg}")
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Git is not installed or not in the system PATH.")

    # 2. If it's not a URL, process it as a standard local file path
    path = Path(project_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Project path not found: {project_path}")
    
    return path


@router.post("/upload-project")
async def upload_project(file: UploadFile = File(...)) -> dict:
    saved = project_store.save_upload(file.filename, await file.read())
    return {"filename": file.filename, "saved_to": str(saved)}


@router.post("/train-models")
def train_models() -> dict:
    return ml_service.train()


@router.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict:
    repo_path = _resolve_project_path(request.project_path)
    analysis = code_analyzer.analyze_repository(repo_path)
    test_results = test_service.analyze(repo_path, analysis)
    documents = [
        {"type": "code", "path": file_info["path"], "content": f"{file_info['path']} {file_info['language']} {file_info['dependencies']}"}
        for file_info in analysis["files"][:1000]
    ]
    semantic_search.build_index(documents)
    return {"analysis": analysis, "test_intelligence": test_results}


@router.post("/predict-defects")
def predict_defects(request: AnalyzeRequest) -> dict:
    repo_path = _resolve_project_path(request.project_path)
    analysis = code_analyzer.analyze_repository(repo_path)
    features = code_analyzer.features_for_prediction(analysis)
    predictions = ml_service.predict(features)
    return {"repository": str(repo_path), "predictions": predictions, "model": ml_service.model_card["best_model"]}


@router.post("/generate-bugs")
def generate_bugs(request: AnalyzeRequest) -> dict:
    repo_path = _resolve_project_path(request.project_path)
    analysis = code_analyzer.analyze_repository(repo_path)
    predictions = ml_service.predict(code_analyzer.features_for_prediction(analysis))
    test_results = test_service.analyze(repo_path, analysis)
    
    # Extract the real repo name from the URL or local path instead of the temp folder
    clean_repo_name = request.project_path.strip("/\\").split("/")[-1].split("\\")[-1].replace(".git", "")
    
    # Pass the 'analysis' dictionary to the bug generator!
    reports = bug_service.generate_reports(clean_repo_name, predictions, test_results, analysis)
    
    return {"repository": clean_repo_name, "bug_reports": reports}

@router.post("/semantic-search")
def semantic_search_endpoint(request: SemanticSearchRequest) -> dict:
    return {"results": semantic_search.search(request.query, request.top_k)}


@router.post("/ask-ai")
def ask_ai(request: AskAIRequest) -> dict:
    return gemini_service.ask(request.question, request.context)