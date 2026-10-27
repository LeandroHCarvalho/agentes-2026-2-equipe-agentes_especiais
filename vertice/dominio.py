"""O mundo da mesa de servico da Vertice, e as seis consultas sobre ele.

Vem do exemplar do Encontro 7, com UMA correcao, e ela esta declarada aqui
porque o Encontro 7 ja foi ministrado e o AGENTS.md 8.1 nao permite reescreve-lo:

    o Enc. 7 CITAVA os chamados C-106 (elena.matos) e C-108 (joao.prado) dentro
    de CHAMADOS_ABERTOS, mas nunca definiu essas duas contas. Chamar
    consultar_conta("elena.matos") devolvia ERRO. Sem elas, o teste de memoria
    deste encontro nao tem como rodar.

Os dois foram acrescentados com a MESMA situacao do diego.rocha: conta ativa,
sem o grupo erp_leitura, que a revisao de perfis de -6h removeu de 12 usuarios.
E essa coincidencia que o teste de memoria explora.

Tudo sintetico. Nenhuma pessoa, empresa ou sistema real.
"""
from typing import Annotated

try:
    from pydantic import Field
except ImportError:                      # PLANO B: o artesanal.py roda sem nada
    def Field(description: str = "", **_):   # noqa: N802
        """Sosia do Field. O `artesanal.py` escreve o schema a mao e NUNCA le a
        assinatura, entao o laco do Encontro 3 continua rodando num ambiente sem
        pydantic. So o framework le isto aqui."""
        return description

# ---------------------------------------------------------------------
# O MUNDO. Tudo sintetico, tudo inventado, nenhum dado de pessoa real.
# A empresa chama-se Vertice. Cinco usuarios, quatro servicos.
# ---------------------------------------------------------------------

CONTAS = {
    "ana.souza":      {"status": "bloqueada",
                       "motivo": "5 tentativas de senha erradas em -19h",
                       "grupos": ["rh_leitura"],
                       "troca_senha": "-38 dias"},
    "bruno.lima":     {"status": "ativa", "motivo": "",
                       "grupos": ["erp_leitura", "erp_lancamento"],
                       "troca_senha": "-12 dias"},
    "carla.dias":     {"status": "ativa", "motivo": "",
                       "grupos": ["rh_leitura", "vpn_externa"],
                       "troca_senha": "-3 dias"},
    "diego.rocha":    {"status": "ativa", "motivo": "",
                       "grupos": ["rh_leitura"],
                       "troca_senha": "-20 dias"},
    "fernando.alves": {"status": "ativa", "motivo": "",
                       "grupos": ["rh_leitura"],
                       "troca_senha": "-9 dias"},
    # --- ACRESCENTADOS NO ENCONTRO 10, e a razao esta no cabecalho ---
    "elena.matos":    {"status": "ativa", "motivo": "",
                       "grupos": ["rh_leitura"],
                       "troca_senha": "-15 dias"},
    "joao.prado":     {"status": "ativa", "motivo": "",
                       "grupos": ["rh_leitura"],
                       "troca_senha": "-27 dias"},
}

SERVICOS = {
    "portal-rh":      {"estado": "no ar", "desde": "-30 dias", "nota": ""},
    "erp-financeiro": {"estado": "no ar", "desde": "-9 dias",
                       "nota": "lentidao relatada por alguns usuarios hoje de manha"},
    "vpn":            {"estado": "em manutencao", "desde": "-1h",
                       "nota": "janela programada, previsao de retorno em +30min"},
    "email":          {"estado": "no ar", "desde": "-30 dias", "nota": ""},
}

MUDANCAS = {
    "erp-financeiro": [("-6h", "revisao de perfis de acesso: o grupo erp_leitura "
                               "foi removido de 12 usuarios"),
                       ("-31h", "atualizacao de indice do banco de dados")],
    "portal-rh":      [],
    "vpn":            [("-1h", "inicio de janela de manutencao programada")],
    "email":          [],
}

CHAMADOS_ABERTOS = {
    "erp-financeiro": ["C-103 diego.rocha: nao consegue acessar",
                       "C-106 elena.matos: nao consegue acessar",
                       "C-108 joao.prado: nao consegue acessar",
                       "C-102 bruno.lima: lentidao ao abrir telas"],
    "portal-rh":      ["C-101 ana.souza: usuario ou senha invalidos"],
    "vpn":            ["C-104 carla.dias: tudo travando"],
    "email":          [],
}

HISTORICO = {
    "ana.souza":      ["-60 dias portal-rh: esqueci a senha",
                       "-120 dias portal-rh: erro ao emitir holerite"],
    "bruno.lima":     ["-14 dias erp-financeiro: relatorio nao fecha",
                       "-45 dias erp-financeiro: exportacao lenta"],
    "carla.dias":     ["-4 dias vpn: cai sozinha depois de 20 min",
                       "-11 dias vpn: nao conecta de casa",
                       "-26 dias vpn: pede certificado toda vez"],
    "diego.rocha":    ["-70 dias erp-financeiro: duvida de lancamento"],
    "fernando.alves": ["-200 dias portal-rh: primeiro acesso"],
    "elena.matos":    ["-90 dias erp-financeiro: duvida de centro de custo"],
    "joao.prado":     ["-55 dias erp-financeiro: relatorio em branco"],
}

BASE_CONHECIMENTO = {
    "senha": ("KB-014: campanha de troca de senha. Entre -3 e +4 dias o TI envia "
              "aviso de expiracao pelo endereco ti@vertice.exemplo. O aviso e "
              "LEGITIMO e pede troca pelo portal, nunca por link no email."),
    "bloqueio": ("KB-002: a conta bloqueia apos 5 tentativas erradas. O desbloqueio "
                 "e feito pelo autoatendimento, sem abrir chamado."),
    "vpn": ("KB-007: janelas de manutencao da VPN ocorrem as quartas, das 6h as 7h, "
            "e sao avisadas por email na vespera."),
    "perfil": ("KB-021: perda de acesso apos revisao de perfis. Se o usuario perdeu "
               "um grupo numa revisao, a devolucao e pedida ao gestor da area."),
}


# ---------------------------------------------------------------------
# AS SEIS CONSULTAS. Sao funcoes Python comuns; viram ferramentas depois.
# Todas devolvem TEXTO, e nenhuma levanta excecao (licao do Encontro 6).
# ---------------------------------------------------------------------

# ---------------------------------------------------------------------------
# OS TIPOS ANOTADOS, e eles sao o conserto de 26/10/2026 (noite)
#
# O QUE ACONTECEU: na rodada com o agent-framework o agente chamou
# `status_do_servico(servico='ERP')`, levou "ERRO: servico ERP nao consta do
# catalogo", e REPORTOU O ERRO COMO DIAGNOSTICO, nos tres chamados.
#
# POR QUE: o framework monta o schema a partir da ASSINATURA. Com `servico: str`
# ele gera {"title": "Servico", "type": "string"} e mais nada. A lista de
# servicos validos existia so no `artesanal.py`, escrita a mao na description do
# parametro. Ou seja: as duas colunas do experimento nao davam a mesma
# informacao ao modelo, e a que faltava era justamente a que ele errou.
#
# O CONSERTO, e ele e de CONTROLE e nao de qualidade: as mesmas strings do
# `artesanal.py`, agora na assinatura, pelo unico caminho que o framework le.
# Repare que e `Annotated[str, Field(description=...)]` e NAO `Literal[...]`:
# o Literal viraria `enum` no schema, que PREVINE o valor errado -- e isso e o
# poka-yoke do argumento do Encontro 5, mais forte do que a prosa do artesanal.
# Igualar por cima seria trocar uma variavel solta por outra. O `Literal` fica
# como EXPERIMENTO separado, que e o seu lugar.
# ---------------------------------------------------------------------------
_Usuario = Annotated[str, Field(description="identificador do usuario, no formato nome.sobrenome")]
_Servico = Annotated[str, Field(description="nome do servico. Um de: portal-rh, erp-financeiro, vpn, email")]
_Horas = Annotated[str, Field(description="janela em horas, como texto. Exemplo: 24")]
_Termo = Annotated[str, Field(description="assunto do artigo. Um de: senha, bloqueio, vpn, perfil")]


def consultar_conta(usuario: _Usuario) -> str:
    """Devolve o estado da conta de um usuario: ativa ou bloqueada, os grupos
    de acesso que ela tem, e ha quanto tempo a senha foi trocada. Nao diz nada
    sobre o servico: para isso use status_do_servico."""
    c = CONTAS.get(usuario)
    if not c:
        return f"ERRO: usuario {usuario} nao consta do diretorio"
    extra = f"; motivo: {c['motivo']}" if c["motivo"] else ""
    return (f"{usuario}: conta {c['status']}{extra}; grupos {', '.join(c['grupos'])}; "
            f"senha trocada {c['troca_senha']}")


def status_do_servico(servico: _Servico) -> str:
    """Devolve o estado ATUAL de um servico corporativo e desde quando. Nao diz
    o que mudou nele: para isso use mudancas_recentes."""
    s = SERVICOS.get(servico)
    if not s:
        return f"ERRO: servico {servico} nao consta do catalogo"
    nota = f" -- {s['nota']}" if s["nota"] else ""
    return f"{servico}: {s['estado']} desde {s['desde']}{nota}"


def mudancas_recentes(servico: _Servico, horas: _Horas = "24") -> str:
    """Lista as mudancas aplicadas a um servico nas ultimas N horas:
    atualizacoes, revisoes de perfil de acesso, janelas de manutencao."""
    if servico not in MUDANCAS:
        return f"ERRO: servico {servico} nao consta do catalogo"
    try:
        janela = int(float(horas))
    except (TypeError, ValueError):
        return "ERRO: horas deve ser um numero, por exemplo 24"
    dentro = [f"{q} {d}" for q, d in MUDANCAS[servico]
              if int(q.strip("-h")) <= janela]
    if not dentro:
        return f"{servico}: 0 mudancas nas ultimas {janela}h"
    return (f"{servico}: {len(dentro)} mudanca(s) nas ultimas {janela}h -- "
            + "; ".join(dentro))


def chamados_semelhantes(servico: _Servico) -> str:
    """Lista os chamados abertos AGORA sobre o mesmo servico. Serve para saber
    se o problema atinge um usuario so ou varios."""
    if servico not in CHAMADOS_ABERTOS:
        return f"ERRO: servico {servico} nao consta do catalogo"
    lista = CHAMADOS_ABERTOS[servico]
    if not lista:
        return f"{servico}: 0 chamados abertos no momento"
    return f"{servico}: {len(lista)} chamado(s) aberto(s) -- " + "; ".join(lista)


def historico_do_usuario(usuario: _Usuario) -> str:
    """Lista os chamados anteriores de um usuario, com o servico de cada um."""
    h = HISTORICO.get(usuario)
    if h is None:
        return f"ERRO: usuario {usuario} nao consta do diretorio"
    if not h:
        return f"{usuario}: nenhum chamado anterior"
    return f"{usuario}: {len(h)} chamado(s) anterior(es) -- " + "; ".join(h)


def base_de_conhecimento(termo: _Termo) -> str:
    """Busca um artigo de procedimento por assunto. Assuntos validos: senha,
    bloqueio, vpn, perfil."""
    t = (termo or "").strip().lower()
    for chave, texto in BASE_CONHECIMENTO.items():
        if chave in t or t in chave:
            return texto
    return (f"nenhum artigo para '{termo}'. Assuntos disponiveis: "
            + ", ".join(BASE_CONHECIMENTO))
