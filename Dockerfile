# FireSight full program: FastAPI backend + SQLite database + search index + dashboard.
# Lightweight image for free hosting (Render free tier). The AI assistant uses a hosted open model
# when FIRESIGHT_LLM_API_KEY is set (Groq free tier by default); otherwise it answers with cited extracts.
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PORT=10000 FIRESIGHT_LLM_LOCAL=off
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY data/ data/
COPY frontend/dist/ frontend/dist/
EXPOSE 10000
CMD ["sh", "-c", "python -m uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
