# backend/app/services/hf_inference.py
"""Cliente para Hugging Face Inference API usando OpenAI client compatible."""

import asyncio
import base64
import hashlib
import json
from pathlib import Path
from typing import Optional, Union

from openai import OpenAI
from huggingface_hub import InferenceClient
from tenacity import retry, stop_after_attempt, wait_exponential
import redis.asyncio as aioredis
import structlog

from app.config import get_settings

settings = get_settings()
logger = structlog.get_logger()


class HFInferenceService:
    """Servicio de inferencia con Hugging Face usando OpenAI-compatible API."""
    
    def __init__(self):
        self._openai_client: Optional[OpenAI] = None
        self._hf_client: Optional[InferenceClient] = None
        self._redis: Optional[aioredis.Redis] = None
        self.embedding_cache_ttl = 86400 * 7  # 7 días
    
    @property
    def openai_client(self) -> OpenAI:
        """Cliente OpenAI apuntando al router de HuggingFace."""
        if self._openai_client is None:
            self._openai_client = OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=settings.hf_token,
            )
        return self._openai_client
    
    @property
    def hf_client(self) -> InferenceClient:
        """Cliente HF para embeddings y otras tareas."""
        if self._hf_client is None:
            self._hf_client = InferenceClient(
                token=settings.hf_token if settings.hf_token else None,
                base_url="https://router.huggingface.co"
            )
        return self._hf_client
    
    async def _get_redis(self) -> aioredis.Redis:
        """Lazy initialization de Redis."""
        if self._redis is None:
            self._redis = await aioredis.from_url(settings.redis_url)
        return self._redis
    
    async def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Llamada genérica al LLM usando OpenAI-compatible API."""
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=settings.hf_model_llm,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("llm_call_error", error=str(e), model=settings.hf_model_llm)
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def classify_transaction(
        self,
        concepto: str,
        importe: float,
        historico: Optional[list[dict]] = None,
    ) -> dict:
        """Clasificar transacción usando LLM."""
        
        historico_text = ""
        if historico:
            historico_text = "\n".join([
                f"- {h['concepto']}: {h['categoria']} ({h['confianza']:.0%})"
                for h in historico[:5]
            ])
        
        prompt = f"""Clasifica la siguiente transacción bancaria según el Plan General Contable español (PGC).

Transacción:
- Concepto: {concepto}
- Importe: {importe}€
- Tipo: {"GASTO" if importe < 0 else "INGRESO"}

{f"Clasificaciones similares previas:{chr(10)}{historico_text}" if historico_text else ""}

Categorías principales de gastos (600-629):
- 600: Compras de mercaderías
- 621: Arrendamientos y cánones
- 622: Reparaciones y conservación
- 623: Servicios profesionales independientes
- 624: Transportes
- 625: Primas de seguros
- 626: Servicios bancarios y similares
- 627: Publicidad, propaganda y relaciones públicas
- 628: Suministros (luz, agua, gas, teléfono)
- 629: Otros servicios

Categorías principales de ingresos (700-759):
- 700: Ventas de mercaderías
- 705: Prestaciones de servicios
- 759: Ingresos por servicios diversos

Responde SOLO con un JSON válido (sin markdown ni explicación adicional):
{{"categoria_pgc": "XXX", "nombre_categoria": "...", "confianza": 0.XX, "explicacion": "..."}}
"""
        
        try:
            response = await self._call_llm(prompt, max_tokens=200)
            
            # Limpiar respuesta y parsear JSON
            response_clean = response.strip()
            if response_clean.startswith("```"):
                response_clean = response_clean.split("```")[1]
                if response_clean.startswith("json"):
                    response_clean = response_clean[4:]
            
            result = json.loads(response_clean.strip())
            
            logger.info(
                "classification_completed",
                concepto=concepto[:50],
                categoria=result.get("categoria_pgc"),
                confianza=result.get("confianza"),
            )
            return result
            
        except json.JSONDecodeError as e:
            logger.error("classification_parse_error", error=str(e), response=response[:200])
            return {
                "categoria_pgc": "629",
                "nombre_categoria": "Otros servicios",
                "confianza": 0.5,
                "explicacion": "No se pudo clasificar automáticamente",
            }
        except Exception as e:
            logger.error("classification_error", error=str(e))
            raise
    
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generar embeddings con caché en Redis."""
        redis = await self._get_redis()
        results: list[list[float] | None] = []
        texts_to_compute: list[tuple[int, str]] = []
        cache_keys: list[str] = []
        
        # Verificar caché
        for text in texts:
            cache_key = f"emb:{hashlib.md5(text.encode()).hexdigest()}"
            cache_keys.append(cache_key)
            
            cached = await redis.get(cache_key)
            if cached:
                results.append(json.loads(cached))
            else:
                results.append(None)
                texts_to_compute.append((len(results) - 1, text))
        
        # Computar embeddings faltantes
        if texts_to_compute:
            indices, batch_texts = zip(*texts_to_compute)
            
            # feature_extraction API acepta el texto directamente
            embeddings = await asyncio.to_thread(
                self.hf_client.feature_extraction,
                list(batch_texts),
                model=settings.hf_model_embeddings,
            )
            
            # Guardar en caché y resultados
            for idx, embedding in zip(indices, embeddings):
                emb_list = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
                results[idx] = emb_list
                await redis.setex(
                    cache_keys[idx],
                    self.embedding_cache_ttl,
                    json.dumps(emb_list),
                )
        
        return results
    
    async def compute_similarity(
        self, embedding1: list[float], embedding2: list[float]
    ) -> float:
        """Calcular similitud coseno entre dos embeddings."""
        import numpy as np
        
        a = np.array(embedding1)
        b = np.array(embedding2)
        
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    
    async def extract_with_vision(
        self,
        image_path: Union[str, Path],
        prompt: str = "Extract all text from this bank statement. Maintain the tabular format.",
        model: Optional[str] = None,
        max_tokens: int = 2000
    ) -> str:
        """
        Extrae texto de imagen usando modelo de visión.
        
        Args:
            image_path: Ruta a la imagen
            prompt: Instrucción para el modelo
            model: Modelo de visión a usar
            max_tokens: Tokens máximos en respuesta
        
        Returns:
            Texto extraído
        """
        if model is None:
            model = settings.hf_model_vision
        
        logger.info(f"Extracting text from image with vision model: {model}")
        
        # Leer y codificar imagen en base64
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        image_b64 = base64.b64encode(image_data).decode('utf-8')
        
        # Detectar tipo de imagen
        ext = Path(image_path).suffix.lower()
        mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }.get(ext, 'image/jpeg')
        
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=model,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_b64}"
                            }
                        }
                    ]
                }],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            extracted_text = response.choices[0].message.content
            logger.info(f"Extracted {len(extracted_text)} characters from image")
            
            return extracted_text
        
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            raise
    
    async def close(self):
        """Cerrar conexiones."""
        if self._redis:
            await self._redis.close()
