from pydantic import BaseModel, Field
from typing import Optional, List

class Municipio(BaseModel):
    codigoIBGE: Optional[str] = None
    nomeIBGE: Optional[str] = None
    uf: Optional[str] = None

    @property
    def descricao(self) -> Optional[str]:
        if self.nomeIBGE and self.uf:
            return f"{self.nomeIBGE} - {self.uf}"
        return self.nomeIBGE or self.uf

class DadosPessoais(BaseModel):
    nome: Optional[str] = Field(None, description="Nome completo")
    cpf: Optional[str] = Field(None, description="CPF formatado")
    nomeMae: Optional[str] = Field(None, description="Nome da mãe")
    dataNascimento: Optional[str] = Field(None, description="Data de nascimento")
    municipioNascimento: Optional[str] = Field(None, description="Município de nascimento")
    ufNascimento: Optional[str] = Field(None, description="UF de nascimento")
    sexo: Optional[str] = Field(None, description="Sexo")
    situacaoCadastral: Optional[str] = Field(None, description="Situação cadastral CPF")

    class Config:
        populate_by_name = True

class Viagem(BaseModel):
    id: Optional[str] = None
    numeroProposta: Optional[str] = Field(None, description="Número da proposta")
    situacao: Optional[str] = Field(None, description="Situação da viagem")
    dataInicio: Optional[str] = Field(None, description="Data de início")
    dataFim: Optional[str] = Field(None, description="Data de fim")
    destinos: Optional[str] = Field(None, description="Destinos da viagem")
    motivoViagem: Optional[str] = Field(None, description="Motivo da viagem")
    valorPassagens: Optional[float] = Field(None, description="Valor total das passagens (R$)")
    valorDiarias: Optional[float] = Field(None, description="Valor total das diárias (R$)")
    valorTotal: Optional[float] = Field(None, description="Valor total da viagem (R$)")
    orgao: Optional[str] = Field(None, description="Órgão solicitante")

class ResumoViagens(BaseModel):
    totalViagens: int = Field(0, description="Total de viagens realizadas")
    valorTotalPassagens: float = Field(0.0, description="Soma das passagens (R$)")
    valorTotalDiarias: float = Field(0.0, description="Soma das diárias (R$)")
    valorGeral: float = Field(0.0, description="Valor geral gasto em viagens (R$)")
    viagens: List[Viagem] = Field(default_factory=list)

class BeneficioPETI(BaseModel):
    nis: Optional[str] = Field(None, description="NIS do beneficiário")
    nome: Optional[str] = Field(None, description="Nome do beneficiário")
    cpf: Optional[str] = Field(None, description="CPF do beneficiário")
    municipio: Optional[str] = Field(None, description="Município")
    uf: Optional[str] = Field(None, description="UF")
    competencia: Optional[str] = Field(None, description="Competência (mês/ano)")
    valorBeneficio: Optional[float] = Field(None, description="Valor do benefício (R$)")
    ativo: Optional[bool] = Field(None, description="Benefício ativo")

class ResumoPETI(BaseModel):
    encontrado: bool = Field(False, description="Se o CPF/NIS possui registros no PETI")
    totalRegistros: int = Field(0, description="Total de registros")
    registros: List[BeneficioPETI] = Field(default_factory=list)

class BeneficioBPC(BaseModel):
    nis: Optional[str] = Field(None, description="NIS do beneficiário")
    nome: Optional[str] = Field(None, description="Nome do beneficiário")
    cpf: Optional[str] = Field(None, description="CPF do beneficiário")
    municipio: Optional[str] = Field(None, description="Município")
    uf: Optional[str] = Field(None, description="UF")
    competencia: Optional[str] = Field(None, description="Competência (mês/ano)")
    valorBeneficio: Optional[float] = Field(None, description="Valor do benefício (R$)")
    tipoBeneficio: Optional[str] = Field(None, description="Tipo de benefício (idoso/deficiência)")
    ativo: Optional[bool] = Field(None, description="Benefício ativo")


class ResumoBPC(BaseModel):
    encontrado: bool = Field(False, description="Se o CPF/NIS possui registros no BPC")
    totalRegistros: int = Field(0, description="Total de registros")
    registros: List[BeneficioBPC] = Field(default_factory=list)

class FonteStatus(BaseModel):
    disponivel: bool
    mensagem: Optional[str] = None


class StatusConsultas(BaseModel):
    pessoaFisica: FonteStatus
    viagens: FonteStatus
    peti: FonteStatus
    bpc: FonteStatus


class CPFConsultaResponse(BaseModel):
    cpf: str = Field(..., description="CPF consultado (apenas dígitos)")
    cpfFormatado: str = Field(..., description="CPF formatado (XXX.XXX.XXX-XX)")
    dadosPessoais: Optional[DadosPessoais] = Field(None, description="Dados cadastrais da pessoa")
    viagens: ResumoViagens = Field(default_factory=ResumoViagens, description="Histórico de viagens a serviço")
    peti: ResumoPETI = Field(default_factory=ResumoPETI, description="Benefícios do Programa de Erradicação do Trabalho Infantil")
    bpc: ResumoBPC = Field(default_factory=ResumoBPC, description="Benefícios de Prestação Continuada")
    statusConsultas: StatusConsultas = Field(..., description="Status de cada fonte consultada")