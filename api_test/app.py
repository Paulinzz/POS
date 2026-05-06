from model import Tarefa
from database import create_db, get_session
from fastapi import FastAPI, Depends
from typing import Annotated
from sqlmodel import Session
from contextlib import asynccontextmanager
from sqlmodel import select

SessionDep = Annotated[Session,Depends(get_session)]

@asynccontextmanager
async def lifespan(app:FastAPI):
    create_db()
    yield

app = FastAPI(lifespan=lifespan)


@app.get('/tarefas')
def listar(session:SessionDep) -> list [Tarefa]:
    lista:list[Tarefa] = []
    lista = session.exec(select(Tarefa)).all
    return lista

@app.post('/tarefas')
def cadastrar(tarefa:Tarefa, session:SessionDep) -> Tarefa:
    session.add(tarefa)
    session.commit()
    session.refresh(tarefa)
    return tarefa

@app.delete('/tarefas/{id}')
def deletar(id:int, session:SessionDep):
    tarefa:Tarefa = session.get(Tarefa,id)
    if tarefa:
        session.delete(tarefa)
        session.commit()

@app.put('tarefas/{id}')
def atualizar(id:int,tarefa:Tarefa, session:SessionDep) -> Tarefa:
    tarefaUpdate:Tarefa = session.get(Tarefa, id)
    tarefaUpdate.descricao = tarefa.descricao
    tarefaUpdate.nome = tarefa.nome
    tarefaUpdate.status = tarefa.status
    session.add(tarefaUpdate)
    session.commit()
    session.refresh(tarefaUpdate)
    return tarefaUpdate 