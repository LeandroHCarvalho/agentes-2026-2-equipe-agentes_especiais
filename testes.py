#!/usr/bin/env python3
"""Os autotestes SEM REDE, agora como script em vez de celula.

E o sucessor do `verificar_notebook.py`: a mesma ideia na fase de repositorio.
Nenhuma chamada de API, nenhum token gasto, e roda em menos de um segundo.

    python testes.py

Rode ANTES de gastar cota. Se algo aqui falhar, o problema esta no mundo ou
nas ferramentas, e nenhuma execucao com chave real vai consertar isso.
"""
import sys

from vertice import dominio
from vertice.casos import CHAMADOS, VERDADE
from vertice.medicao import normalizar, aponta_a_causa

falhas = []


def conferir(nome, condicao, detalhe=""):
    if condicao:
        print(f"  ok   {nome}")
    else:
        print(f"  FALHA {nome}  {detalhe}")
        falhas.append(nome)


print("1. O MUNDO CONTEM A CAUSA DOS TRES CASOS")
for c in CHAMADOS:
    conta = dominio.consultar_conta(c["usuario"])
    conferir(f"{c['id']}: a conta de {c['usuario']} existe",
             not conta.startswith("ERRO"), conta)
    conferir(f"{c['id']}: a conta esta ATIVA (o caso nao e de bloqueio)",
             "ativa" in conta, conta)
    conferir(f"{c['id']}: {c['usuario']} NAO tem erp_leitura",
             "erp_leitura" not in conta, conta)

mud = dominio.mudancas_recentes("erp-financeiro", "24")
conferir("a revisao de perfis de -6h esta no mundo", "revisao de perfis" in mud, mud)
conferir("o servico esta NO AR (quem olhar so isso fecha sem causa)",
         "no ar" in dominio.status_do_servico("erp-financeiro"))

print()
print("2. A CAUSA NAO APARECE NAS DUAS PRIMEIRAS CONSULTAS")
duas = dominio.consultar_conta("diego.rocha") + " " + dominio.status_do_servico("erp-financeiro")
conferir("conta + servico NAO contem a causa", "revisao de perfis" not in duas, duas)
print("       e por isso que o C-103 precisa de uma TERCEIRA consulta.")

print()
print("3. ERRO QUE SE ANUNCIA (poka-yoke do retorno, Encontro 6)")
conferir("usuario inexistente devolve ERRO",
         dominio.consultar_conta("ninguem").startswith("ERRO"))
conferir("servico inexistente devolve ERRO",
         dominio.status_do_servico("inexistente").startswith("ERRO"))
conferir("horas invalido devolve ERRO",
         dominio.mudancas_recentes("erp-financeiro", "abc").startswith("ERRO"))

print()
print("4. O AVALIADOR, E O CONSERTO DA LIMITACAO 3 DO ENCONTRO 9")
conferir("acerta o termo simples",
         aponta_a_causa("a revisao de perfis removeu o seu grupo", "C-103"))
conferir("nao acusa quem nao aponta a causa",
         not aponta_a_causa("sua conta esta ativa e o servico no ar", "C-103"))
conferir("espaco inquebravel NAO reprova mais (era o falso negativo do Enc. 9)",
         normalizar("10 mm²") == "10 mm2",
         normalizar("10 mm²"))
conferir("hifen tipografico vira hifen comum",
         normalizar("D‑05") == "d-05", normalizar("D‑05"))

print()
print("5. AS FERRAMENTAS NAO DAO ORDEM DE USO (invariante dos Enc. 4, 5 e 6)")
try:
    from vertice import artesanal
    nomes = {t["function"]["name"] for t in artesanal.FERRAMENTAS}
    conferir("declaracao e registro batem", nomes == set(artesanal.REGISTRO),
             f"{nomes ^ set(artesanal.REGISTRO)}")
    for t in artesanal.FERRAMENTAS:
        d = t["function"]["description"].lower()
        conferir(f"{t['function']['name']} sem ordem de uso",
                 not any(p in d for p in artesanal._PROIBIDO))
except ImportError as e:
    conferir("importar o artesanal", False, str(e))

print()
print("6. OS TRES CASOS TEM A MESMA CAUSA, QUE E O QUE O TESTE EXPLORA")
causas = {VERDADE[c["id"]]["termos"][0] for c in CHAMADOS}
conferir("os tres compartilham o termo da causa", len(causas) == 1, str(causas))

print()
print("7. AS DUAS FORMAS DECLARAM A MESMA COISA AO MODELO")
print("   (o controle do experimento: se isto falhar, nenhuma comparacao vale)")
try:
    import json
    from agent_framework import FunctionTool
    from vertice import framework

    mao = {f["function"]["name"]: f["function"] for f in artesanal.FERRAMENTAS}
    for f in framework.FERRAMENTAS:
        t = FunctionTool(func=f, name=f.__name__,
                         description=(f.__doc__ or "").strip())
        spec = t.to_json_schema_spec()["function"]
        junta = lambda s: " ".join((s or "").split())
        conferir(f"{f.__name__}: description identica",
                 junta(spec["description"]) == junta(mao[f.__name__]["description"]),
                 f"\n    fw : {junta(spec['description'])}"
                 f"\n    mao: {junta(mao[f.__name__]['description'])}")
        d_fw = {k: junta(v.get("description"))
                for k, v in spec["parameters"]["properties"].items()}
        d_mao = {k: junta(v.get("description"))
                 for k, v in mao[f.__name__]["parameters"]["properties"].items()}
        conferir(f"{f.__name__}: descricao dos parametros identica",
                 d_fw == d_mao, f"\n    fw : {d_fw}\n    mao: {d_mao}")
except ImportError:
    print("  pulado: agent-framework nao esta instalado neste ambiente.")
    print("         O teste 7 e o que impede as duas colunas de divergirem em")
    print("         silencio. Rode-o antes de confiar numa comparacao.")

print()
print("=" * 62)
if falhas:
    print(f"{len(falhas)} FALHA(S): " + ", ".join(falhas))
    sys.exit(1)
print("TUDO PASSOU, e nenhum token foi gasto.")
print()
print("O que isto garante: o mundo contem a causa, os erros se anunciam, e a")
print("contabilidade do avaliador esta certa.")
print("O que NAO garante: o comportamento do modelo. Isso so aparece rodando")
print("com chave, e e o que o rodar_memoria.py faz.")
