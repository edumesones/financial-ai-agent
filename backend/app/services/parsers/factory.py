# backend/app/services/parsers/factory.py
"""Factory para seleccionar parser correcto."""

from .base import BankParser
from .csv_parser import CSVGenericParser
from .ofx_parser import OFXParser

PARSERS = [
    OFXParser(),
    CSVGenericParser(),
]


def get_parser(content: bytes, formato: str | None = None) -> BankParser:
    """
    Obtener parser apropiado para el contenido.
    
    Args:
        content: Contenido del archivo
        formato: Formato opcional (csv, ofx, qfx). Si no se especifica, auto-detecta.
    
    Returns:
        Parser apropiado para el contenido
    
    Raises:
        ValueError: Si no se encuentra parser compatible
    """
    # Si se especifica formato, usar directamente
    if formato:
        formato_lower = formato.lower()
        if formato_lower in ("ofx", "qfx"):
            return OFXParser()
        elif formato_lower == "csv":
            return CSVGenericParser()
    
    # Auto-detectar
    for parser in PARSERS:
        if parser.detect(content):
            return parser
    
    raise ValueError(
        "No se encontró parser compatible. Formatos soportados: CSV, OFX, QFX"
    )
