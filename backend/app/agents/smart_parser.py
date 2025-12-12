# backend/app/agents/smart_parser.py
"""
Smart Parser Agent - Universal document parser using AI.

Fase 1: CSV/Excel flexible support
"""

from typing import TypedDict, Optional
from pathlib import Path
from datetime import datetime

from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseAgent, AgentState


class ParserState(AgentState):
    """Estado del agente de parsing inteligente."""
    # Input
    file_path: str
    tenant_id: str
    empresa_id: str
    cuenta_id: Optional[str]
    
    # Detection
    formato: Optional[str]  # csv, excel, pdf, image, ofx, html
    mime_type: Optional[str]
    
    # Extraction
    raw_content: Optional[str]
    
    # Structure interpretation (Fase 2)
    estructura: Optional[dict]
    
    # Transaction extraction
    transacciones: list[dict]
    transacciones_validadas: list[dict]
    
    # Errors & metadata
    errores: list[dict]
    metadata: dict


class SmartParserAgent(BaseAgent):
    """
    Agente de parsing inteligente que entiende múltiples formatos.
    
    Fase 1: Soporta CSV y Excel con columnas flexibles.
    Fase 2: Agregará interpretación con LLM.
    Fase 3: Agregará soporte para PDF y visión.
    """
    
    def build_graph(self) -> StateGraph:
        """Construye el grafo de estados del agente."""
        graph = StateGraph(ParserState)
        
        # Nodos - Fase 2 (con LLM)
        graph.add_node("detect_format", self.detect_format)
        graph.add_node("extract_raw", self.extract_raw_content)
        graph.add_node("interpret_structure", self.interpret_structure)
        graph.add_node("extract_transactions", self.extract_transactions)
        graph.add_node("validate_clean", self.validate_and_clean)
        
        # Flujo mejorado Fase 2
        graph.add_edge("detect_format", "extract_raw")
        graph.add_edge("extract_raw", "interpret_structure")
        graph.add_edge("interpret_structure", "extract_transactions")
        graph.add_edge("extract_transactions", "validate_clean")
        graph.add_edge("validate_clean", END)
        
        graph.set_entry_point("detect_format")
        
        return graph
    
    async def detect_format(self, state: ParserState) -> dict:
        """
        Detecta el formato del archivo.
        
        Fase 1: Detecta CSV, Excel básico
        Fase 3: Agregará PDF, imágenes
        """
        self.log_step("detect_format", state)
        self.logger.info("🔍 [SMART PARSER] Starting format detection", file_path=state["file_path"])
        
        from app.services.file_detector import FileDetector
        
        detector = FileDetector()
        file_path = state["file_path"]
        
        formato, mime_type = detector.detect(file_path)
        
        self.logger.info(
            "✅ [SMART PARSER] Format detected",
            formato=formato,
            mime_type=mime_type,
            file_size=Path(file_path).stat().st_size
        )
        
        return {
            **state,
            "formato": formato,
            "mime_type": mime_type,
            "metadata": {
                **state.get("metadata", {}),
                "file_size": Path(file_path).stat().st_size,
                "detected_at": datetime.utcnow().isoformat()
            }
        }
    
    async def extract_raw_content(self, state: ParserState) -> dict:
        """
        Extrae contenido RAW del archivo (primeras líneas/muestra).
        
        Fase 2: Solo extrae una muestra para que el LLM interprete estructura.
        Fase 3: Soporta PDF e imágenes con Vision API.
        """
        self.log_step("extract_raw_content", state)
        self.logger.info("📄 [SMART PARSER] Extracting raw content", formato=state["formato"])
        
        formato = state["formato"]
        file_path = state["file_path"]
        
        raw_content = ""
        
        if formato == "csv":
            # Leer primeras 10 líneas
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [f.readline() for _ in range(10)]
                raw_content = "".join(lines)
        
        elif formato == "excel":
            import openpyxl
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook.active
            
            # Leer primeras 10 filas
            rows = list(sheet.iter_rows(values_only=True, max_row=10))
            raw_content = "\n".join(["\t".join([str(cell) if cell else "" for cell in row]) for row in rows])
            workbook.close()
        
        elif formato == "ofx":
            # OFX no necesita interpretación (formato estándar)
            raw_content = "[OFX format - standard structure]"
        
        elif formato == "pdf":
            # PDF: extraer muestra con PDFExtractor
            from app.services.extractors.pdf_extractor import PDFExtractor
            extractor = PDFExtractor(self.hf_service)
            result = await extractor.extract(file_path)
            
            # PDFExtractor retorna texto completo, tomar muestra
            full_text = result[0]['raw_text']
            raw_content = full_text[:2000]  # Primeros 2000 chars para interpretación
            
            # Guardar texto completo en state
            state["_pdf_full_text"] = full_text
        
        elif formato == "image":
            # Imagen: extraer todo con Vision
            from app.services.extractors.image_extractor import ImageExtractor
            extractor = ImageExtractor(self.hf_service)
            result = await extractor.extract(file_path)
            
            # ImageExtractor retorna texto completo
            full_text = result[0]['raw_text']
            raw_content = full_text[:2000]  # Muestra para interpretación
            
            # Guardar texto completo
            state["_image_full_text"] = full_text
        
        self.logger.info(
            "✅ [SMART PARSER] Raw content extracted",
            content_length=len(raw_content),
            formato=formato
        )
        
        return {
            **state,
            "raw_content": raw_content
        }
    
    async def interpret_structure(self, state: ParserState) -> dict:
        """
        FASE 2: El LLM interpreta la estructura del archivo.
        
        Identifica:
        - Qué columnas existen
        - Qué significan (fecha, concepto, importe, etc.)
        - Formato de cada columna
        """
        self.log_step("interpret_structure", state)
        self.logger.info("🤖 [SMART PARSER] LLM interpreting structure", formato=state["formato"])
        
        formato = state["formato"]
        raw_content = state["raw_content"]
        
        # OFX no necesita interpretación
        if formato == "ofx":
            return {
                **state,
                "estructura": {"formato": "ofx", "standard": True}
            }
        
        # Usar LLM para interpretar
        prompt = f"""Analiza este extracto bancario e identifica la estructura de las columnas.

Formato detectado: {formato.upper()}

Contenido (primeras líneas):
{raw_content}

Responde SOLO con JSON válido en este formato:
{{
  "tiene_cabecera": true/false,
  "delimitador": "," o ";" o "\\t" (para CSV),
  "columnas": [
    {{"indice": 0, "nombre_detectado": "Fecha", "tipo": "fecha", "formato_ejemplo": "DD/MM/YYYY"}},
    {{"indice": 1, "nombre_detectado": "Concepto", "tipo": "texto"}},
    {{"indice": 2, "nombre_detectado": "Importe", "tipo": "numero", "formato_ejemplo": "1.234,56"}}
  ],
  "encoding_sugerido": "utf-8",
  "notas": "Cualquier observación importante"
}}

IMPORTANTE:
- Identifica TODAS las columnas que ves
- Para "tipo" usa: fecha, texto, numero, referencia
- Si hay columnas "Debe" y "Haber", márcalas como "numero" ambas
"""
        
        try:
            response = await self.hf_service._call_llm(
                prompt=prompt,
                system_prompt="Eres un experto en análisis de extractos bancarios. Respondes SOLO con JSON válido.",
                max_tokens=800,
                temperature=0.1
            )
            
            # Parsear JSON
            import json
            estructura = json.loads(response.strip())
            
            self.logger.info(
                "✅ [SMART PARSER] Structure interpreted by LLM",
                columnas_detectadas=len(estructura.get('columnas', [])),
                tiene_cabecera=estructura.get('tiene_cabecera'),
                delimitador=estructura.get('delimitador')
            )
            
            return {
                **state,
                "estructura": estructura,
                "metadata": {
                    **state.get("metadata", {}),
                    "llm_interpretation": True
                }
            }
        
        except Exception as e:
            self.logger.error("❌ [SMART PARSER] LLM interpretation failed", error=str(e))
            # Fallback: usar keywords (Fase 1)
            return {
                **state,
                "estructura": {"error": str(e), "fallback": "keywords"},
                "metadata": {
                    **state.get("metadata", {}),
                    "llm_interpretation": False,
                    "llm_error": str(e)
                }
            }
    
    async def extract_transactions(self, state: ParserState) -> dict:
        """
        FASE 2/3: Extrae transacciones usando estructura interpretada por LLM.
        
        Fase 3: Para PDF/imágenes, usa el LLM para parsear el texto extraído.
        """
        self.log_step("extract_transactions", state)
        self.logger.info("💰 [SMART PARSER] Extracting transactions", formato=state["formato"])
        
        formato = state["formato"]
        file_path = state["file_path"]
        estructura = state.get("estructura", {})
        
        # FASE 3: PDF e imágenes usan LLM directo
        if formato in ("pdf", "image"):
            # Recuperar texto completo
            full_text = state.get(f"_{formato}_full_text", state.get("raw_content", ""))
            
            if not full_text:
                raise ValueError(f"No se pudo extraer texto del {formato}")
            
            # Usar LLM para parsear texto a transacciones
            transacciones = await self._parse_text_with_llm(full_text, estructura)
            extractor_name = f"LLM_{formato}"
        
        # FASE 2: CSV/Excel con hints del LLM
        elif estructura.get("llm_interpretation") or "columnas" in estructura:
            if formato == "csv":
                from app.services.extractors.csv_extractor_llm import CSVExtractorLLM
                extractor = CSVExtractorLLM(estructura)
                transacciones = await extractor.extract(file_path)
            
            elif formato == "excel":
                from app.services.extractors.excel_extractor_llm import ExcelExtractorLLM
                extractor = ExcelExtractorLLM(estructura)
                transacciones = await extractor.extract(file_path)
            
            else:
                # OFX
                from app.services.extractors.ofx_extractor import OFXExtractor
                extractor = OFXExtractor()
                transacciones = await extractor.extract(file_path)
            
            extractor_name = extractor.__class__.__name__
        
        else:
            # Fallback a extractores Fase 1 (keywords)
            if formato == "csv":
                from app.services.extractors.csv_extractor import CSVExtractor
                extractor = CSVExtractor()
                transacciones = await extractor.extract(file_path)
            
            elif formato == "excel":
                from app.services.extractors.excel_extractor import ExcelExtractor
                extractor = ExcelExtractor()
                transacciones = await extractor.extract(file_path)
            
            elif formato == "ofx":
                from app.services.extractors.ofx_extractor import OFXExtractor
                extractor = OFXExtractor()
                transacciones = await extractor.extract(file_path)
            
            else:
                raise ValueError(f"Formato no soportado: {formato}")
            
            extractor_name = extractor.__class__.__name__
        
        self.logger.info(
            "✅ [SMART PARSER] Transactions extracted",
            count=len(transacciones),
            extractor=extractor_name,
            used_llm=("columnas" in estructura or formato in ("pdf", "image"))
        )
        
        return {
            **state,
            "transacciones": transacciones,
            "metadata": {
                **state.get("metadata", {}),
                "transacciones_extraidas": len(transacciones),
                "extractor_usado": extractor_name,
                "used_llm_hints": "columnas" in estructura or formato in ("pdf", "image")
            }
        }
    
    async def _parse_text_with_llm(self, text: str, estructura: dict) -> list[dict]:
        """
        Parsea texto extraído (de PDF/imagen) a transacciones usando LLM.
        
        Args:
            text: Texto extraído por Vision/PyPDF
            estructura: Estructura interpretada (puede tener hints)
        
        Returns:
            Lista de transacciones
        """
        prompt = f"""Extrae TODAS las transacciones de este extracto bancario.

Texto:
{text}

Responde SOLO con un array JSON válido:
[
  {{
    "fecha": "DD/MM/YYYY",
    "concepto": "descripción de la transacción",
    "importe": "1234.56" (positivo para ingresos, negativo para gastos),
    "referencia": "ref si existe o null"
  }},
  ...
]

IMPORTANTE:
- Extrae TODAS las transacciones que encuentres
- Normaliza importes a formato numérico
- Si hay columnas "Debe" y "Haber", conviértelas:
  * Debe → importe negativo
  * Haber → importe positivo
- Mantén fechas en formato original
"""
        
        try:
            response = await self.hf_service._call_llm(
                prompt=prompt,
                system_prompt="Eres un experto en extracción de datos de extractos bancarios. Respondes SOLO con JSON válido.",
                max_tokens=3000,
                temperature=0.1
            )
            
            # Parsear JSON
            import json
            transacciones = json.loads(response.strip())
            
            # Agregar metadata
            for tx in transacciones:
                tx['metadata'] = {
                    'formato': 'text_llm_parsed',
                    'extractor': 'llm_direct'
                }
            
            return transacciones
        
        except Exception as e:
            self.logger.error(f"Error parsing text with LLM: {e}")
            # Retornar vacío en caso de error
            return []
    
    async def validate_and_clean(self, state: ParserState) -> dict:
        """
        Valida y limpia las transacciones extraídas.
        
        Normaliza:
        - Fechas a ISO format
        - Importes a float
        - Conceptos (trim, lowercase)
        """
        self.log_step("validate_clean", state)
        self.logger.info("🧹 [SMART PARSER] Validating and cleaning transactions", count=len(state["transacciones"]))
        
        from app.services.validators import TransactionValidator
        
        validator = TransactionValidator()
        transacciones = state["transacciones"]
        
        validadas = []
        errores = []
        
        for idx, tx in enumerate(transacciones):
            try:
                tx_validada = validator.validate(tx)
                validadas.append(tx_validada)
            except Exception as e:
                errores.append({
                    "linea": idx + 1,
                    "transaccion": tx,
                    "error": str(e)
                })
        
        status = "completed" if not errores else "completed_with_errors"
        
        self.logger.info(
            "✅ [SMART PARSER] Validation complete",
            validadas=len(validadas),
            errores=len(errores),
            status=status
        )
        
        return {
            **state,
            "transacciones_validadas": validadas,
            "errores": errores,
            "status": status,
            "metadata": {
                **state.get("metadata", {}),
                "validadas": len(validadas),
                "errores": len(errores)
            }
        }

