from fastapi import APIRouter ,Depends , HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel,Field

from db.database import get_db
from db.models import User
from auth.security import hash_password, verify_password, create_access_token
from auth.dependencies import validate_password_strength

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)

class TokenResponse(BaseModel):
    access_token:str
    token_type:str ="bearer"    


@router.post("/register",status_code=201)
def register(request:RegisterRequest,db:Session = Depends(get_db)):
    validate_password_strength(request.password)

    existing = db.query(User).filter(User.username ==request.username).first()
    if existing:
        raise HTTPException(status_code=400,detail="Username already exists")

    user = User(
        username= request.username,
        hashed_password = hash_password(request.password)
    ) 

    db.add(user)
    db.commit()
    return {"status":"registered","username":user.username}


@router.post("/login",response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm= Depends(),db:Session = Depends(get_db)):

    user =  db.query(User).filter(User.username==form_data.username).first()

    if not user or not verify_password(form_data.password,user.hashed_password):
        raise HTTPException(status_code=401,detail="Invalid username or passowrd.")

    access_token = create_access_token(data={"sub":user.username})     
    return TokenResponse(access_token=access_token)