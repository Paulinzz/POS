import hashlib
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import (
    Papel, PapelCreate, PapelRead, PapelUpdate,
    Usuario, UsuarioCreate, UsuarioRead, UsuarioUpdate, UsuarioPapelLink,
    Produto, ProdutoCreate, ProdutoRead, ProdutoUpdate, ProdutoCategoriaLink,
    Categoria, CategoriaCreate, CategoriaRead, CategoriaUpdate,
    Pedido, PedidoCreate, PedidoRead, PedidoUpdate,
    ItemPedido, ItemPedidoCreate, ItemPedidoRead,
    Pagamento, PagamentoCreate, PagamentoRead,
    Endereco, EnderecoCreate, EnderecoRead, EnderecoUpdate,
    Avaliacao, AvaliacaoCreate, AvaliacaoRead,
    Estoque, EstoqueCreate, EstoqueRead, EstoqueUpdate,
)

SessionDep = Annotated[Session, Depends(get_session)]


def hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="E-commerce API", version="1.0.0", lifespan=lifespan)


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/papeis", tags=["Papéis"])
def listar_papeis(session: SessionDep) -> list[PapelRead]:
    return session.exec(select(Papel)).all()

@app.post("/papeis", tags=["Papéis"], status_code=201)
def criar_papel(data: PapelCreate, session: SessionDep) -> PapelRead:
    if session.exec(select(Papel).where(Papel.nome == data.nome)).first():
        raise HTTPException(409, f"Papel '{data.nome}' já existe.")
    papel = Papel.model_validate(data)
    session.add(papel)
    session.commit()
    session.refresh(papel)
    return papel

@app.get("/papeis/{id}", tags=["Papéis"])
def buscar_papel(id: int, session: SessionDep) -> PapelRead:
    papel = session.get(Papel, id)
    if not papel:
        raise HTTPException(404, f"Papel id={id} não encontrado.")
    return papel

@app.put("/papeis/{id}", tags=["Papéis"])
def atualizar_papel(id: int, data: PapelUpdate, session: SessionDep) -> PapelRead:
    papel = session.get(Papel, id)
    if not papel:
        raise HTTPException(404, f"Papel id={id} não encontrado.")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(papel, campo, valor)
    session.add(papel)
    session.commit()
    session.refresh(papel)
    return papel

@app.delete("/papeis/{id}", tags=["Papéis"])
def deletar_papel(id: int, session: SessionDep):
    papel = session.get(Papel, id)
    if papel:
        session.delete(papel)
        session.commit()


@app.get("/usuarios", tags=["Usuários"])
def listar_usuarios(session: SessionDep) -> list[UsuarioRead]:
    return session.exec(select(Usuario)).all()

@app.post("/usuarios", tags=["Usuários"], status_code=201)
def criar_usuario(data: UsuarioCreate, session: SessionDep) -> UsuarioRead:
    if session.exec(select(Usuario).where(Usuario.email == data.email)).first():
        raise HTTPException(409, f"E-mail '{data.email}' já cadastrado.")
    usuario = Usuario(nome=data.nome, email=data.email, senha_hash=hash_senha(data.senha))
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

@app.get("/usuarios/{id}", tags=["Usuários"])
def buscar_usuario(id: int, session: SessionDep) -> UsuarioRead:
    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(404, f"Usuário id={id} não encontrado.")
    return usuario

@app.put("/usuarios/{id}", tags=["Usuários"])
def atualizar_usuario(id: int, data: UsuarioUpdate, session: SessionDep) -> UsuarioRead:
    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(404, f"Usuário id={id} não encontrado.")
    if data.nome is not None:
        usuario.nome = data.nome
    if data.email is not None:
        if session.exec(select(Usuario).where(Usuario.email == data.email, Usuario.id != id)).first():
            raise HTTPException(409, f"E-mail '{data.email}' já está em uso.")
        usuario.email = data.email
    if data.senha is not None:
        usuario.senha_hash = hash_senha(data.senha)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

@app.delete("/usuarios/{id}", tags=["Usuários"])
def deletar_usuario(id: int, session: SessionDep):
    usuario = session.get(Usuario, id)
    if usuario:
        session.delete(usuario)
        session.commit()

@app.post("/usuarios/{id}/papeis/{papel_id}", tags=["Usuários"])
def adicionar_papel(id: int, papel_id: int, session: SessionDep) -> UsuarioRead:
    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(404, f"Usuário id={id} não encontrado.")
    if not session.get(Papel, papel_id):
        raise HTTPException(404, f"Papel id={papel_id} não encontrado.")
    if session.get(UsuarioPapelLink, (id, papel_id)):
        raise HTTPException(409, "Usuário já possui este papel.")
    session.add(UsuarioPapelLink(usuario_id=id, papel_id=papel_id))
    session.commit()
    session.refresh(usuario)
    return usuario

@app.delete("/usuarios/{id}/papeis/{papel_id}", tags=["Usuários"])
def remover_papel(id: int, papel_id: int, session: SessionDep) -> UsuarioRead:
    usuario = session.get(Usuario, id)
    if not usuario:
        raise HTTPException(404, f"Usuário id={id} não encontrado.")
    vinculo = session.get(UsuarioPapelLink, (id, papel_id))
    if vinculo:
        session.delete(vinculo)
        session.commit()
        session.refresh(usuario)
    return usuario


@app.get("/categorias", tags=["Categorias"])
def listar_categorias(session: SessionDep) -> list[CategoriaRead]:
    return session.exec(select(Categoria)).all()

@app.post("/categorias", tags=["Categorias"], status_code=201)
def criar_categoria(data: CategoriaCreate, session: SessionDep) -> CategoriaRead:
    if session.exec(select(Categoria).where(Categoria.nome == data.nome)).first():
        raise HTTPException(409, f"Categoria '{data.nome}' já existe.")
    categoria = Categoria.model_validate(data)
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria

@app.get("/categorias/{id}", tags=["Categorias"])
def buscar_categoria(id: int, session: SessionDep) -> CategoriaRead:
    categoria = session.get(Categoria, id)
    if not categoria:
        raise HTTPException(404, f"Categoria id={id} não encontrada.")
    return categoria

@app.put("/categorias/{id}", tags=["Categorias"])
def atualizar_categoria(id: int, data: CategoriaUpdate, session: SessionDep) -> CategoriaRead:
    categoria = session.get(Categoria, id)
    if not categoria:
        raise HTTPException(404, f"Categoria id={id} não encontrada.")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(categoria, campo, valor)
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria

@app.delete("/categorias/{id}", tags=["Categorias"])
def deletar_categoria(id: int, session: SessionDep):
    categoria = session.get(Categoria, id)
    if categoria:
        session.delete(categoria)
        session.commit()


@app.get("/produtos", tags=["Produtos"])
def listar_produtos(session: SessionDep) -> list[ProdutoRead]:
    return session.exec(select(Produto)).all()

@app.post("/produtos", tags=["Produtos"], status_code=201)
def criar_produto(data: ProdutoCreate, session: SessionDep) -> ProdutoRead:
    produto = Produto.model_validate(data)
    session.add(produto)
    session.commit()
    session.refresh(produto)
    return produto

@app.get("/produtos/{id}", tags=["Produtos"])
def buscar_produto(id: int, session: SessionDep) -> ProdutoRead:
    produto = session.get(Produto, id)
    if not produto:
        raise HTTPException(404, f"Produto id={id} não encontrado.")
    return produto

@app.put("/produtos/{id}", tags=["Produtos"])
def atualizar_produto(id: int, data: ProdutoUpdate, session: SessionDep) -> ProdutoRead:
    produto = session.get(Produto, id)
    if not produto:
        raise HTTPException(404, f"Produto id={id} não encontrado.")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(produto, campo, valor)
    session.add(produto)
    session.commit()
    session.refresh(produto)
    return produto

@app.delete("/produtos/{id}", tags=["Produtos"])
def deletar_produto(id: int, session: SessionDep):
    produto = session.get(Produto, id)
    if produto:
        session.delete(produto)
        session.commit()

@app.post("/produtos/{id}/categorias/{categoria_id}", tags=["Produtos"])
def adicionar_categoria_produto(id: int, categoria_id: int, session: SessionDep) -> ProdutoRead:
    produto = session.get(Produto, id)
    if not produto:
        raise HTTPException(404, f"Produto id={id} não encontrado.")
    if not session.get(Categoria, categoria_id):
        raise HTTPException(404, f"Categoria id={categoria_id} não encontrada.")
    if session.get(ProdutoCategoriaLink, (id, categoria_id)):
        raise HTTPException(409, "Produto já possui esta categoria.")
    session.add(ProdutoCategoriaLink(produto_id=id, categoria_id=categoria_id))
    session.commit()
    session.refresh(produto)
    return produto

@app.delete("/produtos/{id}/categorias/{categoria_id}", tags=["Produtos"])
def remover_categoria_produto(id: int, categoria_id: int, session: SessionDep) -> ProdutoRead:
    produto = session.get(Produto, id)
    if not produto:
        raise HTTPException(404, f"Produto id={id} não encontrado.")
    vinculo = session.get(ProdutoCategoriaLink, (id, categoria_id))
    if vinculo:
        session.delete(vinculo)
        session.commit()
        session.refresh(produto)
    return produto


@app.get("/pedidos", tags=["Pedidos"])
def listar_pedidos(session: SessionDep) -> list[PedidoRead]:
    return session.exec(select(Pedido)).all()

@app.post("/pedidos", tags=["Pedidos"], status_code=201)
def criar_pedido(data: PedidoCreate, session: SessionDep) -> PedidoRead:
    if not session.get(Usuario, data.usuario_id):
        raise HTTPException(404, f"Usuário id={data.usuario_id} não encontrado.")
    pedido = Pedido.model_validate(data)
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    return pedido

@app.get("/pedidos/{id}", tags=["Pedidos"])
def buscar_pedido(id: int, session: SessionDep) -> PedidoRead:
    pedido = session.get(Pedido, id)
    if not pedido:
        raise HTTPException(404, f"Pedido id={id} não encontrado.")
    return pedido

@app.put("/pedidos/{id}", tags=["Pedidos"])
def atualizar_pedido(id: int, data: PedidoUpdate, session: SessionDep) -> PedidoRead:
    pedido = session.get(Pedido, id)
    if not pedido:
        raise HTTPException(404, f"Pedido id={id} não encontrado.")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(pedido, campo, valor)
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    return pedido

@app.delete("/pedidos/{id}", tags=["Pedidos"])
def deletar_pedido(id: int, session: SessionDep):
    pedido = session.get(Pedido, id)
    if pedido:
        session.delete(pedido)
        session.commit()

@app.get("/pedidos/{id}/itens", tags=["Pedidos"])
def listar_itens_pedido(id: int, session: SessionDep) -> list[ItemPedidoRead]:
    if not session.get(Pedido, id):
        raise HTTPException(404, f"Pedido id={id} não encontrado.")
    return session.exec(select(ItemPedido).where(ItemPedido.pedido_id == id)).all()

@app.post("/pedidos/{id}/itens", tags=["Pedidos"], status_code=201)
def adicionar_item_pedido(id: int, data: ItemPedidoCreate, session: SessionDep) -> ItemPedidoRead:
    if not session.get(Pedido, id):
        raise HTTPException(404, f"Pedido id={id} não encontrado.")
    if not session.get(Produto, data.produto_id):
        raise HTTPException(404, f"Produto id={data.produto_id} não encontrado.")
    item = ItemPedido(pedido_id=id, produto_id=data.produto_id, quantidade=data.quantidade, preco=data.preco)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@app.delete("/pedidos/{id}/itens/{item_id}", tags=["Pedidos"])
def remover_item_pedido(id: int, item_id: int, session: SessionDep):
    item = session.get(ItemPedido, item_id)
    if item and item.pedido_id == id:
        session.delete(item)
        session.commit()


@app.get("/pagamentos", tags=["Pagamentos"])
def listar_pagamentos(session: SessionDep) -> list[PagamentoRead]:
    return session.exec(select(Pagamento)).all()

@app.post("/pagamentos", tags=["Pagamentos"], status_code=201)
def criar_pagamento(data: PagamentoCreate, session: SessionDep) -> PagamentoRead:
    if not session.get(Pedido, data.pedido_id):
        raise HTTPException(404, f"Pedido id={data.pedido_id} não encontrado.")
    pagamento = Pagamento.model_validate(data)
    session.add(pagamento)
    session.commit()
    session.refresh(pagamento)
    return pagamento

@app.get("/pagamentos/{id}", tags=["Pagamentos"])
def buscar_pagamento(id: int, session: SessionDep) -> PagamentoRead:
    pagamento = session.get(Pagamento, id)
    if not pagamento:
        raise HTTPException(404, f"Pagamento id={id} não encontrado.")
    return pagamento

@app.delete("/pagamentos/{id}", tags=["Pagamentos"])
def deletar_pagamento(id: int, session: SessionDep):
    pagamento = session.get(Pagamento, id)
    if pagamento:
        session.delete(pagamento)
        session.commit()


@app.get("/enderecos", tags=["Endereços"])
def listar_enderecos(session: SessionDep) -> list[EnderecoRead]:
    return session.exec(select(Endereco)).all()

@app.post("/enderecos", tags=["Endereços"], status_code=201)
def criar_endereco(data: EnderecoCreate, session: SessionDep) -> EnderecoRead:
    if not session.get(Usuario, data.usuario_id):
        raise HTTPException(404, f"Usuário id={data.usuario_id} não encontrado.")
    endereco = Endereco.model_validate(data)
    session.add(endereco)
    session.commit()
    session.refresh(endereco)
    return endereco

@app.get("/enderecos/{id}", tags=["Endereços"])
def buscar_endereco(id: int, session: SessionDep) -> EnderecoRead:
    endereco = session.get(Endereco, id)
    if not endereco:
        raise HTTPException(404, f"Endereço id={id} não encontrado.")
    return endereco

@app.put("/enderecos/{id}", tags=["Endereços"])
def atualizar_endereco(id: int, data: EnderecoUpdate, session: SessionDep) -> EnderecoRead:
    endereco = session.get(Endereco, id)
    if not endereco:
        raise HTTPException(404, f"Endereço id={id} não encontrado.")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(endereco, campo, valor)
    session.add(endereco)
    session.commit()
    session.refresh(endereco)
    return endereco

@app.delete("/enderecos/{id}", tags=["Endereços"])
def deletar_endereco(id: int, session: SessionDep):
    endereco = session.get(Endereco, id)
    if endereco:
        session.delete(endereco)
        session.commit()


@app.get("/avaliacoes", tags=["Avaliações"])
def listar_avaliacoes(session: SessionDep) -> list[AvaliacaoRead]:
    return session.exec(select(Avaliacao)).all()

@app.post("/avaliacoes", tags=["Avaliações"], status_code=201)
def criar_avaliacao(data: AvaliacaoCreate, session: SessionDep) -> AvaliacaoRead:
    if not session.get(Usuario, data.usuario_id):
        raise HTTPException(404, f"Usuário id={data.usuario_id} não encontrado.")
    if not session.get(Produto, data.produto_id):
        raise HTTPException(404, f"Produto id={data.produto_id} não encontrado.")
    avaliacao = Avaliacao.model_validate(data)
    session.add(avaliacao)
    session.commit()
    session.refresh(avaliacao)
    return avaliacao

@app.get("/avaliacoes/{id}", tags=["Avaliações"])
def buscar_avaliacao(id: int, session: SessionDep) -> AvaliacaoRead:
    avaliacao = session.get(Avaliacao, id)
    if not avaliacao:
        raise HTTPException(404, f"Avaliação id={id} não encontrada.")
    return avaliacao

@app.delete("/avaliacoes/{id}", tags=["Avaliações"])
def deletar_avaliacao(id: int, session: SessionDep):
    avaliacao = session.get(Avaliacao, id)
    if avaliacao:
        session.delete(avaliacao)
        session.commit()


@app.get("/estoque", tags=["Estoque"])
def listar_estoque(session: SessionDep) -> list[EstoqueRead]:
    return session.exec(select(Estoque)).all()

@app.post("/estoque", tags=["Estoque"], status_code=201)
def criar_estoque(data: EstoqueCreate, session: SessionDep) -> EstoqueRead:
    if not session.get(Produto, data.produto_id):
        raise HTTPException(404, f"Produto id={data.produto_id} não encontrado.")
    if session.exec(select(Estoque).where(Estoque.produto_id == data.produto_id)).first():
        raise HTTPException(409, f"Estoque para produto id={data.produto_id} já existe.")
    estoque = Estoque.model_validate(data)
    session.add(estoque)
    session.commit()
    session.refresh(estoque)
    return estoque

@app.get("/estoque/{id}", tags=["Estoque"])
def buscar_estoque(id: int, session: SessionDep) -> EstoqueRead:
    estoque = session.get(Estoque, id)
    if not estoque:
        raise HTTPException(404, f"Estoque id={id} não encontrado.")
    return estoque

@app.put("/estoque/{id}", tags=["Estoque"])
def atualizar_estoque(id: int, data: EstoqueUpdate, session: SessionDep) -> EstoqueRead:
    estoque = session.get(Estoque, id)
    if not estoque:
        raise HTTPException(404, f"Estoque id={id} não encontrado.")
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(estoque, campo, valor)
    session.add(estoque)
    session.commit()
    session.refresh(estoque)
    return estoque

@app.delete("/estoque/{id}", tags=["Estoque"])
def deletar_estoque(id: int, session: SessionDep):
    estoque = session.get(Estoque, id)
    if estoque:
        session.delete(estoque)
        session.commit()