from fastapi import APIRouter,Depends,HTTPException
from database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from passlib.context import CryptContext
from models import Users
from typing import Annotated
from sqlalchemy.orm import Session 
from starlette import status
from pydantic import BaseModel
from jose import jwt,JWTError
from datetime import timedelta,datetime


router=APIRouter()

bcrypt_context=CryptContext(schemes=['bcrypt'], deprecated="auto")
oauth2_bearer= OAuth2PasswordBearer(tokenUrl='token')



SECRET_KEY="691b0d2bf95bea89dce1ed809b0cf49cb9deef82646ac8a691f9a126921b6eb9"
ALGORITTHM="HS256"

# Dependency Injection

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency=Annotated[Session, Depends(get_db)]


class CreateUserRequest(BaseModel):
    username:str
    email:str
    first_name:str
    last_name:str
    password:str
    role:str 

class Token(BaseModel):
    access_token:str    
    token_type:str

# @router.get('/getUsers')
# def getUsers():
#     pass

'''
OAuth2PasswordRequestForm is a class dependency that declares a form body with:
The username.
The password.
An optional scope field as a big string, composed of strings separated by spaces.
An optional grant_type.
''' 
def authenticate_user(username:str,password:str,db):
    user=db.query(Users).filter(Users.username==username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
    return user

def create_access_token(username:str,user_id:int,expires_delta:timedelta):
    encode={'sub':username,'id':user_id}
    expires=datetime.utcnow()+expires_delta
    encode.update({'exp':expires})
    return jwt.encode(encode,SECRET_KEY,algorithm=ALGORITTHM)

async def get_current_user(token:Annotated[str,Depends(oauth2_bearer)]):
    try:
        payload= jwt.decode(token,SECRET_KEY,algorithms=[ALGORITTHM])
        username:str=payload.get("sub")
        user_id:int=payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate user")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate user.")




@router.post("/token",response_model=Token)
async def loging_for_access_token(db:db_dependency,form_data:Annotated[OAuth2PasswordRequestForm,Depends()]):
    user=authenticate_user(form_data.username,form_data.password,db)
    if not user:        
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate user")
    token=create_access_token(user.username,user.id,timedelta(minutes=20))
    return {'access_token':token,"token_type":"bearer"}



@router.post("/auth/",status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency,create_user_request:CreateUserRequest):
    create_user_model= Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True
    )
    db.add(create_user_model)
    db.commit()
    return create_user_model
