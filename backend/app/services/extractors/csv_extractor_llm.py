# backend/app/services/extractors/csv_extractor_llm.py
"""
Extractor CSV que usa estructura interpretada por LLM.

FASE 2: Usa las hints del LLM para parsear con más precisión.
"""

import csv
from typing import List, Dict


class CSVExtractorLLM:
    """
    Extractor CSV guiado por LLM.
    
    Recibe estructura del LLM y extrae basándose en esa información.
    """
    
    def __init__(self, estructura: Dict):
        """
        Args:
            estructura: Output del interpret_structure (LLM)
        """
        self.estructura = estructura
        self.columnas = {col['indice']: col for col in estructura.get('columnas', [])}
        self.delimiter = estructura.get('delimitador', ',')
        self.tiene_cabecera = estructura.get('tiene_cabecera', True)
        self.encoding = estructura.get('encoding_sugerido', 'utf-8')
    
    def _get_column_index_by_type(self, tipo: str) -> int:
        """Encuentra el índice de la columna por tipo."""
        for idx, col in self.columnas.items():
            if col.get('tipo') == tipo:
                return idx
        return None
    
    async def extract(self, file_path: str) -> List[Dict]:
        """
        Extrae transacciones usando la estructura del LLM.
        
        Returns:
            Lista de transacciones
        """
        # Buscar índices de columnas importantes
        fecha_idx = self._get_column_index_by_type('fecha')
        concepto_idx = self._get_column_index_by_type('texto')
        referencia_idx = self._get_column_index_by_type('referencia')
        
        # Para importes, puede haber "Debe" y "Haber" separados
        importe_indices = [idx for idx, col in self.columnas.items() if col.get('tipo') == 'numero']
        
        if fecha_idx is None:
            raise ValueError("LLM no identificó columna de fecha")
        
        if not importe_indices:
            raise ValueError("LLM no identificó columnas de importe")
        
        transacciones = []
        
        with open(file_path, 'r', encoding=self.encoding, errors='ignore') as f:
            reader = csv.reader(f, delimiter=self.delimiter)
            
            # Skip header si lo tiene
            if self.tiene_cabecera:
                try:
                    next(reader)
                except StopIteration:
                    return []
            
            for row_idx, row in enumerate(reader, start=2):
                if not row or len(row) < 2:
                    continue
                
                try:
                    # Extraer fecha
                    fecha = row[fecha_idx].strip() if fecha_idx < len(row) else ''
                    
                    # Extraer concepto
                    concepto = row[concepto_idx].strip() if concepto_idx is not None and concepto_idx < len(row) else ''
                    
                    # Extraer referencia
                    referencia = row[referencia_idx].strip() if referencia_idx is not None and referencia_idx < len(row) else None
                    
                    # Extraer importe(s)
                    # Si hay 2 columnas (Debe/Haber), combinarlas
                    if len(importe_indices) >= 2:
                        # Probablemente Debe (gasto) y Haber (ingreso)
                        debe = row[importe_indices[0]].strip() if importe_indices[0] < len(row) else ''
                        haber = row[importe_indices[1]].strip() if importe_indices[1] < len(row) else ''
                        
                        # El que tenga valor es el importe
                        if debe and debe != '0' and debe != '0,00':
                            importe = f"-{debe}"  # Gasto (negativo)
                        elif haber and haber != '0' and haber != '0,00':
                            importe = haber  # Ingreso (positivo)
                        else:
                            continue  # Skip si ambos vacíos
                    else:
                        # Una sola columna de importe
                        importe = row[importe_indices[0]].strip() if importe_indices[0] < len(row) else ''
                    
                    if not fecha or not importe:
                        continue
                    
                    tx = {
                        'fecha': fecha,
                        'concepto': concepto,
                        'importe': importe,
                        'referencia': referencia,
                        'metadata': {
                            'linea': row_idx,
                            'formato': 'csv',
                            'extractor': 'llm-guided',
                            'llm_estructura': True
                        }
                    }
                    transacciones.append(tx)
                
                except (IndexError, ValueError):
                    continue
        
        return transacciones

