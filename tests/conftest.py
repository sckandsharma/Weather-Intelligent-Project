import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.jwt_handler import create_access_token
from app.auth.password import hash_password
from app.core.security import limiter
from app.database.models import User, UserRole
from app.database.session import engine, get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Disable rate limiter during automated testing
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def regular_user(db: Session) -> User:
    user = User(
        full_name="Regular Test User",
        email=f"user_{datetime.now(timezone.utc).timestamp()}@example.com",
        password_hash=hash_password("UserSecretPass123!"),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def admin_user(db: Session) -> User:
    admin = User(
        full_name="Admin Test User",
        email=f"admin_{datetime.now(timezone.utc).timestamp()}@example.com",
        password_hash=hash_password("AdminSecretPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    db.flush()
    return admin


@pytest.fixture
def evaluator_user(db: Session) -> User:
    evaluator = User(
        full_name="Evaluator Test User",
        email=f"eval_{datetime.now(timezone.utc).timestamp()}@example.com",
        password_hash=hash_password("EvalSecretPass123!"),
        role=UserRole.EVALUATOR,
        is_active=True,
    )
    db.add(evaluator)
    db.flush()
    return evaluator


@pytest.fixture
def user_headers(regular_user: User) -> dict[str, str]:
    token = create_access_token(user_id=regular_user.id, role=regular_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    token = create_access_token(user_id=admin_user.id, role=admin_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def evaluator_headers(evaluator_user: User) -> dict[str, str]:
    token = create_access_token(user_id=evaluator_user.id, role=evaluator_user.role.value)
    return {"Authorization": f"Bearer {token}"}
