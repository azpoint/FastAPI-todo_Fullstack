from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from typing import Annotated
from sqlalchemy.orm import Session
from app.models import Todos
from app.database import SessionLocal
from starlette import status
from pydantic import BaseModel, Field
from app.routers.auth import get_current_user
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(prefix="/todos", tags=["todos"])


# DB connection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# Pydantic Validation model
class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=300)
    priority: int = Field(gt=0, lt=6)
    complete: bool


class TodoResponse(BaseModel):
    id: int
    title: str
    description: str
    priority: int
    complete: bool
    owner_id: int

    class ConfigDict:
        orm_mode = True  # <-- This allows returning SQLAlchemy models directly as json


def redirect_to_login():
    redirect_response = RedirectResponse(
        url="/auth/login-page", status_code=status.HTTP_302_FOUND
    )
    redirect_response.delete_cookie("access_token")
    return redirect_response


### Pages Todos
templates = Jinja2Templates(directory="templates")


@router.get("/todo-page")
async def render_todo_page(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))
        if user is None:
            return redirect_to_login()

        todos = db.query(Todos).filter(Todos.owner_id == user.get("id")).all()

        return templates.TemplateResponse(
            "todo.html", {"request": request, "todos": todos, "user": user}
        )
    except:
        return redirect_to_login()


@router.get("/add-todo-page")
async def render_add_todo_page(request: Request):

    try:
        user = await get_current_user(request.cookies.get("access_token"))

        if user is None:
            return redirect_to_login()

        return templates.TemplateResponse(
            "add-todo.html", {"request": request, "user": user}
        )

    except:
        return redirect_to_login()


@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, todo_id: int, db: db_dependency):

    try:
        user = await get_current_user(request.cookies.get("access_token"))

        if user is None:
            return redirect_to_login()

        todo = db.query(Todos).filter(Todos.id == todo_id).first()

        return templates.TemplateResponse(
            "edit-todo.html", {"request": request, "todo": todo, "user": user}
        )

    except:
        return redirect_to_login()


### Enpoints Todos
# Get all todos
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    return db.query(Todos).filter(Todos.owner_id == user.get("id")).all()


# Get todo by id with path params
@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(
    user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)
):

    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    # DB request
    todo_model = (
        db.query(Todos)
        .filter(Todos.id == todo_id)
        .filter(Todos.owner_id == user.get("id"))
        .first()
    )

    if todo_model is not None:
        return todo_model

    raise HTTPException(status_code=404, detail="Todo not found")


# Create todo
@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(
    user: user_dependency, db: db_dependency, todo_request: TodoRequest
):

    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    # Validate data with Pydantic Model
    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get("id"))

    # Adding the data to the DB
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)

    return todo_model


# Update todo by ID with path params
@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    user: user_dependency,
    db: db_dependency,
    todo_request: TodoRequest,
    todo_id: int = Path(gt=0),
):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    # Fetch todo by ID from DB first before update.
    todo_model = (
        db.query(Todos)
        .filter(Todos.id == todo_id)
        .filter(Todos.owner_id == user.get("id"))
        .first()
    )

    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    # Update data from DB with the request body of the endpoint.
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    # Add and commit changes to the DB
    db.add(todo_model)
    db.commit()


# Delete todo by ID with path params
@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)
):

    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    # Fetch DB data before delete
    todo_model = (
        db.query(Todos)
        .filter(Todos.id == todo_id)
        .filter(Todos.owner_id == user.get("id"))
        .first()
    )

    if todo_model is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    # Actual delete process
    db.query(Todos).filter(Todos.id == todo_id).filter(
        Todos.owner_id == user.get("id")
    ).delete()

    db.commit()
