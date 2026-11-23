"""
leitor_dados.py — Leitura, pré-processamento e validação (Problema 5: Flowshop M1-M2 No-Wait)

Interface devolvida pelas funções de carregamento (dicionário 'dados'):
    dados = {
        'tarefas':  ['J1', 'J2', 'J3', ...],          # Conjunto J de tarefas
        'maquinas': [1, 2, 3],                        # Conjunto M de máquinas (M1, M2, M3)
        'p':        {('J1', 1): 2.0, ('J1', 2): 6.0,  # Tempo de processamento p[j, k]
                     ('J1', 3): 2.0, ...},
        'n':        3,                                # Quantidade de tarefas
        'big_M':    27.0                              # Limitante superior seguro (soma dos tempos)
    }

Formato esperado no arquivo .txt (ajustar em carregar_instancia_txt conforme arquivos do Teams):
    Linha 1: n  (ou: n 3)
    Próximas n linhas: p1 p2 p3  (ou: id p1 p2 p3)
"""

from pathlib import Path


def validar_dados(dados):
    """Verifica inconsistências antes de enviar a instância para o Gurobi."""
    tarefas = dados['tarefas']
    maquinas = dados['maquinas']
    p = dados['p']

    if not tarefas:
        raise ValueError("A lista de tarefas está vazia.")
    if len(tarefas) != len(set(tarefas)):
        raise ValueError("Existem IDs de tarefas duplicados.")
    if maquinas != [1, 2, 3]:
        raise ValueError(f"O problema exige exatamente 3 máquinas [1, 2, 3], recebido: {maquinas}.")

    for j in tarefas:
        for k in maquinas:
            if (j, k) not in p:
                raise ValueError(f"Tempo de processamento ausente para tarefa {j} na máquina {k}.")
            if p[j, k] < 0:
                raise ValueError(f"Tempo negativo detectado em p[{j}, {k}] = {p[j, k]}.")


def carregar_exemplo_manual():
    """
    Retorna a instância pequena (3 tarefas) para validar o modelo no Gurobi.
    Resultados esperados para validação:
      - Modelo correto (no-wait apenas entre M1 e M2): C_max = 16.0 | Seq: (J2, J3, J1)
      - Se der 15.0: faltou a restrição no-wait entre M1 e M2.
      - Se der 17.0: restringiu indevidamente no-wait entre M2 e M3.
    """
    tarefas = ['J1', 'J2', 'J3']
    maquinas = [1, 2, 3]
    p = {
        ('J1', 1): 2.0, ('J1', 2): 6.0, ('J1', 3): 2.0,
        ('J2', 1): 1.0, ('J2', 2): 5.0, ('J2', 3): 3.0,
        ('J3', 1): 4.0, ('J3', 2): 1.0, ('J3', 3): 3.0,
    }
    dados = {
        'tarefas': tarefas,
        'maquinas': maquinas,
        'p': p,
        'n': len(tarefas),
        'big_M': sum(p.values()),
    }
    validar_dados(dados)
    return dados


def carregar_instancia_txt(caminho_arquivo):
    """
    Lê um arquivo de instância de flowshop de 3 máquinas.
    Aceita linhas com 3 colunas (p1 p2 p3) ou 4 colunas (id p1 p2 p3).
    Ignora linhas em branco e comentários iniciados com '#'.
    """
    linhas = []
    with open(Path(caminho_arquivo), 'r', encoding='utf-8') as f:
        for linha in f:
            texto = linha.strip()
            if texto and not texto.startswith('#'):
                linhas.append(texto)

    if not linhas:
        raise ValueError(f"Arquivo vazio: {caminho_arquivo}")

    # Cabeçalho: n (ou "n 3")
    partes_cab = linhas[0].replace(',', ' ').split()
    n = int(partes_cab[0])

    tarefas = []
    maquinas = [1, 2, 3]
    p = {}

    for idx, linha in enumerate(linhas[1:n + 1], start=1):
        partes = linha.replace(',', ' ').split()
        if len(partes) == 3:
            job_id = f"J{idx}"
            tempos = [float(x) for x in partes]
        elif len(partes) >= 4:
            job_id = str(partes[0])
            tempos = [float(x) for x in partes[1:4]]
        else:
            raise ValueError(f"Linha {idx + 1} com formato inesperado: '{linha}'")

        tarefas.append(job_id)
        p[job_id, 1] = tempos[0]
        p[job_id, 2] = tempos[1]
        p[job_id, 3] = tempos[2]

    if len(tarefas) != n:
        raise ValueError(f"Esperadas {n} tarefas, mas foram lidas {len(tarefas)}.")

    dados = {
        'tarefas': tarefas,
        'maquinas': maquinas,
        'p': p,
        'n': n,
        'big_M': sum(p.values()),
    }
    validar_dados(dados)
    return dados


if __name__ == "__main__":
    dados = carregar_exemplo_manual()
    print(f"Instância validada! n={dados['n']}, big_M={dados['big_M']}\n")
    print(f"{'Tarefa':<8}{'M1':>6}{'M2':>6}{'M3':>6}")
    for j in dados['tarefas']:
        print(f"{j:<8}{dados['p'][j, 1]:>6.1f}{dados['p'][j, 2]:>6.1f}{dados['p'][j, 3]:>6.1f}")
