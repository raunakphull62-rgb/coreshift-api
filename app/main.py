from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, database, storage, ai
from app.routers import developers

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

# Developer portal routes (signup, login, projects, keys)
app.include_router(developers.router, prefix="/developers", tags=["Developers"])

# Service routes (used by end developers in their apps)
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(database.router, prefix="/db", tags=["Database"])
app.include_router(storage.router, prefix="/storage", tags=["Storage"])
app.include_router(ai.router, prefix="/ai", tags=["AI"])
