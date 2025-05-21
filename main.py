from fastapi import FastAPI
import agent_router
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "FastAPI server is running"}


app = FastAPI()
app.include_router(agent_router, prefix="/api", tags=["Agent"])
