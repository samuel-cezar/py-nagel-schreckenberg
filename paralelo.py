import random
import numpy as np

# ============================================
# PARÂMETROS DE CONFIGURAÇÃO
# ============================================
COMPRIMENTO_DA_ESTRADA = 1_000_000  # Número de células na estrada
NUM_VEICULOS = 1_000  # Número inicial de veículos
VELOCIDADE_MAXIMA = 5  # Velocidade máxima (células por passo de tempo)
PROBABILIDADE_DESACELERAR = 0.5  # Probabilidade de desaceleração aleatória
PASSOS_DE_TEMPO = 100  # Número de passos de simulação
TAXA_ENTRADA = 0.5  # Probabilidade de um novo carro entrar por passo de tempo
LIMIAR_CONGESTIONAMENTO = 5  # Carros lentos consecutivos para detectar um congestionamento

# Faixa inicial de velocidade
VELOCIDADE_INICIAL_MINIMA = 2
VELOCIDADE_INICIAL_MAXIMA = 3

# ============================================
# MODELO DE NAGEL-SCHRECKENBERG (VECTORIZADO)
# ============================================

class ModeloNagelSchreckenberg:
    def __init__(self):
        # Estrada representada como array: -1 = vazio, >=0 = velocidade do veículo
        self.estrada = np.full(COMPRIMENTO_DA_ESTRADA, -1, dtype=np.int32)
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
        """Colocar veículos iniciais aleatoriamente na estrada (vectorizado)"""
        posicoes = np.random.choice(COMPRIMENTO_DA_ESTRADA, size=min(NUM_VEICULOS, COMPRIMENTO_DA_ESTRADA), replace=False)
        velocidades = np.random.randint(VELOCIDADE_INICIAL_MINIMA, VELOCIDADE_INICIAL_MAXIMA + 1, size=len(posicoes))
        velocidades = np.minimum(velocidades, VELOCIDADE_MAXIMA)
        self.estrada[posicoes] = velocidades
        self.veiculos_entraram = len(posicoes)

    def _calcular_distancias_proximos_veiculos(self):
        """Calcular distância para próximo veículo para cada posição (vectorizado com convolução)"""
        # Criar máscara de veículos
        tem_veiculo = (self.estrada != -1).astype(np.int32)
        
        # Para cada posição, encontrar o próximo veículo
        distancias = np.full(COMPRIMENTO_DA_ESTRADA, COMPRIMENTO_DA_ESTRADA, dtype=np.int32)
        
        # Processar em chunks para evitar overhead de memória
        for offset in range(1, VELOCIDADE_MAXIMA + 2):
            # Deslocar a máscara de veículos
            proximos = np.roll(tem_veiculo, -offset)
            
            # Atualizar distâncias onde não temos veículo e há um à frente
            mask = (self.estrada != -1) & (distancias == COMPRIMENTO_DA_ESTRADA) & proximos
            distancias[mask] = offset
        
        return distancias

    def _etapa_aceleracao(self):
        """Etapa 1: Acelerar veículos (vectorizado)"""
        mask_veiculos = (self.estrada != -1)
        self.estrada[mask_veiculos] = np.minimum(self.estrada[mask_veiculos] + 1, VELOCIDADE_MAXIMA)

    def _etapa_desaceleracao(self):
        """Etapa 2: Reduzir velocidade para evitar colisão (vectorizado)"""
        distancias = self._calcular_distancias_proximos_veiculos()
        mask_veiculos = (self.estrada != -1)
        self.estrada[mask_veiculos] = np.minimum(self.estrada[mask_veiculos], distancias[mask_veiculos])

    def _etapa_randomizacao(self):
        """Etapa 3: Desaceleração aleatória (vectorizado)"""
        mask_veiculos = (self.estrada > 0)
        probabilidades = np.random.random(COMPRIMENTO_DA_ESTRADA)
        mask_desaceleração = mask_veiculos & (probabilidades < PROBABILIDADE_DESACELERAR)
        self.estrada[mask_desaceleração] -= 1

    def _etapa_movimento(self):
        """Etapa 4: Mover veículos (vectorizado)"""
        estrada_final = np.full(COMPRIMENTO_DA_ESTRADA, -1, dtype=np.int32)
        
        # Identificar onde há veículos
        mask_veiculos = (self.estrada != -1)
        indices_veiculos = np.where(mask_veiculos)[0]
        velocidades = self.estrada[indices_veiculos]
        
        # Calcular novas posições
        novas_posicoes = indices_veiculos + velocidades
        
        # Contar quantos saem
        mask_saem = novas_posicoes >= COMPRIMENTO_DA_ESTRADA
        self.veiculos_sairam += np.sum(mask_saem)
        
        # Colocar veículos que não saem nas novas posições
        mask_ficam = ~mask_saem
        novas_posicoes_validas = novas_posicoes[mask_ficam]
        velocidades_validas = velocidades[mask_ficam]
        
        estrada_final[novas_posicoes_validas] = velocidades_validas
        
        return estrada_final

    def _tentar_entrada_veiculo(self):
        """Tentar adicionar novo veículo na entrada (vectorizado)"""
        # Probabilidade de entrada
        if np.random.random() < TAXA_ENTRADA and self.estrada[0] == -1:
            # Verificar se há espaço (próximo veículo a mais de 1 célula)
            distancia_proximo = 0
            for i in range(1, min(10, COMPRIMENTO_DA_ESTRADA)):
                if self.estrada[i] != -1:
                    break
                distancia_proximo += 1
            
            if distancia_proximo > 0:
                nova_velocidade = np.random.randint(VELOCIDADE_INICIAL_MINIMA, VELOCIDADE_INICIAL_MAXIMA + 1)
                nova_velocidade = min(nova_velocidade, VELOCIDADE_MAXIMA)
                self.estrada[0] = nova_velocidade
                self.veiculos_entraram += 1

    def _detectar_congestionamentos(self):
        """Detectar congestionamentos (vectorizado com convolução)"""
        # Máscara de veículos lentos
        lentos = ((self.estrada != -1) & (self.estrada <= 1)).astype(np.int32)
        
        # Usar convolução para encontrar sequências de lentos
        kernel = np.ones(LIMIAR_CONGESTIONAMENTO, dtype=np.int32)
        convolucao = np.convolve(lentos, kernel, mode='valid')
        
        # Contar sequências contíguas de lentos
        self.congestionamentos_detectados += np.sum(convolucao >= LIMIAR_CONGESTIONAMENTO)

    def _coletar_estatisticas(self):
        """Coletar estatísticas (vectorizado)"""
        mask_veiculos = (self.estrada != -1)
        self.velocidade_total += np.sum(self.estrada[mask_veiculos])
        self.veiculos_medidos_total += np.sum(mask_veiculos)

    def passo(self):
        """Executar um passo de tempo do modelo NS"""
        self._etapa_aceleracao()
        self._etapa_desaceleracao()
        self._etapa_randomizacao()
        self.estrada = self._etapa_movimento()

        # Tentar adicionar novo veículo na entrada
        self._tentar_entrada_veiculo()

        # Coletar estatísticas
        self._coletar_estatisticas()
        self._detectar_congestionamentos()

        self.passo_de_tempo += 1

    def visualizar(self):
        """Visualização simples em texto do estado atual da estrada"""
        visualizacao = []
        for celula in self.estrada[:100]:
            if celula == -1:
                visualizacao.append('.')
            else:
                visualizacao.append(str(celula))

        print(f"Passo {self.passo_de_tempo:3d}: {''.join(visualizacao)}")

    def obter_estatisticas(self):
        """Calcular e retornar estatísticas finais"""
        velocidade_media = self.velocidade_total / self.veiculos_medidos_total if self.veiculos_medidos_total > 0 else 0
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
    print("SIMULAÇÃO DE TRÁFEGO NAGEL-SCHRECKENBERG (Vectorizado - NumPy)")
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