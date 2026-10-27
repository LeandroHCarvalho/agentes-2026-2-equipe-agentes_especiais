"""O MESMO agente, agora no Microsoft Agent Framework.

Compare este arquivo com o artesanal.py lado a lado. O mundo e o mesmo, as
seis consultas sao as mesmas, a instrucao e a mesma. O que sumiu foi o LACO:
as trinta linhas do Encontro 3 viraram `agente.run(...)`.

Tres coisas para reparar quando este arquivo subir na tela:

  1. a ferramenta e uma FUNCAO PYTHON COMUM, e a docstring dela vira a
     `description`. Todo o criterio da clinica do Encontro 4 continua valendo,
     no mesmo lugar de sempre. O framework tira de voce o SCHEMA, nao a decisao;
  2. a `base_url` do Groq e aceita, entao o provedor NAO muda: e o mesmo modelo
     dos Encontros 4 a 9, e a variavel do experimento continua sendo a forma;
  3. a memoria e uma SESSAO. Criar uma e passa-la em cada run e a diferenca
     inteira entre lembrar e nao lembrar.

Versao conferida em 26/10/2026: agent-framework 1.23.0. A API da 1.10.x que o
ADR-003 fixou NAO vale mais (nao existe `ChatAgent`).
"""
import functools
import inspect
import time

from . import dominio
from .config import BASE_URL, LLM_MODEL, obter_chave
from .casos import INSTRUCAO_RESPOSTA, INSTRUCAO_AGENTE

_CHAMADAS = {"n": 0, "trilha": []}
_VERBOSO = {"on": True}


def _argumentos(a, k) -> str:
    """So para imprimir. O framework chama por nome, entao `k` e o que importa."""
    partes = [repr(x) for x in a] + [f"{nome}={valor!r}" for nome, valor in k.items()]
    return ", ".join(partes)


def _contado(f):
    """Envolve a consulta para contar E REGISTRAR as invocacoes.

    POR QUE NAO LER DA RESPOSTA: o formato dos campos de uso e de conteudo muda
    entre versoes da biblioteca, e na primeira execucao em sala a contagem saiu
    ZERADA por causa disso. Contar na porta da ferramenta nao depende de versao
    nenhuma: se a funcao rodou, foi uma consulta.

    POR QUE TAMBEM IMPRIMIR: o laco artesanal mostra `volta N: ferramenta(args)`
    a cada passo, e essa trilha e o rastro que as limitacoes 1 e 3 usam. Do lado
    do framework o laco e dele, entao nao ha volta para numerar -- mas a PORTA DA
    FERRAMENTA e nossa, e por ela passa a mesma informacao. Sem isto, as duas
    colunas nao sao igualmente auditaveis, e comparar o que se ve de um lado com
    o que nao se ve do outro nao e comparacao.

    `functools.wraps` preserva nome, docstring e assinatura, que e o que o
    framework le para montar o schema. A description continua sendo a docstring.
    """
    @functools.wraps(f)
    def embrulho(*a, **k):
        _CHAMADAS["n"] += 1
        ordem = len(_CHAMADAS["trilha"]) + 1
        _CHAMADAS["trilha"].append((f.__name__, _argumentos(a, k)))
        if _VERBOSO["on"]:
            print(f"    consulta {ordem}: {f.__name__}({_argumentos(a, k)})")
        return f(*a, **k)
    return embrulho


FERRAMENTAS = [
    _contado(dominio.consultar_conta),
    _contado(dominio.status_do_servico),
    _contado(dominio.mudancas_recentes),
    _contado(dominio.chamados_semelhantes),
    _contado(dominio.historico_do_usuario),
    _contado(dominio.base_de_conhecimento),
]


def construir():
    """Devolve o agente. Importa a biblioteca aqui dentro, de proposito:
    assim o testes.py e o artesanal.py rodam sem ela instalada.
    """
    from agent_framework import Agent
    # OpenAIChatCompletionClient, e NAO OpenAIChatClient. A diferenca derrubou
    # a primeira execucao em sala, em 26/10/2026:
    #
    #   OpenAIChatClient           -> fala a Responses API (/responses)
    #   OpenAIChatCompletionClient -> fala /chat/completions
    #
    # O Groq implementa /chat/completions e NAO a Responses API. Com o primeiro,
    # a chamada volta 400: "Field 'include' is not supported".
    #
    # Guarde este caso: o nome generico aponta para o padrao NOVO da biblioteca,
    # e o padrao novo nao e o que o seu provedor fala. E exatamente o que o
    # cartao "o que ele cobra" diz -- o framework escondeu uma decisao atras de
    # um padrao, e a conta chegou na primeira execucao.
    from agent_framework.openai import OpenAIChatCompletionClient

    cliente = OpenAIChatCompletionClient(model=LLM_MODEL, api_key=obter_chave(),
                                         base_url=BASE_URL)
    # default_options: CONTROLE DO EXPERIMENTO, e nao ajuste fino.
    #
    # Isto faltava ate 26/10/2026, e a falta DERRUBOU a terceira execucao em
    # sala. O artesanal.py chama a API com temperature=0.0 e max_tokens=1200
    # (ver `chamar`, linha 110). Esta funcao nao passava nada, entao a coluna do
    # framework rodava na temperatura PADRAO do provedor.
    #
    # Consequencia, e e a grave: as duas formas diferiam por MAIS do que a
    # forma. Qualquer numero comparado entre elas estava comparando duas coisas
    # ao mesmo tempo. Variavel nao controlada nao e detalhe de implementacao.
    #
    # Consequencia secundaria, que foi o sintoma visivel: com temperatura alta o
    # gpt-oss-20b produziu uma chamada de ferramenta que o parser do Groq nao
    # conseguiu interpretar, e a resposta foi 400 `output_parse_failed`.
    #
    # Conferido na 1.23.0: `default_options` e um ChatOptions (TypedDict) com,
    # entre outras, as chaves temperature, max_tokens, seed e top_p.
    return Agent(client=cliente, name="vertice",
                 instructions=INSTRUCAO_RESPOSTA + "\n\n" + INSTRUCAO_AGENTE,
                 tools=FERRAMENTAS,
                 default_options={"temperature": 0.0, "max_tokens": 1200})


_LACO = None


def _laco():
    """Um unico laco de eventos, vivo pelo processo inteiro.

    POR QUE ASSIM, e isto derrubou a segunda execucao em sala, em 26/10/2026:
    a versao anterior abria um `asyncio.run` por chamada, em uma thread nova.
    Funcionava na primeira e quebrava na segunda com "Event loop is closed",
    porque o cliente HTTP guarda um pool de conexoes preso ao laco que o criou.
    Fechado o laco, o pool morre junto, e a chamada seguinte tenta reusar
    conexao de um laco que nao existe mais.

    A correcao e manter UM laco rodando numa thread de fundo e submeter as
    corrotinas a ele. Funciona dentro e fora de notebook, e o laco do notebook
    nao e tocado.
    """
    global _LACO
    if _LACO is None or _LACO.is_closed():
        import asyncio
        import threading
        _LACO = asyncio.new_event_loop()
        threading.Thread(target=_LACO.run_forever, daemon=True).start()
    return _LACO


async def _aguardar(aguardavel):
    return await aguardavel


def _resolver(valor):
    """Aceita run sincrono ou assincrono, dentro ou fora de notebook."""
    if not inspect.isawaitable(valor):
        return valor
    import asyncio
    return asyncio.run_coroutine_threadsafe(_aguardar(valor), _laco()).result()


def _tokens(resposta) -> tuple:
    """Tira entrada e saida do `usage_details`, que e um DICIONARIO.

    Conferido na 1.23.0: o cliente preenche as chaves input_token_count,
    output_token_count e total_token_count. Lido com .get para nao quebrar se
    mudarem de nome -- nesse caso a tabela mostra zero, que e honesto.
    """
    uso = getattr(resposta, "usage_details", None) or {}
    if not hasattr(uso, "get"):
        return 0, 0
    return int(uso.get("input_token_count") or 0), int(uso.get("output_token_count") or 0)


def _e_falha_de_parser(erro) -> bool:
    """O 400 `output_parse_failed` do Groq.

    O provedor recebeu do modelo um texto que ele nao conseguiu transformar em
    chamada de ferramenta, e devolveu 400 com `failed_generation` VAZIO, isto e,
    sem mostrar o texto que falhou. E falha de GERACAO, nao de pedido: o mesmo
    pedido, repetido, costuma passar. Por isso se repete, e por isso a repeticao
    fica registrada: uma rodada que precisou de duas tentativas nao e igual a
    uma que passou de primeira, e quem le a tabela tem o direito de saber.
    """
    return "output_parse_failed" in str(erro)


def atender(agente, chamado: dict, sessao=None, verboso: bool = True,
            tentativas: int = 3) -> dict:
    """Uma linha de verdade, e o resto e contabilidade.

    `sessao` e a memoria: passe a MESMA sessao entre chamados e o agente
    lembra; passe None e cada chamado comeca do zero.

    `tentativas` existe pelo mesmo motivo que o `chamar(..., tentativas=5)` do
    artesanal.py: o provedor falha, as vezes, por conta propria. A diferenca e
    que la se repete 429 e 503, e aqui se repete tambem o 400 do parser --
    porque neste caso o 400 NAO quer dizer "seu pedido esta errado".
    """
    pedido = (f"Chamado {chamado['id']}, aberto por {chamado['usuario']}:\n"
              f"{chamado['texto']}")
    _VERBOSO["on"] = verboso
    espera = 5.0
    for t in range(tentativas):
        antes = _CHAMADAS["n"]
        marca = len(_CHAMADAS["trilha"])
        try:
            r = _resolver(agente.run(pedido, session=sessao) if sessao is not None
                          else agente.run(pedido))
        except Exception as e:
            if not _e_falha_de_parser(e) or t == tentativas - 1:
                if _e_falha_de_parser(e):
                    # Nao derruba a medicao inteira por causa de um chamado. A
                    # linha entra ZERADA e marcada, que e honesto: a tabela
                    # mostra que faltou, em vez de mostrar um numero inventado.
                    if verboso:
                        print(f"    FALHOU apos {tentativas} tentativas "
                              f"(400 output_parse_failed)")
                    return {"resposta": "[FALHOU: 400 output_parse_failed]",
                            "consultas": 0, "entrada": 0, "saida": 0,
                            "falhou": True, "repeticoes": t,
                            "trilha": _CHAMADAS["trilha"][marca:]}
                raise
            if verboso:
                print(f"    [400 output_parse_failed] tentativa {t + 1} de "
                      f"{tentativas}, esperando {espera:.0f}s")
            # A tentativa que falhou PODE ter rodado ferramentas antes de quebrar.
            # Descarta a trilha e a contagem dela, senao a repeticao soma duas
            # vezes o que o modelo pediu uma vez.
            del _CHAMADAS["trilha"][marca:]
            _CHAMADAS["n"] = antes
            time.sleep(espera)
            espera *= 2
            continue

        consultas = _CHAMADAS["n"] - antes
        entrada, saida = _tokens(r)
        if verboso:
            repetiu = f"  (apos {t} repeticao[oes])" if t else ""
            print(f"    consultas: {consultas}  tokens: {entrada}+{saida}{repetiu}")
        return {"resposta": str(getattr(r, "text", None) or r),
                "consultas": consultas, "entrada": entrada, "saida": saida,
                "falhou": False, "repeticoes": t,
                "trilha": _CHAMADAS["trilha"][marca:]}
