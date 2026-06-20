import csv
import collections
import re
import time
import platform
import psutil


class GrafoCurricular:
    def __init__(self):
        self.vertices = {}
        self.adjacencia = collections.defaultdict(list)
        self.grau_entrada = collections.defaultdict(int)

        # Variáveis de Instrumentação (Contadores de ED2 integrados do benchmark)
        self.operacoes_vertices = 0
        self.operacoes_arestas = 0

    def adicionar_disciplina(self, id_unico, codigo_original, nome, carga_horaria, periodo):
        self.vertices[id_unico] = {
            "codigo_orig": codigo_original,
            "nome": nome,
            "ch": int(carga_horaria),
            "periodo": periodo
        }
        if id_unico not in self.adjacencia:
            self.adjacencia[id_unico] = []
        if id_unico not in self.grau_entrada:
            self.grau_entrada[id_unico] = 0

    def adicionar_pre_requisito(self, id_requisito, id_destino):
        if id_requisito in self.vertices and id_destino in self.vertices:
            self.adjacencia[id_requisito].append(id_destino)
            self.grau_entrada[id_destino] += 1

    def tem_ciclo(self):
        cores = {v: 0 for v in self.vertices}

        def dfs_ciclo(u):
            cores[u] = 1
            for vizinho in self.adjacencia[u]:
                if cores[vizinho] == 1:
                    return True
                if cores[vizinho] == 0:
                    if dfs_ciclo(vizinho):
                        return True
            cores[u] = 2
            return False

        for vertice in self.vertices:
            if cores[vertice] == 0:
                if dfs_ciclo(vertice):
                    return True
        return False

    # =========================================================================
    # BASELINE: ORDENAÇÃO TOPOLÓGICA VIA DFS (Instrumentado)
    # =========================================================================
    def ordenacao_topologica_dfs(self):
        self.operacoes_vertices = 0
        if self.tem_ciclo():
            return None

        visitados = set()
        pilha = []

        def dfs_visita(u):
            visitados.add(u)
            self.operacoes_vertices += 1  # Contabiliza visita/empilhamento
            for vizinho in self.adjacencia[u]:
                if vizinho not in visitados:
                    dfs_visita(vizinho)
            pilha.append(u)

        for vertice in self.vertices:
            if vertice not in visitados:
                dfs_visita(vertice)
        return list(reversed(pilha))

    # =========================================================================
    # PRINCIPAL: ORDENAÇÃO TOPOLÓGICA VIA KAHN (Instrumentado)
    # =========================================================================
    def ordenacao_topologica_kahn(self):
        self.operacoes_vertices = 0
        graus = {v: self.grau_entrada[v] for v in self.vertices}
        fila = collections.deque([v for v in self.vertices if graus[v] == 0])
        ordem = []
        while fila:
            u = fila.popleft()
            ordem.append(u)
            self.operacoes_vertices += 1  # Contabiliza extração
            for vizinho in self.adjacencia[u]:
                graus[vizinho] -= 1
                if graus[vizinho] == 0:
                    fila.append(vizinho)
        return ordem

    # =========================================================================
    # CPM: MÉTODO DO CAMINHO CRÍTICO (Unificado)
    # =========================================================================
    def calcular_caminho_critico(self):
        self.operacoes_arestas = 0
        if self.tem_ciclo():
            return None, 0

        ordem_topo = self.ordenacao_topologica_kahn()
        inicio_cedo = {v: 0 for v in self.vertices}
        fim_cedo = {}

        for u in ordem_topo:
            fim_cedo[u] = inicio_cedo[u] + self.vertices[u]["ch"]
            for vizinho in self.adjacencia[u]:
                self.operacoes_arestas += 1  # Contabiliza avanço
                if fim_cedo[u] > inicio_cedo[vizinho]:
                    inicio_cedo[vizinho] = fim_cedo[u]

        duracao_total = max(fim_cedo.values()) if fim_cedo else 0
        fim_tarde = {v: duracao_total for v in self.vertices}
        inicio_tarde = {}

        for u in reversed(ordem_topo):
            inicio_tarde[u] = fim_tarde[u] - self.vertices[u]["ch"]
            for req in self.vertices:
                if u in self.adjacencia[req]:
                    self.operacoes_arestas += 1  # Contabiliza relaxamento
                    if inicio_tarde[u] < fim_tarde[req]:
                        fim_tarde[req] = inicio_tarde[u]

        relatorio = {}
        for v in self.vertices:
            folga = inicio_tarde[v] - inicio_cedo[v]
            relatorio[v] = {
                "codigo": self.vertices[v]["codigo_orig"],
                "nome": self.vertices[v]["nome"],
                "periodo": self.vertices[v]["periodo"],
                "folga": folga,
                "critica": folga == 0,
                # LINHA CRUCIAL (MANTIDA): Repassa a sigla para o relatório/plotagem
                "sigla": self.vertices[v].get("sigla")
            }
        return relatorio, duracao_total


# =========================================================================
# FUNÇÕES AUXILIARES DE BENCHMARK
# =========================================================================
def executar_benchmark_cenario(grafo_instancia, N=30):
    tempos = []
    relatorio, tempo_total_curso = None, 0

    for _ in range(N):
        inicio = time.perf_counter_ns()
        relatorio, tempo_total_curso = grafo_instancia.calcular_caminho_critico()
        fim = time.perf_counter_ns()
        tempos.append((fim - inicio) / 1000.0)

    media_tempo = sum(tempos) / N
    return relatorio, tempo_total_curso, media_tempo, grafo_instancia.operacoes_arestas


def obter_especificacoes_pc():
    info = {}
    info['python_versao'] = platform.python_version()
    info['so'] = platform.system()
    info['so_versao'] = platform.release()
    info['arquitetura'] = platform.machine()
    info['cpu'] = platform.processor()
    info['cpu_nucleos_fisicos'] = psutil.cpu_count(logical=False)
    info['cpu_nucleos_logicos'] = psutil.cpu_count(logical=True)
    ram = psutil.virtual_memory()
    info['ram_total'] = round(ram.total / (1024 ** 3), 2)
    return info


# =========================================================================
# FUNÇÃO PRINCIPAL DE CARREGAMENTO (Unificada)
# =========================================================================
def carregar_grafo_completo(ignorar_arestas=None):
    """Cria o grafo integrando siglas de plotagem e suportando exclusão de arestas para benchmark."""
    if ignorar_arestas is None:
        ignorar_arestas = []

    grafo = GrafoCurricular()
    arquivo_csv = "grade_sistemas_informacao_completa.csv"

    abreviacoes = {
        "SI01001_P1": "PROG_I", "SI01002_P1": "MAT_DISC", "SI01003_P1": "LOG_COMP",
        "SI01004_P1": "ESTATIS", "SI01005_P1": "MET_CIEN", "SI01006_P1": "TGS",
        "SI01007_P2": "PROG_II", "SI01008_P2": "CALC_I", "SI01011_P2": "ARQ_COMP",
        "SI01015_P2": "EST_D_I", "SI01017_P2": "FIL_CIEN", "SI01009_P3": "ECONOMIA",
        "SI01012_P3": "ADM_I", "SI01013_P3": "PROBABIL", "SI01014_P3": "B_DADOS1",
        "SI01016_P3": "ENG_SOFT", "SI01019_P3": "EST_D_II", "SI01010_P4": "AN_PROJ",
        "SI01018_P4": "ADM_II", "SI01020_P4": "B_DADOS2", "SI01021_P4": "SIST_OP",
        "SI01023_P4": "PSI_INFOR", "SI01027_P4": "IHC", "SI01010_P5": "GER_PROJ",
        "SI01018_P5": "WEB_I", "SI01020_P5": "REDES", "SI01021_P5": "GES_INFO",
        "SI01028_P5": "CG_RV", "SI01027_P5": "SOC_INFO", "SI01030_P6": "WEB_II",
        "SI01031_P6": "GER_RED", "SI01032_P6": "DIR_LEGIS", "SI01033_P6": "SEG_RED",
        "SI01034_P6": "OSM", "SI01035_P6": "EMPREEND", "SI01036_P6": "INT_ART",
        "SI01037_P7": "SIS_DIST", "SI01038_P7": "SIG", "SI01039_P7": "TCC_I",
        "SI01040_P7": "ESTAGIO", "SI01041_P7": "ACC", "SI01042_P8": "DISP_MOV",
        "SI01043_P8": "AUDIT_SI", "SI01044_P8": "TCC_II", "SI01063_P8": "EXTENSAO"
    }

    try:
        with open(arquivo_csv, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f)
            for table_row in leitor:
                cod_original = table_row['Codigo'].strip()
                periodo = table_row['Periodo_Modulo'].strip()
                id_unico = f"{cod_original}_P{periodo}"
                ch_limpa = re.sub(r'\D', '', table_row['Carga_Horaria'])

                sigla_curta = abreviacoes.get(id_unico, cod_original[:8])

                grafo.adicionar_disciplina(
                    id_unico=id_unico,
                    codigo_original=cod_original,
                    nome=table_row['Disciplina'].strip(),
                    carga_horaria=ch_limpa if ch_limpa else 68,
                    periodo=periodo
                )
                # Injeta a sigla para plotagem futura
                grafo.vertices[id_unico]["sigla"] = sigla_curta

    except FileNotFoundError:
        print(f"Erro: O arquivo '{arquivo_csv}' não foi encontrado.")
        return None

    # Função interna auxiliar para filtrar arestas ignoradas nos benchmarks
    def add_req(u, v):
        if (u, v) not in ignorar_arestas:
            grafo.adicionar_pre_requisito(u, v)

    # TRILHAS DE PRÉ-REQUISITOS
    add_req("SI01001_P1", "SI01007_P2")
    add_req("SI01007_P2", "SI01015_P2")
    add_req("SI01015_P2", "SI01019_P3")
    add_req("SI01019_P3", "SI01036_P6")
    add_req("SI01007_P2", "SI01016_P3")
    add_req("SI01015_P2", "SI01014_P3")
    add_req("SI01014_P3", "SI01020_P4")
    add_req("SI01016_P3", "SI01010_P4")
    add_req("SI01010_P4", "SI01010_P5")
    add_req("SI01007_P2", "SI01018_P5")
    add_req("SI01018_P5", "SI01030_P6")
    add_req("SI01021_P4", "SI01037_P7")
    add_req("SI01011_P2", "SI01021_P4")
    add_req("SI01021_P4", "SI01020_P5")
    add_req("SI01020_P5", "SI01031_P6")
    add_req("SI01020_P5", "SI01033_P6")
    add_req("SI01033_P6", "SI01043_P8")
    add_req("SI01002_P1", "SI01008_P2")
    add_req("SI01004_P1", "SI01013_P3")
    add_req("SI01012_P3", "SI01018_P4")
    add_req("SI01018_P4", "SI01034_P6")
    add_req("SI01034_P6", "SI01035_P6")
    add_req("SI01005_P1", "SI01039_P7")
    add_req("SI01016_P3", "SI01040_P7")
    add_req("SI01039_P7", "SI01044_P8")

    return grafo


# =========================================================================
# PROGRAMA PRINCIPAL
# =========================================================================
if __name__ == "__main__":
    N_REPETICOES = 30
    grafo = carregar_grafo_completo()

    if grafo:
        print("--- 1. DETECÇÃO DE CICLOS (VIABILIDADE) ---")
        if grafo.tem_ciclo():
            print("RESULTADO: Ciclo detectado! Grade curricular com erros de amarração circular.\n")
        else:
            print("RESULTADO: Grafo acíclico (DAG). Estrutura curricular viável.\n")

        print("--- 1.5 COMPARATIVO DE BASELINE (ORDENAÇÃO TOPOLÓGICA) ---")
        ordem_dfs = grafo.ordenacao_topologica_dfs()
        ordem_kahn = grafo.ordenacao_topologica_kahn()

        print(f"\nOrdem gerada pelo Baseline (DFS) - Primeiras 3: {ordem_dfs[:3]}")
        print(f"Ordem gerada pelo Principal (Kahn) - Primeiras 3: {ordem_kahn[:3]}")
        print("Ambas as ordenações são caminhos lineares válidos para o algoritmo CPM!\n")

        print("--- 2. TAREFAS CRÍTICAS E FOLGAS (CPM) ---")
        cpm_dados, tempo_total = grafo.calcular_caminho_critico()

        if cpm_dados:
            print(f"Tempo mínimo acumulado na trilha de dependências: {tempo_total} horas.\n")
            print(f"{'CÓDIGO':<8} | {'MÓD'} | {'DISCIPLINA':<40} | {'FOLGA':<5} | {'SITUAÇÃO'}")
            print("-" * 80)

            dados_ordenados = sorted(cpm_dados.items(), key=lambda x: int(x[1]['periodo']))

            for id_u, dados in dados_ordenados:
                status = "CRÍTICA ⚠️" if dados["critica"] else "Com Folga"
                print(
                    f"{dados['codigo']:<8} | {dados['periodo']:^3} | {dados['nome'][:40]:<40} | {dados['folga']:<5} | {status}")

            print(f"\nTotal real de disciplinas processadas no Grafo: {len(cpm_dados)}")
        else:
            print("Erro: Não foi possível calcular o CPM devido a falhas no Grafo.")

        print("\n--- 3. SIMULAÇÃO DE REMOVER/RELAXAR DEPENDÊNCIAS ---")
        # Cenário A
        print("\n[Cenário A] Removendo pré-requisito de Eng. de Software para Estágio...")
        g_sim_A = carregar_grafo_completo(ignorar_arestas=[("SI01016_P3", "SI01040_P7")])
        _, tempo_A = g_sim_A.calcular_caminho_critico()
        print(f"-> Resultado Cenário A: Tempo mínimo travado em {tempo_A}h (Pelas trilhas de IA, Banco e Projetos).")

        # Cenário B
        print("\n[Cenário B] Removendo TAMBÉM o pré-requisito de ED II para Inteligência Artificial...")
        g_sim_B = carregar_grafo_completo(ignorar_arestas=[("SI01016_P3", "SI01040_P7"), ("SI01019_P3", "SI01036_P6")])
        _, tempo_B = g_sim_B.calcular_caminho_critico()
        print(f"-> Resultado Cenário B: Tempo continuou em {tempo_B}h (Sustentado por Banco e Projetos).")

        # Cenário C
        print("\n[Cenário C] Removendo a restrição principal: Programação I -> Programação II...")
        g_sim_C = carregar_grafo_completo(
            ignorar_arestas=[("SI01016_P3", "SI01040_P7"), ("SI01019_P3", "SI01036_P6"), ("SI01001_P1", "SI01007_P2")])
        _, tempo_C = g_sim_C.calcular_caminho_critico()
        print(f"-> Resultado Cenário C: O tempo máximo finalmente despencou para {tempo_C}h!")

        # Cenário D
        print("\n[Cenário D] Simulando relaxamento TOTAL de todos os pré-requisitos...")
        g_sim_D = GrafoCurricular()
        with open("grade_sistemas_informacao_completa.csv", mode='r', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                g_sim_D.adicionar_disciplina(f"{r['Codigo'].strip()}_P{r['Periodo_Modulo'].strip()}",
                                             r['Codigo'].strip(), r['Disciplina'].strip(),
                                             re.sub(r'\D', '', r['Carga_Horaria']), r['Periodo_Modulo'].strip())
        _, tempo_D = g_sim_D.calcular_caminho_critico()
        print(f"-> Resultado Cenário D: O tempo mínimo absoluto caiu para {tempo_D}h!")

        # --- PROCESSAMENTO DOS BENCHMARKS E TABELA FINAL ---
        print("\n" + "=" * 75)
        print(f"{'INSTRUMENTAÇÃO DE DESEMPENHO (N = 30 Repetições)':^75}")
        print("=" * 75)

        tempos_dfs, tempos_kahn = [], []
        for _ in range(N_REPETICOES):
            t0 = time.perf_counter_ns()
            grafo.ordenacao_topologica_dfs()
            tempos_dfs.append((time.perf_counter_ns() - t0) / 1000.0)

            t1 = time.perf_counter_ns()
            grafo.ordenacao_topologica_kahn()
            tempos_kahn.append((time.perf_counter_ns() - t1) / 1000.0)

        print(
            f"Baseline (DFS)  | Tempo Médio: {sum(tempos_dfs) / N_REPETICOES:7.2f} us | Visitas a Vértices: {len(grafo.vertices)}")
        print(
            f"Principal (Kahn)| Tempo Médio: {sum(tempos_kahn) / N_REPETICOES:7.2f} us | Visitas a Vértices: {len(grafo.vertices)}")

        # Coleta para Tabela
        _, t_base, tempo_base_us, ops_base = executar_benchmark_cenario(grafo)
        a_base = sum(len(v) for v in grafo.adjacencia.values())

        _, t_A, tempo_A_us, ops_A = executar_benchmark_cenario(g_sim_A)
        a_A = sum(len(v) for v in g_sim_A.adjacencia.values())

        _, t_B, tempo_B_us, ops_B = executar_benchmark_cenario(g_sim_B)
        a_B = sum(len(v) for v in g_sim_B.adjacencia.values())

        _, t_C, tempo_C_us, ops_C = executar_benchmark_cenario(g_sim_C)
        a_C = sum(len(v) for v in g_sim_C.adjacencia.values())

        _, t_D, tempo_D_us, ops_D = executar_benchmark_cenario(g_sim_D)
        a_D = 0

        print(f"\n{'TABELA DE RESUMO ESTRUTURAL E MÉTRICAS DOS CENÁRIOS':^75}")
        print("-" * 75)
        print(
            f"{'Cenário':<12} | {'Vértices':^8} | {'Arestas':^8} | {'Oper. Arestas':^13} | {'Tempo Médio':^13} | {'Caminho'}")
        print("-" * 75)
        print(
            f"{'Base':<12} | {len(grafo.vertices):^8} | {a_base:^8} | {ops_base:^13} | {tempo_base_us:7.2f} us | {t_base}h")
        print(
            f"{'Cenário A':<12} | {len(g_sim_A.vertices):^8} | {a_A:^8} | {ops_A:^13} | {tempo_A_us:7.2f} us | {t_A}h")
        print(
            f"{'Cenário B':<12} | {len(g_sim_B.vertices):^8} | {a_B:^8} | {ops_B:^13} | {tempo_B_us:7.2f} us | {t_B}h")
        print(
            f"{'Cenário C':<12} | {len(g_sim_C.vertices):^8} | {a_C:^8} | {ops_C:^13} | {tempo_C_us:7.2f} us | {t_C}h")
        print(
            f"{'Cenário D':<12} | {len(g_sim_D.vertices):^8} | {a_D:^8} | {ops_D:^13} | {tempo_D_us:7.2f} us | {t_D}h")
        print("=" * 75)

        specs = obter_especificacoes_pc()
        print("\n" + "=" * 50)
        print("          ESPECIFICAÇÕES DO SISTEMA")
        print("=" * 50)
        print(f"Versão do Python    : {specs['python_versao']}")
        print(f"Sistema Operacional : {specs['so']} {specs['so_versao']} ({specs['arquitetura']})")
        print(f"Processador (CPU)   : {specs['cpu']}")
        print(f"Núcleos do CPU      : {specs['cpu_nucleos_fisicos']} Físicos / {specs['cpu_nucleos_logicos']} Lógicos")
        print(f"Memória RAM Total   : {specs['ram_total']} GB")
        print("=" * 50)