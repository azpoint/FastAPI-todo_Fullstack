from fastapi import FastAPI, Request
from app.models import Base
from app.database import engine
from app.routers import auth, todos, admin, users
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


app = FastAPI()

Base.metadata.create_all(bind=engine)

# Set html template generator
templates = Jinja2Templates(directory="templates")

# Set static files server
app.mount("/static", StaticFiles(directory="static"), name="static")


#
@app.get("/")
def test(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/healthy")
def health_check():
    return {"status": "Healthy"}


app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)
