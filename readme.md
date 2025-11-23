# Modelo de Tráfego Nagel-Schreckenberg

## 🇧🇷 Português

### Descrição
Implementação completa do modelo de tráfego Nagel-Schreckenberg (NS) - um autômato celular para simulação de fluxo de tráfego veicular. Este projeto faz parte de uma disciplina de Sistemas Distribuídos e demonstra três abordagens diferentes: **sequencial**, **paralela** e **distribuída**.

### Características
- ✅ **Versão Sequencial** (`sequencial.py`): Implementação básica do modelo NS em Python puro
- ✅ **Versão Paralela** (`paralelo.py`): Implementação vectorizada com NumPy (até **5x mais rápida**)
- ✅ **Versão Distribuída** (`distribuido_sockets.py`): Arquitetura Master-Worker com sockets
- Fronteiras abertas (veículos entram e saem)
- Detecção de congestionamentos
- Estatísticas de velocidade média e taxa de fluxo
- Centralização de variáveis para facilitar testes

### Parâmetros Principais (em `variaveis.py`)
- Comprimento da estrada: 1.000.000 células (~7.500 km)
- Veículos iniciais: 1.000
- Velocidade máxima: 5 células/passo (~135 km/h)
- Passos de tempo: 300
- Velocidade inicial: 2-3 células/passo (~60-90 km/h)
- Número de Workers (distribuído): 4

### Como Executar

#### 1️⃣ Versão Sequencial
```bash
python sequencial.py
```

#### 2️⃣ Versão Paralela
```bash
python paralelo.py
```

#### 3️⃣ Versão Distribuída (Master-Worker com Sockets)

**Windows:**
```bash
run_sockets_test.bat
```

**Linux/Mac:**
```bash
bash run_sockets_test.sh
```

**Ou manualmente em terminais diferentes:**
```bash
# Terminal 1 (Master)
python distribuido_sockets.py master

# Terminais 2-5 (Workers 0-3)
python distribuido_sockets.py worker 0
python distribuido_sockets.py worker 1
python distribuido_sockets.py worker 2
python distribuido_sockets.py worker 3
```

#### 4️⃣ Benchmark Comparativo
```bash
python main.py
```
Compara o desempenho das versões sequencial e paralela.

---

## 🇺🇸 English

### Description
Complete implementation of the Nagel-Schreckenberg (NS) traffic model - a cellular automaton for vehicular traffic flow simulation. This project is part of a Distributed Systems course and demonstrates three different approaches: **sequential**, **parallel**, and **distributed**.

### Features
- ✅ **Sequential Version** (`sequencial.py`): Basic NS model implementation in pure Python
- ✅ **Parallel Version** (`paralelo.py`): NumPy-vectorized implementation (up to **5x faster**)
- ✅ **Distributed Version** (`distribuido_sockets.py`): Master-Worker architecture with sockets
- Open boundaries (vehicles enter and exit)
- Traffic jam detection
- Average velocity and flow rate statistics
- Centralized variables for easy testing

### Main Parameters (in `variaveis.py`)
- Road length: 1,000,000 cells (~7,500 km)
- Initial vehicles: 1,000
- Maximum velocity: 5 cells/step (~135 km/h)
- Time steps: 300
- Initial velocity: 2-3 cells/step (~60-90 km/h)
- Number of Workers (distributed): 4

### How to Run

#### 1️⃣ Sequential Version
```bash
python sequencial.py
```

#### 2️⃣ Parallel Version
```bash
python paralelo.py
```

#### 3️⃣ Distributed Version (Master-Worker with Sockets)

**Windows:**
```bash
run_sockets_test.bat
```

**Linux/Mac:**
```bash
bash run_sockets_test.sh
```

**Or manually in different terminals:**
```bash
# Terminal 1 (Master)
python distribuido_sockets.py master

# Terminals 2-5 (Workers 0-3)
python distribuido_sockets.py worker 0
python distribuido_sockets.py worker 1
python distribuido_sockets.py worker 2
python distribuido_sockets.py worker 3
```

#### 4️⃣ Comparative Benchmark
```bash
python main.py
```
Compares the performance of sequential and parallel versions.

---

## 📊 Model Overview

The Nagel-Schreckenberg model simulates traffic flow using four simple rules applied each time step:

1. **Acceleration**: Increase velocity by 1 (if below max)
2. **Deceleration**: Slow down to avoid collision with vehicle ahead
3. **Randomization**: Random slowdown with probability p (human behavior)
4. **Movement**: Move forward by current velocity

## 🏗️ Project Architecture

### File Structure
```
├── sequencial.py              # Pure Python implementation
├── paralelo.py                # NumPy-vectorized implementation
├── distribuido_sockets.py     # Master-Worker distributed implementation
├── main.py                    # Benchmark comparison tool
├── variaveis.py               # Centralized configuration
├── run_sockets_test.bat       # Automation script for Windows
├── run_sockets_test.sh        # Automation script for Linux/Mac
├── requirements.txt           # Python dependencies
└── roteiro.md                 # Development journey documentation
```

### Implementation Comparison

| Aspect | Sequential | Parallel | Distributed |
|--------|-----------|----------|-------------|
| **Speed** | Baseline | 5x faster | Network overhead |
| **Scalability** | O(n) | O(n) vectorized | Distributed workload |
| **Complexity** | Simple | Moderate | Complex |
| **Memory** | Single process | Shared memory | Network communication |
| **Best for** | Validation | Large datasets | Multi-machine setup |

## 🔧 Requirements
- Python 3.x
- NumPy
- See `requirements.txt` for full dependencies

## 📝 Development Journey

For detailed information about the development process, challenges overcome, and lessons learned, see [`roteiro.md`](roteiro.md). It includes:
- Sequential implementation basics
- Parallelization challenges and vectorization solutions
- Distributed architecture with sockets
- Variable centralization and testing organization
- Performance optimization insights

## ⚙️ Configuration

All parameters can be modified in `variaveis.py`:
```python
COMPRIMENTO_DA_ESTRADA = 1_000_000      # Road length
NUM_VEICULOS = 1_000                    # Initial vehicles
VELOCIDADE_MAXIMA = 5                   # Max velocity
PROBABILIDADE_DESACELERAR = 0.5         # Deceleration probability
PASSOS_DE_TEMPO = 300                   # Time steps
NUM_WORKERS = 4                         # Number of workers (distributed)
```

## 📚 References

This project implements the Nagel-Schreckenberg model as described in:
- K. Nagel and M. Schreckenberg, "A Cellular Automaton Model for Freeway Traffic", J. Phys. I France, 2(12), 2221-2229 (1992)

---