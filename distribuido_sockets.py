import socket
import struct
import numpy as np
import threading
import time
import sys
from typing import Tuple, List
from variaveis import (
    COMPRIMENTO_DA_ESTRADA,
    NUM_VEICULOS,
    VELOCIDADE_MAXIMA,
    PROBABILIDADE_DESACELERAR,
    PASSOS_DE_TEMPO,
    TAXA_ENTRADA,
    LIMIAR_CONGESTIONAMENTO,
    VELOCIDADE_INICIAL_MINIMA,
    VELOCIDADE_INICIAL_MAXIMA,
    NUM_WORKERS,
    PORTA_BASE,
    HOST
)

# ============================================
# PROTOCOLO DE COMUNICAÇÃO
# ============================================
# Mensagem: [TIPO (1)] [TAMANHO (4)] [DADOS (N)]
TIPO_DADOS = 0
TIPO_COMANDO = 1
TIPO_RESPOSTA = 2

def serializar_array(arr: np.ndarray) -> bytes:
    """Serializar numpy array para bytes"""
    arr_typed = arr.astype(np.int32)
    return arr_typed.tobytes()

def desserializar_array(dados: bytes, dtype=np.int32) -> np.ndarray:
    """Desserializar bytes para numpy array"""
    return np.frombuffer(dados, dtype=dtype)

def enviar_mensagem(sock: socket.socket, tipo: int, dados: bytes) -> None:
    """Enviar mensagem via socket com protocolo"""
    tamanho = len(dados)
    header = struct.pack('!BI', tipo, tamanho)
    sock.sendall(header + dados)

def receber_mensagem(sock: socket.socket) -> Tuple[int, bytes]:
    """Receber mensagem via socket com protocolo"""
    # Receber header (5 bytes: tipo + tamanho)
    header = b''
    while len(header) < 5:
        chunk = sock.recv(5 - len(header))
        if not chunk:
            raise ConnectionError("Conexão fechada")
        header += chunk
    
    tipo, tamanho = struct.unpack('!BI', header)
    
    # Receber dados
    dados = b''
    while len(dados) < tamanho:
        chunk = sock.recv(min(8192, tamanho - len(dados)))
        if not chunk:
            raise ConnectionError("Conexão fechada durante transferência de dados")
        dados += chunk
    
    return tipo, dados

# ============================================
# WORKER (DISTRIBUÍDO)
# ============================================

class WorkerSockets:
    def __init__(self, worker_id: int, porta: int, inicio: int, fim: int):
        self.worker_id = worker_id
        self.porta = porta
        self.inicio = inicio
        self.fim = fim
        self.tamanho_secao = fim - inicio
        
        # Estadísticas
        self.velocidade_total = 0
        self.veiculos_medidos_total = 0
        self.veiculos_sairam = 0
        self.congestionamentos_detectados = 0
        self.passo_de_tempo = 0
        
        self.socket = None
        self.conn = None

    def _inicializar_socket(self) -> None:
        """Inicializar socket e aguardar conexão do master"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((HOST, self.porta))
        self.socket.listen(1)
        print(f"[Worker {self.worker_id}] Aguardando conexão na porta {self.porta}...")
        
        self.conn, addr = self.socket.accept()
        print(f"[Worker {self.worker_id}] Master conectado: {addr}")

    def _etapa_aceleracao(self, secao: np.ndarray) -> None:
        """Etapa 1: Acelerar"""
        mask = (secao != -1)
        secao[mask] = np.minimum(secao[mask] + 1, VELOCIDADE_MAXIMA)

    def _calcular_distancias_proximos_veiculos(self, secao: np.ndarray) -> np.ndarray:
        """Calcular distâncias com wrap-around"""
        tem_veiculo = (secao != -1).astype(np.int32)
        distancias = np.full(len(secao), len(secao), dtype=np.int32)
        
        for offset in range(1, VELOCIDADE_MAXIMA + 2):
            proximos = np.roll(tem_veiculo, -offset)
            mask = (secao != -1) & (distancias == len(secao)) & proximos
            distancias[mask] = offset
        
        return distancias

    def _etapa_desaceleracao(self, secao: np.ndarray) -> None:
        """Etapa 2: Desacelerar para evitar colisão"""
        distancias = self._calcular_distancias_proximos_veiculos(secao)
        mask = (secao != -1)
        secao[mask] = np.minimum(secao[mask], distancias[mask])

    def _etapa_randomizacao(self, secao: np.ndarray) -> None:
        """Etapa 3: Randomização"""
        mask_veiculos = (secao > 0)
        probabilidades = np.random.random(len(secao))
        mask_desaceleracao = mask_veiculos & (probabilidades < PROBABILIDADE_DESACELERAR)
        secao[mask_desaceleracao] -= 1

    def _etapa_movimento(self, secao: np.ndarray) -> Tuple[np.ndarray, int]:
        """Etapa 4: Movimento com tratamento de bordas"""
        secao_final = np.full(len(secao), -1, dtype=np.int32)
        
        mask_veiculos = (secao != -1)
        indices = np.where(mask_veiculos)[0]
        velocidades = secao[indices]
        
        # Novas posições relativas à seção
        novas_posicoes = indices + velocidades
        
        # Veículos que saem pela direita
        mask_saem = novas_posicoes >= len(secao)
        veiculos_saem_local = np.sum(mask_saem)
        
        # Veículos que ficam
        mask_ficam = ~mask_saem
        novas_posicoes_validas = novas_posicoes[mask_ficam]
        velocidades_validas = velocidades[mask_ficam]
        
        secao_final[novas_posicoes_validas] = velocidades_validas
        
        return secao_final, veiculos_saem_local

    def _coletar_estatisticas(self, secao: np.ndarray) -> None:
        """Coletar estatísticas da seção"""
        mask_veiculos = (secao != -1)
        self.velocidade_total += np.sum(secao[mask_veiculos])
        self.veiculos_medidos_total += np.sum(mask_veiculos)

    def _detectar_congestionamentos(self, secao: np.ndarray) -> None:
        """Detectar congestionamentos"""
        lentos = ((secao != -1) & (secao <= 1)).astype(np.int32)
        kernel = np.ones(LIMIAR_CONGESTIONAMENTO, dtype=np.int32)
        convolucao = np.convolve(lentos, kernel, mode='valid')
        self.congestionamentos_detectados += np.sum(convolucao >= LIMIAR_CONGESTIONAMENTO)

    def processar_passo(self, estrada_global: np.ndarray) -> Tuple[np.ndarray, int]:
        """Processar um passo da simulação"""
        # Extrair seção local
        secao = estrada_global[self.inicio:self.fim].copy()
        
        # Aplicar etapas
        self._etapa_aceleracao(secao)
        self._etapa_desaceleracao(secao)
        self._etapa_randomizacao(secao)
        secao, saidas = self._etapa_movimento(secao)
        
        # Coletar estatísticas
        self._coletar_estatisticas(secao)
        self._detectar_congestionamentos(secao)
        
        self.veiculos_sairam += saidas
        self.passo_de_tempo += 1
        
        return secao, saidas

    def run(self) -> None:
        """Loop principal do worker"""
        try:
            self._inicializar_socket()
            print(f"[Worker {self.worker_id}] Pronto para processar")
            
            passo_count = 0
            while True:
                try:
                    # Receber comando/dados do master
                    tipo, dados = receber_mensagem(self.conn)
                    
                    if tipo == TIPO_COMANDO:
                        comando = dados.decode('utf-8')
                        if comando == "SAIR":
                            print(f"[Worker {self.worker_id}] Encerrando...")
                            break
                    
                    elif tipo == TIPO_DADOS:
                        # Dados recebidos: processar e enviar resultado
                        print(f"[Worker {self.worker_id}] Recebido passo {passo_count}")
                        estrada_global = desserializar_array(dados)
                        
                        secao_processada, saidas = self.processar_passo(estrada_global)
                        
                        # Enviar resultado
                        resposta = serializar_array(secao_processada)
                        enviar_mensagem(self.conn, TIPO_RESPOSTA, resposta)
                        print(f"[Worker {self.worker_id}] Passo {passo_count} processado e enviado")
                        passo_count += 1
                
                except Exception as e:
                    print(f"[Worker {self.worker_id}] Erro no loop: {e}")
                    import traceback
                    traceback.print_exc()
                    break
        
        except Exception as e:
            print(f"[Worker {self.worker_id}] Erro crítico: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            if self.conn:
                self.conn.close()
            if self.socket:
                self.socket.close()
            print(f"[Worker {self.worker_id}] Encerrado")

    def obter_estatisticas(self):
        """Obter estatísticas do worker"""
        velocidade_media = self.velocidade_total / self.veiculos_medidos_total if self.veiculos_medidos_total > 0 else 0
        return {
            'velocidade_media': velocidade_media,
            'veiculos_sairam': self.veiculos_sairam,
            'congestionamentos': self.congestionamentos_detectados,
            'passos': self.passo_de_tempo
        }

# ============================================
# MASTER (ORQUESTRADOR)
# ============================================

class MasterSockets:
    def __init__(self, num_workers: int = NUM_WORKERS):
        self.num_workers = num_workers
        self.estrada = np.full(COMPRIMENTO_DA_ESTRADA, -1, dtype=np.int32)
        self.conexoes: List[socket.socket] = []
        self.passo_de_tempo = 0
        
        # Estatísticas globais
        self.velocidade_total = 0
        self.veiculos_medidos_total = 0
        self.veiculos_sairam = 0
        self.congestionamentos_detectados = 0
        
        self._inicializar_veiculos()

    def _inicializar_veiculos(self) -> None:
        """Inicializar veículos na estrada"""
        posicoes = np.random.choice(COMPRIMENTO_DA_ESTRADA, 
                                     size=min(NUM_VEICULOS, COMPRIMENTO_DA_ESTRADA), 
                                     replace=False)
        velocidades = np.random.randint(VELOCIDADE_INICIAL_MINIMA, 
                                         VELOCIDADE_INICIAL_MAXIMA + 1, 
                                         size=len(posicoes))
        velocidades = np.minimum(velocidades, VELOCIDADE_MAXIMA)
        self.estrada[posicoes] = velocidades

    def conectar_workers(self) -> None:
        """Conectar aos workers"""
        print("[Master] Conectando aos workers...")
        
        for i in range(self.num_workers):
            porta = PORTA_BASE + i
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Tentar conectar com retry
            for tentativa in range(5):
                try:
                    sock.connect((HOST, porta))
                    print(f"[Master] Worker {i} conectado na porta {porta}")
                    self.conexoes.append(sock)
                    break
                except ConnectionRefusedError:
                    if tentativa < 4:
                        print(f"[Master] Tentando worker {i} novamente ({tentativa + 1}/5)...")
                        time.sleep(1)
                    else:
                        print(f"[Master] Erro: Worker {i} não respondeu")
                        raise

    def enviar_para_workers(self, estrada: np.ndarray) -> None:
        """Enviar estrada para todos os workers em paralelo"""
        dados = serializar_array(estrada)
        
        threads = []
        for i, conn in enumerate(self.conexoes):
            def enviar_worker(idx, sock, dados_param):
                try:
                    enviar_mensagem(sock, TIPO_DADOS, dados_param)
                except Exception as e:
                    print(f"[Master] Erro ao enviar para worker {idx}: {e}")
            
            t = threading.Thread(target=enviar_worker, args=(i, conn, dados))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()

    def receber_de_workers(self) -> List[np.ndarray]:
        """Receber resultados de todos os workers em paralelo"""
        resultados = [None] * self.num_workers
        threads = []
        
        def receber_worker(idx, sock):
            try:
                tipo, dados = receber_mensagem(sock)
                if tipo == TIPO_RESPOSTA:
                    arr = desserializar_array(dados)
                    resultados[idx] = arr
            except Exception as e:
                print(f"[Master] Erro ao receber de worker {idx}: {e}")
        
        for i, conn in enumerate(self.conexoes):
            t = threading.Thread(target=receber_worker, args=(i, conn))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join(timeout=10)
        
        return resultados

    def _tentar_entrada_veiculo(self) -> None:
        """Tentar adicionar novo veículo na entrada"""
        if np.random.random() < TAXA_ENTRADA and self.estrada[0] == -1:
            distancia_proximo = 0
            for i in range(1, min(10, COMPRIMENTO_DA_ESTRADA)):
                if self.estrada[i] != -1:
                    break
                distancia_proximo += 1
            
            if distancia_proximo > 0:
                nova_velocidade = np.random.randint(VELOCIDADE_INICIAL_MINIMA, 
                                                     VELOCIDADE_INICIAL_MAXIMA + 1)
                nova_velocidade = min(nova_velocidade, VELOCIDADE_MAXIMA)
                self.estrada[0] = nova_velocidade

    def _coletar_estatisticas(self) -> None:
        """Coletar estatísticas globais"""
        mask_veiculos = (self.estrada != -1)
        self.velocidade_total += np.sum(self.estrada[mask_veiculos])
        self.veiculos_medidos_total += np.sum(mask_veiculos)

    def passo(self) -> None:
        """Executar um passo de simulação distribuído"""
        # Enviar estrada para workers
        self.enviar_para_workers(self.estrada)
        
        # Receber resultados
        resultados = self.receber_de_workers()
        
        # Verificar se todos responderam (evitar erro com arrays)
        nenhum_responden = sum(1 for r in resultados if r is None)
        if nenhum_responden > 0:
            raise RuntimeError(f"{nenhum_responden} workers não responderam")
        
        # Recombinar
        self.estrada = np.concatenate(resultados)
        
        # Tentar adicionar novo veículo na entrada
        self._tentar_entrada_veiculo()
        
        # Coletar estatísticas
        self._coletar_estatisticas()
        
        # Contar saídas (aproximado)
        mask_vazio_final = (self.estrada == -1)
        self.veiculos_sairam = int(NUM_VEICULOS + self.passo_de_tempo - np.sum(mask_vazio_final == False))
        
        self.passo_de_tempo += 1

    def visualizar(self) -> None:
        """Visualizar estado da estrada"""
        visualizacao = []
        for celula in self.estrada[:100]:
            if celula == -1:
                visualizacao.append('.')
            else:
                visualizacao.append(str(celula))
        
        print(f"Passo {self.passo_de_tempo:3d}: {''.join(visualizacao)}")

    def obter_estatisticas(self):
        """Obter estatísticas finais"""
        velocidade_media = self.velocidade_total / self.veiculos_medidos_total if self.veiculos_medidos_total > 0 else 0
        
        return {
            'velocidade_media': velocidade_media,
            'veiculos_sairam': self.veiculos_sairam,
            'passos': self.passo_de_tempo
        }

    def fechar_workers(self) -> None:
        """Encerrar workers"""
        print("[Master] Encerrando workers...")
        for conn in self.conexoes:
            try:
                enviar_mensagem(conn, TIPO_COMANDO, b"SAIR")
                conn.close()
            except:
                pass

# ============================================
# MODO EXECUÇÃO
# ============================================

def executar_master():
    """Executar o master"""
    print("=" * 80)
    print("MASTER - SIMULAÇÃO NAGEL-SCHRECKENBERG (Distribuída com Sockets)")
    print("=" * 80)
    print(f"Comprimento: {COMPRIMENTO_DA_ESTRADA} células")
    print(f"Veículos: {NUM_VEICULOS}")
    print(f"Workers: {NUM_WORKERS}")
    print(f"Passos: {PASSOS_DE_TEMPO}")
    print("=" * 80)
    print()
    
    tempo_inicio = time.time()
    
    try:
        master = MasterSockets(NUM_WORKERS)
        master.conectar_workers()
        
        print("Iniciando simulação...\n")
        for passo in range(PASSOS_DE_TEMPO):
            master.passo()
            
            if passo % 1 == 0 or passo == PASSOS_DE_TEMPO - 1:
                master.visualizar()
        
        tempo_decorrido = time.time() - tempo_inicio
        
        print("\n" + "=" * 80)
        print("ESTATÍSTICAS FINAIS")
        print("=" * 80)
        stats = master.obter_estatisticas()
        print(f"Velocidade Média: {stats['velocidade_media']:.3f} células/passo")
        print(f"Veículos Saíram: {stats['veiculos_sairam']}")
        print(f"Passos: {stats['passos']}")
        print(f"Tempo Total: {tempo_decorrido:.3f}s")
        print("=" * 80)
        
        master.fechar_workers()
    
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

def executar_worker(worker_id: int):
    """Executar um worker"""
    porta = PORTA_BASE + worker_id
    tamanho_secao = COMPRIMENTO_DA_ESTRADA // NUM_WORKERS
    inicio = worker_id * tamanho_secao
    fim = inicio + tamanho_secao if worker_id < NUM_WORKERS - 1 else COMPRIMENTO_DA_ESTRADA
    
    worker = WorkerSockets(worker_id, porta, inicio, fim)
    worker.run()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "master":
            executar_master()
        elif sys.argv[1] == "worker":
            worker_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0
            executar_worker(worker_id)
    else:
        print("Uso:")
        print("  python distribuido_sockets.py master")
        print("  python distribuido_sockets.py worker <id>")
