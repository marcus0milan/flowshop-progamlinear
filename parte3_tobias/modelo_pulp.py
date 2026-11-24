"""
modelo_pulp.py — Implementação em PuLP/HiGHS do modelo posicional
(Problema 5: Flowshop F3 | no-wait(M1,M2) | Cmax)

Permite resolver o problema usando PuLP com solver HiGHS (código aberto).

Uso:
    python modelo_pulp.py                      # valida no exemplo de 3 tarefas
    python modelo_pulp.py instancia1.txt ...   # roda instâncias (limite 3600 s)
"""

import sys
from pathlib import Path
import pulp

from leitor_dados import carregar_exemplo_manual, carregar_instancia_txt

TEMPO_LIMITE = 3600


def cronograma_mais_cedo(sequencia, p):
    """Inícios S[j,m] mais cedo possíveis para uma sequência, respeitando o no-wait."""
    S = {}
    c1 = c2 = c3 = 0.0
    for j in sequencia:
        c1 = max(c1 + p[j, 1], c2)     # termina em M1 quando M2 estiver livre
        c2 = c1 + p[j, 2]              # sem espera entre M1 e M2
        c3 = max(c2, c3) + p[j, 3]
        S[j, 1], S[j, 2], S[j, 3] = c1 - p[j, 1], c1, c3 - p[j, 3]
    return S


def resolver(dados, tempo_limite=TEMPO_LIMITE, log=False):
    """Formulação posicional do relatório implementada em PuLP."""
    J = dados['tarefas']
    M = dados['maquinas']          # [1, 2, 3]
    p = dados['p']
    n = dados['n']
    K = list(range(1, n + 1))      # posições 1..n

    prob = pulp.LpProblem("flowshop_nowait_M1M2_posicional", pulp.LpMinimize)

    # Variáveis de decisão
    x = pulp.LpVariable.dicts("x", ((j, k) for j in J for k in K), cat=pulp.LpBinary)
    C = pulp.LpVariable.dicts("C", ((k, m) for k in K for m in M), lowBound=0.0, cat=pulp.LpContinuous)

    def P(k, mq):
        return pulp.lpSum(p[j, mq] * x[j, k] for j in J)

    # Função objetivo: C[n, 3]
    prob += C[n, 3]

    # Atribuição
    for j in J:
        prob += pulp.lpSum(x[j, k] for k in K) == 1, f"atrib_tarefa_{j}"
    for k in K:
        prob += pulp.lpSum(x[j, k] for j in J) == 1, f"atrib_posicao_{k}"

    # Máquina 1
    prob += C[1, 1] >= P(1, 1), "m1_inicio"
    for k in K:
        if k >= 2:
            prob += C[k, 1] >= C[k - 1, 1] + P(k, 1), f"m1_pos_{k}"

    # Sem espera entre M1 e M2 (igualdade)
    for k in K:
        prob += C[k, 2] == C[k, 1] + P(k, 2), f"nowait_pos_{k}"

    # Capacidade da máquina 2
    for k in K:
        if k >= 2:
            prob += C[k, 2] >= C[k - 1, 2] + P(k, 2), f"m2_cap_pos_{k}"

    # Máquina 3: rota e capacidade
    for k in K:
        prob += C[k, 3] >= C[k, 2] + P(k, 3), f"m3_rota_pos_{k}"
        if k >= 2:
            prob += C[k, 3] >= C[k - 1, 3] + P(k, 3), f"m3_cap_pos_{k}"

    # Solver
    solver = pulp.HiGHS(timeLimit=tempo_limite, msg=1 if log else 0)
    status = prob.solve(solver)

    res = {
        'status': pulp.LpStatus[status],
        'tempo': prob.solutionTime if hasattr(prob, 'solutionTime') else 0.0,
        'n': n,
    }

    if status == pulp.LpStatusOptimal:
        pos = {}
        for j in J:
            for k in K:
                if pulp.value(x[j, k]) is not None and pulp.value(x[j, k]) > 0.5:
                    pos[j] = k
                    break
        sequencia = sorted(J, key=lambda j: pos[j])
        obj = pulp.value(prob.objective)
        res.update({
            'obj': obj,
            'bound': obj,
            'gap': 0.0,
            'sequencia': sequencia,
            'S': cronograma_mais_cedo(sequencia, p),
        })
    return res


def imprimir(res, dados):
    print(f"Status: {res['status']} | tempo: {res.get('tempo', 0.0):.3f}s")
    if 'obj' not in res:
        print("Nenhuma solução ótima encontrada.")
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

