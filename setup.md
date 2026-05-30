# Установка окружения

← [Назад к пайплайну](README.md)

---

## 1. PostgreSQL

### Установка (если нет)

```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Создание базы данных

```bash
# Войти в psql от пользователя postgres
sudo -u postgres psql

# Внутри psql:
CREATE DATABASE shoe_store_2 OWNER postgres;
\q
```

Или одной командой:
```bash
sudo -u postgres psql -c "CREATE DATABASE shoe_store_2 OWNER postgres;"
```

**Параметры подключения (как в settings.py преподавателя):**
- HOST: `localhost`
- PORT: `5432`
- NAME: `shoe_store_2`
- USER: `postgres`
- PASSWORD: `826456` ← на экзамене узнай у организаторов или задай свой

### Проверка

```bash
sudo -u postgres psql -d shoe_store_2 -c "\conninfo"
```

---

## 2. Python и uv

### Установка uv

```bash
pip install uv
# или через curl:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Создание проекта

```bash
# Создать папку проекта
mkdir myproject
cd myproject

# Инициализировать uv-проект (создаёт pyproject.toml)
uv init --no-readme

# Добавить зависимости
uv add "django>=6.0.4" "pillow>=12.2.0" "psycopg2-binary>=2.9.12"

# Активировать виртуальное окружение
source .venv/bin/activate
```

### pyproject.toml — полное содержимое

```toml
[project]
name = "demo-26-test"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "django>=6.0.4",
    "pillow>=12.2.0",
    "psycopg2-binary>=2.9.12",
]
```

> **Важно:** `psycopg2-binary` — это драйвер для подключения Django к PostgreSQL. Без него DATABASES не заработает.

### Проверка установки

```bash
python -m django --version   # должно быть 6.0.x
python -c "import PIL; print(PIL.__version__)"  # Pillow
python -c "import psycopg2; print('OK')"        # драйвер
```

---

## 3. Альтернатива — pip без uv

Если uv недоступен:

```bash
python -m venv .venv
source .venv/bin/activate
pip install "django>=6.0.4" "pillow>=12.2.0" "psycopg2-binary>=2.9.12"
```

---

## 4. DBeaver (опционально, для просмотра БД)

- Скачать: dbeaver.io
- Новое подключение → PostgreSQL
- Ввести: `localhost`, `5432`, `shoe_store_2`, `postgres`, `<пароль>`
- Проверить что видны таблицы после `migrate`

---

## Чеклист

- [ ] PostgreSQL запущен, БД `shoe_store_2` создана
- [ ] uv или pip установлен
- [ ] Виртуальное окружение активировано
- [ ] Django, Pillow, psycopg2-binary установлены
- [ ] `python -m django --version` выводит версию без ошибок
