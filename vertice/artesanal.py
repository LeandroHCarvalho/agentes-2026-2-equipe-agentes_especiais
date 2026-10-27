"""O laco do Encontro 3, em modulo. Trinta linhas, e elas funcionam.

Este arquivo existe por duas razoes:

  1. e o PLANO B do Encontro 10: se o agent-framework nao subir, o Lab 2 roda
     daqui, e a migracao de ambiente -- que e o que nao pode falhar -- segue;
  2. e o CONTROLE da comparacao: mesmo mundo, mesmas ferramentas, mesma
     instrucao. A unica variavel e quem orquestra.
"""
import json
import time

from openai import OpenAI

from . import dominio
from .config import BASE_URL, LLM_MODEL, obter_chave
from .casos import INSTRUCAO_RESPOSTA, INSTRUCAO_AGENTE

_cliente = None


def cliente() -> OpenAI:
    global _cliente
    if _cliente is None:
        _cliente = OpenAI(base_url=BASE_URL, api_key=obter_chave())
    return _cliente


def _p(nome, descricao, extras=None):
    props = {nome: {"type": "string", "description": descricao}}
    if extras:
        props.update(extras)
    return {"type": "object", "properties": props, "required": [nome]}


def _f(nome, descricao, parametros):
    return {"type": "function", "function": {
        "name": nome, "description": descricao, "parameters": parametros}}


_D_USUARIO = "identificador do usuario, no formato nome.sobrenome"
_D_SERVICO = "nome do servico. Um de: portal-rh, erp-financeiro, vpn, email"

FERRAMENTAS = [
    _f("consultar_conta",
       "Devolve o estado da conta de um usuario: ativa ou bloqueada, os grupos de "
       "acesso que ela tem, e ha quanto tempo a senha foi trocada. Nao diz nada "
       "sobre o servico: para isso use status_do_servico.",
       _p("usuario", _D_USUARIO)),
    _f("status_do_servico",
       "Devolve o estado ATUAL de um servico corporativo e desde quando. Nao diz o "
       "que mudou nele: para isso use mudancas_recentes.",
       _p("servico", _D_SERVICO)),
    _f("mudancas_recentes",
       "Lista as mudancas aplicadas a um servico nas ultimas N horas: atualizacoes, "
       "revisoes de perfil de acesso, janelas de manutencao.",
       _p("servico", _D_SERVICO,
          extras={"horas": {"type": "string",
                            "description": "janela em horas, como texto. Exemplo: 24"}})),
    _f("chamados_semelhantes",
       "Lista os chamados abertos AGORA sobre o mesmo servico. Serve para saber se o "
       "problema atinge um usuario so ou varios.",
       _p("servico", _D_SERVICO)),
    _f("historico_do_usuario",
       "Lista os chamados anteriores de um usuario, com o servico de cada um.",
       _p("usuario", _D_USUARIO)),
    _f("base_de_conhecimento",
       "Busca um artigo de procedimento por assunto. Assuntos validos: senha, "
       "bloqueio, vpn, perfil.",
       _p("termo", "assunto do artigo. Um de: senha, bloqueio, vpn, perfil")),
]

REGISTRO = {
    "consultar_conta": dominio.consultar_conta,
    "status_do_servico": dominio.status_do_servico,
    "mudancas_recentes": dominio.mudancas_recentes,
    "chamados_semelhantes": dominio.chamados_semelhantes,
    "historico_do_usuario": dominio.historico_do_usuario,
    "base_de_conhecimento": dominio.base_de_conhecimento,
}

# INVARIANTES dos Encontros 4, 5 e 6. Nao apague: o testes.py confere.
_PROIBIDO = ["sempre primeiro", "primeiro quando", "comece pela", "depois use",
             "na ordem", "em seguida use"]


def executar_ferramenta(nome: str, argumentos_json: str) -> str:
    """Roda a ferramenta pedida. Devolve SEMPRE texto, nunca excecao."""
    if nome not in REGISTRO:
        return (f"ERRO: ferramenta '{nome}' nao existe. "
                f"Disponiveis: {', '.join(REGISTRO)}")
    try:
        args = json.loads(argumentos_json or "{}")
    except json.JSONDecodeError as e:
        return f"ERRO: os argumentos nao sao JSON valido: {e}"
    if not isinstance(args, dict):
        return "ERRO: os argumentos precisam ser um objeto JSON"
    try:
        return REGISTRO[nome](**args)
    except TypeError as e:
        return f"ERRO: argumentos invalidos para {nome}: {e}"


def chamar(mensagens, tentativas: int = 5, max_tokens: int = 1200, **extra):
    """Tolerante a 429/503, como nos Encontros 4 a 9."""
    espera = 2.0
    for t in range(tentativas):
        try:
            return cliente().chat.completions.create(
                model=LLM_MODEL, messages=mensagens, temperature=0.0,
                max_tokens=max_tokens, **extra)
        except Exception as e:
            codigo = getattr(e, "status_code", None)
            if codigo not in (429, 500, 502, 503, 504) or t == tentativas - 1:
                raise
            print(f"  [{codigo}] esperando {espera:.0f}s (nao invalida a medicao)")
            time.sleep(espera)
            espera *= 2
    raise RuntimeError("todas as tentativas falharam")


def atender(chamado: dict, historico: list = None, max_voltas: int = 8,
            verboso: bool = True) -> dict:
    """O laco. `historico` e o que transforma isto em agente COM memoria:
    passe a mesma lista entre chamados e a conversa continua.
    """
    if historico is None:
        historico = [{"role": "system",
                      "content": INSTRUCAO_RESPOSTA + "\n\n" + INSTRUCAO_AGENTE}]
    historico.append({"role": "user", "content":
                      f"Chamado {chamado['id']}, aberto por {chamado['usuario']}:\n"
                      f"{chamado['texto']}"})

    entrada = saida = consultas = 0
    resposta = ""
    for volta in range(1, max_voltas + 1):
        r = chamar(historico, tools=FERRAMENTAS)
        msg = r.choices[0].message
        entrada += r.usage.prompt_tokens
        saida += r.usage.completion_tokens

        if not msg.tool_calls:
            resposta = msg.content or ""
            historico.append({"role": "assistant", "content": resposta})
            break

        historico.append({"role": "assistant", "content": msg.content,
                          "tool_calls": [{"id": tc.id, "type": "function",
                                          "function": {"name": tc.function.name,
                                                       "arguments": tc.function.arguments}}
                                         for tc in msg.tool_calls]})
        for tc in msg.tool_calls:
            resultado = executar_ferramenta(tc.function.name, tc.function.arguments)
            consultas += 1
            if verboso:
                print(f"    volta {volta}: {tc.function.name}({tc.function.arguments})")
            historico.append({"role": "tool", "tool_call_id": tc.id,
                              "content": resultado})
    else:
        resposta = "(bateu o teto de voltas sem responder)"

    return {"resposta": resposta, "consultas": consultas,
            "entrada": entrada, "saida": saida, "historico": historico}
