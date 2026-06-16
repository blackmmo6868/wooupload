from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from app.core.config import DATABASE_URL

class Base(DeclarativeBase):
    pass

class Store(Base):
    __tablename__ = "stores"
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(255), nullable=False)
    wc_url          = Column(String(255), nullable=False)
    wp_username     = Column(String(255), default='')
    wp_app_password = Column(String(255), default='')
    store_name      = Column(String(255), default='')
    shortcode       = Column(String(255), default='[thien_display_single_image]')
    created_at      = Column(DateTime, default=datetime.utcnow)
    users           = relationship("User", back_populates="store")
    user_stores     = relationship("UserStore", back_populates="store", cascade="all, delete-orphan")

class UserStore(Base):
    __tablename__ = "user_stores"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    store_id        = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False)
    wp_username     = Column(String(255), default='')
    wp_app_password = Column(String(255), default='')
    created_at      = Column(DateTime, default=datetime.utcnow)
    user            = relationship("User", back_populates="user_stores")
    store           = relationship("Store", back_populates="user_stores")

class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(64), unique=True, nullable=False, index=True)
    email           = Column(String(255), unique=True, nullable=False)
    hashed_pw       = Column(String(255), nullable=False)
    is_admin        = Column(Boolean, default=False)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    wp_username     = Column(String(255), default='')
    wp_app_password = Column(String(255), default='')
    note            = Column(Text, default='')
    store_id        = Column(Integer, ForeignKey("stores.id"), nullable=True)
    store           = relationship("Store", back_populates="users")
    jobs            = relationship("Job", back_populates="user")
    user_stores     = relationship("UserStore", back_populates="user", cascade="all, delete-orphan")

class Settings(Base):
    __tablename__ = "settings"
    id    = Column(Integer, primary_key=True)
    key   = Column(String(128), unique=True, nullable=False)
    value = Column(Text, default="")

class Job(Base):
    __tablename__ = "jobs"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_type   = Column(String(32), nullable=False)
    status     = Column(String(32), default="pending")
    celery_id  = Column(String(255), nullable=True)
    params     = Column(JSON, nullable=True)
    result     = Column(JSON, nullable=True)
    log        = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user       = relationship("User", back_populates="jobs")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from passlib.context import CryptContext
    import os
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter_by(is_admin=True).first():
            pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
            admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123456")
            admin = User(
                username="admin", email="admin@breaktees.com",
                hashed_pw=pwd_ctx.hash(admin_password),
                is_admin=True, is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"✅ Admin tạo xong. Password: {admin_password}")
    finally:
        db.close()
