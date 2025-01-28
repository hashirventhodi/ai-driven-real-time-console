# server/multi_tenancy.py
from typing import Dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from server.database import PlatformSessionLocal
from server.models.tenant import Tenant

SESSION_FACTORIES: Dict[str, sessionmaker] = {}

def fetch_tenant_config(tenant_id: str) -> Tenant:
    """
    Retrieve tenant info from the platform DB.
    """
    with PlatformSessionLocal() as session:
        tenant = session.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant '{tenant_id}' not found.")
        return tenant

def build_db_url(tenant: Tenant) -> str:
    """
    Construct the DB URL for the tenant's data store.
    """
    if tenant.db_type.lower() == "postgresql":
        return f"postgresql://{tenant.username}:{tenant.password}@{tenant.host}:{tenant.port}/{tenant.database_name}"
    elif tenant.db_type.lower() == "mysql":
        return f"mysql+pymysql://{tenant.username}:{tenant.password}@{tenant.host}:{tenant.port}/{tenant.database_name}"
    elif tenant.db_type.lower() == "mssql":
        return f"mssql+pyodbc://{tenant.username}:{tenant.password}@{tenant.host}:{tenant.port}/{tenant.database_name}?driver=ODBC+Driver+17+for+SQL+Server"
    else:
        raise ValueError(f"Unsupported db_type: {tenant.db_type}")

def get_session_factory(tenant_id: str):
    """
    Return a sessionmaker for the tenant's DB, creating an engine if needed.
    """
    if tenant_id in SESSION_FACTORIES:
        return SESSION_FACTORIES[tenant_id]

    tenant = fetch_tenant_config(tenant_id)
    db_url = build_db_url(tenant)

    engine = create_engine(
        db_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True
    )
    factory = sessionmaker(bind=engine)
    SESSION_FACTORIES[tenant_id] = factory
    return factory

def get_tenant_session(tenant_id: str):
    """
    Provide a new Session for the tenant's database.
    """
    factory = get_session_factory(tenant_id)
    return factory()
