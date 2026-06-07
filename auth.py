import uuid

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from database import SessionToken, User, get_db, verify_password
from logger import log_info, log_warning


def login_user(email: str, password: str, db: Session):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        log_warning(f"Попытка входа с несуществующим email: {email}")
        return None, "Пользователь не найден"

    if not verify_password(password, user.password_hash):
        log_warning(f"Неверный пароль для пользователя: {email}")
        return None, "Неверный пароль"

    token = str(uuid.uuid4())
    session = SessionToken(user_id=user.id, token=token)
    db.add(session)
    db.commit()

    log_info(f"Пользователь вошёл в систему: {user.email} (роль: {user.role})")
    return token, user.role


def get_user_by_token(token: str, db: Session):
    session = db.query(SessionToken).filter(SessionToken.token == token).first()
    if not session:
        return None
    return session.user


def logout_user(token: str, db: Session):
    session = db.query(SessionToken).filter(SessionToken.token == token).first()
    if session:
        user_email = session.user.email if session.user else "unknown"
        db.delete(session)
        db.commit()
        log_info(f"Пользователь вышел из системы: {user_email}")
        return True
    return False


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("student_token")
    if not token:
        return None
    return get_user_by_token(token, db)


def get_current_role(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return "guest"
    return user.role
