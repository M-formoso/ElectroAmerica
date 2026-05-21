"""Hacer deposito_id nullable en remitos

Revision ID: 025
Revises: 024
Create Date: 2026-05-21 14:00:00

Cuando se registra una entrada/ingreso desde el modulo Materiales,
el remito de ingreso suma al stock global del material y no esta
asociado a un deposito especifico. Permitir NULL en deposito_id para
ese caso.
"""
from alembic import op


revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('remitos', 'deposito_id', nullable=True)


def downgrade():
    op.alter_column('remitos', 'deposito_id', nullable=False)
