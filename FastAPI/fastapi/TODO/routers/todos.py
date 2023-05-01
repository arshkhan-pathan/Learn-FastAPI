from fastapi import APIRouter
from fastapi import Depends,Path,HTTPException
from models import Todos
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session 
from starlette import status
from pydantic import BaseModel,Field
from .auth import get_current_user



router=APIRouter()



# Dependency Injection

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency=Annotated[Session, Depends(get_db)]

# User dependency will make sure authoarization 😀
user_dependency=Annotated[dict,Depends(get_current_user)]

#request 
class TodoRequest(BaseModel):
    title:str=Field(min_length=3)
    description:str=Field(min_length=3,max_length=100)
    priority:int=Field(gt=0,lt=6)
    complete:bool




@router.post("/todo",status_code=status.HTTP_201_CREATED)
async def create_todo(user:user_dependency,db:db_dependency,todo_request:TodoRequest):
    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")
    
    todo_model=Todos(**todo_request.dict(),owner_id=user.get('id'))
    db.add(todo_model)
    db.commit()


@router.get('/',status_code=status.HTTP_200_OK)
async def read_all(user:user_dependency,db: db_dependency ):
    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")
    return db.query(Todos).filter(Todos.owner_id==user.get("id")).all()  

@router.get('/todo/{todo_id}',status_code=status.HTTP_200_OK)
async def read_by_id(user:user_dependency,db: db_dependency ,todo_id:int=Path(gt=0)):
    todo_model=db.query(Todos).filter(Todos.owner_id==user.get("id")).filter(Todos.id==todo_id).first()
    if todo_model is not None:
        return todo_model         
    raise HTTPException(status_code=404,detail="Todo not Found")



@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependency,
                      todo_request: TodoRequest,
                      todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401,detail="Authentication Failed")
    

    todo_model = db.query(Todos).filter(Todos.owner_id==user.get("id")).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')

    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()





@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo( user: user_dependency,db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail='Authentication Failed')

    todo_model = db.query(Todos).filter(Todos.owner_id == user.get('id')).filter(Todos.id == todo_id).first()
        
    if todo_model is None:
        raise HTTPException(status_code=404, detail='Todo not found.')
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
