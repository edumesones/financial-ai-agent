# backend/app/services/extractors/csv_extractor.py
"""
Extractor flexible para archivos CSV.

NO asume columnas fijas - detecta automáticamente.
"""

import csv
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class CSVExtractor:
    """
    Extractor de CSV que detecta columnas automáticamente.
    
    Busca columnas por palabras clave en lugar de nombres fijos.
    """
    
    # Palabras clave para detectar cada tipo de columna
    FECHA_KEYWORDS = ['fecha', 'date', 'fec', 'f.valor', 'f.operacion', 'datetime']
    CONCEPTO_KEYWORDS = ['concepto', 'descripcion', 'description', 'desc', 'detalle', 'observaciones']
    IMPORTE_KEYWORDS = ['importe', 'amount', 'monto', 'cantidad', 'valor', 'debe', 'haber']
    REFERENCIA_KEYWORDS = ['referencia', 'reference', 'ref', 'num', 'numero']
    
    def __init__(self):
        self.delimiter = None
        self.encoding = None
    
    def _detect_delimiter(self, file_path: str) -> str:
        """
        Detecta el delimitador del CSV.
        
        Prueba: coma, punto y coma, tabulador
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline()
        
        # Contar ocurrencias de cada delimitador
        counts = {
            ',': first_line.count(','),
            ';': first_line.count(';'),
            '\t': first_line.count('\t'),
        }
        
        # Retornar el más común
        return max(counts, key=counts.get)
    
    def _detect_encoding(self, file_path: str) -> str:
        """
        Detecta el encoding del archivo.
        
        Prueba: utf-8, latin-1, cp1252
        """
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read()
                return encoding
            except UnicodeDecodeError:
                continue
        
        return 'utf-8'  # Fallback
    
    def _match_column(self, col_name: str, keywords: List[str]) -> bool:
        """
        Verifica si el nombre de columna coincide con alguna palabra clave.
        """
        col_name_lower = col_name.lower().strip()
        return any(keyword in col_name_lower for keyword in keywords)
    
    def _detect_columns(self, headers: List[str]) -> Dict[str, Optional[int]]:
        """
        Detecta qué columna corresponde a qué campo.
        
        Returns:
            {
                'fecha': index or None,
                'concepto': index or None,
                'importe': index or None,
                'referencia': index or None
            }
        """
        mapping = {
            'fecha': None,
            'concepto': None,
            'importe': None,
            'referencia': None
        }
        
        for idx, header in enumerate(headers):
            if mapping['fecha'] is None and self._match_column(header, self.FECHA_KEYWORDS):
                mapping['fecha'] = idx
            elif mapping['concepto'] is None and self._match_column(header, self.CONCEPTO_KEYWORDS):
                mapping['concepto'] = idx
            elif mapping['importe'] is None and self._match_column(header, self.IMPORTE_KEYWORDS):
                mapping['importe'] = idx
            elif mapping['referencia'] is None and self._match_column(header, self.REFERENCIA_KEYWORDS):
                mapping['referencia'] = idx
        
        return mapping
    
    async def extract(self, file_path: str) -> List[Dict]:
        """
        Extrae transacciones del CSV de forma flexible.
        
        Returns:
            Lista de transacciones en formato estándar
        """
        # Detectar encoding y delimitador
        self.encoding = self._detect_encoding(file_path)
        self.delimiter = self._detect_delimiter(file_path)
        
        transacciones = []
        
        with open(file_path, 'r', encoding=self.encoding) as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            
            # Leer encabezados
            try:
                headers = next(reader)
            except StopIteration:
                raise ValueError("Archivo CSV vacío")
            
            # Detectar columnas
            col_mapping = self._detect_columns(headers)
            
            # Validar que al menos tengamos fecha e importe
            if col_mapping['fecha'] is None:
                raise ValueError(
                    f"No se pudo detectar columna de fecha. "
                    f"Encabezados: {headers}"
                )
            
            if col_mapping['importe'] is None:
                raise ValueError(
                    f"No se pudo detectar columna de importe. "
                    f"Encabezados: {headers}"
                )
            
            # Leer filas
            for row_idx, row in enumerate(reader, start=2):  # Start at 2 (header=1)
                if not row or len(row) < 2:  # Fila vacía
                    continue
                
                try:
                    tx = {
                        'fecha': row[col_mapping['fecha']].strip(),
                        'concepto': row[col_mapping['concepto']].strip() if col_mapping['concepto'] is not None else '',
                        'importe': row[col_mapping['importe']].strip(),
                        'referencia': row[col_mapping['referencia']].strip() if col_mapping['referencia'] is not None else None,
                        'metadata': {
                            'linea': row_idx,
                            'formato': 'csv',
                            'delimiter': self.delimiter,
                            'encoding': self.encoding
                        }
                    }
                    transacciones.append(tx)
                
                except IndexError:
                    # Fila incompleta, skip
                    continue
        
        return transacciones

