# Mesa de servico da Vertice — Encontro 10

O mesmo problema do Encontro 7, agora fora do notebook.

## Como rodar

```
python -m venv .venv && .venv\Scripts\activate     # Windows
pip install -r requirements.txt
copy .env.example .env                             # e preencha a chave
python testes.py                                   # nao gasta token
python rodar_memoria.py                            # laco artesanal
python rodar_memoria.py --framework                # agent-framework
```

No Linux ou no Mac, troque `.venv\Scripts\activate` por `source .venv/bin/activate`
e `copy` por `cp`.

## O que tem aqui

| Arquivo | O que é |
|---|---|
| `vertice/dominio.py` | o mundo sintético e as seis consultas |
| `vertice/casos.py` | C-103, C-106 e C-108, e a verdade de terra |
| `vertice/artesanal.py` | o laço do Encontro 3, em módulo |
| `vertice/framework.py` | o mesmo agente no Microsoft Agent Framework |
| `vertice/medicao.py` | consultas, tokens, dólares e a tabela |
| `testes.py` | os autotestes sem rede |
| `rodar_memoria.py` | o teste de memória, com e sem |

## A regra que não muda de ambiente

**`python testes.py` antes de qualquer coisa que gaste token.** Ele roda em menos
de um segundo e pega o erro mais caro do projeto: o mundo não conter a causa.
