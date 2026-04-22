from models import Tarefa
from database import create_db, get_session
from fastapi import FastAPI, Depends
from typing import Annotated
from sqlmodel import Session

SessionDep = Annotated[Session, Depends (get_session)]
