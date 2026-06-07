from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from auth import get_current_role, get_current_user, login_user, logout_user
from database import Group, Student, get_db, init_db
from logger import log_info, log_warning

init_db()
log_info("Приложение запущено, база данных инициализирована")

app = FastAPI(title="Студенты")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    log_info(f"Страница входа запрошена с IP: {request.client.host}")
    return templates.TemplateResponse(request, "login.html", {})


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    log_info(f"Попытка входа с email: {email}, IP: {request.client.host}")
    token, role = login_user(email, password, db)
    if not token:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Неверный email или пароль"},
        )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="student_token", value=token, httponly=True)
    log_info(f"Успешный вход: {email} (роль: {role})")
    return response


@app.get("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("student_token")
    if token:
        logout_user(token, db)
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("student_token")
    log_info(f"Пользователь вышел, IP: {request.client.host}")
    return response


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)

    if not user:
        log_info(
            "Неавторизованный гость перенаправлен на /login, "
            f"IP: {request.client.host}"
        )
        return RedirectResponse(url="/login", status_code=303)

    role = user.role
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "user": user,
            "role": role,
        },
    )


@app.get("/students")
async def get_students(db: Session = Depends(get_db)):
    students = db.query(Student).all()
    log_info(f"Запрошен список студентов, найдено: {len(students)}")
    result = []
    for student in students:
        result.append(
            {
                "id": student.id,
                "full_name": student.full_name,
                "record_book": student.record_book,
                "group": student.group.name if student.group else None,
                "direction": student.direction,
                "course": student.course,
                "status": student.status,
                "description": student.description,
            }
        )
    return result


@app.get("/students/{student_id}")
async def get_student(student_id: str, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        log_warning(f"Студент с ID {student_id} не найден")
        raise HTTPException(status_code=404, detail="Студент не найден")

    log_info(f"Запрошен студент: {student.full_name} (ID: {student_id})")
    return {
        "id": student.id,
        "full_name": student.full_name,
        "record_book": student.record_book,
        "group": student.group.name if student.group else None,
        "direction": student.direction,
        "course": student.course,
        "status": student.status,
        "description": student.description,
    }


@app.post("/students", status_code=201)
async def create_student(request: Request, db: Session = Depends(get_db)):
    role = get_current_role(request, db)
    if role != "admin":
        log_warning(
            "Попытка добавления студента с недостаточными правами. "
            f"Роль: {role}, IP: {request.client.host}"
        )
        raise HTTPException(status_code=403, detail="Недостаточно прав. Требуется: admin")

    data = await request.json()
    group_name = data.get("group")

    log_info(
        f"Админ добавляет студента: {data.get('full_name')} "
        f"({data.get('record_book')}), группа: {group_name}"
    )

    group = db.query(Group).filter(Group.name == group_name).first()
    if not group:
        group = Group(name=group_name, curator=data.get("curator"))
        db.add(group)
        db.commit()
        db.refresh(group)
        log_info(f"Создана новая группа: {group_name}")

    new_student = Student(
        full_name=data.get("full_name"),
        record_book=data.get("record_book"),
        group_id=group.id,
        direction=data.get("direction"),
        course=data.get("course"),
        status=data.get("status", "Обучается"),
        description=data.get("description"),
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    log_info(f"Студент успешно добавлен: {new_student.full_name} (ID: {new_student.id})")
    return new_student


@app.put("/students/{student_id}")
async def update_student(student_id: str, request: Request, db: Session = Depends(get_db)):
    role = get_current_role(request, db)
    if role != "admin":
        log_warning(
            "Попытка обновления студента с недостаточными правами. "
            f"Роль: {role}"
        )
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        log_warning(f"Студент с ID {student_id} не найден для обновления")
        raise HTTPException(status_code=404, detail="Студент не найден")

    data = await request.json()
    old_name = student.full_name

    if "full_name" in data:
        student.full_name = data["full_name"]
    if "record_book" in data:
        student.record_book = data["record_book"]
    if "group" in data:
        group_name = data["group"]
        group = db.query(Group).filter(Group.name == group_name).first()
        if not group:
            group = Group(name=group_name)
            db.add(group)
            db.commit()
            db.refresh(group)
            log_info(f"Создана новая группа при обновлении: {group_name}")
        student.group_id = group.id
    if "direction" in data:
        student.direction = data["direction"]
    if "course" in data:
        student.course = data["course"]
    if "status" in data:
        student.status = data["status"]
    if "description" in data:
        student.description = data["description"]

    db.commit()
    db.refresh(student)

    log_info(f"Студент обновлен: {old_name} -> {student.full_name} (ID: {student_id})")
    return student


@app.delete("/students/{student_id}")
async def delete_student(student_id: str, request: Request, db: Session = Depends(get_db)):
    role = get_current_role(request, db)
    if role != "admin":
        log_warning(
            "Попытка удаления студента с недостаточными правами. "
            f"Роль: {role}"
        )
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        log_warning(f"Студент с ID {student_id} не найден для удаления")
        raise HTTPException(status_code=404, detail="Студент не найден")

    student_name = student.full_name
    db.delete(student)
    db.commit()

    log_info(f"Студент удален: {student_name} (ID: {student_id})")
    return {"ok": True}


@app.get("/groups")
async def get_groups(db: Session = Depends(get_db)):
    groups = db.query(Group).all()
    log_info(f"Запрошен список групп, найдено: {len(groups)}")
    return [
        {
            "id": group.id,
            "name": group.name,
            "curator": group.curator,
        }
        for group in groups
    ]


@app.get("/student/{student_id}", response_class=HTMLResponse)
async def student_detail_page(request: Request, student_id: str, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    group = db.query(Group).filter(Group.id == student.group_id).first()

    student_data = {
        "id": student.id,
        "full_name": student.full_name,
        "record_book": student.record_book,
        "group": group.name if group else None,
        "direction": student.direction,
        "course": student.course,
        "status": student.status,
        "description": student.description,
    }

    return templates.TemplateResponse(
        request,
        "student_detail.html",
        {
            "user": user,
            "role": user.role,
            "student": student_data,
        },
    )


@app.get("/edit/{student_id}", response_class=HTMLResponse)
async def edit_student_page(request: Request, student_id: str, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if user.role != "admin":
        return RedirectResponse(url="/", status_code=303)

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")

    group = db.query(Group).filter(Group.id == student.group_id).first()

    student_data = {
        "id": student.id,
        "full_name": student.full_name,
        "record_book": student.record_book,
        "group": group.name if group else None,
        "direction": student.direction,
        "course": student.course,
        "status": student.status,
        "description": student.description,
    }

    return templates.TemplateResponse(
        request,
        "edit_student.html",
        {
            "user": user,
            "role": user.role,
            "student": student_data,
        },
    )
