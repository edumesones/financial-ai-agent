# backend/app/services/extractors/image_extractor.py
"""
Extractor para imágenes (JPG, PNG, etc).

FASE 3: Usa Vision API para OCR directo.
"""

from typing import List, Dict
import structlog

logger = structlog.get_logger()


class ImageExtractor:
    """
    Extractor de imágenes usando Vision API.
    
    Para extractos bancarios fotografiados o capturados.
    """
    
    def __init__(self, hf_service):
        """
        Args:
            hf_service: HFInferenceService para Vision API
        """
        if not hf_service:
            raise ValueError("HFInferenceService required for ImageExtractor")
        
        self.hf_service = hf_service
    
    async def extract(self, file_path: str) -> List[Dict]:
        """
        Extrae texto de imagen usando Vision API.
        
        Returns:
            Lista con un item: {'raw_text': str}
        """
        logger.info(f"Extracting image with Vision API: {file_path}")
        
        text = await self.hf_service.extract_with_vision(
            image_path=file_path,
            prompt=(
                "Extract all text from this bank statement image. "
                "Maintain the exact tabular format. "
                "Include ALL transaction details: dates, descriptions, amounts."
            ),
            max_tokens=2500
        )
        
        logger.info(f"Extracted {len(text)} characters from image")
        
        return [{
            'raw_text': text,
            'metadata': {
                'formato': 'image',
                'extraction_method': 'vision_api',
                'text_length': len(text)
            }
        }]

