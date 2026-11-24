"""
modelo_gurobi.py — Implementação em Gurobi do modelo posicional do relatório
(Problema 5: Flowshop F3 | no-wait(M1 -> M2), prmu | Cmax)

Uso:
    python modelo_gurobi.py                      # valida nos exemplos de 3 e 4 tarefas do relatório
    python modelo_gurobi.py instancia1.txt ...   # roda instâncias com limite de 3600 s
"""

import sys
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

from leitor_dados import carregar_exemplo_manual, carregar_instancia_txt

TEMPO_LIMITE = 3600  # limite de 1 hora exigido no enunciado


def cronograma_mais_cedo(sequencia, p):
    """Recalcula os inícios S[j, m] mais cedo possíveis respeitando o no-wait entre M1 e M2.
    Remove folgas arbitrárias devolvidas pelo solver sem alterar Cmax, alinhando a saída ao Gantt."""
    S = {}
    c1 = c2 = c3 = 0.0
    for j in sequencia:
        c1 = max(c1 + p[j, 1], c2)     # termina em M1 quando M2 estiver livre
        c2 = c1 + p[j, 2]              # sem espera entre M1 e M2
        c3 = max(c2, c3) + p[j, 3]     # espera permitida entre M2 e M3
        S[j, 1], S[j, 2], S[j, 3] = c1 - p[j, 1], c1, c3 - p[j, 3]
    return S


def carregar_exemplo_4_tarefas():
    """Instância didática de 4 tarefas do gráfico de Gantt do relatório (Cmax = 21)."""
    tarefas = ['T1', 'T2', 'T3', 'T4']
    maquinas = [1, 2, 3]
    p = {
        ('T1', 1): 3.0, ('T1', 2): 6.0, ('T1', 3): 2.0,
        ('T2', 1): 5.0, ('T2', 2): 2.0, ('T2', 3): 4.0,
        ('T3', 1): 2.0, ('T3', 2): 4.0, ('T3', 3): 5.0,
        ('T4', 1): 4.0, ('T4', 2): 3.0, ('T4', 3): 3.0,
    }
    return {
        'tarefas': tarefas,
        'maquinas': maquinas,
        'p': p,
        'n': len(tarefas),
    }


def resolver(dados, tempo_limite=TEMPO_LIMITE, log=False):
    """Formulação posicional sem big-M adotada na Seção 2 do relatório."""
    J = dados['tarefas']
    M = dados['maquinas']          # [1, 2, 3]
    p = dados['p']
    n = dados['n']
    K = range(1, n + 1)            # posições 1..n

    modelo = gp.Model("flowshop_nowait_M1M2_posicional")
    modelo.Params.OutputFlag = 1 if log else 0
    modelo.Params.TimeLimit = tempo_limite

    # Variáveis de decisão (Domínio: x[j,k] binária, C[k,m] >= 0)
    x = modelo.addVars(J, K, vtype=GRB.BINARY, name="x")
    C = modelo.addVars(K, M, lb=0.0, vtype=GRB.CONTINUOUS, name="C")

    # Tempo de processamento na máquina m da tarefa alocada na posição k: P_{k,m}
    def P(k, m):
        return gp.quicksum(p[j, m] * x[j, k] for j in J)

    # Função objetivo: minimizar C_{n,3} (makespan)
    modelo.setObjective(C[n, 3], GRB.MINIMIZE)

    # Atribuição: cada tarefa em uma posição e cada posição com uma tarefa
    modelo.addConstrs((x.sum(j, '*') == 1 for j in J), name="atrib_tarefa")
    modelo.addConstrs((x.sum('*', k) == 1 for k in K), name="atrib_posicao")

    # Máquina 1: término inicial e capacidade (desigualdade permite atraso proposital em M1)
    modelo.addConstr(C[1, 1] >= P(1, 1), name="m1_inicio")
    modelo.addConstrs((C[k, 1] >= C[k - 1, 1] + P(k, 1) for k in K if k >= 2), name="m1_cap")

    # Não espera entre Máquina 1 e Máquina 2 (igualdade)
    modelo.addConstrs((C[k, 2] == C[k, 1] + P(k, 2) for k in K), name="nowait_m1_m2")

    # Capacidade da Máquina 2
    modelo.addConstrs((C[k, 2] >= C[k - 1, 2] + P(k, 2) for k in K if k >= 2), name="m2_cap")

    # Máquina 3: rota (espera permitida) e capacidade
    modelo.addConstrs((C[k, 3] >= C[k, 2] + P(k, 3) for k in K), name="m3_rota")
    modelo.addConstrs((C[k, 3] >= C[k - 1, 3] + P(k, 3) for k in K if k >= 2), name="m3_cap")

    modelo.optimize()

    res = {
        'status': modelo.Status,
        'tempo': modelo.Runtime,
        'n': n,
        'nodes': int(modelo.NodeCount),
    }

    if modelo.SolCount > 0:
        pos = {j: next(k for k in K if x[j, k].X > 0.5) for j in J}
        sequencia = sorted(J, key=lambda j: pos[j])
        res.update({
            'obj': modelo.ObjVal,
            'bound': modelo.ObjBound,
            'gap': modelo.MIPGap,
            'sequencia': sequencia,
            'S': cronograma_mais_cedo(sequencia, p),
        })

    return res


def imprimir(res, dados):
    nomes = {
        GRB.OPTIMAL: "Ótimo",
        GRB.TIME_LIMIT: "Limite de Tempo",
        GRB.INFEASIBLE: "Inviável",
        GRB.INTERRUPTED: "Interrompido",
    }
    status_txt = nomes.get(res['status'], str(res['status']))
    print(f"Tarefas: {res['n']} | Status: {status_txt} | Tempo: {res['tempo']:.3f}s | Nós: {res['nodes']}")
    if 'obj' not in res:
        print("Nenhuma solução viável encontrada.")
        return

    print(f"Cmax = {res['obj']:.1f} | Bound = {res['bound']:.1f} | Gap = {100 * res['gap']:.1f}%")
    print("Sequência:", " -> ".join(res['sequencia']))

    p = dados['p']
    print(f"\n{'Tarefa':<8}{'M1':>12}{'M2':>12}{'M3':>12}")
    for j in res['sequencia']:
        cols = [f"[{res['S'][j, m]:.0f}, {res['S'][j, m] + p[j, m]:.0f}]" for m in (1, 2, 3)]
        print(f"{j:<8}{cols[0]:>12}{cols[1]:>12}{cols[2]:>12}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("=== Validação 1: Exemplo de 3 tarefas ===")
        dados_3 = carregar_exemplo_manual()
        res_3 = resolver(dados_3)
        imprimir(res_3, dados_3)
        ok_3 = res_3.get('obj') is not None and abs(res_3['obj'] - 16.0) < 1e-6 and res_3['sequencia'] == ['J2', 'J3', 'J1']
        print("VALIDAÇÃO (3 tarefas):", "OK (Cmax=16, J2->J3->J1)\n" if ok_3 else "FALHOU\n")

        print("=== Validação 2: Exemplo de 4 tarefas (Gráfico de Gantt) ===")
        dados_4 = carregar_exemplo_4_tarefas()
        res_4 = resolver(dados_4)
        imprimir(res_4, dados_4)
        ok_4 = res_4.get('obj') is not None and abs(res_4['obj'] - 21.0) < 1e-6 and res_4['sequencia'] == ['T3', 'T4', 'T1', 'T2']
        print("VALIDAÇÃO (4 tarefas):", "OK (Cmax=21, T3->T4->T1->T2)" if ok_4 else "FALHOU")
    else:
        for caminho in sys.argv[1:]:
            dados = carregar_instancia_txt(caminho)
            print(f"\n=== {Path(caminho).name} (n={dados['n']}) ===")
            imprimir(resolver(dados), dados)
