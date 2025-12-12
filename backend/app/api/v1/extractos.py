# backend/app/api/v1/extractos.py
"""Endpoints de carga de extractos bancarios."""

import hashlib
import tempfile
from pathlib import Path
from uuid import UUID
from decimal import Decimal
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, TokenPayload
from app.models.empresa import CuentaBancaria, Empresa
from app.models.transaccion import Transaccion
from app.services.parsers import get_parser
from app.agents.smart_parser import SmartParserAgent
from app.services.hf_inference import HFInferenceService

router = APIRouter(prefix="/extractos", tags=["extractos"])


@router.post("/upload")
async def upload_extracto(
    cuenta_id: UUID = Form(...),
    file: UploadFile = File(...),
    formato: str | None = Form(None),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cargar extracto bancario.
    
    Formatos soportados: CSV, OFX, QFX
    """
    # Verificar que la cuenta pertenece al tenant
    stmt = (
        select(CuentaBancaria)
        .join(CuentaBancaria.empresa)
        .where(
            CuentaBancaria.id == cuenta_id,
            CuentaBancaria.empresa.has(tenant_id=UUID(current_user.tenant_id)),
        )
    )
    result = await db.execute(stmt)
    cuenta = result.scalar_one_or_none()
    
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    # Leer contenido
    content = await file.read()
    
    # Obtener parser apropiado
    try:
        parser = get_parser(content, formato)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Parsear transacciones
    try:
        transacciones_raw = parser.parse(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parseando archivo: {e}")
    
    if not transacciones_raw:
        raise HTTPException(status_code=400, detail="No se encontraron transacciones en el archivo")
    
    # Verificar duplicados y crear transacciones
    created = 0
    duplicados = 0
    
    for tx_raw in transacciones_raw:
        tx_hash = tx_raw.compute_hash()
        
        # Verificar si ya existe
        stmt = select(Transaccion).where(Transaccion.hash == tx_hash)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            duplicados += 1
            continue
        
        # Determinar tipo
        tipo = "ingreso" if tx_raw.importe > 0 else "gasto"
        
        transaccion = Transaccion(
            cuenta_id=cuenta_id,
            fecha=tx_raw.fecha,
            fecha_valor=tx_raw.fecha_valor,
            importe=tx_raw.importe,
            concepto=tx_raw.concepto,
            tipo=tipo,
            referencia=tx_raw.referencia,
            hash=tx_hash,
        )
        db.add(transaccion)
        created += 1
    
    await db.commit()
    
    return {
        "message": "Extracto procesado correctamente",
        "transacciones_creadas": created,
        "duplicados_ignorados": duplicados,
        "total_en_archivo": len(transacciones_raw),
    }


@router.get("/preview")
async def preview_extracto(
    file: UploadFile = File(...),
    formato: str | None = None,
):
    """
    Preview de extracto sin guardar.
    
    Útil para verificar el parseo antes de cargar.
    """
    content = await file.read()
    
    try:
        parser = get_parser(content, formato)
        transacciones_raw = parser.parse(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "total": len(transacciones_raw),
        "transacciones": [
            {
                "fecha": tx.fecha.isoformat(),
                "concepto": tx.concepto,
                "importe": float(tx.importe),
                "saldo": float(tx.saldo) if tx.saldo else None,
            }
            for tx in transacciones_raw[:20]  # Solo primeras 20
        ],
    }


@router.post("/upload-smart")
async def upload_extracto_smart(
    cuenta_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cargar extracto bancario con SMART PARSER (Fase 1).
    
    Ventajas sobre /upload:
    - ✅ Detecta formato automáticamente
    - ✅ Acepta CSV con cualquier columna
    - ✅ Acepta Excel (.xlsx, .xls)
    - ✅ Parseo flexible (palabras clave en headers)
    
    Formatos soportados: CSV, Excel, OFX
    """
    # Verificar que la cuenta pertenece al tenant
    stmt = (
        select(CuentaBancaria)
        .join(Empresa)
        .where(
            CuentaBancaria.id == cuenta_id,
            Empresa.tenant_id == UUID(current_user.tenant_id),
        )
    )
    result = await db.execute(stmt)
    cuenta = result.scalar_one_or_none()
    
    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")
    
    # Guardar archivo temporalmente
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Ejecutar SmartParserAgent
        hf_service = HFInferenceService()
        agent = SmartParserAgent(db, hf_service)
        
        initial_state = {
            "tenant_id": current_user.tenant_id,
            "session_id": f"parse_{cuenta_id}",
            "file_path": tmp_path,
            "empresa_id": str(cuenta.empresa_id),
            "cuenta_id": str(cuenta_id),
            "transacciones": [],
            "transacciones_validadas": [],
            "errores": [],
            "metadata": {
                "filename": file.filename,
                "content_type": file.content_type,
            }
        }
        
        result = await agent.run(initial_state)
        
        if result.get("status") == "error":
            raise HTTPException(
                status_code=400,
                detail=f"Error parseando archivo: {result.get('error')}"
            )
        
        # Insertar transacciones validadas
        transacciones_validadas = result.get("transacciones_validadas", [])
        errores_parseo = result.get("errores", [])
        
        created = 0
        duplicados = 0
        
        for tx_data in transacciones_validadas:
            # Calcular hash para deduplicación
            hash_str = f"{tx_data['fecha']}|{tx_data['concepto']}|{tx_data['importe']}"
            tx_hash = hashlib.md5(hash_str.encode()).hexdigest()
            
            # Verificar duplicado
            stmt = select(Transaccion).where(Transaccion.hash == tx_hash)
            result_dup = await db.execute(stmt)
            if result_dup.scalar_one_or_none():
                duplicados += 1
                continue
            
            # Crear transacción
            tipo = "ingreso" if tx_data['importe'] > 0 else "gasto"
            
            transaccion = Transaccion(
                cuenta_id=cuenta_id,
                fecha=date.fromisoformat(tx_data['fecha']),
                fecha_valor=date.fromisoformat(tx_data['fecha']),  # Por ahora igual
                importe=Decimal(str(tx_data['importe'])),
                concepto=tx_data['concepto'],
                tipo=tipo,
                referencia=tx_data.get('referencia'),
                hash=tx_hash,
                estado="pending",  # Para posterior clasificación
            )
            db.add(transaccion)
            created += 1
        
        await db.commit()
        
        return {
            "message": "Extracto procesado con Smart Parser",
            "formato_detectado": result.get("formato"),
            "transacciones_creadas": created,
            "duplicados_ignorados": duplicados,
            "errores_parseo": len(errores_parseo),
            "total_en_archivo": len(transacciones_validadas) + len(errores_parseo),
            "metadata": result.get("metadata", {}),
            "errores": errores_parseo[:5] if errores_parseo else [],  # Primeros 5
        }
    
    finally:
        # Limpiar archivo temporal
        Path(tmp_path).unlink(missing_ok=True)
