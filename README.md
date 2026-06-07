# Информационная система учёта студентов

Учебное клиент-серверное приложение на FastAPI для просмотра и администрирования карточек студентов.

## Запуск в VS Code

1. Открыть папку проекта в VS Code.
2. Выбрать интерпретатор `.venv\Scripts\python.exe`, если VS Code не выбрал его сам.
3. Запустить задачу: `Terminal -> Run Task -> Run Student FastAPI Server`.

Если виртуальное окружение ещё не создано:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Запуск из терминала

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

После запуска открыть:

```text
http://127.0.0.1:8000
```

## Тестовые аккаунты

```text
admin@example.com / admin123
user@example.com / user123
```

По умолчанию используется SQLite-файл `students.db`. Для PostgreSQL можно задать переменную окружения `DATABASE_URL`, например:

```text
postgresql://postgres:admin@localhost:5432/students_db
```
