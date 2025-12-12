# backend/tests/services/test_validators.py
"""Tests for TransactionValidator."""

import pytest
from app.services.validators import TransactionValidator


class TestTransactionValidator:
    """Test suite for TransactionValidator."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.validator = TransactionValidator()
    
    def test_parse_date_iso(self):
        """Test ISO date parsing."""
        result = self.validator._parse_date("2024-12-15")
        assert result == "2024-12-15"
    
    def test_parse_date_european(self):
        """Test European date format (DD/MM/YYYY)."""
        result = self.validator._parse_date("15/12/2024")
        assert result == "2024-12-15"
    
    def test_parse_date_dashes(self):
        """Test date with dashes (DD-MM-YYYY)."""
        result = self.validator._parse_date("15-12-2024")
        assert result == "2024-12-15"
    
    def test_parse_date_invalid(self):
        """Test invalid date raises error."""
        with pytest.raises(ValueError):
            self.validator._parse_date("invalid_date")
    
    def test_parse_amount_simple(self):
        """Test simple amount parsing."""
        result = self.validator._parse_amount("1234.56")
        assert result == 1234.56
    
    def test_parse_amount_european(self):
        """Test European format (1.234,56)."""
        result = self.validator._parse_amount("1.234,56")
        assert result == 1234.56
    
    def test_parse_amount_negative(self):
        """Test negative amount."""
        result = self.validator._parse_amount("-123.45")
        assert result == -123.45
    
    def test_parse_amount_with_currency(self):
        """Test amount with currency symbol."""
        result = self.validator._parse_amount("€ 1.234,56")
        assert result == 1234.56
    
    def test_clean_concept(self):
        """Test concept cleaning."""
        result = self.validator._clean_concept("  AMAZON   PRIME  ")
        assert result == "AMAZON PRIME"
    
    def test_validate_complete_transaction(self):
        """Test complete transaction validation."""
        tx = {
            'fecha': '15/12/2024',
            'concepto': '  TRANSFERENCIA NOMINA  ',
            'importe': '2.500,00',
            'referencia': 'REF123'
        }
        
        result = self.validator.validate(tx)
        
        assert result['fecha'] == '2024-12-15'
        assert result['concepto'] == 'TRANSFERENCIA NOMINA'
        assert result['importe'] == 2500.0
        assert result['referencia'] == 'REF123'
        assert 'metadata' in result

