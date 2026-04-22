import httpx
from typing import Optional, Any
import logging

from models import (
    CPFConsultaResponse,
    DadosPessoais,
    Viagem,
    ResumoViagens,
    BeneficioPETI,
    ResumoPETI,
    BeneficioBPC,
    ResumoBPC,
    FonteStatus,
    StatusConsultas,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://api.portaldatransparencia.gov.br/api-de-dados"
TIMEOUT = 30.0


def formatar_cpf(cpf: str) -> str:
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def safe_float(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


class TransparenciaService:
    def __init__(self, chave_api: str):
        self.headers = {
            "chave-api-dados": chave_api,
            "Accept": "application/json",
        }

    async def _get(self, endpoint: str, params: dict) -> tuple[Optional[Any], str]:
        """Realiza GET no portal. Retorna (dados, mensagem_erro)."""
        url = f"{BASE_URL}/{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                return response.json(), ""
            elif response.status_code == 401:
                return None, "Chave de API inválida ou sem permissão."
            elif response.status_code == 403:
                try:
                    corpo = response.json()
                    detalhe = corpo.get("message") or corpo.get("mensagem") or corpo.get("error") or str(corpo)
                except Exception:
                    detalhe = response.text[:200] if response.text else "sem detalhes"
                return None, f"Acesso negado (403): {detalhe}"
            elif response.status_code == 404:
                return None, "Nenhum registro encontrado."
            elif response.status_code == 429:
                return None, "Limite de requisições atingido. Tente novamente em instantes."
            else:
                try:
                    corpo = response.json()
                    detalhe = corpo.get("message") or corpo.get("mensagem") or str(corpo)
                except Exception:
                    detalhe = response.text[:200] if response.text else "sem detalhes"
                return None, f"Erro HTTP {response.status_code}: {detalhe}"
        except httpx.TimeoutException:
            return None, "Tempo de resposta excedido."
        except httpx.RequestError as e:
            logger.error(f"Erro de conexão com {url}: {e}")
            return None, "Falha na conexão com o Portal da Transparência."

    async def buscar_pessoa_fisica(self, cpf: str) -> tuple[Optional[DadosPessoais], FonteStatus]:
        dados, erro = await self._get("cpf", {"cpf": cpf, "pagina": 1})

        if erro:
            return None, FonteStatus(disponivel=False, mensagem=erro)

        pessoa = dados[0] if isinstance(dados, list) and dados else dados
        if not pessoa:
            return None, FonteStatus(disponivel=True, mensagem="Nenhum dado encontrado.")

        municipio_nasc = pessoa.get("municipioNascimento") or {}
        uf = municipio_nasc.get("uf", {}) if isinstance(municipio_nasc, dict) else {}

        resultado = DadosPessoais(
            nome=pessoa.get("nomeCompleto") or pessoa.get("nome"),
            cpf=formatar_cpf(cpf),
            nomeMae=pessoa.get("nomeMae"),
            dataNascimento=pessoa.get("dataNascimento"),
            municipioNascimento=(
                municipio_nasc.get("nomeIBGE") if isinstance(municipio_nasc, dict) else str(municipio_nasc)
            ),
            ufNascimento=(
                uf.get("sigla") if isinstance(uf, dict) else str(uf)
            ),
            sexo=pessoa.get("sexo"),
            situacaoCadastral=pessoa.get("situacaoCadastral"),
        )
        return resultado, FonteStatus(disponivel=True)

    async def buscar_viagens(self, cpf: str) -> tuple[ResumoViagens, FonteStatus]:
        dados, erro = await self._get("viagens/passagens-por-cpf", {"cpf": cpf, "pagina": 1})

        if erro:
            return ResumoViagens(), FonteStatus(disponivel=False, mensagem=erro)

        registros = dados if isinstance(dados, list) else []
        viagens: list[Viagem] = []

        total_passagens = 0.0
        total_diarias = 0.0

        for item in registros:
            val_passagens = safe_float(item.get("valorPassagens")) or 0.0
            val_diarias = safe_float(item.get("valorDiarias")) or 0.0
            total_passagens += val_passagens
            total_diarias += val_diarias

            orgao_raw = item.get("orgao") or {}
            destinos_raw = item.get("viagem", {}) or {}

            viagens.append(
                Viagem(
                    id=str(item.get("id", "")),
                    numeroProposta=item.get("numeroProposta"),
                    situacao=item.get("situacao"),
                    dataInicio=item.get("dataInicioAfastamento") or item.get("dataInicio"),
                    dataFim=item.get("dataFimAfastamento") or item.get("dataFim"),
                    destinos=item.get("destinos") or destinos_raw.get("destino"),
                    motivoViagem=item.get("objeto"),
                    valorPassagens=val_passagens,
                    valorDiarias=val_diarias,
                    valorTotal=val_passagens + val_diarias,
                    orgao=(
                        orgao_raw.get("nome") if isinstance(orgao_raw, dict) else str(orgao_raw)
                    ),
                )
            )

        resumo = ResumoViagens(
            totalViagens=len(viagens),
            valorTotalPassagens=round(total_passagens, 2),
            valorTotalDiarias=round(total_diarias, 2),
            valorGeral=round(total_passagens + total_diarias, 2),
            viagens=viagens,
        )
        return resumo, FonteStatus(disponivel=True)

    async def buscar_peti(self, cpf: str) -> tuple[ResumoPETI, FonteStatus]:
        dados, erro = await self._get("peti/por-cpf-nis", {"cpfNis": cpf, "pagina": 1})

        if erro:
            return ResumoPETI(), FonteStatus(disponivel=False, mensagem=erro)

        registros = dados if isinstance(dados, list) else []
        beneficios: list[BeneficioPETI] = []

        for item in registros:
            municipio_raw = item.get("municipio") or {}
            uf_raw = municipio_raw.get("uf", {}) if isinstance(municipio_raw, dict) else {}

            beneficios.append(
                BeneficioPETI(
                    nis=item.get("nis"),
                    nome=item.get("nome"),
                    cpf=item.get("cpf"),
                    municipio=(
                        municipio_raw.get("nomeIBGE") if isinstance(municipio_raw, dict) else str(municipio_raw)
                    ),
                    uf=(
                        uf_raw.get("sigla") if isinstance(uf_raw, dict) else str(uf_raw)
                    ),
                    competencia=item.get("mesAnoCompetencia"),
                    valorBeneficio=safe_float(item.get("valor")),
                    ativo=item.get("ativo"),
                )
            )

        return (
            ResumoPETI(encontrado=bool(beneficios), totalRegistros=len(beneficios), registros=beneficios),
            FonteStatus(disponivel=True),
        )

    async def buscar_bpc(self, cpf: str) -> tuple[ResumoBPC, FonteStatus]:
        dados, erro = await self._get("bpc/por-cpf-nis", {"cpfNis": cpf, "pagina": 1})

        if erro:
            return ResumoBPC(), FonteStatus(disponivel=False, mensagem=erro)

        registros = dados if isinstance(dados, list) else []
        beneficios: list[BeneficioBPC] = []

        for item in registros:
            municipio_raw = item.get("municipio") or {}
            uf_raw = municipio_raw.get("uf", {}) if isinstance(municipio_raw, dict) else {}

            tipo = item.get("tipoBeneficio") or {}
            tipo_desc = tipo.get("descricao") if isinstance(tipo, dict) else str(tipo) if tipo else None

            beneficios.append(
                BeneficioBPC(
                    nis=item.get("nis"),
                    nome=item.get("nome"),
                    cpf=item.get("cpf"),
                    municipio=(
                        municipio_raw.get("nomeIBGE") if isinstance(municipio_raw, dict) else str(municipio_raw)
                    ),
                    uf=(
                        uf_raw.get("sigla") if isinstance(uf_raw, dict) else str(uf_raw)
                    ),
                    competencia=item.get("mesAnoCompetencia"),
                    valorBeneficio=safe_float(item.get("valor")),
                    tipoBeneficio=tipo_desc,
                    ativo=item.get("ativo"),
                )
            )

        return (
            ResumoBPC(encontrado=bool(beneficios), totalRegistros=len(beneficios), registros=beneficios),
            FonteStatus(disponivel=True),
        )

    async def consulta_completa(self, cpf: str) -> CPFConsultaResponse:
        import asyncio

        pessoa_task = self.buscar_pessoa_fisica(cpf)
        viagens_task = self.buscar_viagens(cpf)
        peti_task = self.buscar_peti(cpf)
        bpc_task = self.buscar_bpc(cpf)

        (dados_pessoais, status_pf), (viagens, status_v), (peti, status_peti), (bpc, status_bpc) = (
            await asyncio.gather(pessoa_task, viagens_task, peti_task, bpc_task)
        )

        return CPFConsultaResponse(
            cpf=cpf,
            cpfFormatado=formatar_cpf(cpf),
            dadosPessoais=dados_pessoais,
            viagens=viagens,
            peti=peti,
            bpc=bpc,
            statusConsultas=StatusConsultas(
                pessoaFisica=status_pf,
                viagens=status_v,
                peti=status_peti,
                bpc=status_bpc,
            ),
        )