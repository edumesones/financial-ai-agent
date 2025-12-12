# backend/app/services/file_detector.py
"""
File format detection service.
"""

import mimetypes
from pathlib import Path
from typing import Tuple


class FileDetector:
    """
    Detecta el formato de archivos subidos.
    
    Fase 1: CSV, Excel, OFX
    Fase 3: PDF, imágenes
    """
    
    def __init__(self):
        # Extensiones soportadas por fase
        self.supported_extensions = {
            # Fase 1
            '.csv': 'csv',
            '.txt': 'csv',  # Muchos bancos exportan como .txt
            '.xls': 'excel',
            '.xlsx': 'excel',
            '.xlsm': 'excel',
            '.ofx': 'ofx',
            
            # Fase 3 (ACTIVO)
            '.pdf': 'pdf',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.png': 'image',
            '.webp': 'image',
            '.gif': 'image',
            '.html': 'html',
            '.htm': 'html',
        }
    
    def detect(self, file_path: str) -> Tuple[str, str]:
        """
        Detecta el formato del archivo.
        
        Returns:
            (formato, mime_type)
        
        Raises:
            ValueError si formato no soportado
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Detectar por extensión primero
        extension = path.suffix.lower()
        formato = self.supported_extensions.get(extension)
        
        if not formato:
            raise ValueError(
                f"Formato no soportado: {extension}. "
                f"Soportados: {', '.join(self.supported_extensions.keys())}"
            )
        
        # Detectar MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        return formato, mime_type
    
    def is_supported(self, file_path: str) -> bool:
        """Verifica si el formato es soportado."""
        try:
            self.detect(file_path)
            return True
        except (ValueError, FileNotFoundError):
            return False
    
    def get_supported_formats(self) -> list[str]:
        """Retorna lista de formatos soportados."""
        return list(set(self.supported_extensions.values()))

