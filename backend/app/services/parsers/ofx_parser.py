# backend/app/services/parsers/ofx_parser.py
"""Parser para formato OFX/QFX."""

import io
from decimal import Decimal
from ofxparse import OfxParser as OFX
from .base import BankParser, TransaccionRaw


class OFXParser(BankParser):
    """Parser para formato OFX/QFX estándar bancario."""
    
    def detect(self, content: bytes) -> bool:
        """Detectar si es OFX válido."""
        try:
            text = content.decode("utf-8", errors="ignore")[:500]
            return "OFXHEADER" in text or "<OFX>" in text.upper()
        except Exception:
            return False
    
    def parse(self, content: bytes) -> list[TransaccionRaw]:
        """Parsear OFX."""
        try:
            ofx = OFX.parse(io.BytesIO(content))
        except Exception as e:
            raise ValueError(f"Error parseando OFX: {e}")
        
        transactions = []
        
        for account in ofx.accounts:
            if not hasattr(account, 'statement') or not account.statement:
                continue
                
            for tx in account.statement.transactions:
                concepto = ""
                if tx.memo:
                    concepto = tx.memo
                elif tx.payee:
                    concepto = tx.payee
                
                transactions.append(TransaccionRaw(
                    fecha=tx.date.date() if hasattr(tx.date, 'date') else tx.date,
                    concepto=concepto.strip() or "Sin concepto",
                    importe=Decimal(str(tx.amount)),
                    referencia=tx.id if tx.id else None,
                ))
        
        return transactions
