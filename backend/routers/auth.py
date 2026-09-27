import hashlib
import hmac
import os
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

OPERATOR_KEY = os.environ.get("OPERATOR_KEY", "atanu-telemetry-2026")
OPERATOR_NAME = os.environ.get("OPERATOR_NAME", "Atanu")
SECRET_SALT = os.environ.get("AUTH_SECRET", "streampulse-salt-987214")

def generate_operator_token(key: str) -> str:
    return hmac.new(
        SECRET_SALT.encode(),
        f"operator:{key}".encode(),
        hashlib.sha256
    ).hexdigest()

EXPECTED_TOKEN = generate_operator_token(OPERATOR_KEY)

class LoginRequest(BaseModel):
    key: str

class OperatorProfile(BaseModel):
    name: str
    role: str
    authenticated: bool = True

class LoginResponse(BaseModel):
    token: str
    operator: OperatorProfile

async def verify_operator(authorization: Optional[str] = Header(None)) -> OperatorProfile:
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Restricted access: Operator Authorization header required."
        )
    
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
    else:
        token = authorization

    # Check against expected token or direct key
    if token == EXPECTED_TOKEN or token == OPERATOR_KEY:
        return OperatorProfile(name=OPERATOR_NAME, role="Pipeline Owner")
    
    raise HTTPException(
        status_code=401,
        detail="Invalid operator credentials. Access denied."
    )

@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    if req.key.strip() != OPERATOR_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid passkey. Access restricted to authorized pipeline operator."
        )
    return LoginResponse(
        token=EXPECTED_TOKEN,
        operator=OperatorProfile(name=OPERATOR_NAME, role="Pipeline Owner")
    )

@router.get("/me", response_model=OperatorProfile)
async def get_me(operator: OperatorProfile = Depends(verify_operator)):
    return operator

@router.post("/logout")
async def logout():
    return {"status": "ok", "message": "Operator signed out."}
