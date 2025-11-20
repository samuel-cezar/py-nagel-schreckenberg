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
    print("BENCHMARK: SEQUENCIAL vs PARALELO (NumPy) - Modelo Nagel-Schreckenberg")
    print("=" * 80)
    
    tempos = {}
    
    # Executar versão sequencial
    print("\n[1/2] VERSÃO SEQUENCIAL (Python puro)")
    tempos['sequencial'] = executar_e_medir("sequencial.py")
    
    # Executar versão paralela
    print("\n[2/2] VERSÃO PARALELA (NumPy vetorizado)")
    tempos['paralelo'] = executar_e_medir("paralelo.py")
    
    # Exibir resumo comparativo
    print("\n" + "=" * 80)
    print("RESUMO COMPARATIVO DE PERFORMANCE")
    print("=" * 80)
    
    if tempos['sequencial'] is not None and tempos['paralelo'] is not None:
        print(f"\nTempo Sequencial (Python Nativo):  {tempos['sequencial']:.3f}s")
        print(f"Tempo Paralelo (NumPy):            {tempos['paralelo']:.3f}s")
        
        speedup = tempos['sequencial'] / tempos['paralelo']
        reducao_percentual = ((tempos['sequencial'] - tempos['paralelo']) / tempos['sequencial']) * 100
        
        print(f"\nSpeedup (Sequencial / Paralelo):   {speedup:.2f}x")
        print(f"Redução de Tempo:                  {reducao_percentual:.1f}%")
        
        if tempos['paralelo'] < tempos['sequencial']:
            print(f"\n✓ Versão paralela é {speedup:.2f}x mais rápida!")
        elif tempos['paralelo'] > tempos['sequencial']:
            print(f"\n✗ Versão sequencial foi mais rápida")
        else:
            print(f"\n≈ Tempos similares")
    
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
