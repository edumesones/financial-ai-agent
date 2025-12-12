# backend/app/services/extractors/excel_extractor_llm.py
"""
Extractor Excel que usa estructura interpretada por LLM.

FASE 2: Usa las hints del LLM para parsear con más precisión.
"""

import openpyxl
from typing import List, Dict


class ExcelExtractorLLM:
    """
    Extractor Excel guiado por LLM.
    
    Recibe estructura del LLM y extrae basándose en esa información.
    """
    
    def __init__(self, estructura: Dict):
        """
        Args:
            estructura: Output del interpret_structure (LLM)
        """
        self.estructura = estructura
        self.columnas = {col['indice']: col for col in estructura.get('columnas', [])}
        self.tiene_cabecera = estructura.get('tiene_cabecera', True)
    
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
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.active
        
        # Buscar índices de columnas importantes
        fecha_idx = self._get_column_index_by_type('fecha')
        concepto_idx = self._get_column_index_by_type('texto')
        referencia_idx = self._get_column_index_by_type('referencia')
        
        # Para importes, puede haber "Debe" y "Haber" separados
        importe_indices = [idx for idx, col in self.columnas.items() if col.get('tipo') == 'numero']
        
        if fecha_idx is None:
            workbook.close()
            raise ValueError("LLM no identificó columna de fecha")
        
        if not importe_indices:
            workbook.close()
            raise ValueError("LLM no identificó columnas de importe")
        
        transacciones = []
        rows = list(sheet.iter_rows(values_only=True))
        
        # Skip header si lo tiene
        start_row = 1 if self.tiene_cabecera else 0
        
        for row_idx, row in enumerate(rows[start_row:], start=start_row + 1):
            if not row or all(cell is None for cell in row):
                continue
            
            try:
                # Extraer fecha
                fecha_val = row[fecha_idx] if fecha_idx < len(row) else None
                if not fecha_val:
                    continue
                
                fecha = str(fecha_val).strip()
                
                # Extraer concepto
                concepto_val = row[concepto_idx] if concepto_idx is not None and concepto_idx < len(row) else ''
                concepto = str(concepto_val).strip() if concepto_val else ''
                
                # Extraer referencia
                ref_val = row[referencia_idx] if referencia_idx is not None and referencia_idx < len(row) else None
                referencia = str(ref_val).strip() if ref_val else None
                
                # Extraer importe(s)
                if len(importe_indices) >= 2:
                    # Debe/Haber
                    debe_val = row[importe_indices[0]] if importe_indices[0] < len(row) else None
                    haber_val = row[importe_indices[1]] if importe_indices[1] < len(row) else None
                    
                    debe = str(debe_val).strip() if debe_val not in (None, '', 0) else ''
                    haber = str(haber_val).strip() if haber_val not in (None, '', 0) else ''
                    
                    if debe and debe != '0':
                        importe = f"-{debe}"
                    elif haber and haber != '0':
                        importe = haber
                    else:
                        continue
                else:
                    # Una columna
                    importe_val = row[importe_indices[0]] if importe_indices[0] < len(row) else None
                    if importe_val is None:
                        continue
                    importe = str(importe_val).strip()
                
                if not fecha or not importe:
                    continue
                
                tx = {
                    'fecha': fecha,
                    'concepto': concepto,
                    'importe': importe,
                    'referencia': referencia,
                    'metadata': {
                        'linea': row_idx,
                        'formato': 'excel',
                        'extractor': 'llm-guided',
                        'llm_estructura': True
                    }
                }
                transacciones.append(tx)
            
            except (IndexError, ValueError, AttributeError):
                continue
        
        workbook.close()
        
        return transacciones

