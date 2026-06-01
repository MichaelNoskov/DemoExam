# Запросы к БД через Django ORM

← [Назад к моделям](orm-models.md) | ← [Назад к пайплайну](README.md)

---

## 1. Как устроен ORM: Manager и QuerySet

Каждая модель имеет **менеджер** — `objects`. Через него строятся все запросы.

```python
Product.objects          # менеджер — точка входа
Product.objects.all()    # возвращает QuerySet
```

**QuerySet** — это не список объектов, а описание запроса. SQL выполняется только когда данные реально нужны: при итерации, срезе, `len()`, `list()`.

```python
qs = Product.objects.all()   # SQL ещё НЕ выполнен
qs = qs.filter(quantity=0)   # SQL ещё НЕ выполнен
for p in qs:                  # вот здесь — выполнен
    print(p.name)
```

Это называется **ленивость (lazy evaluation)**. Благодаря ей можно безопасно строить queryset по частям — SQL сформируется один раз в конце.

---

## 2. Получение всех объектов — `.all()`

```python
Product.objects.all()          # SELECT * FROM core_product
Supplier.objects.all()         # SELECT * FROM core_supplier
```

В `ListView` Django вызывает `get_queryset()`, который по умолчанию возвращает `Model.objects.all()`. Переопределяем его когда нужна фильтрация или сортировка.

---

## 3. Получение одного объекта

### `.get()` — ровно один, иначе исключение

```python
product = Product.objects.get(id=5)         # нашёл → объект
product = Product.objects.get(article="A1") # нашёл → объект
# DoesNotExist — если не найден
# MultipleObjectsReturned — если найдено больше одного
```

Используй `.get()` только когда уверен, что запись существует и она одна (например, по `pk` или `unique`-полю).

### `get_object_or_404()` — .get() + HTTP 404 при отсутствии

```python
from django.shortcuts import get_object_or_404

product = get_object_or_404(Product, pk=pk)
# Эквивалентно:
# try:
#     product = Product.objects.get(pk=pk)
# except Product.DoesNotExist:
#     raise Http404
```

Стандарт для views: если пользователь запрашивает несуществующий объект — возвращаем 404, не 500.

### `.first()` — первый или None

```python
pp = PickupPoint.objects.first()   # None если таблица пуста
```

Используется как fallback: `PickupPoint.objects.get(id=pp_id) if ... else PickupPoint.objects.first()`.

---

## 4. Фильтрация — `.filter()`

```python
Product.objects.filter(quantity=0)              # WHERE quantity = 0
Product.objects.filter(supplier_id=5)           # WHERE supplier_id = 5
Product.objects.filter(supplier=supplier_obj)   # то же, через объект
```

### Lookup expressions — условия в имени поля

Пишутся через двойное подчёркивание: `поле__условие`.

| Lookup | SQL | Пример |
|--------|-----|--------|
| `exact` (по умолчанию) | `= значение` | `filter(status="Новый")` |
| `iexact` | `= значение` без учёта регистра | `filter(name__iexact="nike")` |
| `contains` | `LIKE '%значение%'` | `filter(name__contains="ботин")` |
| `icontains` | `ILIKE '%значение%'` | `filter(name__icontains="ботин")` |
| `startswith` | `LIKE 'значение%'` | `filter(article__startswith="A")` |
| `gt` / `gte` | `>` / `>=` | `filter(price__gte=1000)` |
| `lt` / `lte` | `<` / `<=` | `filter(quantity__lt=5)` |
| `in` | `IN (...)` | `filter(status__in=["Новый", "В сборке"])` |
| `isnull` | `IS NULL` | `filter(photo__isnull=True)` |

### Фильтрация через связанные таблицы (JOIN)

Двойное подчёркивание работает и для FK — Django автоматически добавляет JOIN:

```python
# Товары поставщика с именем "Nike"
Product.objects.filter(supplier__name="Nike")

# Товары, у которых в имени поставщика есть "ООО"
Product.objects.filter(supplier__name__icontains="ООО")

# Заказы с пунктом выдачи по адресу
Order.objects.filter(pickup_point__address__icontains="Москва")
```

В проекте:
```python
Q(supplier__name__icontains=search_query)   # поиск по имени поставщика через FK
Q(manufacturer__name__icontains=search_query)  # поиск по производителю через FK
Q(category__name__icontains=search_query)   # поиск по категории через FK
```

---

## 5. Q-объекты — OR и AND в одном запросе

`filter(a=1, b=2)` — это всегда AND. Для OR нужен `Q`:

```python
from django.db.models import Q

# OR — хотя бы одно условие
Product.objects.filter(
    Q(name__icontains=query) | Q(description__icontains=query)
)

# AND явно (то же что filter(a=1, b=2))
Product.objects.filter(Q(price__gte=100) & Q(quantity__gt=0))

# Отрицание
Product.objects.filter(~Q(status="Отменён"))

# Комбинация
Product.objects.filter(
    Q(name__icontains=query) | Q(article__icontains=query),
    supplier_id=5    # это AND с группой Q
)
```

Полный поиск по всем текстовым полям из проекта:

```python
queryset = queryset.filter(
    Q(name__icontains=search_query)
    | Q(description__icontains=search_query)
    | Q(manufacturer__name__icontains=search_query)
    | Q(category__name__icontains=search_query)
    | Q(article__icontains=search_query)
    | Q(supplier__name__icontains=search_query)
)
```

---

## 6. Сортировка — `.order_by()`

```python
Product.objects.all().order_by("quantity")     # ASC (по возрастанию)
Product.objects.all().order_by("-quantity")    # DESC (по убыванию), минус = обратный порядок
Order.objects.all().order_by("-id")            # самые новые первыми

# По нескольким полям
Product.objects.all().order_by("category", "name")
```

---

## 7. Проверка существования — `.exists()`

```python
if product.orderitem_set.exists():    # есть хоть одна запись?
    # нельзя удалять

if User.objects.filter(username=login).exists():
    # пользователь уже есть
```

`.exists()` выполняет `SELECT 1 FROM ... LIMIT 1` — быстрее чем `count()` или `len()`, когда нужно только знать «есть или нет».

---

## 8. Агрегация — `.aggregate()`

Возвращает словарь с результатом вычисления по всей таблице:

```python
from django.db.models import Max, Min, Count, Sum, Avg

result = Product.objects.aggregate(Max("id"))
# → {"id__max": 42}

max_id = Product.objects.aggregate(Max("id"))["id__max"] or 0
next_id = max_id + 1   # предварительный ID для формы добавления
```

| Функция | Что считает |
|---------|------------|
| `Max("поле")` | Максимум |
| `Min("поле")` | Минимум |
| `Count("поле")` | Количество строк |
| `Sum("поле")` | Сумма |
| `Avg("поле")` | Среднее |

---

## 9. Оптимизация — `select_related` и `prefetch_related`

Проблема «N+1 запросов»: если получить 10 товаров и для каждого обратиться к `product.supplier.name`, Django выполнит 1 + 10 = 11 запросов.

### `select_related()` — JOIN для FK и OneToOne

Загружает связанные объекты одним запросом с `JOIN`. Используется для FK (один объект на стороне «один»):

```python
# Без оптимизации: 1 запрос на товары + N запросов на поставщиков
Product.objects.all()

# С оптимизацией: 1 запрос с JOIN
Product.objects.all().select_related("supplier", "category", "manufacturer")
```

```sql
-- Примерно такой SQL:
SELECT core_product.*, core_supplier.*, core_category.*, core_manufacturer.*
FROM core_product
JOIN core_supplier ON core_product.supplier_id = core_supplier.id
JOIN core_category ON core_product.category_id = core_category.id
JOIN core_manufacturer ON core_product.manufacturer_id = core_manufacturer.id
```

### `prefetch_related()` — отдельный запрос для обратных FK и M2M

Для обратных связей (reverse FK, many-to-many) `select_related` не работает — используется `prefetch_related`:

```python
# Заказы + все их позиции + товары позиций
Order.objects.all()
    .select_related("pickup_point", "user")     # FK прямые — через JOIN
    .prefetch_related("items__product")          # items — обратный FK, product — FK внутри items
```

`items__product` означает: сначала prefetch все `OrderItem` для заказов, затем select_related `Product` для каждого `OrderItem`. Итого 3 запроса вместо 1 + N + N×M.

### Когда что использовать

| Ситуация | Метод |
|----------|-------|
| FK / OneToOne → один объект | `select_related` |
| Обратная FK (один ко многим) | `prefetch_related` |
| ManyToMany | `prefetch_related` |
| Цепочка: items__product | `prefetch_related` |

---

## 10. Создание объектов

### `.create()` — создать и сразу сохранить

```python
OrderItem.objects.create(order=order, product=prod, count=5)
# Эквивалентно:
item = OrderItem(order=order, product=prod, count=5)
item.save()
```

### `.save()` — сохранить существующий объект

```python
user = User(username="ivan", full_name="Иван Иванов", role=role_obj)
user.set_password("secret123")
user.save()   # INSERT

user.full_name = "Иван Петров"
user.save()   # UPDATE
```

### `.get_or_create()` — получить или создать

```python
supplier, created = Supplier.objects.get_or_create(name="Nike")
# created=True  — объект был создан
# created=False — объект уже существовал

# Можно с дополнительными полями при создании:
role, _ = Role.objects.get_or_create(name="admin")  # _ означает «нас не интересует created»
```

Выполняет: `SELECT ... WHERE name='Nike'`, если не найдено — `INSERT`. Атомарно на уровне транзакции.

### `.update_or_create()` — обновить или создать

```python
product, created = Product.objects.update_or_create(
    article=row["article"],      # ключ поиска
    defaults={                   # поля для обновления/создания
        "name": row["name"],
        "price": row["price"],
        "supplier": supplier_obj,
    },
)
```

Если запись с `article` существует — обновить поля из `defaults`. Если нет — создать с этими полями. Используется в `import_data` для идемпотентного импорта.

---

## 11. Удаление объектов

### Удаление одного объекта

```python
product = get_object_or_404(Product, pk=pk)
product.delete()   # DELETE FROM core_product WHERE id = pk
```

При `ForeignKey(on_delete=CASCADE)` — зависимые объекты удаляются автоматически (например, `OrderItem` при удалении `Order`).

При `ForeignKey(on_delete=PROTECT)` — Django выбросит `ProtectedError`, если есть зависимые объекты:

```python
from django.db.models import ProtectedError

try:
    product.delete()
except ProtectedError:
    messages.error(request, "Нельзя удалить: есть связанные заказы")
```

### Удаление через queryset (групповое)

```python
Product.objects.filter(quantity=0).delete()   # удалить все с quantity=0
```

---

## 12. Обратные связи (reverse FK)

Когда у `OrderItem` есть FK на `Product`, у объекта `Product` автоматически появляется обратный менеджер для доступа к связанным `OrderItem`:

```python
product = Product.objects.get(pk=1)

# Имя менеджера по умолчанию: <модель>_set
product.orderitem_set.all()      # все позиции заказов с этим товаром
product.orderitem_set.exists()   # есть ли хоть одна?
product.orderitem_set.count()    # сколько?

# Если задан related_name="items":
order.items.all()        # все OrderItem этого заказа
order.items.count()      # количество позиций
order.items.prefetch_related("product")
```

`related_name` задаётся в ForeignKey:
```python
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    # → order.items.all() вместо order.orderitem_set.all()
```

---

## 13. Цепочки запросов — queryset chaining

QuerySet-методы возвращают новый QuerySet — их можно выстраивать в цепочку. SQL строится один раз в конце:

```python
queryset = Product.objects.all()                        # начало
queryset = queryset.select_related("supplier")          # добавить JOIN
queryset = queryset.filter(Q(name__icontains="ботин"))  # добавить WHERE
queryset = queryset.filter(supplier_id=3)               # AND ещё условие
queryset = queryset.order_by("-quantity")               # добавить ORDER BY

# SQL выполняется здесь:
for product in queryset:
    print(product.name)
```

Именно это используется в `ProductListView.get_queryset()` — каждый шаг (поиск, фильтр по поставщику, сортировка) добавляет условие к одному queryset. Если параметра нет — шаг пропускается, queryset не меняется.

---

## Шпаргалка — все методы проекта

| Метод | Что делает | Возвращает |
|-------|-----------|-----------|
| `.all()` | Все записи | QuerySet |
| `.filter(...)` | Записи по условию | QuerySet |
| `.order_by(...)` | Сортировка | QuerySet |
| `.select_related(...)` | JOIN для FK | QuerySet |
| `.prefetch_related(...)` | Отдельный запрос для обратных FK | QuerySet |
| `.get(...)` | Ровно одна запись | объект / исключение |
| `.first()` | Первая запись или None | объект / None |
| `.exists()` | Есть ли хоть одна запись? | bool |
| `.aggregate(Max(...))` | Агрегат по всем строкам | dict |
| `.create(...)` | Создать и сохранить | объект |
| `.get_or_create(...)` | Получить или создать | (объект, bool) |
| `.update_or_create(...)` | Обновить или создать | (объект, bool) |
| `.delete()` | Удалить | (int, dict) |
| `get_object_or_404(Model, ...)` | `.get()` + 404 | объект |
