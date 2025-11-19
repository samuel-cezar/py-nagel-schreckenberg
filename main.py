import subprocess
import time
import sys

# ============================================
# BENCHMARK COMPARATIVO
# ============================================

def executar_e_medir(script_nome):
    """Executar um script e medir o tempo de execução"""
    print(f"\n{'=' * 80}")
    print(f"Executando: {script_nome}")
    print(f"{'=' * 80}\n")
    
    inicio = time.time()
    
    try:
        # Executar o script Python
        resultado = subprocess.run(
            [sys.executable, script_nome],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Exibir saída do script
        print(resultado.stdout)
        
        tempo_decorrido = time.time() - inicio
        
        return tempo_decorrido
    
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar {script_nome}:")
        print(e.stderr)
        return None

def main():
    """Comparar tempo de execução entre sequencial e paralelo"""
    print("\n" + "=" * 80)
    print("BENCHMARK: SEQUENCIAL vs PARALELO (NumPy)")
    print("=" * 80)
    
    # Executar versão sequencial
    tempo_sequencial = executar_e_medir("sequencial.py")
    
    # Executar versão paralela
    tempo_paralelo = executar_e_medir("paralelo.py")
    
    # Exibir resumo comparativo
    print("\n" + "=" * 80)
    print("RESUMO COMPARATIVO")
    print("=" * 80)
    
    if tempo_sequencial is not None and tempo_paralelo is not None:
        print(f"Tempo Sequencial (Python Nativo):  {tempo_sequencial:.3f}s")
        print(f"Tempo Paralelo (NumPy):            {tempo_paralelo:.3f}s")
        
        speedup = tempo_sequencial / tempo_paralelo
        reducao_percentual = ((tempo_sequencial - tempo_paralelo) / tempo_sequencial) * 100
        
        print(f"\nSpeedup (Sequencial / Paralelo):   {speedup:.2f}x")
        print(f"Redução de Tempo:                  {reducao_percentual:.1f}%")
        
        if tempo_paralelo < tempo_sequencial:
            print(f"\n✓ Versão paralela é {speedup:.2f}x mais rápida!")
        elif tempo_paralelo > tempo_sequencial:
            print(f"\n✗ Versão sequencial foi mais rápida (possível overhead de NumPy)")
        else:
            print(f"\n≈ Tempos similares")
    
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
