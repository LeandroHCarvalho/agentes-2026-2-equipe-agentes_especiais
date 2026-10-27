#!/usr/bin/env python3
"""O TESTE DE MEMORIA do Encontro 10.

Tres chamados com A MESMA CAUSA, atendidos em sequencia, de dois jeitos:

    SEM memoria  cada chamado comeca do zero e reapura tudo
    COM memoria  a conversa continua, e o que ja foi apurado esta la

Uso:
    python rodar_memoria.py              # artesanal (sempre funciona)
    python rodar_memoria.py --framework  # agent-framework

O que se mede e o que importa: consultas, tokens e dolares, com e sem.
"""
import sys
import time

from vertice.casos import CHAMADOS, INSTRUCAO_RESPOSTA, INSTRUCAO_AGENTE
from vertice.medicao import Registro, grid, leitura, respostas

PAUSA = 20          # TPM de 8.000: contexto cresce, entao espace as chamadas


def rodar_artesanal():
    from vertice import artesanal
    sem = Registro("SEM memoria")
    com = Registro("COM memoria")

    print("### SEM MEMORIA -- cada chamado do zero")
    for i, c in enumerate(CHAMADOS):
        print(f"  {c['id']} ({c['usuario']})")
        r = artesanal.atender(c, historico=None)
        sem.anotar(c["id"], r["consultas"], r["entrada"], r["saida"], r["resposta"])
        if i < len(CHAMADOS) - 1:
            time.sleep(PAUSA)

    print()
    print("### COM MEMORIA -- a mesma conversa, do comeco ao fim")
    historico = [{"role": "system",
                  "content": INSTRUCAO_RESPOSTA + "\n\n" + INSTRUCAO_AGENTE}]
    time.sleep(PAUSA)
    for i, c in enumerate(CHAMADOS):
        print(f"  {c['id']} ({c['usuario']})")
        r = artesanal.atender(c, historico=historico)
        historico = r["historico"]
        com.anotar(c["id"], r["consultas"], r["entrada"], r["saida"], r["resposta"])
        if i < len(CHAMADOS) - 1:
            time.sleep(PAUSA)
    return sem, com


def rodar_framework():
    from vertice import framework
    agente = framework.construir()
    sem = Registro("SEM memoria")
    com = Registro("COM memoria")

    print("### SEM MEMORIA -- sem sessao, cada run isolado")
    for i, c in enumerate(CHAMADOS):
        print(f"  {c['id']} ({c['usuario']})")
        r = framework.atender(agente, c, sessao=None)
        sem.anotar(c["id"], r["consultas"], r["entrada"], r["saida"], r["resposta"])
        if i < len(CHAMADOS) - 1:
            time.sleep(PAUSA)

    print()
    print("### COM MEMORIA -- uma sessao so, passada nos tres")
    sessao = agente.create_session()
    time.sleep(PAUSA)
    for i, c in enumerate(CHAMADOS):
        print(f"  {c['id']} ({c['usuario']})")
        r = framework.atender(agente, c, sessao=sessao)
        com.anotar(c["id"], r["consultas"], r["entrada"], r["saida"], r["resposta"])
        if i < len(CHAMADOS) - 1:
            time.sleep(PAUSA)
    return sem, com


if __name__ == "__main__":
    usar_fw = "--framework" in sys.argv
    print("=" * 70)
    print("TESTE DE MEMORIA -- Encontro 10")
    print("forma:", "agent-framework" if usar_fw else "laco artesanal")
    print("=" * 70)
    print()
    sem, com = rodar_framework() if usar_fw else rodar_artesanal()
    print()
    print("=" * 70)
    grid(sem, com)
    leitura(sem, com)
    respostas(sem, com)
    print()
    print("Previsao registrada no PLANO_DE_AULA antes de rodar: as consultas")
    print("caem muito, e o custo NAO cai na mesma proporcao. Confira.")
