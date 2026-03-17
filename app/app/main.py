from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, database, storage, ai

app = FastAPI(
    title="CoreShift API",
    description="Free Backend-as-a-Service for everyone",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "CoreShift is running", "version": "1.0.0"}

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(database.router, prefix="/db", tags=["Database"])
app.include_router(storage.router, prefix="/storage", tags=["Storage"])
app.include_router(ai.router, prefix="/ai", tags=["AI"])
