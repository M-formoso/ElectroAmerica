import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base_class import Base
from app.core.deps import get_db
from app.core.security import get_password_hash
from app.models.usuario import Usuario, RolUsuario

# Test database URL (SQLite in memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db() -> Generator:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """Create test client with database override."""
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db) -> Usuario:
    """Create admin user for testing."""
    user = Usuario(
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        nombre="Admin",
        apellido="Test",
        rol=RolUsuario.administrador,
        activo=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def supervisor_user(db) -> Usuario:
    """Create supervisor user for testing."""
    user = Usuario(
        email="supervisor@test.com",
        hashed_password=get_password_hash("super123"),
        nombre="Supervisor",
        apellido="Test",
        rol=RolUsuario.supervisor,
        activo=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def operario_user(db) -> Usuario:
    """Create operario user for testing."""
    user = Usuario(
        email="operario@test.com",
        hashed_password=get_password_hash("oper123"),
        nombre="Operario",
        apellido="Test",
        rol=RolUsuario.operario,
        activo=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def cliente_user(db) -> Usuario:
    """Create cliente user for testing."""
    user = Usuario(
        email="cliente@test.com",
        hashed_password=get_password_hash("cliente123"),
        nombre="Cliente",
        apellido="Test",
        rol=RolUsuario.cliente,
        activo=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(client, admin_user) -> str:
    """Get admin JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@test.com", "password": "admin123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def supervisor_token(client, supervisor_user) -> str:
    """Get supervisor JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "supervisor@test.com", "password": "super123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def operario_token(client, operario_user) -> str:
    """Get operario JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "operario@test.com", "password": "oper123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def cliente_token(client, cliente_user) -> str:
    """Get cliente JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "cliente@test.com", "password": "cliente123"}
    )
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    """Generate authorization headers."""
    return {"Authorization": f"Bearer {token}"}
