const API_URL = '/students';
const TOGGLE_BTN_ID = 'toggleFormBtn';
const FORM_CONTAINER_ID = 'studentFormContainer';
const CANCEL_BTN_ID = 'cancelFormBtn';

function init() {
    loadStudents();
    loadGroupsHints();
    setupEventListeners();
}

function setupEventListeners() {
    document.getElementById('refreshBtn').addEventListener('click', () => loadStudents());
    document.getElementById('searchInput').addEventListener('input', filterStudents);

    const toggleBtn = document.getElementById(TOGGLE_BTN_ID);
    if (toggleBtn) toggleBtn.addEventListener('click', toggleForm);

    const cancelBtn = document.getElementById(CANCEL_BTN_ID);
    if (cancelBtn) cancelBtn.addEventListener('click', hideForm);

    const studentForm = document.getElementById('studentForm');
    if (studentForm) studentForm.addEventListener('submit', addStudent);
}

function toggleForm() {
    const container = document.getElementById(FORM_CONTAINER_ID);
    const toggleBtn = document.getElementById(TOGGLE_BTN_ID);
    const isHidden = container.style.display === 'none' || container.style.display === '';
    container.style.display = isHidden ? 'block' : 'none';
    toggleBtn.textContent = isHidden ? 'Скрыть форму' : '+ Новая запись';
}

function hideForm() {
    const container = document.getElementById(FORM_CONTAINER_ID);
    const toggleBtn = document.getElementById(TOGGLE_BTN_ID);
    const studentForm = document.getElementById('studentForm');
    container.style.display = 'none';
    toggleBtn.textContent = '+ Новая запись';
    if (studentForm) studentForm.reset();
}

async function loadGroupsHints() {
    try {
        const response = await fetch('/groups');
        const groups = await response.json();
        updateGroupCounter(groups.length);

        const datalist = document.getElementById('groups-list');
        if (datalist) {
            datalist.innerHTML = '';
            groups.forEach(group => {
                const option = document.createElement('option');
                option.value = group.name;
                datalist.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Ошибка загрузки групп:', error);
    }
}

async function loadStudents() {
    try {
        const response = await fetch(API_URL);
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/login';
            return;
        }
        const students = await response.json();
        renderStudents(students);
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('studentsList').innerHTML = '<div class="empty-message">Не удалось загрузить список студентов</div>';
    }
}

let allStudents = [];

function renderStudents(students) {
    allStudents = students;
    updateStudentCounter(students.length);

    const container = document.getElementById('studentsList');
    if (students.length === 0) {
        container.innerHTML = '<div class="empty-message">Нет данных о студентах. Добавьте первую запись.</div>';
        return;
    }

    container.innerHTML = students.map(student => `
        <article class="student-card" data-id="${student.id}">
            <div class="student-main" onclick="goToStudentPage('${student.id}')">
                <div class="student-avatar">${escapeHtml(getInitials(student.full_name))}</div>
                <div class="student-summary">
                    <div class="student-name">${escapeHtml(student.full_name)}</div>
                    <div class="student-record">№ ${escapeHtml(student.record_book)}</div>
                    <div class="student-details">
                        <span>${escapeHtml(student.group)}</span>
                        <span>${escapeHtml(student.course)} курс</span>
                        <span>${escapeHtml(shortDirection(student.direction))}</span>
                    </div>
                </div>
                <span class="status-badge status-${student.status.replace(/ /g, '_')}">${student.status}</span>
            </div>
            ${window.currentUserRole === 'admin' ? `
                <div class="student-actions">
                    <button class="edit-btn" data-id="${student.id}">Изменить</button>
                    <button class="delete-btn" data-id="${student.id}">Удалить</button>
                </div>
            ` : ''}
        </article>
    `).join('');

    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            const id = btn.getAttribute('data-id');
            const student = allStudents.find(s => s.id === id);
            if (student) editStudent(student);
        };
    });
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.stopPropagation();
            const id = btn.getAttribute('data-id');
            deleteStudent(id);
        };
    });
}

function updateStudentCounter(count) {
    const counter = document.getElementById('totalStudents');
    if (counter) counter.textContent = count;
}

function updateGroupCounter(count) {
    const counter = document.getElementById('groupCount');
    if (counter) counter.textContent = count;
}

function getInitials(fullName) {
    return fullName
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map(part => part[0])
        .join('')
        .toUpperCase();
}

function shortDirection(direction) {
    if (!direction) return '';
    return direction.replace('Информатика и вычислительная техника', 'ИВТ')
        .replace('Прикладная математика и информатика', 'ПМИ')
        .replace('Информационные системы и технологии', 'ИСТ');
}

function goToStudentPage(id) {
    window.location.href = `/student/${id}`;
}

function filterStudents() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const filtered = allStudents.filter(student =>
        student.full_name.toLowerCase().includes(searchTerm) ||
        student.record_book.toLowerCase().includes(searchTerm) ||
        (student.group && student.group.toLowerCase().includes(searchTerm))
    );
    renderStudents(filtered);
}

async function addStudent(e) {
    e.preventDefault();
    const student = {
        full_name: document.getElementById('full_name').value,
        record_book: document.getElementById('record_book').value,
        group: document.getElementById('group').value,
        direction: document.getElementById('direction').value,
        course: document.getElementById('course').value,
        description: document.getElementById('description').value,
        status: document.getElementById('status').value
    };
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(student)
        });
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/login';
            return;
        }
        if (response.ok) {
            document.getElementById('studentForm').reset();
            await loadGroupsHints();
            await loadStudents();
            hideForm();
            alert('Студент успешно добавлен!');
        } else {
            const error = await response.json();
            alert('Ошибка: ' + JSON.stringify(error));
        }
    } catch (error) {
        alert('Ошибка соединения');
    }
}

function editStudent(student) {
    window.location.href = `/edit/${student.id}`;
}

async function deleteStudent(id) {
    if (!confirm('Удалить выбранного студента?')) return;
    try {
        const response = await fetch(`${API_URL}/${id}`, { method: 'DELETE' });
        if (response.status === 401 || response.status === 403) {
            window.location.href = '/login';
            return;
        }
        if (response.ok) {
            loadStudents();
            alert('Студент удален!');
        } else {
            alert('Ошибка при удалении');
        }
    } catch (error) {
        alert('Ошибка соединения');
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

init();
