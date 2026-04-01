# CSV Fallback - Modo Offline

## Visão Geral

Quando o banco de dados não está disponível, a aplicação automaticamente ativa um modo de fallback que armazena os dados em arquivos CSV em vez de no banco de dados.

## Como Funciona

### 1. **Inicialização Automática** (`main.py`)

Quando a aplicação inicia:
- Tenta conectar ao banco de dados com até **30 tentativas** (com intervalo de 1 segundo)
- Se conseguir conectar, usa o banco de dados normalmente
- Se não conseguir após todas as tentativas:
  - Registra um aviso no log
  - Ativa o modo CSV fallback automaticamente
  - Armazena um gerenciador CSV (`CSVManager`) no estado da aplicação

### 2. **Armazenamento de Dados**

Os arquivos CSV são salvos em: `./output/`

Exemplo:
```
output/
├── iqair_data.csv
├── iqair_data_20231227_101530.csv
└── ...
```

### 3. **Como Usar no Código**

#### Opção A: Usar o wrapper com fallback automático

```python
from src.persistence.repositories.iqair.iqair_repository_with_csv_fallback import IQAirRepositoryWithCSVFallback
from fastapi import Depends

def get_iqair_repository(
    db: Session = Depends(get_db),
    request: Request
) -> IQAirRepositoryWithCSVFallback:
    """Dependency injection do repositório com fallback"""
    csv_manager = getattr(request.app.state, 'csv_manager', None)
    database_available = getattr(request.app.state, 'database_available', True)
    
    return IQAirRepositoryWithCSVFallback(
        db=db,
        csv_manager=csv_manager,
        database_available=database_available
    )
```

#### Opção B: Usar o CSVManager diretamente

```python
from src.shared.utils.csv_utils import CSVManager

# Criar dados
csv_manager = CSVManager(output_dir="output")

# Escrever múltiplos registros
data = [
    {'id': 1, 'city': 'São Paulo', 'aqi': 75},
    {'id': 2, 'city': 'Rio de Janeiro', 'aqi': 65},
]
csv_manager.write_to_csv(data, "meus_dados.csv")

# Adicionar um registro
csv_manager.append_to_csv({'id': 3, 'city': 'Brasília', 'aqi': 55}, "meus_dados.csv")

# Ler dados
data = csv_manager.read_csv("meus_dados.csv")
print(data)
```

## API do CSVManager

### Métodos disponíveis

#### `write_to_csv(data: List[Dict], filename: str = None) -> Path`
Escreve uma lista de dicionários em um arquivo CSV

```python
data = [
    {'city': 'SP', 'aqi': 75},
    {'city': 'RJ', 'aqi': 65},
]
path = csv_manager.write_to_csv(data, "dados.csv")
```

#### `append_to_csv(data: Dict, filename: str = None) -> Path`
Adiciona uma linha a um arquivo CSV existente (cria se não existir)

```python
csv_manager.append_to_csv({'city': 'MG', 'aqi': 70}, "dados.csv")
```

#### `read_csv(filename: str = None) -> List[Dict]`
Lê todos os dados de um arquivo CSV

```python
data = csv_manager.read_csv("dados.csv")
for row in data:
    print(row)
```

#### `get_csv_path(filename: str = None) -> Path`
Obtém o caminho completo de um arquivo CSV

```python
path = csv_manager.get_csv_path("dados.csv")
print(f"Arquivo em: {path}")
```

## Exemplo de Uso Completo

```python
from fastapi import FastAPI, HTTPException
from src.shared.utils.csv_utils import CSVManager

app = FastAPI()
csv_manager = CSVManager(output_dir="output")

@app.post("/data")
def create_data(city: str, aqi: int):
    """Cria um novo registro"""
    try:
        data = {
            'city': city,
            'aqi': aqi,
            'timestamp': datetime.now().isoformat()
        }
        csv_manager.append_to_csv(data, "iqair_data.csv")
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data")
def get_all_data():
    """Retorna todos os registros"""
    try:
        data = csv_manager.read_csv("iqair_data.csv")
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Logs

Todos os eventos são registrados automaticamente:

```
INFO: Banco de dados não disponível. Alterando para modo CSV fallback...
INFO: Modo CSV fallback ativado. Os dados serão armazenados em arquivos CSV em ./output/
INFO: Dados escritos com sucesso no CSV: output/iqair_data_20231227_101530.csv
INFO: Dados lidos do CSV: output/iqair_data.csv (5 linhas)
```

## Comportamento em Caso de Falha

Se o banco de dados **ficar indisponível durante a execução**:
- A aplicação continua funcionando com o CSV
- Todos os dados são salvos em arquivos CSV no diretório `output/`
- Quando o banco de dados estiver disponível novamente, você pode migrar os dados manualmente

## Migração de Dados CSV para Banco de Dados

Para migrar dados armazenados em CSV de volta ao banco de dados:

```python
from src.shared.utils.csv_utils import CSVManager
from src.persistence.repositories.iqair.iqair_repository import IQAirRepository
from src.persistence.entities.iqair.iqair_entity import IQAirEntity
from datetime import datetime

csv_manager = CSVManager()
repository = IQAirRepository(db)

# Ler dados do CSV
data = csv_manager.read_csv("iqair_data.csv")

# Migrar para banco de dados
for row in data:
    entity = IQAirEntity(
        city=row.get('city'),
        country=row.get('country'),
        aqi=float(row.get('aqi', 0)),
        pm25=float(row.get('pm25', 0)),
        # ... outros campos
        created_at=datetime.fromisoformat(row.get('created_at'))
    )
    repository.create(entity)

print(f"Migrados {len(data)} registros para o banco de dados")
```

## Estrutura de Diretórios

```
project/
├── output/                    # Diretório dos arquivos CSV
│   ├── iqair_data.csv
│   └── iqair_data_*.csv
├── src/
│   ├── shared/
│   │   ├── utils/
│   │   │   ├── csv_utils.py      # Gerenciador de CSV
│   │   │   └── ...
│   ├── persistence/
│   │   └── repositories/
│   │       └── iqair/
│   │           ├── iqair_repository.py
│   │           └── iqair_repository_with_csv_fallback.py
│   └── main.py               # Inicialização com fallback automático
```

## Considerações de Performance

- **CSV é mais lento que banco de dados** para grandes volumes
- Recomenda-se usar CSV apenas como fallback temporário
- Para produção, configure redundância e alta disponibilidade do banco de dados
- Monitorar o tamanho dos arquivos CSV (podem crescer rapidamente)

## Limpeza de Arquivos CSV Antigos

Você pode deletar arquivos CSV antigos do diretório `output/` quando não forem mais necessários:

```powershell
# PowerShell - Remove CSV com mais de 30 dias
Get-ChildItem output/*.csv | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item
```
