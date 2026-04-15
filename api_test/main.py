from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import httpx
import re
from typing import Optional

from models import CPFConsultaResponse
from services import TransparenciaService

app = FastAPI(
    title="API Transparência CPF",
    description="Consulta informações de cidadãos no Portal da Transparência do Governo Federal",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def validar_cpf(cpf: str) -> str:
    """Remove formatação e valida estrutura básica do CPF."""
    cpf_limpo = re.sub(r"\D", "", cpf)
    if len(cpf_limpo) != 11:
        raise HTTPException(
            status_code=422,
            detail="CPF inválido. Informe 11 dígitos (com ou sem formatação).",
        )
    return cpf_limpo


@app.get("/", tags=["Status"])
async def root():
    return {
        "status": "online",
        "mensagem": "API Transparência CPF - Consulte /docs para ver os endpoints disponíveis.",
    }


@app.get(
    "/consulta/{cpf}",
    response_model=CPFConsultaResponse,
    summary="Consulta completa por CPF",
    description=(
        "Realiza consulta nos endpoints do Portal da Transparência: "
        "dados pessoais, viagens, PETI e BPC."
    ),
    tags=["Consulta"],
)
async def consultar_cpf(
    cpf: str,
    chave_api: str = Query(..., alias="chave-api", description="Chave de acesso à API do Portal da Transparência"),
):
    cpf_limpo = validar_cpf(cpf)
    service = TransparenciaService(chave_api=chave_api)
    resultado = await service.consulta_completa(cpf_limpo)
    return resultado