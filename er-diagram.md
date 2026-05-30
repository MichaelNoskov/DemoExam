# ER-диаграмма в draw.io

← [Назад к пайплайну](README.md)

---

## 1. Открыть draw.io

- Сайт: **app.diagrams.net** (работает в браузере)
- Или десктоп-приложение: **diagrams.net**

При открытии выбрать: **Blank Diagram** (или Entity Relationship в разделе Other).

---

## 2. Создать сущности (таблицы)

Для каждой таблицы в draw.io:

1. Слева в панели найти **Entity** (в категории Entity Relation) или нарисовать прямоугольник вручную
2. Удобнее использовать **таблицу**: Insert → Table → ввести количество строк

**Быстрый способ:**
- Перетащить фигуру "Entity" из левой панели на холст
- Дважды кликнуть — ввести название таблицы
- Добавить строки для каждого поля

### Что писать в каждой сущности

```
┌─────────────────────────────┐
│         Role                │
├──────┬──────────────────────┤
│ PK   │ id : BIGINT          │
├──────┼──────────────────────┤
│      │ name : VARCHAR(50)   │
└──────┴──────────────────────┘
```

---

## 3. Все сущности и их поля

### Role
```
PK  id : BIGINT
    name : VARCHAR(50) UNIQUE
```

### User
```
PK  id : BIGINT
    username : VARCHAR(150) UNIQUE
    password : VARCHAR(128)
    full_name : VARCHAR(255)
FK  role_id → Role(id)
```

### Supplier
```
PK  id : BIGINT
    name : VARCHAR(200) UNIQUE
```

### PickupPoint
```
PK  id : BIGINT
    address : TEXT
```

### Product
```
PK  id : BIGINT
    article : VARCHAR(50) UNIQUE
    name : VARCHAR(255)
    unit : VARCHAR(20)
    price : DECIMAL(10,2)
    manufacturer : VARCHAR(200)
    category : VARCHAR(200)
    discount : DECIMAL(5,2)
    quantity : INTEGER
    description : TEXT
    photo : VARCHAR(100) NULL
FK  supplier_id → Supplier(id)
```

### Order
```
PK  id : BIGINT
    order_date : TIMESTAMP
    delivery_date : TIMESTAMP
    client_name : VARCHAR(255) NULL
    pickup_code : INTEGER
    status : VARCHAR(50)
FK  pickup_point_id → PickupPoint(id)
FK  user_id → User(id) NULL
```

### OrderItem
```
PK  id : BIGINT
    count : INTEGER
FK  order_id → Order(id)
FK  product_id → Product(id)
```

---

## 4. Добавить связи между сущностями

В draw.io связи рисуются стрелками. Нотация для ER: **Crow's Foot (вороньи лапки)**.

| Связь | Кардинальность | Нотация на стороне N |
|-------|---------------|----------------------|
| Role → User | 1:N (у одной роли много пользователей) | "вороньи лапки" у User |
| Supplier → Product | 1:N | "вороньи лапки" у Product |
| PickupPoint → Order | 1:N | "вороньи лапки" у Order |
| User → Order | 1:N | "вороньи лапки" у Order |
| Order → OrderItem | 1:N | "вороньи лапки" у OrderItem |
| Product → OrderItem | 1:N | "вороньи лапки" у OrderItem |

### Как нарисовать связь в draw.io:
1. Навести мышь на границу сущности — появятся синие стрелочки
2. Потянуть стрелку к другой сущности
3. Кликнуть правой кнопкой на линии → Edit Connection → выбрать стиль Crow's Foot

Или в меню Format → Connection → выбрать нотацию.

---

## 5. Расположить читаемо

Рекомендуемое расположение:
```
Role          Supplier        PickupPoint
  ↓               ↓                ↓
User          Product           Order
                  ↘               ↙
                    OrderItem
```

---

## 6. Экспорт в PDF

1. Меню **File → Export As → PDF**
2. Или: **File → Print → Сохранить как PDF**
3. Ориентация: альбомная (Landscape)
4. Убедиться что вся диаграмма помещается на лист (Ctrl+Shift+H — подогнать масштаб)
5. Назвать файл: `ER-diagram.pdf`

---

## 7. Чеклист ER-диаграммы

- [ ] Все 7 таблиц присутствуют
- [ ] У каждой таблицы указаны все поля
- [ ] PK и FK помечены
- [ ] Все связи нарисованы
- [ ] Кардинальность указана (1:N)
- [ ] Экспортировано в PDF
