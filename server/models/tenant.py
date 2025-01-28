# server/models/tenant.py
from sqlalchemy import Column, String, Integer
from server.models.base import Base

class Tenant(Base):
    __tablename__ = "tenants"

    tenant_id = Column(String, primary_key=True, index=True)
    db_type = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    database_name = Column(String, nullable=False)
