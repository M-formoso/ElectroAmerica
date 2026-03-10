import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from tests.conftest import auth_headers
from app.models.proyecto import Proyecto, EstadoProyecto


class TestProyectos:
    """Tests for project endpoints."""

    def test_create_proyecto_admin(self, client: TestClient, admin_token, cliente_user):
        """Test creating a project as admin."""
        response = client.post(
            "/api/v1/proyectos/",
            json={
                "nombre": "Proyecto Test",
                "descripcion": "Descripción del proyecto",
                "ubicacion": "Buenos Aires",
                "cliente_id": str(cliente_user.id)
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 201
        data = response.json()
        assert data["nombre"] == "Proyecto Test"
        assert data["estado"] == "planificacion"

    def test_create_proyecto_operario_forbidden(self, client: TestClient, operario_token):
        """Test that operarios cannot create projects."""
        response = client.post(
            "/api/v1/proyectos/",
            json={
                "nombre": "Proyecto Test",
                "descripcion": "Descripción"
            },
            headers=auth_headers(operario_token)
        )
        assert response.status_code == 403

    def test_list_proyectos(self, client: TestClient, admin_token, db, cliente_user):
        """Test listing projects."""
        # Create some projects
        for i in range(3):
            proyecto = Proyecto(
                nombre=f"Proyecto {i}",
                cliente_id=cliente_user.id,
                estado=EstadoProyecto.planificacion
            )
            db.add(proyecto)
        db.commit()

        response = client.get(
            "/api/v1/proyectos/",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_proyecto(self, client: TestClient, admin_token, db, cliente_user):
        """Test getting a single project."""
        proyecto = Proyecto(
            nombre="Proyecto Detalle",
            cliente_id=cliente_user.id,
            estado=EstadoProyecto.planificacion
        )
        db.add(proyecto)
        db.commit()
        db.refresh(proyecto)

        response = client.get(
            f"/api/v1/proyectos/{proyecto.id}",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Proyecto Detalle"

    def test_get_proyecto_not_found(self, client: TestClient, admin_token):
        """Test getting nonexistent project."""
        response = client.get(
            f"/api/v1/proyectos/{uuid4()}",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 404

    def test_update_proyecto(self, client: TestClient, admin_token, db, cliente_user):
        """Test updating a project."""
        proyecto = Proyecto(
            nombre="Proyecto Original",
            cliente_id=cliente_user.id,
            estado=EstadoProyecto.planificacion
        )
        db.add(proyecto)
        db.commit()
        db.refresh(proyecto)

        response = client.put(
            f"/api/v1/proyectos/{proyecto.id}",
            json={"nombre": "Proyecto Actualizado"},
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["nombre"] == "Proyecto Actualizado"

    def test_delete_proyecto(self, client: TestClient, admin_token, db, cliente_user):
        """Test soft deleting a project."""
        proyecto = Proyecto(
            nombre="Proyecto a Eliminar",
            cliente_id=cliente_user.id,
            estado=EstadoProyecto.planificacion
        )
        db.add(proyecto)
        db.commit()
        db.refresh(proyecto)

        response = client.delete(
            f"/api/v1/proyectos/{proyecto.id}",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 204

        # Verify soft delete
        db.refresh(proyecto)
        assert proyecto.activo == False

    def test_cambiar_estado_proyecto(self, client: TestClient, admin_token, db, cliente_user):
        """Test changing project status."""
        proyecto = Proyecto(
            nombre="Proyecto Estado",
            cliente_id=cliente_user.id,
            estado=EstadoProyecto.planificacion
        )
        db.add(proyecto)
        db.commit()
        db.refresh(proyecto)

        response = client.put(
            f"/api/v1/proyectos/{proyecto.id}/estado",
            params={"nuevo_estado": "en_ejecucion"},
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "en_ejecucion"

    def test_cliente_only_sees_own_projects(
        self, client: TestClient, cliente_token, db, cliente_user, admin_user
    ):
        """Test that clients only see their own projects."""
        # Create project for this client
        proyecto_cliente = Proyecto(
            nombre="Mi Proyecto",
            cliente_id=cliente_user.id,
            estado=EstadoProyecto.planificacion
        )
        # Create project for another client (admin as client for test)
        proyecto_otro = Proyecto(
            nombre="Proyecto Ajeno",
            cliente_id=admin_user.id,
            estado=EstadoProyecto.planificacion
        )
        db.add_all([proyecto_cliente, proyecto_otro])
        db.commit()

        response = client.get(
            "/api/v1/proyectos/",
            headers=auth_headers(cliente_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["nombre"] == "Mi Proyecto"
