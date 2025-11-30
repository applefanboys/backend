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
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- 관계 설정 (Relationships) ---
    
    # 1. 온보딩 정보
    onboarding = relationship("UserOnBoarding", back_populates="user", uselist=False)
    
    # 2. ✅ [복구됨] 비밀번호 재설정 토큰 (이게 없어서 에러가 났었습니다)
    reset_tokens = relationship("PasswordResetToken", back_populates="user")

    # 3. [추가됨] 로그인용 일반 토큰
    tokens = relationship("UserToken", back_populates="user")


class UserOnBoarding(Base):
    __tablename__ = "user_onboarding"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    q1_categories = Column(JSON, nullable=True) 
    q2_keywords   = Column(JSON, nullable=True) 
    q3_keywords   = Column(JSON, nullable=True) 

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="onboarding")


# 로그인용 토큰 테이블
class UserToken(Base):
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="tokens")