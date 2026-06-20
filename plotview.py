import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from teste import carregar_grafo_completo

# Mapeamento manual baseado estritamente na estrutura de dados que você cadastrou no seu arquivo principal
trilhas_dados = {
    "Programação / ED": {"disciplinas": 5, "pre_requisitos": 4},
    "Eng. Software / BD": {"disciplinas": 5, "pre_requisitos": 4},
    "Dev Web / Distribuídos": {"disciplinas": 4, "pre_requisitos": 3},
    "Arq. / Redes / Seg.": {"disciplinas": 6, "pre_requisitos": 5},
    "Matemática": {"disciplinas": 4, "pre_requisitos": 2},
    "Adm. / Empreendedorismo": {"disciplinas": 4, "pre_requisitos": 3},
    "Formatura (TCC/Estágio)": {"disciplinas": 4, "pre_requisitos": 3}
}

# Preparando os dados para a plotagem
nomes_trilhas = list(trilhas_dados.keys())
qtd_vertices = [info["disciplinas"] for info in trilhas_dados.values()]
qtd_arestas = [info["pre_requisitos"] for info in trilhas_dados.values()]

x = np.arange(len(nomes_trilhas))  # Localização das trilhas no eixo X
largura = 0.35  # Largura das barras

fig, ax = plt.subplots(figsize=(14, 7))

# Plotagem das duas barras lado a lado
barra_vertices = ax.bar(x - largura/2, qtd_vertices, largura, label='Disciplinas (Vértices)', color='#0984e3', edgecolor='black', alpha=0.9)
barra_arestas = ax.bar(x + largura/2, qtd_arestas, largura, label='Pré-requisitos (Arestas)', color='#2d3436', edgecolor='black', alpha=0.9)

# Customização técnica e acadêmica do gráfico
ax.set_title('Análise de Complexidade de Grafo por Trilha Curricular\n(Mapeamento de Pontos Críticos de Acoplamento)', fontsize=14, fontweight='bold', pad=15)
ax.set_xlabel('Trilhas Acadêmicas do Curso', fontsize=12, labelpad=10)
ax.set_ylabel('Quantidade Absoluta no Sistema', fontsize=12, labelpad=10)
ax.set_xticks(x)
ax.set_xticklabels(nomes_trilhas, rotation=15, ha='right', fontsize=10)
ax.set_yticks(range(0, max(qtd_vertices) + 2))
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.legend(fontsize=11)

# Adiciona os números exatos em cima de cada barra para facilitar a leitura no relatório
def adicionar_rotulos(barras):
    for barra in barras:
        altura = barra.get_height()
        ax.annotate(f'{altura}',
                    xy=(barra.get_x() + barra.get_width() / 2, altura),
                    xytext=(0, 3),  # 3 pontos de deslocamento vertical
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

adicionar_rotulos(barra_vertices)
adicionar_rotulos(barra_arestas)

plt.tight_layout()

# Salva a imagem para o seu grupo anexar na seção de Viabilidade do Plano
plt.savefig("grafico_complexidade_ciclos.png", dpi=300)
print("Gráfico de análise de ciclos gerado com sucesso como 'grafico_complexidade_ciclos.png'!")
plt.show()

def plotar_grafo_curricular():
    # 1. Obtém o grafo populado com as disciplinas e pré-requisitos do seu CSV
    grafo_dados = carregar_grafo_completo()

    if not grafo_dados:
        print("Erro ao carregar os dados do grafo.")
        return

    # 2. Calcula o CPM para sabermos quais disciplinas são críticas (folga == 0)
    cpm_dados, _ = grafo_dados.calcular_caminho_critico()

    # 3. Cria o objeto de Grafo Direcionado do NetworkX
    G = nx.DiGraph()

    # 4. Alimenta o NetworkX com os vértices e define as cores dos nós
    cores_nos = []
    labels = {}

    # Ordena por período para que a distribuição visual faça sentido cronológico
    dados_ordenados = sorted(cpm_dados.items(), key=lambda x: int(x[1]['periodo']))

    for id_u, dados in dados_ordenados:
        G.add_node(id_u)

        labels[id_u] = dados.get("sigla", dados.get("codigo_orig"))

        if dados["critica"]:
            cores_nos.append('#ff7675')
        else:
            cores_nos.append('#74b9ff')

    # 5. Alimenta o NetworkX com as arestas (os pré-requisitos reais)
    cores_arestas = []
    for u in grafo_dados.adjacencia:
        for v in grafo_dados.adjacencia[u]:
            G.add_edge(u, v)

    # 6. Configuração do Layout de exibição (Posicionamento dos nós)
    plt.figure(figsize=(16, 10))

    # O shell_layout ou multipartite_layout tenta agrupar, mas o spring_layout com k maior afasta os nós espremidos
    pos = nx.spring_layout(G, k=0.8, iterations=50, seed=42)

    # 7. Desenha os componentes do Grafo
    # Desenha os nós (círculos)
    nx.draw_networkx_nodes(G, pos, node_color=cores_nos, node_size=1800, edgecolors='black', alpha=0.9)

    # Desenha as setas direcionais
    nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20, edge_color='#636e72', width=1.5)

    # Desenha os textos (Códigos das disciplinas) dentro dos nós
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', font_family='sans-serif')

    # 8. Customizações acadêmicas e legenda
    plt.title(
        "Grafo de Dependências Curriculares (Análise CPM)\nEm Vermelho: Caminho Crítico (Folga = 0) | Em Azul: Matérias com Folga",
        fontsize=14, fontweight='bold', pad=20)

    # Adiciona uma legenda manual flutuante para o relatório
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#ff7675', edgecolor='black', label='Trilha Crítica (Gargalo do Curso)'),
        Patch(facecolor='#74b9ff', edgecolor='black', label='Matéria com Margem de Folga')
    ]
    plt.legend(handles=legend_elements, loc='upper left', fontsize=12)

    # Remove as bordas dos eixos cartesianos para ficar limpo
    plt.axis('off')
    plt.tight_layout()

    # 9. Salva a imagem com alta resolução para o relatório do grupo
    plt.savefig("grafo_mapa_curricular.png", dpi=300)
    print("Grafo gerado e salvo com sucesso como 'grafo_mapa_curricular.png'!")
    plt.show()


if __name__ == "__main__":
    plotar_grafo_curricular()