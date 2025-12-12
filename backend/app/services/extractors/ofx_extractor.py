# backend/app/services/extractors/ofx_extractor.py
"""
Extractor para archivos OFX (Open Financial Exchange).

Usa el parser existente de ofxparse.
"""

import ofxparse
from typing import List, Dict
from datetime import datetime


class OFXExtractor:
    """
    Extractor de archivos OFX.
    
    OFX es un formato estándar, no necesita detección flexible.
    """
    
    async def extract(self, file_path: str) -> List[Dict]:
        """
        Extrae transacciones del archivo OFX.
        
        Returns:
            Lista de transacciones en formato estándar
        """
        with open(file_path, 'rb') as f:
            ofx = ofxparse.OfxParser.parse(f)
        
        transacciones = []
        
        # OFX puede tener múltiples cuentas
        for account in ofx.accounts:
            for tx in account.statement.transactions:
                transacciones.append({
                    'fecha': tx.date.isoformat() if isinstance(tx.date, datetime) else str(tx.date),
                    'concepto': tx.memo or tx.payee or '',
                    'importe': str(tx.amount),
                    'referencia': tx.id,
                    'metadata': {
                        'formato': 'ofx',
                        'account_id': account.account_id,
                        'type': tx.type
                    }
                })
        
        return transacciones

