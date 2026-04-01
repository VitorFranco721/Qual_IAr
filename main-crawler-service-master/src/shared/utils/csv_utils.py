"""
Utilitários para gerenciar CSV como fallback quando o banco de dados não está disponível
"""
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class CSVManager:
    """Gerenciador de CSV para armazenar dados quando o banco de dados não está disponível"""
    
    def __init__(self, output_dir: str = "output"):
        """
        Inicializa o gerenciador de CSV
        
        Args:
            output_dir: Diretório onde os arquivos CSV serão armazenados
        """
        output_path = Path(output_dir)
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / output_path

        self.output_dir = output_path
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"CSVManager usando diretório de saída: {self.output_dir}")
    
    def get_csv_path(self, filename: str = None) -> Path:
        """
        Obtém o caminho do arquivo CSV
        
        Args:
            filename: Nome do arquivo (padrão: iqair_data_{timestamp}.csv)
        
        Returns:
            Path: Caminho completo do arquivo CSV
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"iqair_data_{timestamp}.csv"
        
        return self.output_dir / filename
    
    def write_to_csv(self, data: List[Dict[str, Any]], filename: str = None) -> Path:
        """
        Escreve dados em um arquivo CSV
        
        Args:
            data: Lista de dicionários com os dados
            filename: Nome do arquivo (padrão: iqair_data_{timestamp}.csv)
        
        Returns:
            Path: Caminho do arquivo criado
        """
        if not data:
            self.logger.warning("Nenhum dado para escrever no CSV")
            return None
        
        csv_path = self.get_csv_path(filename)
        
        try:
            processed_data, fieldnames = self._prepare_rows_for_write(data)
            if not fieldnames:
                self.logger.warning("Nenhuma coluna válida para escrever no CSV")
                return None # type: ignore
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(processed_data)
            
            self.logger.info(f"Dados escritos com sucesso no CSV: {csv_path}")
            return csv_path
        except Exception as e:
            self.logger.error(f"Erro ao escrever no CSV: {e}")
            raise
    
    def append_to_csv(self, data: Dict[str, Any], filename: str = None) -> Path:
        """
        Adiciona uma linha a um arquivo CSV existente
        
        Args:
            data: Dicionário com os dados da linha
            filename: Nome do arquivo (se não existir, será criado)
        
        Returns:
            Path: Caminho do arquivo
        """
        csv_path = self.get_csv_path(filename)
        
        try:
            existing_rows: List[Dict[str, Any]] = []

            if csv_path.exists():
                with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    existing_rows = list(reader)

            all_rows = existing_rows + [data]
            processed_rows, fieldnames = self._prepare_rows_for_write(all_rows)

            if not fieldnames:
                self.logger.warning("Nenhuma coluna válida para atualizar o CSV")
                return csv_path

            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(processed_rows)
            
            self.logger.info(f"Linha adicionada ao CSV: {csv_path}")
            return csv_path
        except Exception as e:
            self.logger.error(f"Erro ao adicionar linha ao CSV: {e}")
            raise

    def _is_empty_value(self, value: Any) -> bool:
        if value is None:
            return True
        value_str = str(value).strip()
        return value_str == "" or value_str.lower() in {"none", "null", "nan", "na"}

    def _prepare_rows_for_write(self, rows: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[str]]:
        if not rows:
            return [], []

        ordered_fields: List[str] = []
        for row in rows:
            for field in row.keys():
                if field not in ordered_fields:
                    ordered_fields.append(field)

        non_empty_fields = [
            field for field in ordered_fields
            if any(not self._is_empty_value(row.get(field, "")) for row in rows)
        ]

        processed_rows: List[Dict[str, Any]] = []
        for row in rows:
            processed_row = {field: row.get(field, "") for field in non_empty_fields}
            processed_rows.append(processed_row)

        return processed_rows, non_empty_fields
    
    def read_csv(self, filename: str = None) -> List[Dict[str, Any]]: # pyright: ignore[reportArgumentType]
        """
        Lê dados de um arquivo CSV
        
        Args:
            filename: Nome do arquivo CSV
        
        Returns:
            List[Dict]: Lista de dicionários com os dados do CSV
        """
        csv_path = self.get_csv_path(filename)
        
        if not csv_path.exists():
            self.logger.warning(f"Arquivo CSV não encontrado: {csv_path}")
            return []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                data = list(reader)
            
            self.logger.info(f"Dados lidos do CSV: {csv_path} ({len(data)} linhas)")
            return data
        except Exception as e:
            self.logger.error(f"Erro ao ler CSV: {e}")
            raise
