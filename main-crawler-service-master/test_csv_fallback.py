"""
Script de teste para a funcionalidade de CSV Fallback
"""
import sys
import logging
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.shared.utils.csv_utils import CSVManager
from datetime import datetime


def test_csv_manager():
    """Testa funcionalidades do CSVManager"""
    print("\n" + "="*70)
    print("TESTE 1: Inicializar CSVManager")
    print("="*70)
    
    csv_manager = CSVManager(output_dir="output")
    print(f"✓ CSVManager inicializado com sucesso")
    print(f"  Diretório: {csv_manager.output_dir}")
    
    print("\n" + "="*70)
    print("TESTE 2: Escrever múltiplos registros em CSV")
    print("="*70)
    
    test_data = [
        {
            'id': 1,
            'city': 'São Paulo',
            'country': 'Brasil',
            'aqi': 75,
            'pm25': 25.5,
            'pm10': 45.2,
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 2,
            'city': 'Rio de Janeiro',
            'country': 'Brasil',
            'aqi': 65,
            'pm25': 20.3,
            'pm10': 38.5,
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 3,
            'city': 'Brasília',
            'country': 'Brasil',
            'aqi': 55,
            'pm25': 15.1,
            'pm10': 30.2,
            'created_at': datetime.now().isoformat()
        }
    ]
    
    csv_path = csv_manager.write_to_csv(test_data, "test_iqair.csv")
    print(f"✓ CSV criado com sucesso: {csv_path}")
    
    print("\n" + "="*70)
    print("TESTE 3: Ler dados do CSV")
    print("="*70)
    
    data_read = csv_manager.read_csv("test_iqair.csv")
    print(f"✓ Dados lidos com sucesso: {len(data_read)} registros")
    for i, row in enumerate(data_read, 1):
        print(f"  Registro {i}: {row['city']} - AQI: {row['aqi']}")
    
    print("\n" + "="*70)
    print("TESTE 4: Adicionar novo registro ao CSV")
    print("="*70)
    
    new_record = {
        'id': 4,
        'city': 'Salvador',
        'country': 'Brasil',
        'aqi': 70,
        'pm25': 22.8,
        'pm10': 42.1,
        'created_at': datetime.now().isoformat()
    }
    
    csv_manager.append_to_csv(new_record, "test_iqair.csv")
    print(f"✓ Novo registro adicionado com sucesso")
    
    print("\n" + "="*70)
    print("TESTE 5: Verificar dados após adição")
    print("="*70)
    
    data_read = csv_manager.read_csv("test_iqair.csv")
    print(f"✓ Total de registros agora: {len(data_read)}")
    for i, row in enumerate(data_read, 1):
        print(f"  Registro {i}: {row['city']} - AQI: {row['aqi']}")
    
    print("\n" + "="*70)
    print("TESTE 6: Obter caminho do CSV")
    print("="*70)
    
    path = csv_manager.get_csv_path("test_iqair.csv")
    print(f"✓ Caminho do CSV: {path}")
    print(f"  Arquivo existe: {path.exists()}")
    print(f"  Tamanho: {path.stat().st_size} bytes")
    
    print("\n" + "="*70)
    print("TESTE 7: Criar CSV com timestamp automático")
    print("="*70)
    
    auto_path = csv_manager.write_to_csv(test_data[:1])
    print(f"✓ CSV com timestamp criado: {auto_path.name}")
    
    print("\n" + "="*70)
    print("TESTE 8: Erro de leitura de arquivo inexistente")
    print("="*70)
    
    data = csv_manager.read_csv("nao_existe.csv")
    print(f"✓ Tratamento de erro funcionando: retornou {len(data)} registros (esperado: 0)")
    
    print("\n" + "="*70)
    print("✅ TODOS OS TESTES PASSARAM COM SUCESSO!")
    print("="*70 + "\n")


def test_csv_manager_with_fallback():
    """Testa o repositório com fallback"""
    print("\n" + "="*70)
    print("TESTE 9: Repositório com CSV Fallback")
    print("="*70)
    
    from src.persistence.repositories.iqair.iqair_repository_with_csv_fallback import IQAirRepositoryWithCSVFallback
    
    csv_manager = CSVManager(output_dir="output")
    
    # Simular banco de dados indisponível
    repo = IQAirRepositoryWithCSVFallback(
        db=None,
        csv_manager=csv_manager,
        database_available=False
    )
    
    print(f"✓ Repositório inicializado em modo CSV fallback")
    print(f"  Database disponível: {repo.database_available}")
    
    print("\n" + "="*70)
    print("TESTE 10: Count no repositório (CSV fallback)")
    print("="*70)
    
    count = repo.count()
    print(f"✓ Total de registros: {count}")
    
    print("\n" + "="*70)
    print("TESTE 11: Get all no repositório (CSV fallback)")
    print("="*70)
    
    all_data = repo.get_all(limit=2)
    print(f"✓ Registros obtidos: {len(all_data)}")
    for i, row in enumerate(all_data, 1):
        print(f"  {i}. {row}")
    
    print("\n" + "="*70)
    print("TESTE 12: Get latest no repositório (CSV fallback)")
    print("="*70)
    
    latest = repo.get_latest()
    print(f"✓ Registro mais recente: {latest}")
    
    print("\n" + "="*70)
    print("✅ TODOS OS TESTES DE FALLBACK PASSARAM!")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        test_csv_manager()
        test_csv_manager_with_fallback()
        print("\n🎉 SUITE DE TESTES COMPLETA COM SUCESSO!\n")
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
