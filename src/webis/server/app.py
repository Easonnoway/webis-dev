"""
Webis API Server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from webis import __version__
from webis.server.routers import ingest, query, tasks, compliance

app = FastAPI(
    title="Webis API",
    description="AI-Powered Knowledge Pipeline API",
    version=__version__,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Instrumentation
Instrumentator().instrument(app).expose(app)

# Include routers
app.include_router(ingest.router, prefix="/api/v1/ingest", tags=["Ingestion"])
app.include_router(query.router, prefix="/api/v1/query", tags=["Query"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["Compliance"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": __version__}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webis.server.app:app", host="0.0.0.0", port=8000, reload=True)
