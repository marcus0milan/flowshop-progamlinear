"""
modelo_gurobi.py — Implementação no Gurobi do modelo da Pessoa 2
(Problema 5: Flowshop F3 | no-wait(M1,M2) | Cmax)

resolver()             -> formulação POSICIONAL (a do relatório, seção Modelagem)
resolver_disjuntivo()  -> formulação disjuntiva big-M (alternativa, para comparação)

Uso:
    python modelo_gurobi.py                      # valida no exemplo de 3 tarefas
    python modelo_gurobi.py instancia1.txt ...   # roda instâncias (limite 3600 s)
"""

import sys
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

from leitor_dados import carregar_exemplo_manual, carregar_instancia_txt

TEMPO_LIMITE = 3600  # exigido no enunciado


def cronograma_mais_cedo(sequencia, p):
    """Inícios S[j,m] mais cedo possíveis para uma sequência, respeitando o no-wait.
    O solver pode devolver operações com folgas desnecessárias (o Cmax não muda);
    isto as remove, para a tabela bater com o Gantt do relatório."""
    S = {}
    c1 = c2 = c3 = 0.0
    for j in sequencia:
        c1 = max(c1 + p[j, 1], c2)     # termina em M1 quando M2 estiver livre
        c2 = c1 + p[j, 2]              # sem espera entre M1 e M2
        c3 = max(c2, c3) + p[j, 3]
        S[j, 1], S[j, 2], S[j, 3] = c1 - p[j, 1], c1, c3 - p[j, 3]
    return S


def resolver(dados, tempo_limite=TEMPO_LIMITE, cortes=False, log=False):
    """Formulação posicional do relatório: x[j,k] e C[k,m]."""
    J = dados['tarefas']
    M = dados['maquinas']          # [1, 2, 3]
    p = dados['p']
    n = dados['n']
    K = range(1, n + 1)            # posições 1..n

    m = gp.Model("flowshop_nowait_M1M2_posicional")
    m.Params.OutputFlag = 1 if log else 0
    m.Params.TimeLimit = tempo_limite

    # Variáveis de decisão
    x = m.addVars(J, K, vtype=GRB.BINARY, name="x")           # tarefa j na posição k
    C = m.addVars(K, M, lb=0.0, vtype=GRB.CONTINUOUS, name="C")  # término da posição k na máquina m

    # P[k,m] = tempo, na máquina m, da tarefa colocada na posição k
    def P(k, mq):
        return gp.quicksum(p[j, mq] * x[j, k] for j in J)

    # (1) Objetivo: makespan = término da posição n na máquina 3
    m.setObjective(C[n, 3], GRB.MINIMIZE)

    # (2)-(3) Atribuição
    m.addConstrs((x.sum(j, '*') == 1 for j in J), name="atrib_tarefa")
    m.addConstrs((x.sum('*', k) == 1 for k in K), name="atrib_posicao")

    # (4)-(5) Máquina 1 (">=" permite atrasar o início em M1)
    m.addConstr(C[1, 1] >= P(1, 1), name="m1_inicio")
    m.addConstrs((C[k, 1] >= C[k - 1, 1] + P(k, 1) for k in K if k >= 2), name="m1")

    # (6) Sem espera entre M1 e M2 (igualdade)
    m.addConstrs((C[k, 2] == C[k, 1] + P(k, 2) for k in K), name="nowait")

    # (7) Capacidade da máquina 2
    m.addConstrs((C[k, 2] >= C[k - 1, 2] + P(k, 2) for k in K if k >= 2), name="m2")

    # (8)-(9) Máquina 3: rota (espera permitida) e capacidade
    m.addConstrs((C[k, 3] >= C[k, 2] + P(k, 3) for k in K), name="rota")
    m.addConstrs((C[k, 3] >= C[k - 1, 3] + P(k, 3) for k in K if k >= 2), name="m3")

    # Cortes válidos opcionais (não fazem parte do modelo do relatório)
    if cortes:
        for mq in M:
            antes = min(sum(p[j, t] for t in M if t < mq) for j in J)
            depois = min(sum(p[j, t] for t in M if t > mq) for j in J)
            carga = sum(p[j, mq] for j in J)
            m.addConstr(C[n, 3] >= antes + carga + depois, name=f"corte_{mq}")

    m.optimize()

    res = {
        'status': m.Status,
        'tempo': m.Runtime,
        'n': n,
        'nodes': m.NodeCount,
    }
    if m.SolCount > 0:
        pos = {j: next(k for k in K if x[j, k].X > 0.5) for j in J}
        sequencia = sorted(J, key=lambda j: pos[j])
        res.update({
            'obj': m.ObjVal,
            'bound': m.ObjBound,
            'gap': m.MIPGap,
            'sequencia': sequencia,
            'S': cronograma_mais_cedo(sequencia, p),
        })
    return res


def resolver_disjuntivo(dados, tempo_limite=TEMPO_LIMITE, cortes=True, log=False):
    """Formulação disjuntiva big-M original (mantida para comparação)."""
    J = dados['tarefas']
    M = dados['maquinas']
    p = dados['p']
    B = dados['big_M']

    m = gp.Model("flowshop_nowait_M1M2")
    m.Params.OutputFlag = 1 if log else 0
    m.Params.TimeLimit = tempo_limite

    # Variáveis
    S = m.addVars(J, M, lb=0.0, vtype=GRB.CONTINUOUS, name="S")
    pares = [(J[a], J[b]) for a in range(len(J)) for b in range(a + 1, len(J))]
    y = m.addVars(pares, vtype=GRB.BINARY, name="y")
    Cmax = m.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="Cmax")

    # Objetivo
    m.setObjective(Cmax, GRB.MINIMIZE)

    # No-wait entre M1 e M2 (igualdade)
    m.addConstrs((S[j, 2] == S[j, 1] + p[j, 1] for j in J), name="nowait")
    # Rota: M3 só após M2 (espera permitida)
    m.addConstrs((S[j, 3] >= S[j, 2] + p[j, 2] for j in J), name="rota")
    # Disjuntivas big-M, mesma ordem em todas as máquinas
    for (i, j) in pares:
        for k in M:
            m.addConstr(S[j, k] >= S[i, k] + p[i, k] - B * (1 - y[i, j]),
                        name=f"disj1_{i}_{j}_{k}")
            m.addConstr(S[i, k] >= S[j, k] + p[j, k] - B * y[i, j],
                        name=f"disj2_{i}_{j}_{k}")
    # Makespan
    m.addConstrs((Cmax >= S[j, 3] + p[j, 3] for j in J), name="cmax")

    # Cortes válidos (carga da máquina + menor antes + menor depois)
    if cortes:
        for k in M:
            antes = min(sum(p[j, t] for t in M if t < k) for j in J)
            depois = min(sum(p[j, t] for t in M if t > k) for j in J)
            carga = sum(p[j, k] for j in J)
            m.addConstr(Cmax >= antes + carga + depois, name=f"corte_{k}")

    m.optimize()

    res = {
        'status': m.Status,
        'tempo': m.Runtime,
        'n': dados['n'],
        'nodes': m.NodeCount,
    }
    if m.SolCount > 0:
        sequencia = sorted(J, key=lambda j: S[j, 1].X)
        res.update({
            'obj': m.ObjVal,
            'bound': m.ObjBound,
            'gap': m.MIPGap,
            'sequencia': sequencia,
            'S': {(j, k): S[j, k].X for j in J for k in M},
        })
    return res


def imprimir(res, dados):
    nomes = {GRB.OPTIMAL: "ÓTIMO", GRB.TIME_LIMIT: "LIMITE DE TEMPO",
             GRB.INFEASIBLE: "INVIÁVEL", GRB.INTERRUPTED: "INTERROMPIDO"}
    print(f"Status: {nomes.get(res['status'], res['status'])} | tempo: {res['tempo']:.2f}s")
    if 'obj' not in res:
        print("Nenhuma solução encontrada.")
        return
    print(f"Cmax = {res['obj']:.1f} | bound = {res['bound']:.1f} | gap = {100 * res['gap']:.2f}%")
    print("Sequência:", " -> ".join(res['sequencia']))
    p = dados['p']
    print(f"\n{'Tarefa':<8}{'M1':>12}{'M2':>12}{'M3':>12}")
    for j in res['sequencia']:
        cols = []
        for k in (1, 2, 3):
            s = res['S'][j, k]
            cols.append(f"[{s:.0f},{s + p[j, k]:.0f}]")
        print(f"{j:<8}{cols[0]:>12}{cols[1]:>12}{cols[2]:>12}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        dados = carregar_exemplo_manual()
        res = resolver(dados, log=False)
        imprimir(res, dados)
        ok = res.get('obj') is not None and abs(res['obj'] - 16.0) < 1e-6 and res['sequencia'] == ['J2', 'J3', 'J1']
        print("\nVALIDAÇÃO:", "OK (Cmax=16, J2->J3->J1)" if ok else "FALHOU")
    else:
        for caminho in sys.argv[1:]:
            dados = carregar_instancia_txt(caminho)
            print(f"\n=== {Path(caminho).name} (n={dados['n']}) ===")
            imprimir(resolver(dados), dados)
