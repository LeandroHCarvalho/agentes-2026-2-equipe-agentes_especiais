#!/usr/bin/env python3
"""Separa VARIANCIA de MEMORIA, que a rodada de 26/10 nao conseguiu separar.

POR QUE ISTO EXISTE
-------------------
Na primeira execucao real, o C-103 -- que e o PRIMEIRO chamado, e portanto
nao tem memoria nenhuma para usar -- se comportou diferente nas duas colunas:

    sem memoria:  status_do_servico -> consultar_conta -> chamados_semelhantes
    com memoria:  status_do_servico -> mudancas_recentes

As mensagens enviadas eram IDENTICAS nos dois casos, com temperature=0.0.
A diferenca foi do modelo, nao do desenho. E foi ela que produziu o placar
de 0/3 contra 3/3: a coluna da direita achou a causa por sorte na primeira
jogada e carregou dali em diante.

Com n=1 por celula, nao da para dizer o que e memoria e o que e variacao.
Este script roda cada lado N vezes e mostra a dispersao.

USO
---
    python rodar_variancia.py            # 3 repeticoes de cada lado
    python rodar_variancia.py 5          # 5 repeticoes

CUSTO
-----
Cada repeticao de cada lado sao 3 chamados. Com N=3 sao 18 atendimentos.
A pausa entre chamados respeita o TPM. Reserve uns 15 minutos para N=3.
"""
import statistics as st
import sys
import time

from vertice import artesanal
from vertice.casos import CHAMADOS, INSTRUCAO_RESPOSTA, INSTRUCAO_AGENTE
from vertice.config import custo_usd
from vertice.medicao import aponta_a_causa

PAUSA = 20


def uma_rodada(com_memoria: bool) -> dict:
    """Atende os tres chamados uma vez. Devolve o agregado da rodada."""
    historico = ([{"role": "system",
                   "content": INSTRUCAO_RESPOSTA + "\n\n" + INSTRUCAO_AGENTE}]
                 if com_memoria else None)
    consultas = entrada = saida = acertos = 0
    ferramentas_usadas = set()

    for i, c in enumerate(CHAMADOS):
        r = artesanal.atender(c, historico=historico, verboso=False)
        if com_memoria:
            historico = r["historico"]
        consultas += r["consultas"]
        entrada += r["entrada"]
        saida += r["saida"]
        acertos += bool(aponta_a_causa(r["resposta"], c["id"]))
        if i < len(CHAMADOS) - 1:
            time.sleep(PAUSA)

    return {"consultas": consultas, "entrada": entrada, "saida": saida,
            "custo": custo_usd(entrada, saida), "acertos": acertos}


def resumir(nome: str, rodadas: list) -> None:
    def disp(campo):
        v = [r[campo] for r in rodadas]
        if len(v) < 2:
            return f"{v[0]}"
        return f"{st.mean(v):.4g}  (min {min(v):.4g}, max {max(v):.4g})"

    print(f"\n{nome}")
    print(f"  consultas : {disp('consultas')}")
    print(f"  custo US$ : {disp('custo')}")
    print(f"  acertos   : {[r['acertos'] for r in rodadas]}  de "
          f"{len(CHAMADOS)} por rodada")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 3
    print("=" * 70)
    print(f"VARIANCIA x MEMORIA -- {n} repeticoes de cada lado")
    print("=" * 70)

    sem, com = [], []
    for k in range(n):
        print(f"\n--- repeticao {k + 1}/{n} ---")
        print("  sem memoria...", flush=True)
        sem.append(uma_rodada(False))
        time.sleep(PAUSA)
        print("  com memoria...", flush=True)
        com.append(uma_rodada(True))
        if k < n - 1:
            time.sleep(PAUSA)

    print("\n" + "=" * 70)
    resumir("SEM MEMORIA", sem)
    resumir("COM MEMORIA", com)

    print("\n" + "=" * 70)
    print("COMO LER, e a ordem importa:")
    print()
    print("  1. Olhe a DISPERSAO de cada lado, antes de comparar os lados.")
    print("     Se o min e o max de um lado se sobrepoem aos do outro, a")
    print("     diferenca que voce viu com n=1 era variacao, nao memoria.")
    print()
    print("  2. So depois compare as medias.")
    print()
    print("  3. E compare o CUSTO so entre rodadas com o MESMO numero de")
    print("     acertos. O custo de uma resposta errada e desperdicio, nao")
    print("     economia -- e foi exatamente o erro que a tabela de 26/10")
    print("     convidava a cometer.")
    print()
    print("Temperatura zero reduz a variacao. Nao a elimina. Esta e a")
    print("demonstracao disso, com o seu proprio dinheiro.")
