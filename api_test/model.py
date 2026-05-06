#pip install fastapi uvicorn sqlmodel

from sqlmodel import SQLModel, Field

class Tarefa(SQLModel,table=True):
    id:int |None = Field(default=None,primary_key=True)
    nome:str = Field(index=False)
    descricao:str = Field(index=False)
    status:bool = Field(default=False)