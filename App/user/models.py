# App/user/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, ForeignKey, JSON
from sqlalchemy.orm import relationship

from App.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    onboarding = relationship("UserOnBoarding", back_populates="user", uselist=False)
    reset_tokens = relationship("PasswordResetToken", back_populates="user")

class UserOnBoarding(Base):
    __tablename__ = "user_onboarding"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    q1_categories = Column(JSON, nullable=True) # ["all_economy", "stock", ...]
    q2_keywords   = Column(JSON, nullable=True) # ["환율", "달러", ...]
    q3_keywords   = Column(JSON, nullable=True) # ["장기투자", "단타", ...]

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship("User", back_populates="onboarding")