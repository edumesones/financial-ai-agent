# backend/app/services/parsers/base.py
"""Clase base para parsers de extractos bancarios."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
import hashlib


@dataclass
class TransaccionRaw:
    """Transacción parseada de extracto bancario."""
    fecha: date
    concepto: str
    importe: Decimal
    saldo: Decimal | None = None
    referencia: str | None = None
    fecha_valor: date | None = None
    
    def compute_hash(self) -> str:
        """Hash único para detectar duplicados."""
        data = f"{self.fecha.isoformat()}|{self.concepto}|{float(self.importe)}"
        if self.referencia:
            data += f"|{self.referencia}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class BankParser(ABC):
    """Clase base abstracta para parsers de extractos."""
    
    @abstractmethod
    def parse(self, content: bytes) -> list[TransaccionRaw]:
        """Parsear contenido y devolver transacciones."""
        pass
    
    @abstractmethod
    def detect(self, content: bytes) -> bool:
        """Detectar si este parser puede manejar el contenido."""
        pass
    
    @staticmethod
    def normalize_amount(value: str) -> Decimal:
        """Normalizar importe desde string."""
        if not value or not value.strip():
            return Decimal("0")
        
        # Eliminar espacios y símbolos de moneda
        cleaned = value.strip().replace("€", "").replace("EUR", "").replace(" ", "").strip()
        
        # Detectar formato español (1.234,56) vs internacional (1,234.56)
        if "," in cleaned and "." in cleaned:
            if cleaned.rindex(",") > cleaned.rindex("."):
                # Formato español: 1.234,56
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # Formato internacional: 1,234.56
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            # Solo coma: asumimos decimal español
            cleaned = cleaned.replace(",", ".")
        
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return Decimal("0")
    
    @staticmethod
    def parse_date(value: str) -> date:
        """Parsear fecha desde múltiples formatos."""
        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d/%m/%y",
            "%Y%m%d",
        ]
        
        value = value.strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        
        raise ValueError(f"Formato de fecha no reconocido: {value}")
