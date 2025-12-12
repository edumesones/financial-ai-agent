# backend/app/services/extractors/excel_extractor.py
"""
Extractor flexible para archivos Excel.

Detecta automáticamente columnas y hojas.
"""

import openpyxl
from typing import List, Dict, Optional


class ExcelExtractor:
    """
    Extractor de Excel que detecta columnas automáticamente.
    
    Similar a CSVExtractor pero para archivos .xlsx/.xls
    """
    
    # Reusar las mismas keywords que CSV
    FECHA_KEYWORDS = ['fecha', 'date', 'fec', 'f.valor', 'f.operacion', 'datetime']
    CONCEPTO_KEYWORDS = ['concepto', 'descripcion', 'description', 'desc', 'detalle', 'observaciones']
    IMPORTE_KEYWORDS = ['importe', 'amount', 'monto', 'cantidad', 'valor', 'debe', 'haber']
    REFERENCIA_KEYWORDS = ['referencia', 'reference', 'ref', 'num', 'numero']
    
    def _match_column(self, col_name: str, keywords: List[str]) -> bool:
        """Verifica si el nombre de columna coincide con alguna palabra clave."""
        if not col_name:
            return False
        col_name_lower = str(col_name).lower().strip()
        return any(keyword in col_name_lower for keyword in keywords)
    
    def _detect_columns(self, headers: List) -> Dict[str, Optional[int]]:
        """
        Detecta qué columna corresponde a qué campo.
        
        Returns:
            {'fecha': index, 'concepto': index, ...}
        """
        mapping = {
            'fecha': None,
            'concepto': None,
            'importe': None,
            'referencia': None
        }
        
        for idx, header in enumerate(headers):
            if header is None:
                continue
                
            if mapping['fecha'] is None and self._match_column(header, self.FECHA_KEYWORDS):
                mapping['fecha'] = idx
            elif mapping['concepto'] is None and self._match_column(header, self.CONCEPTO_KEYWORDS):
                mapping['concepto'] = idx
            elif mapping['importe'] is None and self._match_column(header, self.IMPORTE_KEYWORDS):
                mapping['importe'] = idx
            elif mapping['referencia'] is None and self._match_column(header, self.REFERENCIA_KEYWORDS):
                mapping['referencia'] = idx
        
        return mapping
    
    def _find_data_sheet(self, workbook) -> openpyxl.worksheet.worksheet.Worksheet:
        """
        Encuentra la hoja con datos de transacciones.
        
        Prioriza:
        1. Hoja con nombre relacionado a movimientos/transacciones
        2. Primera hoja con datos
        """
        # Nombres comunes de hojas con transacciones
        preferred_names = ['movimientos', 'transacciones', 'extracto', 'movements', 'transactions']
        
        # Buscar por nombre
        for sheet in workbook.worksheets:
            sheet_name_lower = sheet.title.lower()
            if any(name in sheet_name_lower for name in preferred_names):
                return sheet
        
        # Fallback: primera hoja
        return workbook.active
    
    async def extract(self, file_path: str) -> List[Dict]:
        """
        Extrae transacciones del Excel de forma flexible.
        
        Returns:
            Lista de transacciones en formato estándar
        """
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = self._find_data_sheet(workbook)
        
        transacciones = []
        
        # Leer encabezados (primera fila con datos)
        rows = list(sheet.iter_rows(values_only=True))
        
        if not rows:
            raise ValueError("Hoja de Excel vacía")
        
        headers = list(rows[0])
        
        # Detectar columnas
        col_mapping = self._detect_columns(headers)
        
        # Validar que tengamos fecha e importe
        if col_mapping['fecha'] is None:
            raise ValueError(
                f"No se pudo detectar columna de fecha en hoja '{sheet.title}'. "
                f"Encabezados: {headers}"
            )
        
        if col_mapping['importe'] is None:
            raise ValueError(
                f"No se pudo detectar columna de importe en hoja '{sheet.title}'. "
                f"Encabezados: {headers}"
            )
        
        # Leer filas (skip header)
        for row_idx, row in enumerate(rows[1:], start=2):
            if not row or all(cell is None for cell in row):
                continue
            
            try:
                # Extraer valores
                fecha_val = row[col_mapping['fecha']] if col_mapping['fecha'] < len(row) else None
                concepto_val = row[col_mapping['concepto']] if col_mapping['concepto'] is not None and col_mapping['concepto'] < len(row) else ''
                importe_val = row[col_mapping['importe']] if col_mapping['importe'] < len(row) else None
                ref_val = row[col_mapping['referencia']] if col_mapping['referencia'] is not None and col_mapping['referencia'] < len(row) else None
                
                # Skip si no hay fecha o importe
                if fecha_val is None or importe_val is None:
                    continue
                
                tx = {
                    'fecha': str(fecha_val).strip() if fecha_val else '',
                    'concepto': str(concepto_val).strip() if concepto_val else '',
                    'importe': str(importe_val).strip() if importe_val else '',
                    'referencia': str(ref_val).strip() if ref_val else None,
                    'metadata': {
                        'linea': row_idx,
                        'formato': 'excel',
                        'hoja': sheet.title
                    }
                }
                
                transacciones.append(tx)
            
            except (IndexError, AttributeError):
                # Fila incompleta, skip
                continue
        
        workbook.close()
        
        return transacciones

