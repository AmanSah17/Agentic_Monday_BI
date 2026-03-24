from fastapi import FastAPI
import uvicorn
from founder_bi_agent.backend.api.v1.endpoints import user, chat

app = FastAPI()
app.include_router(user.router, prefix="/user")
app.include_router(chat.router, prefix="/chat")

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8015)
