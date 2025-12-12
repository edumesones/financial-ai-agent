# backend/tests/services/test_file_detector.py
"""Tests for FileDetector."""

import pytest
from pathlib import Path
from app.services.file_detector import FileDetector


class TestFileDetector:
    """Test suite for FileDetector."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.detector = FileDetector()
    
    def test_csv_detection(self):
        """Test CSV file detection."""
        # Create temp file
        test_file = Path("tests/fixtures/sample_extracto.csv")
        
        formato, mime_type = self.detector.detect(str(test_file))
        
        assert formato == "csv"
        assert "text" in mime_type or "csv" in mime_type
    
    def test_supported_formats(self):
        """Test getting supported formats."""
        formats = self.detector.get_supported_formats()
        
        assert "csv" in formats
        assert "excel" in formats
        assert "ofx" in formats
        assert "pdf" in formats
        assert "image" in formats
    
    def test_unsupported_format(self):
        """Test unsupported format raises error."""
        with pytest.raises(ValueError, match="Formato no soportado"):
            self.detector.detect("test.unknown")
    
    def test_file_not_found(self):
        """Test non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            self.detector.detect("non_existent_file.csv")
    
    def test_is_supported(self):
        """Test is_supported method."""
        test_file = Path("tests/fixtures/sample_extracto.csv")
        
        assert self.detector.is_supported(str(test_file)) is True
        assert self.detector.is_supported("non_existent.csv") is False

