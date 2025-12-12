# backend/tests/services/test_csv_extractor.py
"""Tests for CSVExtractor."""

import pytest
from pathlib import Path
from app.services.extractors.csv_extractor import CSVExtractor


class TestCSVExtractor:
    """Test suite for CSVExtractor."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.extractor = CSVExtractor()
    
    def test_detect_delimiter_semicolon(self):
        """Test semicolon delimiter detection."""
        test_file = Path("tests/fixtures/sample_extracto.csv")
        
        delimiter = self.extractor._detect_delimiter(str(test_file))
        
        assert delimiter == ";"
    
    def test_match_column_fecha(self):
        """Test fecha column matching."""
        assert self.extractor._match_column("Fecha", self.extractor.FECHA_KEYWORDS) is True
        assert self.extractor._match_column("Date", self.extractor.FECHA_KEYWORDS) is True
        assert self.extractor._match_column("F. Valor", self.extractor.FECHA_KEYWORDS) is True
        assert self.extractor._match_column("Random", self.extractor.FECHA_KEYWORDS) is False
    
    def test_match_column_concepto(self):
        """Test concepto column matching."""
        assert self.extractor._match_column("Concepto", self.extractor.CONCEPTO_KEYWORDS) is True
        assert self.extractor._match_column("Descripción", self.extractor.CONCEPTO_KEYWORDS) is True
        assert self.extractor._match_column("Description", self.extractor.CONCEPTO_KEYWORDS) is True
    
    def test_match_column_importe(self):
        """Test importe column matching."""
        assert self.extractor._match_column("Importe", self.extractor.IMPORTE_KEYWORDS) is True
        assert self.extractor._match_column("Amount", self.extractor.IMPORTE_KEYWORDS) is True
        assert self.extractor._match_column("Monto", self.extractor.IMPORTE_KEYWORDS) is True
    
    @pytest.mark.asyncio
    async def test_extract_transactions(self):
        """Test complete transaction extraction."""
        test_file = Path("tests/fixtures/sample_extracto.csv")
        
        transacciones = await self.extractor.extract(str(test_file))
        
        assert len(transacciones) == 3
        
        # First transaction
        tx1 = transacciones[0]
        assert tx1['fecha'] == '15/12/2024'
        assert 'NOMINA' in tx1['concepto']
        assert tx1['importe'] == '2500.00'
        
        # Second transaction (negative)
        tx2 = transacciones[1]
        assert 'AMAZON' in tx2['concepto']
        assert '-' in tx2['importe']
        
        # Check metadata
        assert tx1['metadata']['formato'] == 'csv'
        assert tx1['metadata']['delimiter'] == ';'

