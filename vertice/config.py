"""Chave, modelo e precos. Primeiro modulo que NAO roda no Colab.

Mudanca de ambiente do ADR-002: a chave sai dos Secrets do Colab e passa a
vir do ambiente ou de um .env local. O .env e a PRIMEIRA linha do .gitignore,
e versiona-lo e o acidente que abre o Encontro 15.
"""
import os
from pathlib import Path


def carregar_env(caminho: str = ".env") -> None:
    """Le um .env simples. Sem dependencia: sao oito linhas."""
    p = Path(caminho)
    if not p.exists():
        return
    for linha in p.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        nome, valor = linha.split("=", 1)
        os.environ.setdefault(nome.strip(), valor.strip().strip('"').strip("'"))


def obter_chave(nome: str = "GROQ_API_KEY") -> str:
    """Le a chave de onde ela estiver, nesta ordem: Secrets do Colab, ambiente,
    .env local.

    Os tres caminhos existem porque o MESMO modulo roda nos dois mundos: no
    VS Code depois da migracao, e no Colab para quem ficou no plano B. O codigo
    do agente nao muda; so muda de onde vem a chave.
    """
    try:                                   # 1. Secrets do Colab
        from google.colab import userdata
        valor = userdata.get(nome)
        if valor:
            return valor
    except Exception:
        pass

    carregar_env()                         # 2. .env local, 3. ambiente
    valor = os.getenv(nome)
    if not valor:
        raise RuntimeError(
            f"Defina {nome} nos Secrets do Colab, no ambiente, ou num arquivo "
            f".env na raiz do projeto (modelo em .env.example). "
            f"NUNCA versione o .env."
        )
    return valor


LLM_MODEL = "openai/gpt-oss-20b"
BASE_URL = "https://api.groq.com/openai/v1"

# Dolares por MILHAO de tokens, preco publicado do Groq.
PRECOS = {"openai/gpt-oss-20b": {"entrada": 0.075, "saida": 0.30},
          "openai/gpt-oss-120b": {"entrada": 0.150, "saida": 0.60}}
TPM = 8_000


def custo_usd(entrada: int, saida: int, modelo: str = None) -> float:
    p = PRECOS[modelo or LLM_MODEL]
    return (entrada * p["entrada"] + saida * p["saida"]) / 1_000_000
