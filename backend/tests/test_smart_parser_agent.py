# backend/tests/test_smart_parser_agent.py
"""Tests for SmartParserAgent."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path


class TestSmartParserAgent:
    """Test suite for SmartParserAgent (basic smoke tests)."""
    
    def test_import_agent(self):
        """Test that SmartParserAgent can be imported."""
        from app.agents.smart_parser import SmartParserAgent
        assert SmartParserAgent is not None
    
    def test_parser_state_structure(self):
        """Test ParserState structure."""
        from app.agents.smart_parser import ParserState
        
        # ParserState should be a TypedDict, check it exists
        assert ParserState is not None
    
    @pytest.mark.asyncio
    async def test_detect_format_node(self):
        """Test detect_format node with mock."""
        from app.agents.smart_parser import SmartParserAgent
        
        # Mock dependencies
        mock_db = Mock()
        mock_hf_service = Mock()
        
        agent = SmartParserAgent(mock_db, mock_hf_service)
        
        # Create test state
        test_file = Path("tests/fixtures/sample_extracto.csv")
        state = {
            "tenant_id": "test-tenant",
            "session_id": "test-session",
            "file_path": str(test_file),
            "empresa_id": "test-empresa",
            "cuenta_id": None,
            "formato": None,
            "mime_type": None,
            "raw_content": None,
            "estructura": None,
            "transacciones": [],
            "transacciones_validadas": [],
            "errores": [],
            "metadata": {}
        }
        
        # Call detect_format
        result = await agent.detect_format(state)
        
        # Verify formato was detected
        assert result["formato"] == "csv"
        assert result["mime_type"] is not None
        assert "file_size" in result["metadata"]
    
    @pytest.mark.asyncio
    async def test_extract_raw_content_csv(self):
        """Test extract_raw_content for CSV."""
        from app.agents.smart_parser import SmartParserAgent
        
        mock_db = Mock()
        mock_hf_service = Mock()
        
        agent = SmartParserAgent(mock_db, mock_hf_service)
        
        test_file = Path("tests/fixtures/sample_extracto.csv")
        state = {
            "tenant_id": "test-tenant",
            "session_id": "test-session",
            "file_path": str(test_file),
            "formato": "csv",
            "metadata": {}
        }
        
        result = await agent.extract_raw_content(state)
        
        # Verify content was extracted
        assert result["raw_content"] is not None
        assert len(result["raw_content"]) > 0
        assert "Fecha" in result["raw_content"]
        assert "Concepto" in result["raw_content"]

