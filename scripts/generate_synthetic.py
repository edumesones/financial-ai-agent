#!/usr/bin/env python3
"""
Script para generar datos sintéticos de prueba.

Uso:
    python scripts/generate_synthetic.py

Genera:
    - 1 tenant de prueba
    - 1 usuario admin
    - 3 empresas con cuentas bancarias
    - ~500 transacciones por empresa
    - Algunas reglas de clasificación
"""

import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4
import hashlib

from faker import Faker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Añadir path del proyecto
import sys
import os
sys.path.insert(0, 'backend')
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import get_settings
from app.core.security import hash_password
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.empresa import Empresa, CuentaBancaria
from app.models.transaccion import Transaccion
from app.models.clasificacion import ReglaClasificacion

settings = get_settings()
fake = Faker('es_ES')

# Categorías PGC comunes
CATEGORIAS_GASTOS = [
    ("621", "Arrendamientos y cánones", ["alquiler", "renting", "leasing"]),
    ("622", "Reparaciones y conservación", ["reparación", "mantenimiento", "arreglo"]),
    ("623", "Servicios profesionales", ["asesoría", "consultoría", "abogado", "notario"]),
    ("624", "Transportes", ["taxi", "uber", "gasolina", "peaje", "parking"]),
    ("625", "Primas de seguros", ["seguro", "póliza", "mutua"]),
    ("626", "Servicios bancarios", ["comisión", "transferencia", "mantenimiento cuenta"]),
    ("627", "Publicidad", ["publicidad", "marketing", "google ads", "facebook"]),
    ("628", "Suministros", ["luz", "agua", "gas", "teléfono", "internet", "iberdrola", "endesa"]),
    ("629", "Otros servicios", ["limpieza", "mensajería", "suscripción"]),
    ("600", "Compras de mercaderías", ["mercancía", "stock", "inventario", "proveedor"]),
]

BANCOS = ["Santander", "BBVA", "CaixaBank", "Sabadell", "Bankinter"]


def generate_iban() -> str:
    """Generar IBAN español ficticio."""
    return f"ES{random.randint(10, 99)}{random.randint(1000, 9999)}{random.randint(1000, 9999)}{random.randint(10, 99)}{random.randint(1000000000, 9999999999)}"


def generate_transaction_concept(tipo: str) -> tuple[str, str]:
    """Generar concepto de transacción y categoría sugerida."""
    if tipo == "gasto":
        categoria, nombre, keywords = random.choice(CATEGORIAS_GASTOS)
        
        templates = [
            f"Pago {random.choice(keywords)} - {fake.company()}",
            f"Factura {fake.company()} - {random.choice(keywords)}",
            f"Recibo {random.choice(keywords).upper()}",
            f"TRANSF. {fake.company()[:20]}",
            f"ADEUDO {random.choice(keywords).upper()} {fake.date_this_year().strftime('%m/%y')}",
        ]
        return random.choice(templates), categoria
    else:
        templates = [
            f"Cobro factura {fake.random_number(digits=6)}",
            f"TRANSF. DE {fake.company()[:20]}",
            f"Ingreso {fake.company()}",
            f"Pago cliente {fake.name()}",
        ]
        return random.choice(templates), "700"


async def generate_data():
    """Generar todos los datos sintéticos."""
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("🏢 Creando tenant de prueba...")
        tenant = Tenant(
            nombre="Gestoría Demo S.L.",
            cif="B12345678",
            email="demo@gestoria.es",
        )
        db.add(tenant)
        await db.flush()
        
        print("👤 Creando usuario admin...")
        admin = Usuario(
            tenant_id=tenant.id,
            email="admin@gestoria.es",
            password_hash=hash_password("admin123"),
            nombre="Admin",
            apellidos="Demo",
            rol="admin",
        )
        db.add(admin)
        
        print("🏭 Creando empresas...")
        empresas = []
        sectores = ["Comercio", "Servicios", "Construcción", "Hostelería", "Tecnología"]
        
        for i in range(3):
            empresa = Empresa(
                tenant_id=tenant.id,
                nombre=fake.company(),
                cif=f"B{random.randint(10000000, 99999999)}",
                sector=random.choice(sectores),
                direccion=fake.address(),
            )
            
            # Añadir 1-2 cuentas bancarias
            for j in range(random.randint(1, 2)):
                cuenta = CuentaBancaria(
                    banco=random.choice(BANCOS),
                    iban=generate_iban(),
                    alias=f"Cuenta {['Principal', 'Secundaria', 'Nóminas'][j]}",
                )
                empresa.cuentas.append(cuenta)
            
            db.add(empresa)
            empresas.append(empresa)
        
        await db.flush()
        
        print("💸 Generando transacciones...")
        total_tx = 0
        
        for empresa in empresas:
            for cuenta in empresa.cuentas:
                # Generar transacciones de los últimos 6 meses
                fecha_inicio = date.today() - timedelta(days=180)
                
                for _ in range(random.randint(150, 200)):
                    # Fecha aleatoria
                    dias_offset = random.randint(0, 180)
                    fecha = fecha_inicio + timedelta(days=dias_offset)
                    
                    # 70% gastos, 30% ingresos
                    tipo = "gasto" if random.random() < 0.7 else "ingreso"
                    
                    concepto, categoria = generate_transaction_concept(tipo)
                    
                    if tipo == "gasto":
                        importe = -Decimal(str(round(random.uniform(10, 5000), 2)))
                    else:
                        importe = Decimal(str(round(random.uniform(100, 15000), 2)))
                    
                    # Hash único
                    hash_data = f"{fecha.isoformat()}|{concepto}|{float(importe)}|{uuid4()}"
                    tx_hash = hashlib.sha256(hash_data.encode()).hexdigest()[:16]
                    
                    tx = Transaccion(
                        cuenta_id=cuenta.id,
                        fecha=fecha,
                        importe=importe,
                        concepto=concepto,
                        tipo=tipo,
                        hash=tx_hash,
                    )
                    db.add(tx)
                    total_tx += 1
        
        print(f"   ✅ {total_tx} transacciones creadas")
        
        print("📋 Creando reglas de clasificación...")
        reglas = [
            {
                "nombre": "Iberdrola -> Suministros",
                "condicion": {"campo": "concepto", "operador": "contains", "valor": "iberdrola"},
                "categoria_pgc": "628",
            },
            {
                "nombre": "Endesa -> Suministros", 
                "condicion": {"campo": "concepto", "operador": "contains", "valor": "endesa"},
                "categoria_pgc": "628",
            },
            {
                "nombre": "Alquiler -> Arrendamientos",
                "condicion": {"campo": "concepto", "operador": "contains", "valor": "alquiler"},
                "categoria_pgc": "621",
            },
            {
                "nombre": "Seguro -> Primas de seguros",
                "condicion": {"campo": "concepto", "operador": "contains", "valor": "seguro"},
                "categoria_pgc": "625",
            },
            {
                "nombre": "Comisión bancaria -> Servicios bancarios",
                "condicion": {"campo": "concepto", "operador": "contains", "valor": "comisión"},
                "categoria_pgc": "626",
            },
        ]
        
        for regla_data in reglas:
            regla = ReglaClasificacion(
                tenant_id=tenant.id,
                nombre=regla_data["nombre"],
                condicion=regla_data["condicion"],
                categoria_pgc=regla_data["categoria_pgc"],
                prioridad=10,
            )
            db.add(regla)
        
        await db.commit()
        
        print("\n" + "="*50)
        print("✅ Datos sintéticos generados correctamente!")
        print("="*50)
        print(f"\n📧 Usuario de prueba:")
        print(f"   Email: admin@gestoria.es")
        print(f"   Password: admin123")
        print(f"\n📊 Datos creados:")
        print(f"   - 1 tenant (gestoría)")
        print(f"   - 1 usuario admin")
        print(f"   - {len(empresas)} empresas")
        print(f"   - {total_tx} transacciones")
        print(f"   - {len(reglas)} reglas de clasificación")
        print("="*50)


if __name__ == "__main__":
    asyncio.run(generate_data())
