# Modelo de Tráfego Nagel-Schreckenberg

## 🇧🇷 Português

### Descrição
Implementação do modelo de tráfego Nagel-Schreckenberg (NS) - um autômato celular para simulação de fluxo de tráfego veicular. Este projeto faz parte de uma disciplina de Sistemas Distribuídos.

### Características
- **Versão Sequencial**: Implementação básica do modelo NS
- Fronteiras abertas (veículos entram e saem)
- Detecção de congestionamentos
- Estatísticas de velocidade média e taxa de fluxo

### Parâmetros Principais
- Comprimento da estrada: 1000 células (~7.5 km)
- Veículos iniciais: 100
- Velocidade máxima: 5 células/passo (~135 km/h)
- Passos de tempo: 100
- Velocidade inicial: 2-3 células/passo (~60-90 km/h)

### Como Executar
```bash
python nagel_schreckenberg.py
```

### Próximas Versões
- ⏳ Implementação paralela (memória compartilhada)
- ⏳ Implementação distribuída (sensível à latência)

---

## 🇬🇧 English

### Description
Implementation of the Nagel-Schreckenberg (NS) traffic model - a cellular automaton for vehicular traffic flow simulation. This project is part of a Distributed Systems course assignment.

### Features
- **Sequential Version**: Basic NS model implementation
- Open boundaries (vehicles enter and exit)
- Traffic jam detection
- Average velocity and flow rate statistics

### Main Parameters
- Road length: 1000 cells (~7.5 km)
- Initial vehicles: 100
- Maximum velocity: 5 cells/step (~135 km/h)
- Time steps: 100
- Initial velocity: 2-3 cells/step (~60-90 km/h)

### How to Run
```bash
python nagel_schreckenberg.py
```

### Upcoming Versions
- ⏳ Parallel implementation (shared memory)
- ⏳ Distributed implementation (latency-sensitive)

---

## 📊 Model Overview

The Nagel-Schreckenberg model simulates traffic flow using four simple rules applied each time step:

1. **Acceleration**: Increase velocity by 1 (if below max)
2. **Deceleration**: Slow down to avoid collision with vehicle ahead
3. **Randomization**: Random slowdown with probability p (human behavior)
4. **Movement**: Move forward by current velocity

## 🔧 Requirements
- Python 3.x
- NumPy