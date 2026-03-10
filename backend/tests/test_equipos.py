import pytest
from uuid import uuid4
from datetime import date, timedelta
from fastapi.testclient import TestClient
from tests.conftest import auth_headers
from app.models.equipo import Equipo, EstadoEquipo, TipoEquipo
from app.models.proyecto import Proyecto, EstadoProyecto


class TestEquipos:
    """Tests for equipment endpoints."""

    def test_create_equipo(self, client: TestClient, admin_token):
        """Test creating equipment."""
        response = client.post(
            "/api/v1/equipos/",
            json={
                "codigo": "EQ-001",
                "nombre": "Taladro Industrial",
                "tipo": "herramienta",
                "marca": "Bosch",
                "modelo": "GSB 18V"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 201
        data = response.json()
        assert data["codigo"] == "EQ-001"
        assert data["estado"] == "disponible"

    def test_list_equipos(self, client: TestClient, admin_token, db):
        """Test listing equipment."""
        for i in range(3):
            equipo = Equipo(
                codigo=f"EQ-{i:03d}",
                nombre=f"Equipo {i}",
                tipo=TipoEquipo.herramienta,
                estado=EstadoEquipo.disponible
            )
            db.add(equipo)
        db.commit()

        response = client.get(
            "/api/v1/equipos/",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_filter_equipos_disponibles(self, client: TestClient, admin_token, db):
        """Test filtering available equipment."""
        equipo_disponible = Equipo(
            codigo="EQ-DISP",
            nombre="Equipo Disponible",
            tipo=TipoEquipo.herramienta,
            estado=EstadoEquipo.disponible
        )
        equipo_asignado = Equipo(
            codigo="EQ-ASIG",
            nombre="Equipo Asignado",
            tipo=TipoEquipo.herramienta,
            estado=EstadoEquipo.asignado
        )
        db.add_all([equipo_disponible, equipo_asignado])
        db.commit()

        response = client.get(
            "/api/v1/equipos/?estado=disponible",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["codigo"] == "EQ-DISP"

    def test_asignar_equipo(self, client: TestClient, admin_token, db, cliente_user):
        """Test assigning equipment to a project."""
        equipo = Equipo(
            codigo="EQ-ASIGNAR",
            nombre="Equipo a Asignar",
            tipo=TipoEquipo.maquinaria,
            estado=EstadoEquipo.disponible
        )
        proyecto = Proyecto(
            nombre="Proyecto Asignación",
            cliente_id=cliente_user.id,
            estado=EstadoProyecto.en_ejecucion
        )
        db.add_all([equipo, proyecto])
        db.commit()
        db.refresh(equipo)
        db.refresh(proyecto)

        response = client.post(
            f"/api/v1/equipos/{equipo.id}/asignar",
            json={
                "proyecto_id": str(proyecto.id),
                "fecha_devolucion_est": (date.today() + timedelta(days=30)).isoformat()
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "asignado"

    def test_asignar_equipo_no_disponible(self, client: TestClient, admin_token, db, cliente_user):
        """Test that unavailable equipment cannot be assigned."""
        equipo = Equipo(
            codigo="EQ-NODISP",
            nombre="Equipo No Disponible",
            tipo=TipoEquipo.herramienta,
            estado=EstadoEquipo.mantenimiento
        )
        proyecto = Proyecto(
            nombre="Proyecto Intento",
            cliente_id=cliente_user.id,
            estado=EstadoProyecto.en_ejecucion
        )
        db.add_all([equipo, proyecto])
        db.commit()
        db.refresh(equipo)
        db.refresh(proyecto)

        response = client.post(
            f"/api/v1/equipos/{equipo.id}/asignar",
            json={"proyecto_id": str(proyecto.id)},
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 400

    def test_devolver_equipo(self, client: TestClient, admin_token, db, cliente_user):
        """Test returning equipment."""
        equipo = Equipo(
            codigo="EQ-DEV",
            nombre="Equipo a Devolver",
            tipo=TipoEquipo.herramienta,
            estado=EstadoEquipo.asignado
        )
        db.add(equipo)
        db.commit()
        db.refresh(equipo)

        response = client.post(
            f"/api/v1/equipos/{equipo.id}/devolver",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "disponible"

    def test_cambiar_estado_mantenimiento(self, client: TestClient, admin_token, db):
        """Test changing equipment status to maintenance."""
        equipo = Equipo(
            codigo="EQ-MANT",
            nombre="Equipo Mantenimiento",
            tipo=TipoEquipo.maquinaria,
            estado=EstadoEquipo.disponible
        )
        db.add(equipo)
        db.commit()
        db.refresh(equipo)

        response = client.put(
            f"/api/v1/equipos/{equipo.id}/estado",
            params={"nuevo_estado": "mantenimiento"},
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "mantenimiento"

    def test_delete_equipo_admin_only(self, client: TestClient, operario_token, db):
        """Test that only admin can delete equipment."""
        equipo = Equipo(
            codigo="EQ-PROT",
            nombre="Equipo Protegido",
            tipo=TipoEquipo.herramienta,
            estado=EstadoEquipo.disponible
        )
        db.add(equipo)
        db.commit()
        db.refresh(equipo)

        response = client.delete(
            f"/api/v1/equipos/{equipo.id}",
            headers=auth_headers(operario_token)
        )
        assert response.status_code == 403
