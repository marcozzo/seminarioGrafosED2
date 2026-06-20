import csv
import collections
import re


class GrafoCurricular:
    def __init__(self):
        self.vertices = {}
        self.adjacencia = collections.defaultdict(list)
        self.grau_entrada = collections.defaultdict(int)

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
    # BASELINE: ORDENAÇÃO TOPOLÓGICA VIA DFS
    # =========================================================================
    def ordenacao_topologica_dfs(self):
        if self.tem_ciclo():
            return None

        visitados = set()
        pilha = []

        def dfs_visita(u):
            visitados.add(u)
            for vizinho in self.adjacencia[u]:
                if vizinho not in visitados:
                    dfs_visita(vizinho)
            # Elemento entra na pilha após todos os seus descendentes serem visitados
            pilha.append(u)

        for vertice in self.vertices:
            if vertice not in visitados:
                dfs_visita(vertice)

        # Retorna a pilha invertida para obter a ordem topológica correta
        return list(reversed(pilha))

    # =========================================================================
    # PRINCIPAL: ORDENAÇÃO TOPOLÓGICA VIA KAHN
    # =========================================================================
    def ordenacao_topologica_kahn(self):
        graus = {v: self.grau_entrada[v] for v in self.vertices}
        fila = collections.deque([v for v in self.vertices if graus[v] == 0])
        ordem = []
        while fila:
            u = fila.popleft()
            ordem.append(u)
            for vizinho in self.adjacencia[u]:
                graus[vizinho] -= 1
                if graus[vizinho] == 0:
                    fila.append(vizinho)
        return ordem

    def calcular_caminho_critico(self):
        if self.tem_ciclo():
            return None, 0

        # O CPM usa a ordenação principal (Kahn) como padrão
        ordem_topo = self.ordenacao_topologica_kahn()
        inicio_cedo = {v: 0 for v in self.vertices}
        fim_cedo = {}

        for u in ordem_topo:
            fim_cedo[u] = inicio_cedo[u] + self.vertices[u]["ch"]
            for vizinho in self.adjacencia[u]:
                if fim_cedo[u] > inicio_cedo[vizinho]:
                    inicio_cedo[vizinho] = fim_cedo[u]

        duracao_total = max(fim_cedo.values()) if fim_cedo else 0
        fim_tarde = {v: duracao_total for v in self.vertices}
        inicio_tarde = {}

        for u in reversed(ordem_topo):
            inicio_tarde[u] = fim_tarde[u] - self.vertices[u]["ch"]
            for req in self.vertices:
                if u in self.adjacencia[req]:
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
                # LINHA CRUCIAL ADICIONADA: Repassa a sigla para o relatório
                "sigla": self.vertices[v].get("sigla")
            }
        return relatorio, duracao_total

# =========================================================================
# PROGRAMA PRINCIPAL
# =========================================================================


def carregar_grafo_completo():

        """Função utilitária que cria, popula e retorna o grafo pronto."""
        grafo = GrafoCurricular()
        arquivo_csv = "grade_sistemas_informacao_completa.csv"

        abreviacoes = {
            # --- 1º MÓDULO ---
            "SI01001_P1": "PROG_I",
            "SI01002_P1": "MAT_DISC",
            "SI01003_P1": "LOG_COMP",
            "SI01004_P1": "ESTATIS",
            "SI01005_P1": "MET_CIEN",
            "SI01006_P1": "TGS",

            # --- 2º MÓDULO ---
            "SI01007_P2": "PROG_II",
            "SI01008_P2": "CALC_I",
            "SI01011_P2": "ARQ_COMP",
            "SI01015_P2": "EST_D_I",
            "SI01017_P2": "FIL_CIEN",

            # --- 3º MÓDULO ---
            "SI01009_P3": "ECONOMIA",
            "SI01012_P3": "ADM_I",
            "SI01013_P3": "PROBABIL",
            "SI01014_P3": "B_DADOS1",
            "SI01016_P3": "ENG_SOFT",
            "SI01019_P3": "EST_D_II",

            # --- 4º MÓDULO ---
            "SI01010_P4": "AN_PROJ",  # Colisão resolvida (SI01010)
            "SI01018_P4": "ADM_II",  # Colisão resolvida (SI01018)
            "SI01020_P4": "B_DADOS2",  # Colisão resolvida (SI01020)
            "SI01021_P4": "SIST_OP",
            "SI01023_P4": "PSI_INFOR",
            "SI01027_P4": "IHC",  # Colisão resolvida (SI01027)

            # --- 5º MÓDULO ---
            "SI01010_P5": "GER_PROJ",  # Colisão de código resolvida
            "SI01018_P5": "WEB_I",  # Colisão de código resolvida
            "SI01020_P5": "REDES",  # Colisão de código resolvida
            "SI01021_P5": "GES_INFO",
            "SI01028_P5": "CG_RV",
            "SI01027_P5": "SOC_INFO",  # Colisão de código resolvida

            # --- 6º MÓDULO ---
            "SI01030_P6": "WEB_II",
            "SI01031_P6": "GER_RED",
            "SI01032_P6": "DIR_LEGIS",
            "SI01033_P6": "SEG_RED",
            "SI01034_P6": "OSM",
            "SI01035_P6": "EMPREEND",
            "SI01036_P6": "INT_ART",

            # --- 7º MÓDULO ---
            "SI01037_P7": "SIS_DIST",
            "SI01038_P7": "SIG",
            "SI01039_P7": "TCC_I",
            "SI01040_P7": "ESTAGIO",
            "SI01041_P7": "ACC",

            # --- 8º MÓDULO ---
            "SI01042_P8": "DISP_MOV",
            "SI01043_P8": "AUDIT_SI",
            "SI01044_P8": "TCC_II",
            "SI01063_P8": "EXTENSAO"
        }

        # 2. CARGA DOS VÉRTICES (Lendo o CSV)
        try:
            with open(arquivo_csv, mode='r', encoding='utf-8') as f:
                leitor = csv.DictReader(f)
                for table_row in leitor:
                    cod_original = table_row['Codigo'].strip()
                    periodo = table_row['Periodo_Modulo'].strip()
                    id_unico = f"{cod_original}_P{periodo}"
                    ch_limpa = re.sub(r'\D', '', table_row['Carga_Horaria'])

                    # BUSCA CORRIGIDA: Agora ele procura pela chave "SI01001_P1" e não mais por "SI01001"
                    sigla_curta = abreviacoes.get(id_unico, cod_original[:8])

                    grafo.adicionar_disciplina(
                        id_unico=id_unico,
                        codigo_original=cod_original,
                        nome=table_row['Disciplina'].strip(),
                        carga_horaria=ch_limpa if ch_limpa else 68,
                        periodo=periodo
                    )

                    # Injeta a sigla na estrutura do vértice para que qualquer função possa ler depois
                    grafo.vertices[id_unico]["sigla"] = sigla_curta

        except FileNotFoundError:
            print(f"Erro: O arquivo '{arquivo_csv}' não foi encontrado.")
            return None

        # 2. DEFINIÇÃO DAS ARESTAS (Todos os seus blocos de pré-requisitos)
        # TRILHA DE PROGRAMAÇÃO E ESTRUTURAS DE DADOS
        grafo.adicionar_pre_requisito("SI01001_P1", "SI01007_P2")  # Programação I -> Programação II
        grafo.adicionar_pre_requisito("SI01007_P2", "SI01015_P2")  # Programação II -> Estrutura de Dados I
        grafo.adicionar_pre_requisito("SI01015_P2", "SI01019_P3")  # Estrutura de Dados I -> Estrutura de Dados II
        grafo.adicionar_pre_requisito("SI01019_P3", "SI01036_P6")  # Estrutura de Dados II -> Inteligência Artificial

        # --- TRILHA DE ENGENHARIA DE SOFTWARE E BANCO DE DADOS ---
        grafo.adicionar_pre_requisito("SI01007_P2", "SI01016_P3")  # Programação II -> Engenharia de Software
        grafo.adicionar_pre_requisito("SI01015_P2", "SI01014_P3")  # Estrutura de Dados I -> Banco de Dados I
        grafo.adicionar_pre_requisito("SI01014_P3", "SI01020_P4")  # Banco de Dados I -> Banco de Dados II
        grafo.adicionar_pre_requisito("SI01016_P3", "SI01010_P4")  # Eng. Software -> Análise e Projeto de Sistemas
        grafo.adicionar_pre_requisito("SI01010_P4", "SI01010_P5")  # Análise e Proj. -> Gerência e Projeto de Software

        # --- TRILHA DE DESENVOLVIMENTO WEB E DISTRIBUÍDOS ---
        grafo.adicionar_pre_requisito("SI01007_P2", "SI01018_P5")  # Programação II -> Desenv. para Web I
        grafo.adicionar_pre_requisito("SI01018_P5", "SI01030_P6")  # Desenv. para Web I -> Desenv. para Web II
        grafo.adicionar_pre_requisito("SI01021_P4", "SI01037_P7")  # Sistemas Operacionais -> Sistemas Distribuídos

        # --- TRILHA DE ARQUITETURA, REDES E SEGURANÇA ---
        grafo.adicionar_pre_requisito("SI01011_P2",
                                      "SI01021_P4")  # Org. e Arq. de Computadores -> Sistemas Operacionais
        grafo.adicionar_pre_requisito("SI01021_P4", "SI01020_P5")  # Sistemas Operacionais -> Redes de Computadores
        grafo.adicionar_pre_requisito("SI01020_P5", "SI01031_P6")  # Redes de Computadores -> Ger. de Redes
        grafo.adicionar_pre_requisito("SI01020_P5", "SI01033_P6")  # Redes de Computadores -> Seg. em Redes
        grafo.adicionar_pre_requisito("SI01033_P6", "SI01043_P8")  # Seg. em Redes -> Seg. e Auditoria de SI

        # --- TRILHA DE MATEMÁTICA E CÁLCULO ---
        grafo.adicionar_pre_requisito("SI01002_P1", "SI01008_P2")  # Matemática Discreta -> Cálculo I
        grafo.adicionar_pre_requisito("SI01004_P1", "SI01013_P3")  # Estatística -> Probabilidade

        # --- TRILHA DE ADMINISTRAÇÃO E EMPREENDEDORISMO ---
        grafo.adicionar_pre_requisito("SI01012_P3", "SI01018_P4")  # Administração I -> Administração II
        grafo.adicionar_pre_requisito("SI01018_P4",
                                      "SI01034_P6")  # Administração II -> Organização de Sistemas e Métodos
        grafo.adicionar_pre_requisito("SI01034_P6", "SI01035_P6")  # Org. Sistemas e Métodos -> Empreendedorismo

        # --- TRILHA DE FORMATURA (TCC E ESTÁGIO) ---
        grafo.adicionar_pre_requisito("SI01005_P1", "SI01039_P7")  # Metodologia Científica -> TCC I
        grafo.adicionar_pre_requisito("SI01016_P3", "SI01040_P7")  # Engenharia de Software -> Estágio Supervisionado
        grafo.adicionar_pre_requisito("SI01039_P7", "SI01044_P8")  # Trabalho de Conclusão de Curso I -> TCC II
        return grafo

if __name__ == "__main__":
    grafo = carregar_grafo_completo()
    arquivo_csv = ("grade_sistemas_informacao_completa.csv")

    # 1. CARGA COMPLETA DOS VÉRTICES (Resolvendo a colisão de IDs duplicados)
    try:
        with open(arquivo_csv, mode='r', encoding='utf-8') as f:
            leitor = csv.DictReader(f)
            for table_row in leitor:
                cod_original = table_row['Codigo'].strip()
                periodo = table_row['Periodo_Modulo'].strip()
                id_unico = f"{cod_original}_P{periodo}"

                ch_limpa = re.sub(r'\D', '', table_row['Carga_Horaria'])

                grafo.adicionar_disciplina(
                    id_unico=id_unico,
                    codigo_original=cod_original,
                    nome=table_row['Disciplina'].strip(),
                    carga_horaria=ch_limpa if ch_limpa else 68,
                    periodo=periodo
                )
    except FileNotFoundError:
        print(
            f"Erro: O arquivo '{arquivo_csv}' não foi encontrado. Certifique-se de que ele está na mesma pasta do script.")
        exit()


    # ele ainda executa os prints e simulações como antes.
if __name__ == "__main__":
        grafo = carregar_grafo_completo()
        if grafo:
            print("--- 1. DETECÇÃO DE CICLOS (VIABILIDADE) ---")
            if grafo.tem_ciclo():
                print("RESULTADO: Ciclo detectado! Grade curricular com erros de amarração circular.\n")
            else:
                print("RESULTADO: Grafo acíclico (DAG). Estrutura curricular viável.\n")

            # Código para colocar dentro do bloco `if __name__ == "__main__":`
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

            # -------------------------------------------------------------------------
            # CENÁRIO A: Relaxando Engenharia de Software -> Estágio
            # -------------------------------------------------------------------------
            print("\n[Cenário A] Removendo pré-requisito de Eng. de Software para Estágio...")
            grafo_simulado_A = GrafoCurricular()
            for c, v in grafo.vertices.items():
                grafo_simulado_A.adicionar_disciplina(c, v["codigo_orig"], v["nome"], v["ch"], v["periodo"])

            for u in grafo.adjacencia:
                for v in grafo.adjacencia[u]:
                    if u == "SI01016_P3" and v == "SI01040_P7":
                        continue
                    grafo_simulado_A.adicionar_pre_requisito(u, v)

            _, tempo_A = grafo_simulado_A.calcular_caminho_critico()
            print(
                f"-> Resultado Cenário A: Tempo mínimo travado em {tempo_A}h (Pelas trilhas de IA, Banco e Projetos).")

            # -------------------------------------------------------------------------
            # CENÁRIO B: Relaxando TAMBÉM a trilha de Inteligência Artificial
            # -------------------------------------------------------------------------
            print("\n[Cenário B] Removendo TAMBÉM o pré-requisito de ED II para Inteligência Artificial...")
            grafo_simulado_B = GrafoCurricular()
            for c, v in grafo.vertices.items():
                grafo_simulado_B.adicionar_disciplina(c, v["codigo_orig"], v["nome"], v["ch"], v["periodo"])

            for u in grafo.adjacencia:
                for v in grafo.adjacencia[u]:
                    if (u == "SI01016_P3" and v == "SI01040_P7") or (u == "SI01019_P3" and v == "SI01036_P6"):
                        continue
                    grafo_simulado_B.adicionar_pre_requisito(u, v)

            _, tempo_B = grafo_simulado_B.calcular_caminho_critico()
            print(
                f"-> Resultado Cenário B: Tempo continuou em {tempo_B}h (Pois as cadeias de Banco de Dados e Projetos sustentam o peso).")

            # -------------------------------------------------------------------------
            # CENÁRIO C: Cortando o Gargalo Principal (Programação I -> Programação II)
            # -------------------------------------------------------------------------
            print("\n[Cenário C] Removendo a restrição principal: Programação I -> Programação II...")
            grafo_simulado_C = GrafoCurricular()
            for c, v in grafo.vertices.items():
                grafo_simulado_C.adicionar_disciplina(c, v["codigo_orig"], v["nome"], v["ch"], v["periodo"])

            for u in grafo.adjacencia:
                for v in grafo.adjacencia[u]:
                    # Mantém todos os relaxamentos passados e quebra o nó principal de Prog II
                    if (u == "SI01016_P3" and v == "SI01040_P7") or \
                            (u == "SI01019_P3" and v == "SI01036_P6") or \
                            (u == "SI01001_P1" and v == "SI01007_P2"):
                        continue
                    grafo_simulado_C.adicionar_pre_requisito(u, v)

            _, tempo_C = grafo_simulado_C.calcular_caminho_critico()
            print(f"-> Resultado Cenário C: O tempo máximo finalmente despencou para {tempo_C}h!")

            # -------------------------------------------------------------------------
            # CENÁRIO D: Relaxamento Total (A melhor carga horária possível)
            # -------------------------------------------------------------------------
            print("\n[Cenário D] Simulando relaxamento TOTAL de todos os pré-requisitos...")
            grafo_simulado_D = GrafoCurricular()

            # Adicionamos apenas as disciplinas (vértices), deixando a lista de arestas vazia
            for c, v in grafo.vertices.items():
                grafo_simulado_D.adicionar_disciplina(c, v["codigo_orig"], v["nome"], v["ch"], v["periodo"])

            # NENHUMA aresta é adicionada aqui (grafo sem dependências)

            _, tempo_D = grafo_simulado_D.calcular_caminho_critico()
            print(f"-> Resultado Cenário D: O tempo mínimo absoluto caiu para {tempo_D}h!")
            print(f"   (Equivale à maior disciplina isolada do curso: Atividades de Extensão Universitária).")

