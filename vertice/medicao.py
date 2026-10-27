"""Contagem, avaliacao e tabela. A mesma dos Encontros 5, 6, 7 e 9,
agora como modulo em vez de celula.
"""
import re
import unicodedata

from .config import custo_usd
from .casos import VERDADE


def normalizar(t: str) -> str:
    """NFKD junta duas coisas: tira acento E iguala as variantes de espaco e
    de hifen que o modelo escreve. Sem isso, '10 mm' nao casa com '10<NBSP>mm'.

    Esta funcao e o conserto da limitacao 3 do Encontro 9, e ele foi conferido:
    com NFD, quatro variantes de espaco reprovavam uma resposta certa.
    """
    t = unicodedata.normalize("NFKD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    for h in ("‐", "‑", "–", "—"):
        t = t.replace(h, "-")
    return re.sub(r"\s+", " ", t).strip()


def aponta_a_causa(resposta: str, chamado_id: str) -> bool:
    """A resposta menciona algum termo da causa verdadeira?

    E sugestao, nao veredito: o Encontro 9 produziu um falso positivo E um
    falso negativo desta mesma coluna, em rodadas reais. Leia as respostas.
    """
    texto = normalizar(resposta)
    return any(normalizar(a) in texto for a in VERDADE[chamado_id]["termos"])


class Registro:
    """Acumula o que cada execucao gastou, para a tabela do fim."""

    def __init__(self, rotulo: str):
        self.rotulo = rotulo
        self.linhas = []

    def anotar(self, chamado_id, consultas, entrada, saida, resposta):
        self.linhas.append({
            "id": chamado_id, "consultas": consultas,
            "entrada": entrada, "saida": saida,
            "custo": custo_usd(entrada, saida),
            "causa": aponta_a_causa(resposta, chamado_id),
            "resposta": resposta,
        })
        return self.linhas[-1]

    @property
    def consultas(self):
        return sum(l["consultas"] for l in self.linhas)

    @property
    def custo(self):
        return sum(l["custo"] for l in self.linhas)

    @property
    def entrada(self):
        return sum(l["entrada"] for l in self.linhas)

    @property
    def saida(self):
        return sum(l["saida"] for l in self.linhas)

    @property
    def acertos(self):
        return sum(1 for l in self.linhas if l["causa"])


def grid(*registros) -> None:
    """A tabela do encontro. Leve-a ao quadro."""
    print(f"{'caso':>7}", end="")
    for r in registros:
        print(f" | {r.rotulo:>28}", end="")
    print()
    print(f"{'':>7}", end="")
    for _ in registros:
        print(f" | {'consultas  tokens      US$':>28}", end="")
    print()
    print("-" * (7 + 31 * len(registros)))
    for i, l0 in enumerate(registros[0].linhas):
        print(f"{l0['id']:>7}", end="")
        for r in registros:
            l = r.linhas[i]
            print(f" | {l['consultas']:>8}  {l['entrada'] + l['saida']:>6}  "
                  f"{l['custo']:>9.6f}", end="")
        print()
    print("-" * (7 + 31 * len(registros)))
    print(f"{'total':>7}", end="")
    for r in registros:
        print(f" | {r.consultas:>8}  {r.entrada + r.saida:>6}  {r.custo:>9.6f}", end="")
    print()
    print(f"{'causa':>7}", end="")
    for r in registros:
        print(f" | {f'{r.acertos}/{len(r.linhas)} apontadas':>28}", end="")
    print()


def respostas(*registros, largura: int = 78) -> None:
    """Imprime o TEXTO que cada lado gerou, chamado por chamado.

    POR QUE ISTO EXISTE, e nao e enfeite: a coluna `causa` da tabela e feita por
    `aponta_a_causa`, que e casamento de termo -- e no Encontro 9 essa mesma
    coluna produziu um falso positivo E um falso negativo em rodadas reais. A
    propria docstring dela diz: e sugestao, nao veredito, LEIA AS RESPOSTAS.

    Ate agora a tabela saia sem elas, e quem quisesse conferir tinha de rodar de
    novo. Isto e o conserto: o veredito automatico e o texto que o produziu,
    lado a lado, no mesmo lugar.
    """
    print()
    print("=" * 70)
    print("AS RESPOSTAS, que e o que a coluna 'causa' tentou julgar:")
    for i, l0 in enumerate(registros[0].linhas):
        print()
        print(f"--- {l0['id']} " + "-" * (70 - len(l0['id']) - 5))
        for r in registros:
            l = r.linhas[i]
            veredito = "APONTA a causa" if l["causa"] else "NAO aponta"
            print(f"  [{r.rotulo}]  {l['consultas']} consulta(s), {veredito}")
            texto = " ".join((l["resposta"] or "(vazio)").split())
            while texto:
                print(f"      {texto[:largura]}")
                texto = texto[largura:]
    print()
    print("Confira voce mesmo. Se o veredito automatico discordar do texto, o")
    print("defeito e do avaliador, e isso tambem e um resultado do encontro.")


def leitura(sem, com) -> None:
    """As tres perguntas que a tabela responde, e a terceira e a que importa."""
    def razao(a, b):
        return f"{a / b:.2f}x" if b else "n/a"

    print()
    print("=" * 70)
    print("A LEITURA, e ela tem tres perguntas:")
    print()
    print(f"  1. consultas:  {sem.consultas} sem memoria  ->  {com.consultas} com memoria"
          f"   ({razao(com.consultas, sem.consultas)})")
    print(f"  2. custo:      US$ {sem.custo:.6f}  ->  US$ {com.custo:.6f}"
          f"   ({razao(com.custo, sem.custo)})")
    print(f"  3. entrada:    {sem.entrada} tokens  ->  {com.entrada} tokens"
          f"   ({razao(com.entrada, sem.entrada)})")
    print()
    print("A terceira explica a segunda. Memoria e CONTEXTO CARREGADO: cada")
    print("chamado seguinte leva a conversa inteira junto, entao a entrada")
    print("cresce. Se as consultas cairem muito e o custo cair pouco, voce")
    print("acabou de medir o preco da memoria -- e ele nao e zero.")
    print()
    print("E confira a coluna 'causa' nas duas: economizar consulta so vale")
    print("se a resposta continuar certa.")
