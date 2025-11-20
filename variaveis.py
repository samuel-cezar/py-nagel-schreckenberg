# ============================================
# VARIÁVEIS COMPARTILHADAS
# ============================================
# Parâmetros de configuração da simulação
# Utilizadas em todas as implementações:
# - sequencial.py
# - paralelo.py
# - distribuido_sockets.py
# - distribuido_rmi.py

# PARÂMETROS DA ESTRADA
COMPRIMENTO_DA_ESTRADA = 1_000_000  # Número de células na estrada
NUM_VEICULOS = 1_000  # Número inicial de veículos
VELOCIDADE_MAXIMA = 5  # Velocidade máxima (células por passo de tempo)

# PARÂMETROS DE COMPORTAMENTO
PROBABILIDADE_DESACELERAR = 0.5  # Probabilidade de desaceleração aleatória
TAXA_ENTRADA = 0.5  # Probabilidade de um novo carro entrar por passo de tempo

# PARÂMETROS DE SIMULAÇÃO
PASSOS_DE_TEMPO = 300  # Número de passos de simulação
LIMIAR_CONGESTIONAMENTO = 5  # Carros lentos consecutivos para detectar um congestionamento

# VELOCIDADE INICIAL DOS VEÍCULOS
# Faixa inicial de velocidade (km/h convertida para células/passo)
# Supondo 1 célula = 7,5m, 1 passo de tempo = 1 segundo
# 60-80 km/h ≈ 16,7-22,2 m/s ≈ 2-3 células/passo
VELOCIDADE_INICIAL_MINIMA = 2
VELOCIDADE_INICIAL_MAXIMA = 3

# PARÂMETROS DE DISTRIBUIÇÃO (para distribuido_sockets.py e distribuido_rmi.py)
NUM_WORKERS = 4
PORTA_BASE = 9090
HOST = 'localhost'
