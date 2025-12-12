"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-12-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tenant
    op.create_table(
        'tenant',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('cif', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Usuario
    op.create_table(
        'usuario',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('apellidos', sa.String(200), nullable=True),
        sa.Column('rol', sa.String(20), nullable=False, server_default='gestor'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_usuario_email', 'usuario', ['email'], unique=True)
    op.create_index('ix_usuario_tenant_id', 'usuario', ['tenant_id'])
    
    # Empresa
    op.create_table(
        'empresa',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('cif', sa.String(20), nullable=True),
        sa.Column('sector', sa.String(100), nullable=True),
        sa.Column('direccion', sa.String(500), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_empresa_tenant_id', 'empresa', ['tenant_id'])
    op.create_index('ix_empresa_cif', 'empresa', ['cif'])
    
    # CuentaBancaria
    op.create_table(
        'cuenta_bancaria',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('empresa_id', sa.UUID(), nullable=False),
        sa.Column('banco', sa.String(100), nullable=True),
        sa.Column('iban', sa.String(34), nullable=True),
        sa.Column('alias', sa.String(100), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cuenta_bancaria_empresa_id', 'cuenta_bancaria', ['empresa_id'])
    op.create_index('ix_cuenta_bancaria_iban', 'cuenta_bancaria', ['iban'])
    
    # Transaccion
    op.create_table(
        'transaccion',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('cuenta_id', sa.UUID(), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('fecha_valor', sa.Date(), nullable=True),
        sa.Column('importe', sa.Numeric(15, 2), nullable=False),
        sa.Column('concepto', sa.String(500), nullable=True),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('referencia', sa.String(100), nullable=True),
        sa.Column('hash', sa.String(64), nullable=False),
        sa.Column('metadata_extra', sa.JSON(), nullable=True),
        sa.Column('embedding', Vector(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['cuenta_id'], ['cuenta_bancaria.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transaccion_cuenta_id', 'transaccion', ['cuenta_id'])
    op.create_index('ix_transaccion_fecha', 'transaccion', ['fecha'])
    op.create_index('ix_transaccion_hash', 'transaccion', ['hash'], unique=True)
    op.create_index('idx_transaccion_cuenta_fecha', 'transaccion', ['cuenta_id', 'fecha'])
    
    # Clasificacion
    op.create_table(
        'clasificacion',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('transaccion_id', sa.UUID(), nullable=False),
        sa.Column('categoria_pgc', sa.String(10), nullable=False),
        sa.Column('subcuenta', sa.String(20), nullable=True),
        sa.Column('confianza', sa.Numeric(3, 2), nullable=False),
        sa.Column('metodo', sa.String(20), nullable=False),
        sa.Column('explicacion', sa.String(500), nullable=True),
        sa.Column('validado_por', sa.UUID(), nullable=True),
        sa.Column('validado_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['transaccion_id'], ['transaccion.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['validado_por'], ['usuario.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_clasificacion_transaccion_id', 'clasificacion', ['transaccion_id'], unique=True)
    
    # Conciliacion
    op.create_table(
        'conciliacion',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('transaccion_id', sa.UUID(), nullable=False),
        sa.Column('asiento_id', sa.String(100), nullable=True),
        sa.Column('confianza', sa.Numeric(3, 2), nullable=False),
        sa.Column('estado', sa.String(20), nullable=False, server_default='pendiente'),
        sa.Column('match_type', sa.String(20), nullable=False),
        sa.Column('match_details', sa.JSON(), nullable=True),
        sa.Column('validado_por', sa.UUID(), nullable=True),
        sa.Column('validado_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['transaccion_id'], ['transaccion.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['validado_por'], ['usuario.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_conciliacion_transaccion_id', 'conciliacion', ['transaccion_id'], unique=True)
    
    # ReglaClasificacion
    op.create_table(
        'regla_clasificacion',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('empresa_id', sa.UUID(), nullable=True),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.String(500), nullable=True),
        sa.Column('condicion', sa.JSON(), nullable=False),
        sa.Column('categoria_pgc', sa.String(10), nullable=False),
        sa.Column('prioridad', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_regla_clasificacion_tenant_id', 'regla_clasificacion', ['tenant_id'])


def downgrade() -> None:
    op.drop_table('regla_clasificacion')
    op.drop_table('conciliacion')
    op.drop_table('clasificacion')
    op.drop_table('transaccion')
    op.drop_table('cuenta_bancaria')
    op.drop_table('empresa')
    op.drop_table('usuario')
    op.drop_table('tenant')
