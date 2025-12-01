# main.py
import json
import os
import secrets

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from passlib.hash import bcrypt
from pydantic import BaseModel, constr

# ---------- Configurações ----------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_COOKIE = "session_id"
SESSION_TTL = 60 * 60 * 24  # 1 dia

# Cliente Redis assíncrono
r = redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI()


# ---------- Schemas ----------
class RegisterIn(BaseModel):
    username: constr(strip_whitespace=True, min_length=3)
    password: constr(min_length=6)
    role: str | None = "user"


class LoginIn(BaseModel):
    username: str
    password: str


# ---------- Helpers ----------
def user_key(username: str) -> str:
    return f"user:{username}"


def session_key(session_id: str) -> str:
    return f"session:{session_id}"


# ---------- Registro (signup) ----------
@app.post("/register", status_code=201)
async def register(payload: RegisterIn):
    """
    Registra um novo usuário.
    - Verifica se o username já existe.
    - Faz hash da senha com bcrypt.
    - Armazena o usuário no Redis como JSON.
    Em produção, use um banco relacional e validações adicionais.
    """
    key = user_key(payload.username)
    exists = await r.exists(key)
    if exists:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    # Hash da senha (não armazene senhas em texto)
    hashed = bcrypt.hash(payload.password)

    user_data = {
        "id": secrets.token_hex(8),  # id simples para exemplo
        "username": payload.username,
        "password": hashed,
        "role": payload.role,
    }
    await r.set(key, json.dumps(user_data))
    return {"msg": "usuário criado", "username": payload.username}


# ---------- Login (cria sessão) ----------
@app.post("/login")
async def login(payload: LoginIn, response: Response):
    """
    Autentica usuário e cria sessão no Redis.
    Retorna cookie HttpOnly com session_id.
    """
    key = user_key(payload.username)
    raw = await r.get(key)
    if not raw:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    user = json.loads(raw)

    # Verifica senha com bcrypt
    if not bcrypt.verify(payload.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    # Cria session_id e armazena dados essenciais da sessão
    session_id = secrets.token_urlsafe(32)
    session_data = {"user_id": user["id"], "username": user["username"], "role": user["role"]}
    await r.set(session_key(session_id), json.dumps(session_data), ex=SESSION_TTL)

    # Define cookie HttpOnly; em produção use secure=True e ajuste SameSite
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        httponly=True,
        max_age=SESSION_TTL,
        samesite="lax",
        # secure=True  # habilitar em produção com HTTPS
    )
    return {"msg": "logado"}


# ---------- Dependência: recupera usuário da sessão ----------
async def get_current_user(request: Request):
    session_id: str | None = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        raise HTTPException(status_code=401, detail="Não autenticado")
    raw = await r.get(session_key(session_id))
    if not raw:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada")
    session = json.loads(raw)
    return session


# ---------- Dependência geradora para checar role ----------
def require_role(role: str):
    async def checker(user=Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(status_code=403, detail="Acesso negado")
        return user

    return checker


# ---------- Rotas protegidas ----------
@app.get("/profile")
async def profile(user=Depends(get_current_user)):
    """Retorna dados básicos do usuário logado."""
    return {"user": user}


@app.get("/admin")
async def admin_area(user=Depends(require_role("admin"))):
    """Rota acessível apenas para admins."""
    return {"msg": f"Olá {user['username']}, você é admin"}


# ---------- Logout ----------
@app.post("/logout")
async def logout(request: Request, response: Response):
    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id:
        await r.delete(session_key(session_id))
    response.delete_cookie(SESSION_COOKIE)
    return {"msg": "deslogado"}
