const API_BASE = "http://localhost:8000";

async function post(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  analyze: (projectPath) => post("/analyze", { project_path: projectPath }),
  predictDefects: (projectPath) => post("/predict-defects", { project_path: projectPath }),
  generateBugs: (projectPath) => post("/generate-bugs", { project_path: projectPath }),
  askAI: (question, context) => post("/ask-ai", { question, context }),
  trainModels: () => post("/train-models", {})
};
