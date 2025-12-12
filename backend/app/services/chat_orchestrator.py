# backend/app/services/chat_orchestrator.py
"""Orquestador de chat que usa LLM para decidir qué agente llamar."""

import json
import re
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.services.hf_inference import HFInferenceService
from app.models.empresa import Empresa, CuentaBancaria
from app.models.transaccion import Transaccion
from app.agents.tesoreria import TesoreriaAgent
from app.agents.clasificacion import ClasificacionAgent

logger = structlog.get_logger()

SYSTEM_PROMPT = """Eres un asistente financiero para gestorías españolas. Tu trabajo es ayudar a los gestores a analizar las finanzas de sus clientes.

Tienes acceso a las siguientes herramientas:

1. **listar_empresas** - Muestra las empresas disponibles
   - Usa cuando pregunten: qué empresas hay, lista de clientes, mostrar empresas, cuantas empresas

2. **tesoreria** - Analiza cash flow, métricas financieras, proyecciones y alertas de una empresa
   - Usa cuando pregunten sobre: saldo, tesorería, cash flow, liquidez, runway, burn rate, proyecciones
   
3. **clasificar** - Clasifica transacciones bancarias según el Plan General Contable (PGC)
   - Usa cuando pregunten sobre: clasificar gastos, categorizar transacciones, PGC

4. **info_empresa** - Muestra información detallada de una empresa específica
   - Usa cuando pregunten sobre una empresa específica sin análisis financiero

5. **respuesta_directa** - Responde directamente sin usar herramientas
   - Usa para saludos, preguntas generales, o cuando no necesitas datos

IMPORTANTE: 
- Si el usuario menciona una empresa por nombre, busca su ID
- Si no especifica empresa y hay contexto de empresa_id, usa ese
- Responde SIEMPRE en español
- Responde SOLO con el JSON, sin explicaciones adicionales

Formato de respuesta (SOLO JSON):
{"tool": "nombre_herramienta", "params": {}, "reasoning": "explicación breve"}

Ejemplo para "qué empresas tengo":
{"tool": "listar_empresas", "params": {}, "reasoning": "El usuario quiere ver sus empresas"}
"""


class ChatOrchestrator:
    """Orquesta el chat usando LLM para routing a agentes."""
    
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.hf = HFInferenceService()
    
    async def process_message(
        self, 
        message: str, 
        context: Optional[dict] = None
    ) -> dict:
        """Procesa un mensaje del usuario y devuelve respuesta."""
        context = context or {}
        
        # Obtener lista de empresas para contexto
        empresas = await self._get_empresas()
        empresas_text = "\n".join([
            f"- {e['nombre']} (ID: {e['id']})" for e in empresas
        ])
        
        # Construir prompt
        context_text = ""
        if context.get("empresa_id"):
            emp = next((e for e in empresas if e["id"] == context["empresa_id"]), None)
            if emp:
                context_text = f"\nEmpresa actualmente seleccionada: {emp['nombre']} (ID: {emp['id']})"
        
        user_prompt = f"""Empresas disponibles:
{empresas_text}
{context_text}

Mensaje del usuario: {message}

Responde SOLO con JSON, sin texto adicional:"""

        # Llamar a LLM para decidir
        try:
            decision = await self._call_llm_for_routing(user_prompt)
            logger.info("llm_decision", decision=decision, message=message[:50])
        except Exception as e:
            logger.error("llm_routing_error", error=str(e))
            return {
                "response": f"Error al procesar: {str(e)}",
                "tool_used": "error",
                "data": None
            }
        
        # Ejecutar herramienta decidida
        return await self._execute_tool(decision, context, empresas)
    
    async def _call_llm_for_routing(self, user_prompt: str) -> dict:
        """Llama al LLM para decidir qué herramienta usar."""
        
        full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"
        
        # Usar el servicio HF
        response_text = await self.hf._call_llm(full_prompt)
        
        logger.info("llm_raw_response", response=response_text[:500])
        
        # DeepSeek R1 puede incluir <think>...</think> antes de la respuesta
        # Eliminar bloques de pensamiento
        clean_response = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
        clean_response = clean_response.strip()
        
        logger.info("llm_cleaned_response", response=clean_response[:300])
        
        # Buscar JSON en la respuesta (puede estar en bloque de código)
        # Primero intentar extraer de bloque ```json
        json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean_response, re.DOTALL)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Buscar JSON directo (más permisivo, permite nested objects)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}', clean_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                logger.error("json_parse_error", error=str(e), text=json_match.group()[:200])
        
        # Intentar parsear toda la respuesta como JSON
        try:
            return json.loads(clean_response)
        except json.JSONDecodeError:
            pass
        
        # Detección manual de intención como fallback
        message_lower = user_prompt.lower()
        if any(kw in message_lower for kw in ['empresa', 'empresas', 'clientes', 'tengo', 'lista']):
            return {"tool": "listar_empresas", "params": {}, "reasoning": "fallback detection"}
        if any(kw in message_lower for kw in ['tesorería', 'tesoreria', 'saldo', 'cash', 'dinero']):
            return {"tool": "tesoreria", "params": {}, "reasoning": "fallback detection"}
        if any(kw in message_lower for kw in ['clasific', 'categoriz', 'pgc']):
            return {"tool": "clasificar", "params": {}, "reasoning": "fallback detection"}
        
        # Si no puede parsear, respuesta directa con el texto del LLM
        return {
            "tool": "respuesta_directa",
            "response": clean_response if clean_response else "No sé cómo ayudarte con eso.",
            "reasoning": "No se pudo parsear decisión"
        }
    
    async def _execute_tool(
        self, 
        decision: dict, 
        context: dict,
        empresas: list
    ) -> dict:
        """Ejecuta la herramienta decidida por el LLM."""
        
        tool = decision.get("tool", "respuesta_directa")
        params = decision.get("params", {})
        
        logger.info("executing_tool", tool=tool, params=params)
        
        if tool == "respuesta_directa":
            return {
                "response": decision.get("response", "No sé cómo ayudarte con eso."),
                "tool_used": "respuesta_directa",
                "data": None
            }
        
        elif tool == "listar_empresas":
            empresas_text = "\n".join([
                f"• **{e['nombre']}** - {e.get('sector', 'Sin sector')}" 
                for e in empresas
            ])
            return {
                "response": f"Tienes {len(empresas)} empresas:\n\n{empresas_text}",
                "tool_used": "listar_empresas",
                "data": {"empresas": empresas}
            }
        
        elif tool == "tesoreria":
            empresa_id = params.get("empresa_id") or context.get("empresa_id")
            
            # Si pasaron nombre, buscar ID
            if not empresa_id and params.get("empresa_nombre"):
                nombre = params["empresa_nombre"].lower()
                emp = next(
                    (e for e in empresas if nombre in e["nombre"].lower()), 
                    None
                )
                if emp:
                    empresa_id = emp["id"]
            
            if not empresa_id:
                return {
                    "response": "¿De qué empresa quieres analizar la tesorería? Dime el nombre.",
                    "tool_used": "tesoreria",
                    "data": None,
                    "needs_input": True
                }
            
            # Ejecutar agente de tesorería
            agent = TesoreriaAgent(self.db, self.hf)
            result = await agent.run({
                "tenant_id": self.tenant_id,
                "empresa_id": empresa_id,
                "periodo_dias": params.get("periodo_dias", 90)
            })
            
            # Formatear respuesta
            data = result.get("results", {})
            metricas = data.get("metricas", {})
            alertas = data.get("alertas", [])
            
            response = f"""📊 **Análisis de Tesorería**

💰 **Saldo actual:** €{metricas.get('saldo_total', 0):,.2f}
🔥 **Burn rate mensual:** €{metricas.get('burn_rate_mensual', 0):,.2f}
🛤️ **Runway:** {metricas.get('runway_meses', '∞')} meses
📈 **Ratio ingresos/gastos:** {metricas.get('ratio_ingresos_gastos', 'N/A')}"""

            if alertas:
                response += "\n\n⚠️ **Alertas:**\n" + "\n".join(alertas)
            
            recomendaciones = data.get("recomendaciones", [])
            if recomendaciones:
                response += "\n\n💡 **Recomendaciones:**\n" + "\n".join(f"• {r}" for r in recomendaciones)
            
            return {
                "response": response,
                "tool_used": "tesoreria",
                "data": data
            }
        
        elif tool == "clasificar":
            empresa_id = params.get("empresa_id") or context.get("empresa_id")
            
            if not empresa_id:
                return {
                    "response": "¿De qué empresa quieres clasificar transacciones?",
                    "tool_used": "clasificar",
                    "data": None,
                    "needs_input": True
                }
            
            # Obtener transacciones sin clasificar
            tx_ids = await self._get_unclassified_transactions(empresa_id)
            
            if not tx_ids:
                return {
                    "response": "✅ No hay transacciones pendientes de clasificar para esta empresa.",
                    "tool_used": "clasificar",
                    "data": None
                }
            
            # Ejecutar agente
            agent = ClasificacionAgent(self.db, self.hf)
            result = await agent.run({
                "tenant_id": self.tenant_id,
                "transaccion_ids": tx_ids[:20],  # Máximo 20
                "review_threshold": 0.75
            })
            
            data = result.get("results", {})
            total = data.get("total", 0)
            
            return {
                "response": f"✅ He clasificado **{total} transacciones**. Las de baja confianza requieren tu revisión.",
                "tool_used": "clasificar",
                "data": data
            }
        
        elif tool == "info_empresa":
            empresa_id = params.get("empresa_id") or context.get("empresa_id")
            nombre = params.get("empresa_nombre", "").lower()
            
            emp = None
            if empresa_id:
                emp = next((e for e in empresas if e["id"] == empresa_id), None)
            elif nombre:
                emp = next((e for e in empresas if nombre in e["nombre"].lower()), None)
            
            if not emp:
                return {
                    "response": "No encontré esa empresa. ¿Puedes decirme el nombre exacto?",
                    "tool_used": "info_empresa",
                    "data": None
                }
            
            # Obtener más detalles
            cuentas = await self._get_cuentas(emp["id"])
            tx_count = await self._get_transaction_count(emp["id"])
            
            cuentas_text = "\n".join([
                f"  • {c['banco']} - {c['iban'][-8:]}" for c in cuentas
            ]) or "  (ninguna)"
            
            return {
                "response": f"""🏢 **{emp['nombre']}**

📋 **CIF:** {emp.get('cif', 'N/A')}
🏭 **Sector:** {emp.get('sector', 'N/A')}
📍 **Dirección:** {emp.get('direccion', 'N/A')}

🏦 **Cuentas bancarias:**
{cuentas_text}

💳 **Transacciones:** {tx_count}""",
                "tool_used": "info_empresa",
                "data": emp
            }
        
        else:
            return {
                "response": f"No reconozco la herramienta '{tool}'. Intenta de otra forma.",
                "tool_used": "unknown",
                "data": None
            }
    
    async def _get_empresas(self) -> list:
        """Obtiene lista de empresas del tenant."""
        stmt = (
            select(Empresa)
            .where(Empresa.tenant_id == UUID(self.tenant_id), Empresa.activo == True)
        )
        result = await self.db.execute(stmt)
        empresas = result.scalars().all()
        return [
            {
                "id": str(e.id),
                "nombre": e.nombre,
                "cif": e.cif,
                "sector": e.sector,
                "direccion": e.direccion
            }
            for e in empresas
        ]
    
    async def _get_cuentas(self, empresa_id: str) -> list:
        """Obtiene cuentas de una empresa."""
        stmt = select(CuentaBancaria).where(CuentaBancaria.empresa_id == UUID(empresa_id))
        result = await self.db.execute(stmt)
        return [
            {"id": str(c.id), "banco": c.banco, "iban": c.iban}
            for c in result.scalars().all()
        ]
    
    async def _get_transaction_count(self, empresa_id: str) -> int:
        """Cuenta transacciones de una empresa."""
        from sqlalchemy import func
        stmt = (
            select(func.count(Transaccion.id))
            .join(CuentaBancaria)
            .where(CuentaBancaria.empresa_id == UUID(empresa_id))
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0
    
    async def _get_unclassified_transactions(self, empresa_id: str) -> list[str]:
        """Obtiene IDs de transacciones sin clasificar."""
        from app.models.clasificacion import Clasificacion
        
        # Transacciones que no tienen clasificación
        subquery = select(Clasificacion.transaccion_id)
        
        stmt = (
            select(Transaccion.id)
            .join(CuentaBancaria)
            .where(
                CuentaBancaria.empresa_id == UUID(empresa_id),
                ~Transaccion.id.in_(subquery)
            )
            .limit(50)
        )
        result = await self.db.execute(stmt)
        return [str(row[0]) for row in result.fetchall()]
