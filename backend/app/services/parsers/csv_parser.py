# backend/app/services/parsers/csv_parser.py
"""Parser genérico CSV con detección automática."""

import csv
import re
import io
from .base import BankParser, TransaccionRaw


class CSVGenericParser(BankParser):
    """Parser genérico CSV con detección automática de columnas."""
    
    COLUMN_PATTERNS = {
        "fecha": re.compile(r"fecha|date|f\.|valor|fec|fcha", re.IGNORECASE),
        "concepto": re.compile(
            r"concepto|descripcion|description|detalle|movimiento|observ", re.IGNORECASE
        ),
        "importe": re.compile(
            r"importe|amount|cantidad|cargo|abono|€|monto|valor", re.IGNORECASE
        ),
        "saldo": re.compile(r"saldo|balance", re.IGNORECASE),
        "referencia": re.compile(r"referencia|ref|numero|num", re.IGNORECASE),
    }
    
    def detect(self, content: bytes) -> bool:
        """Detectar si es CSV válido."""
        try:
            # Intentar decodificar
            for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
                try:
                    text = content.decode(encoding)[:2000]
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return False
            
            # Verificar que parece CSV
            dialect = csv.Sniffer().sniff(text)
            return True
        except Exception:
            return False
    
    def parse(self, content: bytes) -> list[TransaccionRaw]:
        """Parsear CSV genérico."""
        # Detectar encoding
        text = None
        for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if text is None:
            raise ValueError("No se pudo decodificar el archivo")
        
        # Detectar delimitador
        try:
            dialect = csv.Sniffer().sniff(text[:2000])
        except csv.Error:
            # Fallback a punto y coma (común en España)
            dialect = csv.excel
            dialect.delimiter = ";"
        
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        
        if not reader.fieldnames:
            raise ValueError("No se encontraron columnas en el CSV")
        
        # Mapear columnas
        column_map = self._detect_columns(reader.fieldnames)
        
        transactions = []
        for row in reader:
            try:
                # Obtener concepto
                concepto = row.get(column_map.get("concepto", ""), "")
                if not concepto:
                    concepto = "Sin concepto"
                
                # Parsear importe
                importe_str = row.get(column_map.get("importe", ""), "0")
                importe = self.normalize_amount(importe_str)
                
                if importe == 0:
                    continue  # Saltar filas sin importe
                
                # Parsear fecha
                fecha_str = row.get(column_map.get("fecha", ""), "")
                if not fecha_str:
                    continue
                fecha = self.parse_date(fecha_str)
                
                # Saldo opcional
                saldo = None
                if column_map.get("saldo"):
                    saldo_str = row.get(column_map["saldo"], "")
                    if saldo_str:
                        saldo = self.normalize_amount(saldo_str)
                
                # Referencia opcional
                referencia = None
                if column_map.get("referencia"):
                    referencia = row.get(column_map["referencia"], "")
                
                tx = TransaccionRaw(
                    fecha=fecha,
                    concepto=concepto.strip(),
                    importe=importe,
                    saldo=saldo,
                    referencia=referencia,
                )
                transactions.append(tx)
                
            except (KeyError, ValueError) as e:
                # Skip filas con errores
                continue
        
        return transactions
    
    def _detect_columns(self, fieldnames: list[str]) -> dict[str, str]:
        """Detectar columnas por nombre."""
        column_map = {}
        
        for field in fieldnames:
            if not field:
                continue
            for col_type, pattern in self.COLUMN_PATTERNS.items():
                if pattern.search(field) and col_type not in column_map:
                    column_map[col_type] = field
                    break
        
        # Validar columnas requeridas
        required = ["fecha", "importe"]
        missing = [r for r in required if r not in column_map]
        if missing:
            raise ValueError(f"Columnas requeridas no encontradas: {missing}")
        
        return column_map
