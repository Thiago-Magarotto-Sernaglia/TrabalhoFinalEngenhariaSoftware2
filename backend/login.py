# main.py
import json
import os
import secrets

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel

# Config
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_COOKIE = "session_id"
SESSION_TTL = 60 * 60 * 24  # 1 dia

# Redis client (async)
r = redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI()

# Simulação de "usuários" para exemplo (em produção use DB)
USERS = {
    "alice": {"password": "senha123", "role": "admin", "id": 1},
    "bob": {"password": "senha456", "role": "user", "id": 2},
}


class LoginIn(BaseModel):
    username: str
    password: str


# Cria sessão no Redis e seta cookie HttpOnly
@app.post("/login")
async def login(payload: LoginIn, response: Response):
    user = USERS.get(payload.username)
    if not user or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    session_id = secrets.token_urlsafe(32)
    session_data = {"user_id": user["id"], "username": payload.username, "role": user["role"]}

    # Armazena sessão como JSON com TTL
    await r.set(session_id, json.dumps(session_data), ex=SESSION_TTL)

    # Cookie seguro; em produção use secure=True and samesite as needed
    response.set_cookie(
        SESSION_COOKIE, session_id, httponly=True, max_age=SESSION_TTL, samesite="lax"
    )
    return {"msg": "logado"}


# Dependência que recupera sessão do Redis
async def get_current_user(request: Request):
    session_id: str | None = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    raw = await r.get(session_id)
    if not raw:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada")
    session = json.loads(raw)
    return session


# Gerador de dependência para checar role
def require_role(role: str):
    async def checker(user=Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(status_code=403, detail="Acesso negado")
        return user

    return checker


# Rota protegida para admins
@app.get("/admin")
async def admin_area(user=Depends(require_role("admin"))):
    return {"msg": f"Olá {user['username']}, você é admin"}


# Rota protegida para usuários autenticados
@app.get("/profile")
async def profile(user=Depends(get_current_user)):
    return {"user": user}


# Logout: remove sessão e expira cookie
@app.post("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id:
        await r.delete(session_id)
    response.delete_cookie(SESSION_COOKIE)
    return {"msg": "deslogado"}
