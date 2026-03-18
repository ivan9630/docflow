"""API Authentification — DocuFlow v2"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.database import get_db
from app.models.models import User
from app.services.auth_service import (
    verify_password, hash_password, create_token, get_current_user,
)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    nom_complet: str
    role: str = "gestionnaire"


@router.post("/login")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(User).where(User.username == req.username))
    user = r.scalar_one_or_none()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")
    token = create_token({"sub": str(user.id), "role": user.role, "username": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "nom_complet": user.nom_complet,
            "role": user.role,
        },
    }


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {
        "id": str(user.id),
        "username": user.username,
        "nom_complet": user.nom_complet,
        "role": user.role,
    }


@router.post("/register")
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Seul un admin peut créer des comptes")
    if req.role not in ("admin", "gestionnaire", "conformite"):
        raise HTTPException(status_code=400, detail="Rôle invalide (admin, gestionnaire, conformite)")
    existing = await db.execute(select(User).where(User.username == req.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username déjà pris")
    user = User(
        username=req.username,
        hashed_password=hash_password(req.password),
        nom_complet=req.nom_complet,
        role=req.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": f"Utilisateur {req.username} créé", "role": req.role}
