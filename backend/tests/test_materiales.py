import pytest
from uuid import uuid4
from decimal import Decimal
from fastapi.testclient import TestClient
from tests.conftest import auth_headers
from app.models.material import Material


class TestMateriales:
    """Tests for materials endpoints."""

    def test_create_material(self, client: TestClient, admin_token):
        """Test creating a material."""
        response = client.post(
            "/api/v1/materiales/",
            json={
                "codigo": "MAT-001",
                "nombre": "Cable 2.5mm",
                "unidad": "metros",
                "stock_actual": 100,
                "stock_minimo": 20,
                "precio_unitario": 150.50
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 201
        data = response.json()
        assert data["codigo"] == "MAT-001"
        assert data["nombre"] == "Cable 2.5mm"
        assert data["stock_actual"] == 100

    def test_create_material_duplicate_code(self, client: TestClient, admin_token, db):
        """Test that duplicate codes are rejected."""
        material = Material(
            codigo="MAT-DUP",
            nombre="Material Existente",
            unidad="unidad",
            stock_actual=50
        )
        db.add(material)
        db.commit()

        response = client.post(
            "/api/v1/materiales/",
            json={
                "codigo": "MAT-DUP",
                "nombre": "Nuevo Material",
                "unidad": "unidad"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 400

    def test_list_materiales(self, client: TestClient, admin_token, db):
        """Test listing materials."""
        for i in range(5):
            material = Material(
                codigo=f"MAT-{i:03d}",
                nombre=f"Material {i}",
                unidad="unidad",
                stock_actual=i * 10
            )
            db.add(material)
        db.commit()

        response = client.get(
            "/api/v1/materiales/",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_get_material(self, client: TestClient, admin_token, db):
        """Test getting a single material."""
        material = Material(
            codigo="MAT-GET",
            nombre="Material Detalle",
            unidad="kg",
            stock_actual=75
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        response = client.get(
            f"/api/v1/materiales/{material.id}",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Material Detalle"

    def test_update_material(self, client: TestClient, admin_token, db):
        """Test updating a material."""
        material = Material(
            codigo="MAT-UPD",
            nombre="Material Original",
            unidad="unidad",
            stock_actual=50
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        response = client.put(
            f"/api/v1/materiales/{material.id}",
            json={"nombre": "Material Actualizado", "stock_minimo": 15},
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Material Actualizado"
        assert data["stock_minimo"] == 15

    def test_registrar_entrada_stock(self, client: TestClient, admin_token, db):
        """Test registering stock entry."""
        material = Material(
            codigo="MAT-ENT",
            nombre="Material Entrada",
            unidad="unidad",
            stock_actual=100
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        response = client.post(
            f"/api/v1/materiales/{material.id}/entrada",
            json={
                "cantidad": 50,
                "motivo": "Compra nueva"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stock_actual"] == 150

    def test_registrar_salida_stock(self, client: TestClient, admin_token, db):
        """Test registering stock exit."""
        material = Material(
            codigo="MAT-SAL",
            nombre="Material Salida",
            unidad="unidad",
            stock_actual=100
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        response = client.post(
            f"/api/v1/materiales/{material.id}/salida",
            json={
                "cantidad": 30,
                "motivo": "Uso en proyecto"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["stock_actual"] == 70

    def test_salida_stock_insuficiente(self, client: TestClient, admin_token, db):
        """Test that exit fails with insufficient stock."""
        material = Material(
            codigo="MAT-INS",
            nombre="Material Insuficiente",
            unidad="unidad",
            stock_actual=10
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        response = client.post(
            f"/api/v1/materiales/{material.id}/salida",
            json={
                "cantidad": 50,
                "motivo": "Intento de salida"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 400

    def test_stock_bajo(self, client: TestClient, admin_token, db):
        """Test getting materials with low stock."""
        # Material con stock bajo
        material_bajo = Material(
            codigo="MAT-BAJO",
            nombre="Material Bajo",
            unidad="unidad",
            stock_actual=5,
            stock_minimo=20
        )
        # Material con stock ok
        material_ok = Material(
            codigo="MAT-OK",
            nombre="Material OK",
            unidad="unidad",
            stock_actual=100,
            stock_minimo=20
        )
        db.add_all([material_bajo, material_ok])
        db.commit()

        response = client.get(
            "/api/v1/materiales/stock-bajo",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["codigo"] == "MAT-BAJO"

    def test_operario_cannot_delete(self, client: TestClient, operario_token, db):
        """Test that operarios cannot delete materials."""
        material = Material(
            codigo="MAT-DEL",
            nombre="Material Protegido",
            unidad="unidad",
            stock_actual=50
        )
        db.add(material)
        db.commit()
        db.refresh(material)

        response = client.delete(
            f"/api/v1/materiales/{material.id}",
            headers=auth_headers(operario_token)
        )
        assert response.status_code == 403
