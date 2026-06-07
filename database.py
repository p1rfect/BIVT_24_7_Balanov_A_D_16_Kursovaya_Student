import hashlib
import os
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./students.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.now)


class Group(Base):
    __tablename__ = "groups"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    curator = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    students = relationship("Student", back_populates="group")


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, default=generate_uuid)
    full_name = Column(String, nullable=False)
    record_book = Column(String, unique=True, nullable=False)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False)
    direction = Column(String, nullable=False)
    course = Column(String, nullable=False)
    status = Column(String, default="Обучается")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    group = relationship("Group", back_populates="students")


class SessionToken(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    token = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User")


def init_db():
    Base.metadata.create_all(engine)
    db = SessionLocal()

    if db.query(Group).count() == 0:
        groups = [
            Group(name="БИВТ-24-7", curator="Микитенко И.И."),
            Group(name="БИВТ-24-8", curator="Абросимов Н.А."),
            Group(name="БПМ-23-1", curator="Шелудяков П.А."),
            Group(name="БАСО-22-2", curator="Иванова Е.С."),
            Group(name="БЭК-25-1", curator="Петрова А.В."),
        ]
        db.add_all(groups)
        db.commit()

    if db.query(Student).count() == 0:
        bivt_247 = db.query(Group).filter(Group.name == "БИВТ-24-7").first()
        bivt_248 = db.query(Group).filter(Group.name == "БИВТ-24-8").first()
        bpm_231 = db.query(Group).filter(Group.name == "БПМ-23-1").first()
        baso_222 = db.query(Group).filter(Group.name == "БАСО-22-2").first()

        students = [
            Student(
                full_name="Баланов Артём Дмитриевич",
                record_book="24-7-016",
                group_id=bivt_247.id,
                direction="09.03.01 Информатика и вычислительная техника",
                course="2",
                status="Обучается",
                description="Студент выполняет учебные проекты по клиент-серверным приложениям.",
            ),
            Student(
                full_name="Иванов Иван Петрович",
                record_book="24-8-021",
                group_id=bivt_248.id,
                direction="09.03.01 Информатика и вычислительная техника",
                course="2",
                status="Обучается",
                description="Участвует в лабораторных работах по базам данных и веб-разработке.",
            ),
            Student(
                full_name="Смирнова Анна Сергеевна",
                record_book="23-1-008",
                group_id=bpm_231.id,
                direction="01.03.02 Прикладная математика и информатика",
                course="3",
                status="Академический отпуск",
                description="Временно не проходит обучение по уважительной причине.",
            ),
            Student(
                full_name="Кузнецов Артём Игоревич",
                record_book="22-2-014",
                group_id=baso_222.id,
                direction="09.03.02 Информационные системы и технологии",
                course="4",
                status="Выпускник",
                description="Завершил обучение и проходит итоговую аттестацию.",
            ),
        ]
        db.add_all(students)
        db.commit()

    if db.query(User).count() == 0:
        users = [
            User(
                name="Администратор",
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                role="admin",
            ),
            User(
                name="Иван Петров",
                email="user@example.com",
                password_hash=hash_password("user123"),
                role="user",
            ),
        ]
        db.add_all(users)
        db.commit()

    db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
