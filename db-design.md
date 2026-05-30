# Проектирование базы данных

← [Назад к пайплайну](README.md)

---

## 1. Нормальные формы (теория)

### 1НФ — Первая нормальная форма
**Правило:** Каждая ячейка содержит атомарное (неделимое) значение.

**Нарушение:** В таблице `orders` поле `items = "А112Т4, 2, F635R4, 2"` — список в одном поле.

**Исправление:** Выносим позиции заказа в отдельную таблицу `order_items`.

### 2НФ — Вторая нормальная форма
**Правило:** Все неключевые поля зависят от **всего** первичного ключа (актуально для составных PK).

В нашем проекте все таблицы имеют суррогатный PK (`id`), поэтому 2НФ выполняется автоматически.

### 3НФ — Третья нормальная форма
**Правило:** Нет **транзитивных зависимостей** — неключевое поле не должно зависеть от другого неключевого поля.

**Пример нарушения (исходные данные):**
```
products: article → supplier_name → supplier_address
```
`supplier_address` зависит от `supplier_name`, а не от `article`. Это транзитивная зависимость.

**Исправление:** Выносим поставщика в отдельную таблицу `Supplier`. Именно так сделано в проекте:
- `Product.supplier` → ForeignKey на `Supplier`
- `Supplier.name` — уникальное имя поставщика

---

## 2. Схема таблиц проекта

### Таблица: `core_role` (Role)

| Поле | Тип | Ограничения |
|------|-----|-------------|
| id | BIGINT | PK, AUTO |
| name | VARCHAR(50) | UNIQUE, NOT NULL |

Значения: `admin`, `manager`, `client`

---

### Таблица: `core_user` (User — расширяет Django AbstractUser)

| Поле | Тип | Ограничения |
|------|-----|-------------|
| id | BIGINT | PK, AUTO |
| username | VARCHAR(150) | UNIQUE, NOT NULL |
| password | VARCHAR(128) | NOT NULL (хеш) |
| email | VARCHAR(254) | — |
| is_staff | BOOLEAN | DEFAULT False |
| is_active | BOOLEAN | DEFAULT True |
| full_name | VARCHAR(255) | NOT NULL |
| role_id | BIGINT | FK → core_role(id), NULL |

---

### Таблица: `core_supplier` (Supplier)

| Поле | Тип | Ограничения |
|------|-----|-------------|
| id | BIGINT | PK, AUTO |
| name | VARCHAR(200) | UNIQUE, NOT NULL |

---

### Таблица: `core_pickuppoint` (PickupPoint)

| Поле | Тип | Ограничения |
|------|-----|-------------|
| id | BIGINT | PK, AUTO |
| address | TEXT | NOT NULL |

35 записей — пункты выдачи в г. Лесной.

---

### Таблица: `core_product` (Product)

| Поле | Тип | Ограничения |
|------|-----|-------------|
| id | BIGINT | PK, AUTO |
| article | VARCHAR(50) | UNIQUE, NOT NULL |
| name | VARCHAR(255) | NOT NULL |
| unit | VARCHAR(20) | DEFAULT 'шт.' |
| price | DECIMAL(10,2) | NOT NULL |
| manufacturer | VARCHAR(200) | NOT NULL |
| supplier_id | BIGINT | FK → core_supplier(id), CASCADE |
| category | VARCHAR(200) | NOT NULL |
| discount | DECIMAL(5,2) | DEFAULT 0 |
| quantity | INTEGER | DEFAULT 0 |
| description | TEXT | NOT NULL |
| photo | VARCHAR(100) | NULL (путь к файлу) |

---

### Таблица: `core_order` (Order)

| Поле | Тип | Ограничения |
|------|-----|-------------|
| id | BIGINT | PK, AUTO |
| order_date | TIMESTAMP | AUTO (created_at) |
| delivery_date | TIMESTAMP | NOT NULL |
| pickup_point_id | BIGINT | FK → core_pickuppoint(id), CASCADE |
| client_name | VARCHAR(255) | NULL |
| pickup_code | INTEGER | NOT NULL |
| status | VARCHAR(50) | DEFAULT 'Новый' |
| user_id | BIGINT | FK → core_user(id), SET NULL |

---

### Таблица: `core_orderitem` (OrderItem)

| Поле | Тип | Ограничения |
|------|-----|-------------|
| id | BIGINT | PK, AUTO |
| order_id | BIGINT | FK → core_order(id), CASCADE |
| product_id | BIGINT | FK → core_product(id), CASCADE |
| count | INTEGER | NOT NULL |

---

## 3. Схема связей (текстовая)

```
Role ──< User              (1 роль → много пользователей)
User ──< Order             (1 пользователь → много заказов)
Supplier ──< Product       (1 поставщик → много товаров)
PickupPoint ──< Order      (1 пункт выдачи → много заказов)
Order ──< OrderItem        (1 заказ → много позиций)
Product ──< OrderItem      (1 товар → в разных позициях)
```

---

## 4. Правила именования

| Элемент | Стиль | Пример |
|---------|-------|--------|
| Модели Python | PascalCase | `OrderItem`, `PickupPoint` |
| Таблицы БД | snake_case (Django) | `core_order_item` |
| Поля моделей | snake_case | `order_date`, `pickup_point` |
| FK-поля | `model_name_id` | `supplier_id`, `user_id` |
| Первичные ключи | `id` | всегда `id` |

---

## 5. Получение SQL-дампа для сдачи

Django создаёт таблицы через миграции. Для сдачи нужен SQL-скрипт.

### Посмотреть SQL одной миграции:
```bash
python manage.py sqlmigrate core 0001
```

### Получить дамп всей структуры (после migrate):
```bash
# Только структура (без данных):
pg_dump -U postgres -s shoe_store_2 > schema.sql

# Структура + данные:
pg_dump -U postgres shoe_store_2 > full_dump.sql
```

### Альтернатива — через DBeaver:
1. Правой кнопкой на базе данных
2. Tools → Dump Database
3. Выбрать "Schema only" или "All"
4. Сохранить как .sql

---

## 6. Проверка 3НФ по проекту

| Потенциальное нарушение | Как решено |
|-------------------------|-----------|
| Поставщик в каждом товаре | Вынесен в `Supplier`, связь через FK |
| Список товаров в заказе | Вынесен в `OrderItem` |
| Роль строкой в пользователе | Вынесена в `Role`, связь через FK |
| Производитель как текст | Остался текстом (допустимо для учебного проекта) |
| Категория как текст | Остался текстом (допустимо) |

> На строгом экзамене могут спросить почему manufacturer не вынесен в справочник. Ответ: для данного проекта это намеренное упрощение, производитель — атрибут товара.
