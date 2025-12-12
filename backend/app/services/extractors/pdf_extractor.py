# backend/app/services/extractors/pdf_extractor.py
"""
Extractor para archivos PDF.

FASE 3:
- Intenta extracción de texto primero (PDFs nativos)
- Si falla, usa Vision API para OCR (PDFs escaneados)
"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict
from pdf2image import convert_from_path
import PyPDF2
import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class PDFExtractor:
    """
    Extractor de PDFs con fallback a Vision OCR.
    
    Flujo:
    1. Intenta extraer texto con PyPDF2
    2. Si no hay texto, convierte a imágenes
    3. Usa Vision API para OCR
    """
    
    def __init__(self, hf_service=None):
        """
        Args:
            hf_service: HFInferenceService para Vision API
        """
        self.hf_service = hf_service
    
    def _extract_text_pypdf(self, file_path: str) -> str:
        """
        Intenta extraer texto nativo del PDF.
        
        Returns:
            Texto extraído (vacío si es PDF escaneado)
        """
        try:
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            return text.strip()
        
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {e}")
            return ""
    
    async def _extract_text_vision(self, file_path: str) -> str:
        """
        Extrae texto usando Vision API (para PDFs escaneados).
        
        Convierte PDF → imágenes → OCR
        """
        if not self.hf_service:
            raise ValueError("HFInferenceService required for Vision OCR")
        
        logger.info("Converting PDF to images for OCR")
        
        # Convertir PDF a imágenes (una por página)
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Usar poppler_path si existe, sino confiar en PATH del sistema
            poppler_kwargs = {}
            if settings.poppler_path and os.path.exists(settings.poppler_path):
                poppler_kwargs['poppler_path'] = settings.poppler_path
                logger.info(f"Using poppler from: {settings.poppler_path}")
            else:
                logger.warning(f"Poppler not found at {settings.poppler_path}, trying system PATH")
            
            images = convert_from_path(
                file_path,
                dpi=200,  # Calidad razonable
                output_folder=tmp_dir,
                fmt='png',
                **poppler_kwargs
            )
            
            logger.info(f"Converted PDF to {len(images)} images")
            
            # Extraer texto de cada imagen
            all_text = []
            
            for idx, image in enumerate(images, start=1):
                # Guardar imagen temporalmente
                image_path = Path(tmp_dir) / f"page_{idx}.png"
                image.save(image_path, "PNG")
                
                logger.info(f"Extracting text from page {idx}/{len(images)}")
                
                # Usar Vision API
                page_text = await self.hf_service.extract_with_vision(
                    image_path=str(image_path),
                    prompt="Extract all text from this bank statement page. Maintain the exact tabular format with columns aligned.",
                    max_tokens=2500
                )
                
                all_text.append(f"--- Page {idx} ---\n{page_text}")
            
            return "\n\n".join(all_text)
    
    async def extract(self, file_path: str) -> List[Dict]:
        """
        Extrae transacciones del PDF.
        
        NO parsea directamente a transacciones - retorna texto raw
        para que interpret_structure lo entienda.
        
        Returns:
            Lista con un item: {'raw_text': str}
        """
        logger.info(f"Extracting PDF: {file_path}")
        
        # Intento 1: Texto nativo
        text = self._extract_text_pypdf(file_path)
        
        if text and len(text) > 100:  # Si hay contenido razonable
            logger.info(f"Extracted {len(text)} chars with PyPDF2")
            extraction_method = "pypdf"
        
        else:
            # Intento 2: Vision OCR
            logger.info("PDF appears to be scanned, using Vision OCR")
            text = await self._extract_text_vision(file_path)
            extraction_method = "vision_ocr"
        
        # Retornar texto raw (no parseado todavía)
        return [{
            'raw_text': text,
            'metadata': {
                'formato': 'pdf',
                'extraction_method': extraction_method,
                'text_length': len(text)
            }
        }]

