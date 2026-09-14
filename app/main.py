from fastapi import FastAPI

app = FastAPI(title="PayAI")


@app.get("/")
def root():
    return {
        "message": "Welcome to PayAI",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }