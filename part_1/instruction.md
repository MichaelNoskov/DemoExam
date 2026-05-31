# Инструкция по разработке БД для системы учета обуви

## Содержание

1. [Общее описание задания](#1-общее-описание-задания)
2. [Анализ исходных данных](#2-анализ-исходных-данных)
3. [Проектирование БД](#3-проектирование-бд)
4. [Создание БД в PostgreSQL](#4-создание-бд-в-postgresql)
5. [Создание ER-диаграммы](#5-создание-er-диаграммы)
6. [Подготовка данных для импорта](#6-подготовка-данных-для-импорта)
7. [Импорт данных в БД](#7-импорт-данных-в-бд)
8. [Сохранение результатов](#8-сохранение-результатов)
9. [Проверка работоспособности](#9-проверка-работоспособности)

---

## 1. Общее описание задания

**Заказчик:** ООО «Обувь»

**Цель:** Разработать информационную систему для учета обуви со следующими возможностями:

- Окно входа с авторизацией (логин/пароль из БД) или вход гостем
- Разделение прав доступа:
  - **Гость:** просмотр товаров (без фильтрации, сортировки, поиска)
  - **Клиент:** просмотр товаров (без фильтрации, сортировки, поиска)
  - **Менеджер:** просмотр товаров (с фильтрацией, сортировкой, поиском), просмотр заказов
  - **Администратор:** полное управление товарами и заказами

**Требования к БД:**
- PostgreSQL
- 3 нормальная форма (3НФ)
- Согласованная схема именования
- Ссылочная целостность (foreign keys)

---

## 2. Анализ исходных данных

### 2.1 Файлы с исходными данными

Исходные файлы находятся в директории: `part_1/add_2/import/`

| Файл | Описание | Количество записей |
|------|----------|-------------------|
| `user_import.xlsx` | Пользователи системы | 10 |
| `Tovar.xlsx` | Каталог товаров | 30 |
| `Заказ_import.xlsx` | Заказы | 10 |
| `Пункты выдачи_import.xlsx` | Пункты выдачи/склады | 35 |

### 2.2 Структура файлов

#### user_import.xlsx
| Колонка | Тип | Описание |
|---------|-----|----------|
| Роль сотрудника | text | Роль: Администратор, Менеджер, Клиент |
| ФИО | text | Полное имя |
| Логин | text | Email пользователя |
| Пароль | text | Пароль |

#### Tovar.xlsx
| Колонка | Тип | Описание |
|---------|-----|----------|
| Артикул | text | Уникальный артикул товара |
| Наименование товара | text | Название |
| Единица измерения | text | Обычно "шт." |
| Цена | number | Цена в рублях |
| Поставщик | text | Название поставщика |
| Производитель | text | Бренд |
| Категория товара | text | Категория |
| Действующая скидка | number | Скидка в % |
| Кол-во на складе | number | Количество |
| Описание товара | text | Описание |
| Фото | text | Имя файла изображения |

#### Заказ_import.xlsx
| Колонка | Тип | Описание |
|---------|-----|----------|
| Номер заказа | number | Уникальный номер |
| Артикул заказа | text | Список артикулов через запятую |
| Дата заказа | date | Дата оформления |
| Дата доставки | date | Планируемая дата |
| Адрес пункта выдачи | text | ID склада |
| ФИО авторизированного клиента | text | Имя клиента |
| Код для получения | number | Код |
| Статус заказа | text | Статус |

#### Пункты выдачи_import.xlsx
| Колонка | Тип | Описание |
|---------|-----|----------|
| Адрес | text | Полный адрес (индекс, город, улица, дом) |

### 2.3 Допущения

На основе анализа структуры файлов принять следующие допущения:

1. **orders.Артикул заказа** содержит несколько артикулов через запятую (например "А112Т4, 2, F635R4, 2"), где после каждого артикула идет количество
2. **Пункты выдачи** играют роль складов
3. **users** содержат и администраторов, и менеджеров, и клиентов
4. **orders.Адрес пункта выдачи** - это ID склада (из первых цифр адреса)

---

## 3. Проектирование БД

### 3.1 Схема таблиц

#### Таблица: users (Пользователи)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    login VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'manager', 'client')),
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(100)
);
```

#### Таблица: warehouses (Склады/Пункты выдачи)
```sql
CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    address VARCHAR(400) NOT NULL,
    phone VARCHAR(20)
);
```

#### Таблица: products (Товары)
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    article VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(20) DEFAULT 'шт.',
    price DECIMAL(10,2) NOT NULL,
    supplier VARCHAR(200),
    manufacturer VARCHAR(200),
    category VARCHAR(100),
    discount DECIMAL(5,2) DEFAULT 0,
    quantity INTEGER DEFAULT 0,
    description TEXT,
    warehouse_id INTEGER REFERENCES warehouses(id)
);
```

#### Таблица: orders (Заказы)
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL,
    delivery_date DATE,
    status VARCHAR(50) DEFAULT 'Новый',
    user_id INTEGER REFERENCES users(id),
    pickup_point_id INTEGER REFERENCES warehouses(id),
    client_full_name VARCHAR(200),
    pickup_code INTEGER,
    total_amount DECIMAL(10,2) DEFAULT 0
);
```

#### Таблица: order_items (Позиции заказа)
```sql
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id),
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL
);
```

### 3.2 Схема именования

- **Схема БД:** `shoe_store`
- **Таблицы:** snake_case, множественное число (users, products, orders)
- **Колонки:** snake_case (user_id, order_date)
- **Первичные ключи:** id
- **Внешние ключи:** table_name_id (user_id, product_id)
- **Индексы:** idx_table_column (idx_users_login)

### 3.3 Нормализация

Все таблицы соответствуют 3НФ:
- Каждая таблица имеет первичный ключ
- Нет транзитивных зависимостей
- Атомарные значения (нет списков через запятую)

---

## 4. Создание БД в PostgreSQL

### 4.1 Подключение к PostgreSQL

Через DBeaver:
1. Открыть DBeaver
2. Создать новое подключение к PostgreSQL
3. Ввести параметры подключения (хост, порт, БД, пользователь, пароль)

### 4.2 Создание базы данных

```sql
CREATE DATABASE shoe_store
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LOCALE_PROVIDER = 'icu'
    ICU_LOCALE = 'ru-RU'
    TEMPLATE = template0;
```

### 4.3 Создание таблиц

Выполнить SQL-скрипты из раздела 3.1 в следующем порядке:
1. users
2. warehouses
3. products
4. orders
5. order_items

### 4.4 Добавление ограничений

```sql
-- Индексы для ускорения поиска
CREATE INDEX idx_products_article ON products(article);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_manufacturer ON products(manufacturer);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
```

---

## 5. Создание ER-диаграммы

### 5.1 Через DBeaver

1. Подключиться к БД в DBeaver
2. Выбрать: База данных → Reverse Engineering
3. Выбрать таблицы для диаграммы
4. Настроить отображение (таблицы, связи, атрибуты, ключи)
5. Экспортировать в PDF

### 5.2 Через другой инструмент

Можно использовать:
- PostgreSQL ERD инструменты (SchemaSpy, pgModeler)
- Универсальные UML-редакторы (StarUML, PlantUML, draw.io)

### 5.3 Требования к ER-диаграмме

Диаграмма должна содержать:
- Все таблицы с названиями
- Все атрибуты каждой таблицы
- Типы данных атрибутов (можно опустить)
- Первичные ключи (PK)
- Внешние ключи (FK)
- Связи между таблицами со стрелками и кардинальностью (1:N, N:M)

### 5.4 Экспорт в PDF

- Формат: PDF
- Ориентация: альбомная (Landscape)
- Размер: A4 или больше

---

## 6. Подготовка данных для импорта

### 6.1 Подготовка users

Из `user_import.xlsx`:
- id: автоинкремент
- login: из колонки "Логин"
- password: из колонки "Пароль"
- role: преобразовать "Администратор" → "admin", "Менеджер" → "manager", "Клиент" → "client"
- full_name: из колонки "ФИО"
- email: из колонки "Логин" (дублирование)

### 6.2 Подготовка warehouses

Из `Пункты выдачи_import.xlsx`:
- id: автоинкремент
- name: "Пункт выдачи №" + id
- address: из единственной колонки
- phone: NULL

### 6.3 Подготовка products

Из `Tovar.xlsx`:
- id: автоинкремент
- article: из колонки "Артикул"
- name: из "Наименование товара"
- unit: из "Единица измерения"
- price: из "Цена"
- supplier: из "Поставщик"
- manufacturer: из "Производитель"
- category: из "Категория товара"
- discount: из "Действующая скидка"
- quantity: из "Кол-во на складе"
- description: из "Описание товара"
- warehouse_id: 1 (по умолчанию) или распределить по складам

### 6.4 Подготовка orders

Из `Заказ_import.xlsx`:
Требуется парсинг "Артикул заказа" (формат: "А112Т4, 2, F635R4, 2" = артикул, кол-во, артикул, кол-во)

- id: из "Номер заказа"
- order_date: из "Дата заказа"
- delivery_date: из "Дата доставки"
- status: из "Статус заказа"
- pickup_point_id: из "Адрес пункта выдачи" (первые цифры как ID)
- client_full_name: из "ФИО авторизированного клиента"
- pickup_code: из "Код для получения"
- total_amount: вычислить из суммы (цена × количество)

### 6.5 Подготовка order_items

Создается на основе данных заказов:
- id: автоинкремент
- order_id: id из orders
- product_id: найти по article
- quantity: из распарсенного списка
- price: из products.price

### 6.6 Формат для импорта

Сохранить как CSV с разделителем точкой с запятой (;):
```csv
id;login;password;role;full_name;email
1;94d5ous@gmail.com;uzWC67;admin;Никифорова Весения Николаевна;94d5ous@gmail.com
```

---

## 7. Импорт данных в БД

### 7.1 Через DBeaver

1. Кликнуть правой кнопкой на таблице
2. Выбрать "Импорт данных"
3. Выбрать файл CSV
4. Настроить разделитель
5. Сопоставить колонки
6. Запустить импорт

### 7.2 Через psql

```bash
psql -h хост -U пользователь -d shoe_store -c "\copy users FROM '/path/users.csv' WITH (FORMAT csv, DELIMITER ';', HEADER true)"
```

### 7.3 Порядок импорта

1. users (10 записей)
2. warehouses (35 записей)
3. products (30 записей)
4. orders (10 записей)
5. order_items (после парсинга)

---

## 8. Сохранение результатов

### 8.1 SQL-скрипт

Сохранить полный скрипт создания БД: `shoe_store.sql`

```sql
-- shoe_store.sql
-- База данных: shoe_store
-- Дата создания: 2026-04-20

-- Создание таблиц
CREATE TABLE users (...);
CREATE TABLE warehouses (...);
CREATE TABLE products (...);
CREATE TABLE orders (...);
CREATE TABLE order_items (...);

-- Индексы
CREATE INDEX idx_products_article ON products(article);
...
```

### 8.2 Экспорт структуры через DBeaver

1. Выбрать: База данных → Экспорт SQL
2. Выбрать объекты (таблицы, индексы, ограничения)
3. Настроить параметры
4. Сохранить в файл

### 8.3 Дополнительные результаты

- ER-диаграмма: `ER-diagram.pdf`
- Дамп данных: `shoe_store_dump.sql` (опционально)

---

## 9. Проверка работоспособности

### 9.1 Проверка структуры

```sql
-- Список таблиц
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Проверка связей
SELECT
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

### 9.2 Проверка данных

```sql
-- Количество записей в таблицах
SELECT 'users' AS table_name, COUNT(*) AS count FROM users
UNION ALL
SELECT 'warehouses', COUNT(*) FROM warehouses
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items;
```

### 9.3 Тестовые запросы

```sql
-- Список товаров
SELECT article, name, price, quantity FROM products;

-- Список заказов с клиентами
SELECT o.id, o.order_date, o.status, u.full_name 
FROM orders o 
LEFT JOIN users u ON o.user_id = u.id;
```

---

## Контрольный список

- [ ] Создана база данных shoe_store
- [ ] Созданы все 5 таблиц
- [ ] Добавлены первичные ключи
- [ ] Добавлены внешние ключи
- [ ] Добавлены ограничения NOT NULL
- [ ] Созданы индексы
- [ ] Импортированы данные users (10)
- [ ] Импортированы данные warehouses (35)
- [ ] Импортированы данные products (30)
- [ ] Импортированы данные orders (10)
- [ ] Созданы order_items
- [ ] Создана ER-диаграмма в PDF
- [ ] Сохранен SQL-скрипт

---

## 10. Анализ и рекомендации по улучшению (Дополнение)

На основе сопоставления данной инструкции с требованиями задания (`task.md`) и анализа исходных данных, выделены следующие ключевые моменты и рекомендации по логике проектирования.

### 10.1 Соответствие требованиям
Инструкция полностью покрывает функциональные требования:
- **Роли и доступ:** Отражены все уровни доступа (Гость, Клиент, Менеджер, Администратор).
- **3-я нормальная форма (3НФ):** Предложенная структура решает проблему нарушения 1НФ в исходных данных (списки артикулов через запятую в заказах) путем введения таблицы `order_items`.

### 10.2 Архитектурный анализ 3НФ
Для "строгого" соблюдения 3НФ и получения высшего балла рекомендуется обратить внимание на следующие аспекты:
- **Справочники (Lookup Tables):** В таблице `products` колонки `supplier`, `manufacturer` и `category` сейчас хранятся как текст. Для исключения избыточности их следует вынести в отдельные таблицы (`suppliers`, `brands`, `categories`).
- **Вычисляемые поля:** Поле `orders.total_amount` является избыточным с точки зрения теории БД, так как сумма вычисляется через `order_items`. Оно допустимо для денормализации ради производительности, но в учебных целях может быть отмечено как отклонение от "чистой" 3НФ.
- **Связь Товар-Склад:** Текущая схема предполагает связь 1:N (товар принадлежит одному складу). Если предметная область подразумевает наличие одного артикула на разных складах, потребуется таблица остатков (`inventory/stocks`).

### 10.3 Обоснование логики импорта
- **Парсинг артикулов:** Инструкция фиксирует необходимость разделения строки `Артикул, Кол-во` на отдельные записи, что критично для обеспечения целостности.
- **Нормализация данных:** Предусмотрено преобразование русских наименований ролей ("Администратор") в системные константы ("admin"), что упрощает программную реализацию.
- **ID пунктов выдачи:** Обосновано использование первых цифр адреса как временных идентификаторов для связки данных при импорте.

### 10.4 Рекомендации по реализации
- **Foreign Keys:** Рекомендуется использовать `ON DELETE RESTRICT` для связки товаров с заказами, чтобы предотвратить удаление номенклатуры, участвующей в транзакциях.
- **Индексация:** Помимо предложенных индексов, стоит рассмотреть составной индекс на `orders(user_id, order_date)` для ускорения поиска истории заказов конкретного клиента.

### 10.5 Улучшенная схема со справочниками (SQL)

Для реализации "строгой" 3НФ (пункт 10.2) следует заменить текстовые поля в `products` на внешние ключи.

```sql
-- 1. Создание справочников
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE manufacturers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL
);

CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL
);

-- 2. Обновленная таблица товаров
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    article VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    unit VARCHAR(20) DEFAULT 'шт.',
    price DECIMAL(10,2) NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    manufacturer_id INTEGER REFERENCES manufacturers(id),
    supplier_id INTEGER REFERENCES suppliers(id),
    discount DECIMAL(5,2) DEFAULT 0,
    quantity INTEGER DEFAULT 0,
    description TEXT,
    warehouse_id INTEGER REFERENCES warehouses(id)
);
```

---

## Инструменты

- **PostgreSQL** - СУБД
- **DBeaver** - клиент для управления БД
- **Python + pandas + openpyxl** - обработка файлов Excel
- **CSV** - формат для импорта