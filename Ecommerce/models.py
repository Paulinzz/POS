from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class UsuarioPapelLink(SQLModel, table=True):
    __tablename__ = "usuario_papeis"

    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id", primary_key=True)
    papel_id: Optional[int] = Field(default=None, foreign_key="papeis.id", primary_key=True)


class ProdutoCategoriaLink(SQLModel, table=True):
    __tablename__ = "produto_categorias"

    produto_id: Optional[int] = Field(default=None, foreign_key="produtos.id", primary_key=True)
    categoria_id: Optional[int] = Field(default=None, foreign_key="categorias.id", primary_key=True)


class PapelBase(SQLModel):
    nome: str = Field(max_length=50)

class Papel(PapelBase, table=True):
    __tablename__ = "papeis"
    id: Optional[int] = Field(default=None, primary_key=True)
    usuarios: List["Usuario"] = Relationship(back_populates="papeis", link_model=UsuarioPapelLink)

class PapelCreate(PapelBase):
    pass

class PapelRead(PapelBase):
    id: int

class PapelUpdate(SQLModel):
    nome: Optional[str] = Field(default=None, max_length=50)


class UsuarioBase(SQLModel):
    nome: str = Field(max_length=100)
    email: str = Field(max_length=150)

class Usuario(UsuarioBase, table=True):
    __tablename__ = "usuarios"
    id: Optional[int] = Field(default=None, primary_key=True)
    senha_hash: str = Field(max_length=255)
    criado_em: Optional[datetime] = Field(default_factory=datetime.utcnow)
    papeis: List[Papel] = Relationship(back_populates="usuarios", link_model=UsuarioPapelLink)
    pedidos: List["Pedido"] = Relationship(back_populates="usuario")
    enderecos: List["Endereco"] = Relationship(back_populates="usuario")
    avaliacoes: List["Avaliacao"] = Relationship(back_populates="usuario")

class UsuarioCreate(UsuarioBase):
    senha: str

class UsuarioRead(UsuarioBase):
    id: int
    criado_em: datetime
    papeis: List[PapelRead] = []

class UsuarioUpdate(SQLModel):
    nome: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=150)
    senha: Optional[str] = None


class CategoriaBase(SQLModel):
    nome: str = Field(max_length=100)

class Categoria(CategoriaBase, table=True):
    __tablename__ = "categorias"
    id: Optional[int] = Field(default=None, primary_key=True)
    produtos: List["Produto"] = Relationship(back_populates="categorias", link_model=ProdutoCategoriaLink)

class CategoriaCreate(CategoriaBase):
    pass

class CategoriaRead(CategoriaBase):
    id: int

class CategoriaUpdate(SQLModel):
    nome: Optional[str] = Field(default=None, max_length=100)


class ProdutoBase(SQLModel):
    nome: str = Field(max_length=150)
    descricao: Optional[str] = None
    preco: Decimal = Field(max_digits=10, decimal_places=2)

class Produto(ProdutoBase, table=True):
    __tablename__ = "produtos"
    id: Optional[int] = Field(default=None, primary_key=True)
    criado_em: Optional[datetime] = Field(default_factory=datetime.utcnow)
    categorias: List[Categoria] = Relationship(back_populates="produtos", link_model=ProdutoCategoriaLink)
    itens_pedido: List["ItemPedido"] = Relationship(back_populates="produto")
    avaliacoes: List["Avaliacao"] = Relationship(back_populates="produto")
    estoque: Optional["Estoque"] = Relationship(back_populates="produto")

class ProdutoCreate(ProdutoBase):
    pass

class ProdutoRead(ProdutoBase):
    id: int
    criado_em: datetime
    categorias: List[CategoriaRead] = []

class ProdutoUpdate(SQLModel):
    nome: Optional[str] = Field(default=None, max_length=150)
    descricao: Optional[str] = None
    preco: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)


class PedidoBase(SQLModel):
    total: Decimal = Field(max_digits=10, decimal_places=2)
    status: str = Field(max_length=50)

class Pedido(PedidoBase, table=True):
    __tablename__ = "pedidos"
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    criado_em: Optional[datetime] = Field(default_factory=datetime.utcnow)
    usuario: Optional[Usuario] = Relationship(back_populates="pedidos")
    itens: List["ItemPedido"] = Relationship(back_populates="pedido")
    pagamentos: List["Pagamento"] = Relationship(back_populates="pedido")

class PedidoCreate(PedidoBase):
    usuario_id: int

class PedidoRead(PedidoBase):
    id: int
    usuario_id: int
    criado_em: datetime

class PedidoUpdate(SQLModel):
    total: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    status: Optional[str] = Field(default=None, max_length=50)


class ItemPedidoBase(SQLModel):
    quantidade: int
    preco: Decimal = Field(max_digits=10, decimal_places=2)

class ItemPedido(ItemPedidoBase, table=True):
    __tablename__ = "itens_pedido"
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: Optional[int] = Field(default=None, foreign_key="pedidos.id")
    produto_id: Optional[int] = Field(default=None, foreign_key="produtos.id")
    pedido: Optional[Pedido] = Relationship(back_populates="itens")
    produto: Optional[Produto] = Relationship(back_populates="itens_pedido")

class ItemPedidoCreate(ItemPedidoBase):
    produto_id: int

class ItemPedidoRead(ItemPedidoBase):
    id: int
    pedido_id: int
    produto_id: int


class PagamentoBase(SQLModel):
    valor: Decimal = Field(max_digits=10, decimal_places=2)
    metodo: str = Field(max_length=50)
    status: str = Field(max_length=50)
    pago_em: Optional[datetime] = None

class Pagamento(PagamentoBase, table=True):
    __tablename__ = "pagamentos"
    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: Optional[int] = Field(default=None, foreign_key="pedidos.id")
    pedido: Optional[Pedido] = Relationship(back_populates="pagamentos")

class PagamentoCreate(PagamentoBase):
    pedido_id: int

class PagamentoRead(PagamentoBase):
    id: int
    pedido_id: int


class EnderecoBase(SQLModel):
    rua: Optional[str] = Field(default=None, max_length=150)
    cidade: Optional[str] = Field(default=None, max_length=100)
    estado: Optional[str] = Field(default=None, max_length=100)
    cep: Optional[str] = Field(default=None, max_length=20)

class Endereco(EnderecoBase, table=True):
    __tablename__ = "enderecos"
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    usuario: Optional[Usuario] = Relationship(back_populates="enderecos")

class EnderecoCreate(EnderecoBase):
    usuario_id: int

class EnderecoRead(EnderecoBase):
    id: int
    usuario_id: int

class EnderecoUpdate(EnderecoBase):
    pass


class AvaliacaoBase(SQLModel):
    nota: int
    comentario: Optional[str] = None

class Avaliacao(AvaliacaoBase, table=True):
    __tablename__ = "avaliacoes"
    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuarios.id")
    produto_id: Optional[int] = Field(default=None, foreign_key="produtos.id")
    criado_em: Optional[datetime] = Field(default_factory=datetime.utcnow)
    usuario: Optional[Usuario] = Relationship(back_populates="avaliacoes")
    produto: Optional[Produto] = Relationship(back_populates="avaliacoes")

class AvaliacaoCreate(AvaliacaoBase):
    usuario_id: int
    produto_id: int

class AvaliacaoRead(AvaliacaoBase):
    id: int
    usuario_id: int
    produto_id: int
    criado_em: datetime


class EstoqueBase(SQLModel):
    quantidade: int

class Estoque(EstoqueBase, table=True):
    __tablename__ = "estoque"
    id: Optional[int] = Field(default=None, primary_key=True)
    produto_id: Optional[int] = Field(default=None, foreign_key="produtos.id", unique=True)
    atualizado_em: Optional[datetime] = Field(default_factory=datetime.utcnow)
    produto: Optional[Produto] = Relationship(back_populates="estoque")

class EstoqueCreate(EstoqueBase):
    produto_id: int

class EstoqueRead(EstoqueBase):
    id: int
    produto_id: int
    atualizado_em: datetime

class EstoqueUpdate(SQLModel):
    quantidade: Optional[int] = None