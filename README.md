# AI-Powered Software Quality Platform

An end-to-end software quality platform that combines:

- Multi-language code analysis
- ML-based defect prediction
- Test intelligence
- Bug report generation
- Semantic search
- Gemini 2.5 Flash developer assistant
- React dashboard

## Project Structure

```text
backend/
  app.py
  routes/
  services/
frontend/
  src/
ml/
  preprocess.py
  train_model.py
data/
  raw/
  processed/
models/
Dataset/
```

## Step 1: ML Pipeline + Dataset Preprocessing

Implemented in:

- `ml/preprocess.py`
- `ml/train_model.py`
- `backend/services/ml_model.py`

Highlights:

- Loads `cm1.csv`, `jm1.csv`, `SoftwareDefectDataset.csv`, and all Kaggle `.arff` datasets
- Replaces noisy missing values such as `?` with `NaN`
- Uses feature union across datasets rather than feature intersection
- Converts mixed target labels to a unified binary defect target
- Applies median imputation and `SMOTE`
- Trains Random Forest, SVM, Logistic Regression, and ANN
- Selects the best model by defect recall first, then F1 score

## Step 2: Backend APIs

Run the API:

```bash
uvicorn backend.app:app --reload
```

Core endpoints:

- `POST /train-models`
- `POST /analyze`
- `POST /predict-defects`
- `POST /generate-bugs`
- `POST /semantic-search`
- `POST /ask-ai`

Example request:

```json
{
  "project_path": "Dataset/express"
}
```

## Step 3: Gemini Integration

Create `.env` values:

```env
GEMINI_API_KEY=your_key
GEMINI_MODEL=gemini-2.5-flash
```

The assistant endpoint uses repository analysis, predictions, bugs, and search context to answer:

- code explanation
- fix suggestions
- refactoring advice
- test generation ideas
- quality triage

## Step 4: Frontend Dashboard

Frontend stack:

- React
- Vite
- Tailwind CSS

Run:

```bash
cd frontend
npm install
npm run dev
```

## Setup

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m ml.train_model
uvicorn backend.app:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Sample Run

1. Train the models with `python -m ml.train_model`
2. Start FastAPI with `uvicorn backend.app:app --reload`
3. Open the React dashboard
4. Enter a repository path such as `Dataset/express`
5. Review defect predictions, test gaps, bug reports, and AI responses

## Notes

- The semantic search service currently uses a local FAISS index with lightweight hashed embeddings so the system runs without an external embedding dependency.
- The code analyzer uses AST for Python and lightweight structural parsing for JavaScript/TypeScript and Java.
- Gemini calls require network access and a valid API key.
