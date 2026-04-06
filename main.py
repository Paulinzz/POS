from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, timedelta
from uuid import uuid4

app = FastAPI(
    title="API Biblioteca",
    description="Sistema de gerenciamento de biblioteca com empréstimos",
    version="1.0.0"
)


livros_db: dict = {}
usuarios_db: dict = {}
emprestimos_db: dict = {}




class LivroCreate(BaseModel):
    titulo: str = Field(..., example="Didatica Magica")
    autor: str = Field(..., example="Pedro Assad")
    isbn: str = Field(..., example="978-85-359-0277-4")
    ano_publicacao: int = Field(..., example=1605)
    quantidade_total: int = Field(..., ge=1, example=3)

class LivroUpdate(BaseModel):
    titulo: Optional[str] = None
    autor: Optional[str] = None
    isbn: Optional[str] = None
    ano_publicacao: Optional[int] = None
    quantidade_total: Optional[int] = Field(None, ge=1)

class LivroResponse(BaseModel):
    id: str
    titulo: str
    autor: str
    isbn: str
    ano_publicacao: int
    quantidade_total: int
    quantidade_disponivel: int

class UsuarioCreate(BaseModel):
    nome: str = Field(..., example="João Silva")
    email: str = Field(..., example="joao@email.com")
    cpf: str = Field(..., example="123.456.789-00")
    telefone: Optional[str] = Field(None, example="(84) 99999-0000")

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None

class UsuarioResponse(BaseModel):
    id: str
    nome: str
    email: str
    cpf: str
    telefone: Optional[str]
    ativo: bool

class EmprestimoCreate(BaseModel):
    usuario_id: str
    livro_id: str
    dias_prazo: int = Field(default=14, ge=1, le=60, example=14)

class EmprestimoResponse(BaseModel):
    id: str
    usuario_id: str
    usuario_nome: str
    livro_id: str
    livro_titulo: str
    data_emprestimo: date
    data_devolucao_prevista: date
    data_devolucao_real: Optional[date]
    devolvido: bool
    em_atraso: bool


# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def calcular_disponivel(livro_id: str) -> int:
    emprestados = sum(
        1 for e in emprestimos_db.values()
        if e["livro_id"] == livro_id and not e["devolvido"]
    )
    total = livros_db[livro_id]["quantidade_total"]
    return total - emprestados

def montar_livro_response(livro_id: str) -> LivroResponse:
    l = livros_db[livro_id]
    return LivroResponse(
        **l,
        quantidade_disponivel=calcular_disponivel(livro_id)
    )

def montar_emprestimo_response(emp_id: str) -> EmprestimoResponse:
    e = emprestimos_db[emp_id]
    usuario = usuarios_db.get(e["usuario_id"], {})
    livro = livros_db.get(e["livro_id"], {})
    hoje = date.today()
    em_atraso = (
        not e["devolvido"] and
        hoje > e["data_devolucao_prevista"]
    )
    return EmprestimoResponse(
        id=emp_id,
        usuario_id=e["usuario_id"],
        usuario_nome=usuario.get("nome", "Desconhecido"),
        livro_id=e["livro_id"],
        livro_titulo=livro.get("titulo", "Desconhecido"),
        data_emprestimo=e["data_emprestimo"],
        data_devolucao_prevista=e["data_devolucao_prevista"],
        data_devolucao_real=e.get("data_devolucao_real"),
        devolvido=e["devolvido"],
        em_atraso=em_atraso,
    )


# ─────────────────────────────────────────
# ROTAS — LIVROS
# ─────────────────────────────────────────

@app.post("/livros", response_model=LivroResponse, status_code=201, tags=["Livros"])
def criar_livro(livro: LivroCreate):
    """Cadastra um novo livro."""
    # ISBN único
    for l in livros_db.values():
        if l["isbn"] == livro.isbn:
            raise HTTPException(400, "ISBN já cadastrado.")
    livro_id = str(uuid4())
    livros_db[livro_id] = {"id": livro_id, **livro.model_dump()}
    return montar_livro_response(livro_id)


@app.get("/livros", response_model=List[LivroResponse], tags=["Livros"])
def listar_livros(apenas_disponiveis: bool = False):
    """
    Lista todos os livros.  
    Use `apenas_disponiveis=true` para filtrar somente os que têm exemplares livres
    (livros emprestados NÃO aparecem nesse filtro).
    """
    resultado = []
    for lid in livros_db:
        disp = calcular_disponivel(lid)
        if apenas_disponiveis and disp == 0:
            continue
        resultado.append(montar_livro_response(lid))
    return resultado


@app.get("/livros/{livro_id}", response_model=LivroResponse, tags=["Livros"])
def buscar_livro(livro_id: str):
    """Retorna um livro pelo ID."""
    if livro_id not in livros_db:
        raise HTTPException(404, "Livro não encontrado.")
    return montar_livro_response(livro_id)


@app.put("/livros/{livro_id}", response_model=LivroResponse, tags=["Livros"])
def atualizar_livro(livro_id: str, dados: LivroUpdate):
    """Atualiza dados de um livro."""
    if livro_id not in livros_db:
        raise HTTPException(404, "Livro não encontrado.")
    livro = livros_db[livro_id]
    for campo, valor in dados.model_dump(exclude_none=True).items():
        livro[campo] = valor
    return montar_livro_response(livro_id)


@app.delete("/livros/{livro_id}", status_code=204, tags=["Livros"])
def deletar_livro(livro_id: str):
    """Remove um livro (somente se não houver empréstimos ativos)."""
    if livro_id not in livros_db:
        raise HTTPException(404, "Livro não encontrado.")
    emprestimo_ativo = any(
        e["livro_id"] == livro_id and not e["devolvido"]
        for e in emprestimos_db.values()
    )
    if emprestimo_ativo:
        raise HTTPException(400, "Livro possui empréstimos ativos e não pode ser removido.")
    del livros_db[livro_id]


# ─────────────────────────────────────────
# ROTAS — USUÁRIOS
# ─────────────────────────────────────────

@app.post("/usuarios", response_model=UsuarioResponse, status_code=201, tags=["Usuários"])
def criar_usuario(usuario: UsuarioCreate):
    """Cadastra um novo usuário."""
    for u in usuarios_db.values():
        if u["cpf"] == usuario.cpf:
            raise HTTPException(400, "CPF já cadastrado.")
        if u["email"] == usuario.email:
            raise HTTPException(400, "E-mail já cadastrado.")
    uid = str(uuid4())
    usuarios_db[uid] = {"id": uid, "ativo": True, **usuario.model_dump()}
    return UsuarioResponse(**usuarios_db[uid])


@app.get("/usuarios", response_model=List[UsuarioResponse], tags=["Usuários"])
def listar_usuarios(apenas_ativos: bool = True):
    """Lista usuários. Por padrão retorna apenas usuários ativos."""
    return [
        UsuarioResponse(**u)
        for u in usuarios_db.values()
        if not apenas_ativos or u["ativo"]
    ]


@app.get("/usuarios/{usuario_id}", response_model=UsuarioResponse, tags=["Usuários"])
def buscar_usuario(usuario_id: str):
    """Retorna um usuário pelo ID."""
    if usuario_id not in usuarios_db:
        raise HTTPException(404, "Usuário não encontrado.")
    return UsuarioResponse(**usuarios_db[usuario_id])


@app.put("/usuarios/{usuario_id}", response_model=UsuarioResponse, tags=["Usuários"])
def atualizar_usuario(usuario_id: str, dados: UsuarioUpdate):
    """Atualiza dados de um usuário."""
    if usuario_id not in usuarios_db:
        raise HTTPException(404, "Usuário não encontrado.")
    usuario = usuarios_db[usuario_id]
    for campo, valor in dados.model_dump(exclude_none=True).items():
        usuario[campo] = valor
    return UsuarioResponse(**usuario)


@app.delete("/usuarios/{usuario_id}", status_code=204, tags=["Usuários"])
def desativar_usuario(usuario_id: str):
    """Desativa um usuário (soft delete). Usuários com empréstimos ativos não podem ser desativados."""
    if usuario_id not in usuarios_db:
        raise HTTPException(404, "Usuário não encontrado.")
    emprestimo_ativo = any(
        e["usuario_id"] == usuario_id and not e["devolvido"]
        for e in emprestimos_db.values()
    )
    if emprestimo_ativo:
        raise HTTPException(400, "Usuário possui empréstimos ativos.")
    usuarios_db[usuario_id]["ativo"] = False


# ─────────────────────────────────────────
# ROTAS — EMPRÉSTIMOS
# ─────────────────────────────────────────

@app.post("/emprestimos", response_model=EmprestimoResponse, status_code=201, tags=["Empréstimos"])
def realizar_emprestimo(dados: EmprestimoCreate):
    """Realiza o empréstimo de um livro para um usuário."""
    # Validações
    if dados.usuario_id not in usuarios_db:
        raise HTTPException(404, "Usuário não encontrado.")
    if not usuarios_db[dados.usuario_id]["ativo"]:
        raise HTTPException(400, "Usuário inativo não pode realizar empréstimos.")
    if dados.livro_id not in livros_db:
        raise HTTPException(404, "Livro não encontrado.")

    # Verifica se usuário já tem esse livro emprestado
    ja_emprestado = any(
        e["usuario_id"] == dados.usuario_id and
        e["livro_id"] == dados.livro_id and
        not e["devolvido"]
        for e in emprestimos_db.values()
    )
    if ja_emprestado:
        raise HTTPException(400, "Usuário já possui este livro emprestado.")

    # Verifica disponibilidade
    if calcular_disponivel(dados.livro_id) == 0:
        raise HTTPException(400, "Não há exemplares disponíveis deste livro.")

    # Verifica se usuário tem empréstimos em atraso
    hoje = date.today()
    tem_atraso = any(
        e["usuario_id"] == dados.usuario_id and
        not e["devolvido"] and
        hoje > e["data_devolucao_prevista"]
        for e in emprestimos_db.values()
    )
    if tem_atraso:
        raise HTTPException(400, "Usuário possui empréstimos em atraso. Regularize antes de novo empréstimo.")

    emp_id = str(uuid4())
    emprestimos_db[emp_id] = {
        "usuario_id": dados.usuario_id,
        "livro_id": dados.livro_id,
        "data_emprestimo": hoje,
        "data_devolucao_prevista": hoje + timedelta(days=dados.dias_prazo),
        "data_devolucao_real": None,
        "devolvido": False,
    }
    return montar_emprestimo_response(emp_id)


@app.post("/emprestimos/{emprestimo_id}/devolver", response_model=EmprestimoResponse, tags=["Empréstimos"])
def devolver_livro(emprestimo_id: str):
    """Registra a devolução de um livro."""
    if emprestimo_id not in emprestimos_db:
        raise HTTPException(404, "Empréstimo não encontrado.")
    emp = emprestimos_db[emprestimo_id]
    if emp["devolvido"]:
        raise HTTPException(400, "Este empréstimo já foi devolvido.")
    emp["devolvido"] = True
    emp["data_devolucao_real"] = date.today()
    return montar_emprestimo_response(emprestimo_id)


@app.get("/emprestimos", response_model=List[EmprestimoResponse], tags=["Empréstimos"])
def listar_emprestimos(apenas_ativos: bool = False):
    """Lista todos os empréstimos. Use `apenas_ativos=true` para ver somente os não devolvidos."""
    resultado = []
    for eid in emprestimos_db:
        if apenas_ativos and emprestimos_db[eid]["devolvido"]:
            continue
        resultado.append(montar_emprestimo_response(eid))
    return resultado


@app.get("/emprestimos/atraso", response_model=List[EmprestimoResponse], tags=["Empréstimos"])
def listar_emprestimos_em_atraso():
    """Lista todos os empréstimos que estão em atraso (não devolvidos e prazo vencido)."""
    hoje = date.today()
    resultado = []
    for eid, e in emprestimos_db.items():
        if not e["devolvido"] and hoje > e["data_devolucao_prevista"]:
            resultado.append(montar_emprestimo_response(eid))
    return resultado


@app.get("/emprestimos/{emprestimo_id}", response_model=EmprestimoResponse, tags=["Empréstimos"])
def buscar_emprestimo(emprestimo_id: str):
    """Busca um empréstimo pelo ID."""
    if emprestimo_id not in emprestimos_db:
        raise HTTPException(404, "Empréstimo não encontrado.")
    return montar_emprestimo_response(emprestimo_id)


@app.get("/usuarios/{usuario_id}/emprestimos", response_model=List[EmprestimoResponse], tags=["Empréstimos"])
def emprestimos_do_usuario(usuario_id: str, apenas_ativos: bool = False):
    """Lista todos os empréstimos de um usuário específico."""
    if usuario_id not in usuarios_db:
        raise HTTPException(404, "Usuário não encontrado.")
    resultado = []
    for eid, e in emprestimos_db.items():
        if e["usuario_id"] == usuario_id:
            if apenas_ativos and e["devolvido"]:
                continue
            resultado.append(montar_emprestimo_response(eid))
    return resultado