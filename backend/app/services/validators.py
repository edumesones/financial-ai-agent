# backend/app/services/validators.py
"""
Transaction validator and normalizer.
"""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict


class TransactionValidator:
    """
    Valida y normaliza transacciones extraídas.
    
    Convierte strings a formatos estándar:
    - Fechas → ISO format (YYYY-MM-DD)
    - Importes → float
    - Conceptos → cleaned text
    """
    
    # Patrones de fecha comunes
    DATE_PATTERNS = [
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{2})/(\d{2})/(\d{4})',  # DD/MM/YYYY
        r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
        r'(\d{2})\.(\d{2})\.(\d{4})',  # DD.MM.YYYY
    ]
    
    def _parse_date(self, date_str: str) -> str:
        """
        Parsea fecha de múltiples formatos a ISO.
        
        Returns:
            YYYY-MM-DD string
        
        Raises:
            ValueError si no se puede parsear
        """
        date_str = str(date_str).strip()
        
        # Intentar parseo directo con datetime
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%Y/%m/%d']:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.date().isoformat()
            except ValueError:
                continue
        
        # Intentar con regex
        for pattern in self.DATE_PATTERNS:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                
                # Detectar orden (YYYY-MM-DD vs DD-MM-YYYY)
                if len(groups[0]) == 4:  # YYYY primero
                    year, month, day = groups
                else:  # DD primero
                    day, month, year = groups
                
                try:
                    dt = datetime(int(year), int(month), int(day))
                    return dt.date().isoformat()
                except ValueError:
                    continue
        
        raise ValueError(f"No se pudo parsear fecha: {date_str}")
    
    def _parse_amount(self, amount_str: str) -> float:
        """
        Parsea importe de múltiples formatos.
        
        Maneja:
        - 1.234,56 (formato europeo)
        - 1,234.56 (formato US)
        - 1234.56
        - -1234.56
        
        Returns:
            float
        
        Raises:
            ValueError si no se puede parsear
        """
        amount_str = str(amount_str).strip()
        
        # Remover espacios y símbolos de moneda
        amount_str = amount_str.replace(' ', '').replace('€', '').replace('$', '').replace('USD', '').replace('EUR', '')
        
        # Detectar formato por cantidad de puntos y comas
        num_commas = amount_str.count(',')
        num_dots = amount_str.count('.')
        
        if num_commas > 0 and num_dots > 0:
            # Ambos presentes, determinar cuál es decimal
            last_comma = amount_str.rfind(',')
            last_dot = amount_str.rfind('.')
            
            if last_comma > last_dot:
                # Formato europeo: 1.234,56
                amount_str = amount_str.replace('.', '').replace(',', '.')
            else:
                # Formato US: 1,234.56
                amount_str = amount_str.replace(',', '')
        
        elif num_commas > 0:
            # Solo comas
            if num_commas == 1 and amount_str.rfind(',') > len(amount_str) - 4:
                # Probablemente decimal: 1234,56
                amount_str = amount_str.replace(',', '.')
            else:
                # Separador de miles: 1,234
                amount_str = amount_str.replace(',', '')
        
        # Convertir a float
        try:
            return float(amount_str)
        except ValueError:
            raise ValueError(f"No se pudo parsear importe: {amount_str}")
    
    def _clean_concept(self, concept: str) -> str:
        """
        Limpia el concepto.
        
        - Trim whitespace
        - Remove extra spaces
        - Capitalize
        """
        concept = str(concept).strip()
        concept = re.sub(r'\s+', ' ', concept)  # Múltiples espacios → uno
        return concept
    
    def validate(self, tx: Dict) -> Dict:
        """
        Valida y normaliza una transacción.
        
        Args:
            tx: {'fecha': str, 'concepto': str, 'importe': str, ...}
        
        Returns:
            Transacción normalizada con tipos correctos
        
        Raises:
            ValueError si validación falla
        """
        return {
            'fecha': self._parse_date(tx['fecha']),
            'concepto': self._clean_concept(tx.get('concepto', '')),
            'importe': self._parse_amount(tx['importe']),
            'referencia': tx.get('referencia'),
            'metadata': tx.get('metadata', {})
        }

