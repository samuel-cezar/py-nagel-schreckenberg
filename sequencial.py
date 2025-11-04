import random
import numpy as np
from collections import deque

# ============================================
# PARÂMETROS DE CONFIGURAÇÃO
# ============================================
COMPRIMENTO_DA_ESTRADA = 1000  # Número de células na estrada
NUM_VEICULOS = 100  # Número inicial de veículos
VELOCIDADE_MAXIMA = 5  # Velocidade máxima (células por passo de tempo)
PROBABILIDADE_DESACELERAR = 0.3  # Probabilidade de desaceleração aleatória
PASSOS_DE_TEMPO = 100  # Número de passos de simulação
TAXA_ENTRADA = 0.3  # Probabilidade de um novo carro entrar por passo de tempo
LIMIAR_CONGESTIONAMENTO = 5  # Carros lentos consecutivos para detectar um congestionamento

# Faixa inicial de velocidade (km/h convertida para células/passo)
# Supondo 1 célula = 7,5m, 1 passo de tempo = 1 segundo
# 60-80 km/h ≈ 16,7-22,2 m/s ≈ 2-3 células/passo
VELOCIDADE_INICIAL_MINIMA = 2
VELOCIDADE_INICIAL_MAXIMA = 3

# ============================================
# MODELO DE NAGEL-SCHRECKENBERG
# ============================================

class ModeloNagelSchreckenberg:
    def __init__(self):
        # Estrada representada como array: -1 = vazio, >=0 = velocidade do veículo
        self.estrada = np.full(COMPRIMENTO_DA_ESTRADA, -1, dtype=int)
        self.passo_de_tempo = 0

        # Rastreamento de estatísticas
        self.velocidade_total = 0
        self.veiculos_medidos_total = 0
        self.veiculos_sairam = 0
        self.veiculos_entraram = 0
        self.congestionamentos_detectados = 0

        # Inicializar veículos
        self._inicializar_veiculos()

    def _inicializar_veiculos(self):
        """Colocar veículos iniciais aleatoriamente na estrada"""
        posicoes = random.sample(range(COMPRIMENTO_DA_ESTRADA), min(NUM_VEICULOS, COMPRIMENTO_DA_ESTRADA))
        for pos in posicoes:
            velocidade = random.randint(VELOCIDADE_INICIAL_MINIMA, VELOCIDADE_INICIAL_MAXIMA)
            velocidade = min(velocidade, VELOCIDADE_MAXIMA)
            self.estrada[pos] = velocidade
            self.veiculos_entraram += 1

    def _obter_distancia_para_proximo_veiculo(self, posicao):
        """Calcular distância para o próximo veículo à frente"""
        distancia = 0
        for i in range(1, COMPRIMENTO_DA_ESTRADA):
            posicao_verificar = (posicao + i) % COMPRIMENTO_DA_ESTRADA
            if self.estrada[posicao_verificar] != -1:
                return distancia
            distancia += 1
        return distancia

    def _etapa_aceleracao(self, nova_estrada):
        """Etapa 1: Acelerar veículos se abaixo da velocidade máxima"""
        for i in range(COMPRIMENTO_DA_ESTRADA):
            if self.estrada[i] != -1:
                nova_estrada[i] = min(self.estrada[i] + 1, VELOCIDADE_MAXIMA)

    def _etapa_desaceleracao(self, nova_estrada):
        """Etapa 2: Reduzir velocidade para evitar colisão"""
        for i in range(COMPRIMENTO_DA_ESTRADA):
            if nova_estrada[i] != -1:
                distancia = self._obter_distancia_para_proximo_veiculo(i)
                nova_estrada[i] = min(nova_estrada[i], distancia)

    def _etapa_randomizacao(self, nova_estrada):
        """Etapa 3: Desaceleração aleatória com probabilidade p"""
        for i in range(COMPRIMENTO_DA_ESTRADA):
            if nova_estrada[i] > 0 and random.random() < PROBABILIDADE_DESACELERAR:
                nova_estrada[i] -= 1

    def _etapa_movimento(self, nova_estrada):
        """Etapa 4: Mover veículos para frente com base em sua velocidade"""
        estrada_final = np.full(COMPRIMENTO_DA_ESTRADA, -1, dtype=int)

        for i in range(COMPRIMENTO_DA_ESTRADA):
            if nova_estrada[i] != -1:
                velocidade = nova_estrada[i]
                nova_posicao = i + velocidade

                # Lidar com saída (fronteira aberta)
                if nova_posicao >= COMPRIMENTO_DA_ESTRADA:
                    self.veiculos_sairam += 1
                else:
                    estrada_final[nova_posicao] = velocidade

        return estrada_final

    def _tentar_entrada_veiculo(self, estrada):
        """Tentar adicionar um novo veículo na entrada (posição 0)"""
        if random.random() < TAXA_ENTRADA and estrada[0] == -1:
            # Verificar se há espaço suficiente para entrada
            if self._obter_distancia_para_proximo_veiculo(0) > 0:
                estrada[0] = random.randint(VELOCIDADE_INICIAL_MINIMA, min(VELOCIDADE_INICIAL_MAXIMA, VELOCIDADE_MAXIMA))
                self.veiculos_entraram += 1

    def _detectar_congestionamentos(self):
        """Detectar congestionamentos (veículos consecutivos com baixa velocidade)"""
        lentos_consecutivos = 0

        for i in range(COMPRIMENTO_DA_ESTRADA):
            if self.estrada[i] != -1 and self.estrada[i] <= 1:
                lentos_consecutivos += 1
                if lentos_consecutivos >= LIMIAR_CONGESTIONAMENTO:
                    self.congestionamentos_detectados += 1
                    # Avançar para evitar contagem dupla
                    while i < COMPRIMENTO_DA_ESTRADA and self.estrada[i] != -1:
                        i += 1
                    lentos_consecutivos = 0
            else:
                lentos_consecutivos = 0

    def _coletar_estatisticas(self):
        """Coletar estatísticas de velocidade para este passo de tempo"""
        for velocidade in self.estrada:
            if velocidade != -1:
                self.velocidade_total += velocidade
                self.veiculos_medidos_total += 1

    def passo(self):
        """Executar um passo de tempo do modelo NS"""
        # Criar cópia de trabalho para atualizações
        nova_estrada = np.copy(self.estrada)

        # Aplicar regras do modelo NS
        self._etapa_aceleracao(nova_estrada)
        self._etapa_desaceleracao(nova_estrada)
        self._etapa_randomizacao(nova_estrada)
        self.estrada = self._etapa_movimento(nova_estrada)

        # Tentar adicionar novo veículo na entrada
        self._tentar_entrada_veiculo(self.estrada)

        # Coletar estatísticas
        self._coletar_estatisticas()
        self._detectar_congestionamentos()

        self.passo_de_tempo += 1

    def visualizar(self):
        """Visualização simples em texto do estado atual da estrada"""
        visualizacao = []
        for celula in self.estrada:
            if celula == -1:
                visualizacao.append('.')
            else:
                visualizacao.append(str(celula))

        print(f"Passo {self.passo_de_tempo:3d}: {''.join(visualizacao[:100])}")  # Mostrar as primeiras 100 células

    def obter_estatisticas(self):
        """Calcular e retornar estatísticas finais"""
        velocidade_media = self.velocidade_total / self.veiculos_medidos_total if self.veiculos_medidos_total > 0 else 0

        # Taxa de fluxo: veículos por passo de tempo
        taxa_fluxo = self.veiculos_sairam / self.passo_de_tempo if self.passo_de_tempo > 0 else 0

        return {
            'velocidade_media': velocidade_media,
            'taxa_fluxo': taxa_fluxo,
            'congestionamentos_totais': self.congestionamentos_detectados,
            'veiculos_entraram': self.veiculos_entraram,
            'veiculos_sairam': self.veiculos_sairam,
            'passos_de_tempo': self.passo_de_tempo
        }

# ============================================
# SIMULAÇÃO PRINCIPAL
# ============================================

def executar_simulacao():
    """Executar a simulação completa do tráfego NS"""
    print("=" * 80)
    print("SIMULAÇÃO DE TRÁFEGO NAGEL-SCHRECKENBERG (Sequencial)")
    print("=" * 80)
    print(f"Comprimento da Estrada: {COMPRIMENTO_DA_ESTRADA} células")
    print(f"Veículos Iniciais: {NUM_VEICULOS}")
    print(f"Velocidade Máxima: {VELOCIDADE_MAXIMA} células/passo")
    print(f"Probabilidade de Desaceleração: {PROBABILIDADE_DESACELERAR}")
    print(f"Passos de Tempo: {PASSOS_DE_TEMPO}")
    print(f"Taxa de Entrada: {TAXA_ENTRADA}")
    print("=" * 80)
    print()

    # Criar modelo
    modelo = ModeloNagelSchreckenberg()

    # Executar simulação
    print("Iniciando simulação...\n")
    for passo in range(PASSOS_DE_TEMPO):
        modelo.passo()

        # Visualizar a cada 10 passos
        if passo % 10 == 0 or passo == PASSOS_DE_TEMPO - 1:
            modelo.visualizar()

    # Exibir estatísticas finais
    print("\n" + "=" * 80)
    print("ESTATÍSTICAS FINAIS")
    print("=" * 80)
    estatisticas = modelo.obter_estatisticas()
    print(f"Velocidade Média: {estatisticas['velocidade_media']:.3f} células/passo")
    print(f"Taxa de Fluxo: {estatisticas['taxa_fluxo']:.3f} veículos/passo")
    print(f"Total de Congestionamentos Detectados: {estatisticas['congestionamentos_totais']}")
    print(f"Veículos Entraram: {estatisticas['veiculos_entraram']}")
    print(f"Veículos Saíram: {estatisticas['veiculos_sairam']}")
    print(f"Passos de Tempo Simulados: {estatisticas['passos_de_tempo']}")
    print("=" * 80)

if __name__ == "__main__":
    executar_simulacao()