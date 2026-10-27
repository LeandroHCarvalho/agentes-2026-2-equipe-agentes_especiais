"""Os tres chamados do teste de memoria, e a verdade de terra de cada um.

Os tres tem A MESMA CAUSA: a revisao de perfis de -6h removeu o grupo
erp_leitura de 12 usuarios, e esses tres estao entre eles.

E isso que faz deles o teste de memoria: quem ja apurou a causa no primeiro
nao precisa apurar de novo no segundo e no terceiro. Quem nao lembra, refaz
as quatro consultas tres vezes.
"""

CHAMADOS = [
    {"id": "C-103", "usuario": "diego.rocha",
     "texto": "Nao consigo acessar o ERP. Ontem funcionava normal."},
    {"id": "C-106", "usuario": "elena.matos",
     "texto": "Desde hoje de manha o ERP nao abre para mim."},
    {"id": "C-108", "usuario": "joao.prado",
     "texto": "Perdi o acesso ao ERP financeiro, nao sei por que."},
]

VERDADE = {
    "C-103": {"causa": "a revisao de perfis de -6h removeu o grupo erp_leitura",
              "termos": ["perfil", "perfis", "grupo", "permiss", "revisao"],
              "encaminhamento": "pedir a devolucao do grupo ao gestor (KB-021)"},
    "C-106": {"causa": "a mesma revisao de perfis de -6h",
              "termos": ["perfil", "perfis", "grupo", "permiss", "revisao"],
              "encaminhamento": "pedir a devolucao do grupo ao gestor (KB-021)"},
    "C-108": {"causa": "a mesma revisao de perfis de -6h",
              "termos": ["perfil", "perfis", "grupo", "permiss", "revisao"],
              "encaminhamento": "pedir a devolucao do grupo ao gestor (KB-021)"},
}

INSTRUCAO_RESPOSTA = """Voce atende a mesa de servico interna da empresa Vertice.

Responda ao usuario em portugues, em ate seis linhas. A resposta PRECISA dizer,
sempre: qual e a causa provavel do problema, a evidencia que sustenta essa causa,
e o que o usuario deve fazer agora.

Nunca invente estado de conta, de servico ou de mudanca. Se a evidencia que voce
tem nao sustenta uma causa, diga que nao foi possivel determinar a causa e o que
falta apurar. Dizer 'nao sei' e melhor do que arriscar."""

INSTRUCAO_AGENTE = """Use as ferramentas disponiveis para apurar antes de responder.
Pare de chamar ferramentas quando tiver evidencia suficiente para apontar uma causa."""
