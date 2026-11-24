# Guia de Preparação para a Arguição / Apresentação
**Disciplina:** Programação Linear — Prof. Me. Júnior César Bonafim  
**Instituição:** FATEC Ribeirão Preto | Curso de Análise e Desenvolvimento de Sistemas  
**Trabalho Final — Problema 5:** *Flowshop de Três Máquinas com Restrição No-Wait Parcial* ($F3 \mid \text{no-wait}(M_1 \to M_2),\, \text{prmu} \mid C_{\max}$)

---

## 🎯 Por que este guia é importante?
Na descrição do trabalho, o professor definiu:
> *"Cada grupo passará por uma arguição sobre o trabalho entregue. A nota será composta pela avaliação do relatório (5,0 pontos) e apresentação (5,0 pontos). A fração da nota referente à apresentação é individual."*

Ou seja, **a sua nota individual depende de responder com segurança** às perguntas sobre o problema, a modelagem matemática, o código e os resultados computacionais.

Abaixo estão todos os conceitos essenciais, as perguntas mais prováveis que o professor Bonafim pode fazer e como respondê-las com clareza.

---

## 1. O Problema (Conceitos Fundamentais)

### O que é o Problema 5?
Temos **três máquinas** ($M_1, M_2, M_3$) dispostas em linha (*flowshop*). Um conjunto de $n$ tarefas precisa passar obrigatoriamente por $M_1$, depois por $M_2$ e finalmente por $M_3$. Cada tarefa tem tempos de processamento conhecidos ($p_{j,m}$) em cada máquina.

### Qual é a regra especial desse problema?
A regra principal é a **ausência de espera parcial (*no-wait*)**:
* **Entre $M_1$ e $M_2$ NÃO PODE HAVER ESPERA:** assim que a tarefa sai da máquina 1, ela precisa entrar **imediatamente** na máquina 2 ($S_{j,2} = C_{j,1}$). Na indústria real, isso é comum em processos químicos, alimentícios ou metalúrgicos (ex.: a peça sai do forno e precisa ir direto para a prensa para não perder temperatura ou estragar).
* **Entre $M_2$ e $M_3$ A ESPERA É PERMITIDA:** a tarefa que sai de $M_2$ pode aguardar em um estoque intermediário (*buffer*) até que a máquina 3 fique livre ($S_{j,3} \ge C_{j,2}$).

### Qual é o objetivo?
Minimizar o **makespan** ($C_{\max}$), que é o instante em que a última tarefa é concluída na última máquina ($M_3$). Em termos práticos, significa terminar todo o lote de tarefas no menor tempo total possível.

### Qual a classificação de Graham ($\alpha \mid \beta \mid \gamma$)?
$$F3 \mid \text{no-wait}(M_1 \to M_2),\, \text{prmu} \mid C_{\max}$$
* $\alpha = F3$: *Flowshop* com 3 máquinas;
* $\beta = \text{no-wait}(M_1 \to M_2),\, \text{prmu}$: Restrição de não espera entre $M_1$ e $M_2$, com soluções de permutação;
* $\gamma = C_{\max}$: Minimização do *makespan*.

---

## 2. Modelagem Matemática (As Perguntas mais Prováveis)

### ❓ Pergunta 1: "Por que vocês assumiram a mesma sequência de tarefas em todas as máquinas (permutação)?"
> **Resposta:**
> "Demonstramos na Proposição 1 do relatório que restringir a busca a soluções de permutação não perde nenhuma solução ótima:
> 1. **Entre $M_1$ e $M_2$:** Como a entrada em $M_2$ é instantânea após o término em $M_1$ e os tempos são positivos, a ordem de liberação em $M_1$ é necessariamente a ordem de entrada em $M_2$. Logo, as duas máquinas têm obrigatoriamente a mesma sequência.
> 2. **Entre $M_2$ e $M_3$:** Aplicamos o teorema clássico de trocas adjacentes de Conway, Maxwell e Miller (1967). Se duas tarefas consecutivas em $M_3$ estivessem invertidas em relação a $M_2$, inverter a ordem delas em $M_3$ para coincidir com $M_2$ nunca aumenta o *makespan* e não interfere na restrição de *no-wait* prévia entre $M_1$ e $M_2$. Logo, sempre existe um ótimo permutacional."

---

### ❓ Pergunta 2: "Por que vocês usaram uma formulação posicional em vez do modelo disjuntivo clássico com big-M?"
> **Resposta:**
> "Optamos pela modelagem posicional por três motivos técnicos fundamentais:
> 1. **Não usa constantes arbitrárias $M$ (*big-M*):** Modelos com *big-M* costumam sofrer com relaxações lineares fracas (*bounds* duais distantes do ótimo) e instabilidade numérica no solver.
> 2. **Relaxação linear muito mais firme:** Na modelagem posicional, a relaxação do nó raiz é tão forte que, em metade dos nossos testes (incluindo a instância de 20 tarefas), o solver encontrou e provou o ótimo explorando **apenas 1 nó** na árvore de busca.
> 3. **Modelo compacto:** Temos apenas $n^2$ variáveis binárias ($x_{jk}$ indicando se a tarefa $j$ ocupa a posição $k$), $3n$ variáveis contínuas ($C_{k,m}$) e $7n - 2$ restrições estruturais."

---

### ❓ Pergunta 3: "Como o modelo garante o no-wait sem travar se a máquina 2 ainda estiver ocupada?"
> **Resposta:**
> "A restrição da máquina 1 usa desigualdade:
> $$C_{k,1} \ge C_{k-1,1} + P_{k,1}$$
> Isso permite que a máquina 1 fique ociosa intencionalmente. Ou seja, podemos **atrasar o início da tarefa em $M_1$** para que ela termine exatamente no momento em que $M_2$ fica livre.
> Quando ela termina em $M_1$, a igualdade estrita:
> $$C_{k,2} = C_{k,1} + P_{k,2}$$
> garante que ela comece em $M_2$ no mesmo instante, satisfazendo o *no-wait* com perfeição."

---

### ❓ Pergunta 4: "Para que serve a restrição de capacidade de $M_2$ ($C_{k,2} \ge C_{k-1,2} + P_{k,2}$) se já temos a igualdade de no-wait?"
> **Resposta:**
> "Substituindo a igualdade de não espera $C_{k,2} = C_{k,1} + P_{k,2}$ dentro da restrição de capacidade de $M_2$, obtemos:
> $$C_{k,1} \ge C_{k-1,2}$$
> Ela representa a condição física de que a tarefa da posição $k$ só pode **terminar** em $M_1$ depois que a tarefa anterior desocupa $M_2$. É exatamente essa restrição que, combinada com a desigualdade de $M_1$, força o atraso no início da tarefa em $M_1$."

---

### ❓ Pergunta 5: "Como vocês modelaram a função objetivo? Precisou de variável auxiliar $C_{\max}$?"
> **Resposta:**
> "Não precisamos de variável auxiliar. Minimizamos diretamente $C_{n,3}$ (o instante de término na máquina 3 da tarefa que ocupa a última posição $n$). Como a capacidade de $M_3$ impõe que $C_{k,3} \ge C_{k-1,3} + P_{k,3}$, os tempos de término em $M_3$ são estritamente não decrescentes em relação às posições, garantindo que o término do lote inteiro ocorra sempre na posição $n$."

---

## 3. Validação do Modelo

### ❓ Pergunta 6: "Como vocês testaram e validaram que o modelo realmente está correto?"
> **Resposta:**
> "Validamos em 3 etapas complementares:
> 1. **Instância manual de 3 tarefas:** Calculamos na mão o cronograma de todas as $3! = 6$ sequências possíveis. Apenas a sequência $(J_2, J_3, J_1)$ atingiu o ótimo de $C_{\max} = 16$. Esse teste funcionou como diagnóstico: se esquecêssemos a restrição de não espera, o modelo daria 15 (incorreto); se colocássemos não espera também em $M_3$, o ótimo subiria para 17 (incorreto). O solver cravou exatamente 16.
> 2. **Instância de 4 tarefas com gráfico de Gantt:** Plotamos o diagrama de Gantt (feito em TikZ no relatório), onde foi possível observar visualmente a tarefa $T_2$ sofrendo um atraso voluntário em $M_1$ (começando em $t = 10$ em vez de $t = 9$) para sincronizar com $M_2$, e a tarefa $T_4$ esperando no buffer antes de entrar em $M_3$.
> 3. **Validação cruzada em 30 instâncias aleatórias:** Criamos um script que comparou o resultado do modelo com a enumeração completa das permutações em 30 instâncias de 3 a 8 tarefas, obtendo 100% de concordância."

---

## 4. Implementação e Código (Tobias / Guilherme / Savegnago)

### ❓ Pergunta 7: "Quais ferramentas e bibliotecas vocês usaram no código?"
> **Resposta:**
> "Implementamos o código em **Python**. Para demonstrar interoperabilidade, temos implementações em dois solvers:
> * **PuLP 3.3.2 com solver HiGHS 1.16.0:** solver de código aberto de alta performance, utilizado para registrar os resultados oficiais da Tabela do relatório.
> * **Gurobi (gurobipy 14.0):** solver comercial utilizado como segunda validação, incluindo código comparativo com formulação disjuntiva."

### ❓ Pergunta 8: "O que faz a função `cronograma_mais_cedo` no código?"
> **Resposta:**
> "O solver foca unicamente em minimizar a função objetivo ($C_{n,3}$). Em problemas com soluções ótimas alternativas, o solver pode retornar folgas artificiais em operações intermediárias que não alteram o $C_{\max}$ final. A função `cronograma_mais_cedo` recalcula os instantes mais cedo possíveis para a sequência ótima encontrada, eliminando folgas desnecessárias e garantindo que o cronograma e o gráfico de Gantt fiquem compactos para aplicação em chão de fábrica."

---

## 5. Experimentos Computacionais e Resultados

### Tabela Oficial de Resultados (Tenha estes números em mente!)

| Instância | Tarefas ($n$) | Espaço ($n!$) | $C_{\max}$ Ótimo | Bound | Gap | Tempo (s) | Nós na Árvore | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | 6 | 720 | **104** | 104 | **0,0%** | **0,079 s** | 1 | Ótimo |
| **2** | 8 | 40.320 | **179** | 179 | **0,0%** | **0,364 s** | 5 | Ótimo |
| **3** | 10 | $\approx 3{,}6 \times 10^6$ | **295** | 295 | **0,0%** | **0,657 s** | 9 | Ótimo |
| **4** | 12 | $\approx 4{,}79 \times 10^8$ | **304** | 304 | **0,0%** | **1,340 s** | 9 | Ótimo |
| **5** | 15 | $\approx 1{,}3 \times 10^{12}$ | **374** | 374 | **0,0%** | **0,563 s** | 1 | Ótimo |
| **6** | 20 | $\approx 2{,}43 \times 10^{18}$ | **586** | 586 | **0,0%** | **2,308 s** | 1 | Ótimo |

### ❓ Pergunta 9: "Por que a instância de 15 tarefas resolveu mais rápido (0,56 s) do que a de 12 tarefas (1,34 s)?"
> **Resposta:**
> "Porque a dificuldade de um problema de otimização combinatória não depende exclusivamente da quantidade de tarefas ($n$). Ela também é fortemente influenciada pela estrutura dos tempos de processamento, pela correlação de cargas entre as máquinas e pelas folgas existentes. Na instância de 15 tarefas, os limitantes e cortes no nó raiz permitiram comprovar o ótimo imediatamente (em 1 único nó), enquanto a de 12 tarefas exigiu a exploração de 9 nós na árvore de branch-and-cut."

### ❓ Pergunta 10: "O tempo limite de 3600 segundos (1 hora) foi respeitado?"
> **Resposta:**
> "Sim, com muita folga. O tempo máximo entre todas as instâncias foi de apenas **2,308 segundos** (para a instância de 20 tarefas), e a soma do tempo de todas as seis instâncias deu apenas **5,311 segundos**, atingindo gap de 0,0% em 100% dos testes."

---

## 6. Complexidade Teórica e Trabalhos Futuros

### ❓ Pergunta 11: "Esse problema é fácil ou difícil computacionalmente?"
> **Resposta:**
> "Teoricamente, ele é **NP-difícil**. Isso porque o problema clássico de *flowshop* com 3 máquinas sem restrição de espera ($F3 \mid\mid C_{\max}$) já foi provado NP-difícil no sentido forte por Garey, Johnson e Sethi (1976).
> Embora tenhamos resolvido até 20 tarefas em menos de 3 segundos devido à força da formulação posicional, o crescimento do espaço de busca é fatorial ($n!$). Para instâncias com 50 ou 100 tarefas, o tempo de um método puramente exato pode estourar o limite de 1 hora."

### ❓ Pergunta 12: "O que vocês proporiam para resolver problemas de 100 ou 500 tarefas?"
> **Resposta:**
> "Para instâncias de grande porte, proporíamos:
> 1. **Heurísticas construtivas dedicadas:** como uma extensão do algoritmo NEH adaptada para a restrição de *no-wait*;
> 2. **Meta-heurísticas:** como *Simulated Annealing*, Algoritmos Genéticos ou *Variable Neighborhood Search* (VNS), que encontram soluções muito próximas da ótima em frações de segundo;
> 3. **Cortes válidos combinatórios:** adicionar desigualdades de corte poliédrico baseadas em cargas mínimas das máquinas para fortalecer ainda mais o branch-and-cut."

---

## 7. Bate-Bola Rápido (Resumo para Lembrar na Hora!)

* **Objetivo:** Minimizar o tempo total de conclusão do lote ($C_{\max}$).
* **Máquinas:** 3 máquinas na sequência fixa $M_1 \to M_2 \to M_3$.
* **Restrição principal:** Não pode esperar entre $M_1$ e $M_2$ (*no-wait*). Entre $M_2$ e $M_3$ pode esperar.
* **Tipo de modelo:** Programação Linear Inteira Mista (PLIM) Posicional.
* **Variáveis:** $x_{jk}$ (binária: tarefa $j$ na posição $k$) e $C_{k,m}$ (contínua: instante de término da posição $k$ na máquina $m$).
* **Por que não big-M?** Porque o modelo posicional tem relaxação linear muito mais justa e não gera instabilidade numérica.
* **Por que permutação?** Provado por relação bijetiva entre $M_1$ e $M_2$ e teorema de trocas de Conway para $M_3$.
* **Maior instância testada:** 20 tarefas ($20! \approx 2{,}43 \times 10^{18}$ sequências possíveis).
* **Tempo da maior instância:** 2,308 segundos (comprovadamente ótima, gap de 0,0%).
* **Solvers:** HiGHS (via PuLP) e Gurobi.
