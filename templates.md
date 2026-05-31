# HTML-шаблоны Django

← [Назад к пайплайну](README.md)

---

## 1. Синтаксис шаблонов Django

### Переменные

```html
{{ variable }}              <!-- вывод переменной -->
{{ user.full_name }}        <!-- атрибут объекта -->
{{ product.supplier.name }} <!-- цепочка атрибутов -->
```

### Теги

```html
{% tag %}                   <!-- управляющая конструкция -->
```

| Тег | Описание |
|-----|---------|
| `{% if condition %}...{% elif %}...{% else %}...{% endif %}` | Условие |
| `{% for item in list %}...{% empty %}...{% endfor %}` | Цикл |
| `{% block name %}...{% endblock %}` | Блок для наследования |
| `{% extends "base.html" %}` | Наследовать шаблон |
| `{% include "partial.html" %}` | Включить другой шаблон |
| `{% load static %}` | Загрузить тег static |
| `{% static "path/file.css" %}` | Путь к статическому файлу |
| `{% url "view_name" arg %}` | Генерация URL |
| `{% csrf_token %}` | CSRF-токен (обязателен в POST-формах) |
| `{% comment %}...{% endcomment %}` | Комментарий |

### Фильтры

```html
{{ value|filter }}
{{ value|filter:arg }}
```

| Фильтр | Что делает | Пример |
|--------|-----------|--------|
| `floatformat:2` | Округлить до 2 знаков | `{{ price|floatformat:2 }}` |
| `stringformat:"i"` | Целое число как строка | `{{ id|stringformat:"i" }}` |
| `default:"нет"` | Значение если пустое | `{{ name|default:"Нет имени" }}` |
| `date:"d.m.Y"` | Формат даты | `{{ order_date|date:"d.m.Y" }}` |
| `length` | Длина | `{{ list|length }}` |
| `upper` / `lower` | Регистр | `{{ name|upper }}` |
| `linebreaks` | Переносы строк → `<br>` | `{{ text|linebreaks }}` |

---

## 2. Наследование шаблонов

**base.html** — базовый шаблон с общим layout:
```html
<!DOCTYPE html>
<html>
<head>
    {% block title %}Дефолтный заголовок{% endblock %}
</head>
<body>
    <header>...</header>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

**child.html** — дочерний шаблон:
```html
{% extends "core/base.html" %}

{% block title %}Список товаров{% endblock %}

{% block content %}
    <p>Контент страницы</p>
{% endblock %}
```

---

## 3. Частые паттерны

### POST-форма с CSRF

```html
<form method="post" enctype="multipart/form-data">
    {% csrf_token %}
    {{ form }}
    <button type="submit">Сохранить</button>
</form>
```

> `enctype="multipart/form-data"` — **обязательно** для загрузки файлов (ImageField).

### GET-форма (поиск/фильтр)

```html
<form method="get">
    <input type="text" name="search" value="{{ current_search }}">
    <button type="submit">Найти</button>
</form>
```

### Условный CSS-класс

```html
<div class="product-card 
    {% if product.discount > 15 %}sale{% endif %}
    {% if product.quantity == 0 %}out-of-stock{% endif %}">
```

### Дебаунс (отложенная отправка формы)

```html
<input type="text" name="search" value="{{ current_search }}"
    oninput="clearTimeout(this.delay); this.delay = setTimeout(() => this.form.submit(), 500);">
```
500 мс паузы — форма отправляется только когда пользователь перестал печатать.

### Изображение с заглушкой

```html
{% if product.photo %}
    <img src="{{ product.photo.url }}" alt="{{ product.name }}">
{% else %}
    <img src="{% static 'images/picture.png' %}" alt="Заглушка">
{% endif %}
```

---

## 4. Полный код всех шаблонов

### core/templates/core/base.html

```html
{% load static %}
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}ООО «Обувь»{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
    <link rel="icon" type="image/png" href="{% static 'images/Icon.ico' %}">
</head>
<body>
    <header>
        <div class="header-left">
            <img src="{% static 'images/Icon.png' %}" alt="Логотип">
            <span>ООО «Обувь»</span>
        </div>
        <div>
            {% if user.is_authenticated %}
                <span>{{ user.role.name }}</span>
                <strong>{{ user.full_name }}</strong> | 
                <form action="{% url 'logout' %}" method="post" style="display: inline;">
                    {% csrf_token %}
                    <button type="submit" style="background: none; border: none; color: blue; text-decoration: underline; cursor: pointer; padding: 0; font-family: inherit; font-size: inherit;">Выйти</button>
                </form>
            {% else %}
                <span class="role-badge">Гость</span> | 
                <a href="{% url 'login' %}">Вернуться ко входу</a>
            {% endif %}
        </div>
    </header>

    <div class="container">
        <h1>{% block h1 %}{% endblock %}</h1>
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

---

### core/templates/core/login.html

```html
{% extends 'core/base.html' %}

{% block title %}Авторизация - ООО «Обувь»{% endblock %}
{% block h1 %}Вход в систему{% endblock %}

{% block content %}
<div>
    <form method="post">
        {% csrf_token %}
        {% if form.errors %}
        <div style="color: red;">
            {% for field in form %}
            {% for error in field.errors %}
            {{ error }}
            {% endfor %}
            {% endfor %}
            {% for error in form.non_field_errors %}
            {{ error }}
            {% endfor %}
        </div>
        {% endif %}

        <label>Логин (Email):</label><br>
        <input type="text" name="username">
        <label>Пароль:</label><br>
        <input type="password" name="password">
        <button type="submit" class="btn">Войти</button>
    </form>
    
    <a href="{% url 'product_list' %}">Войти как гость</a>
</div>
{% endblock %}
```

---

### core/templates/core/product_list.html

```html
{% extends 'core/base.html' %}
{% load static %}

{% block title %}Список товаров - ООО «Обувь»{% endblock %}
{% block h1 %}Каталог товаров{% endblock %}

{% block content %}
{% if user.role.name == "admin" or user.role.name == "manager" %}
<div>
    <form method="get" style="display: flex;">
        <div>
            <label>Поиск:</label><br>
            <input type="text" name="search" value="{{ current_search }}" placeholder="Найти..."
                oninput="clearTimeout(this.delay); this.delay = setTimeout(() => this.form.submit(), 500);">
        </div>

        <div>
            <label>Поставщик:</label><br>
            <select name="supplier" onchange="this.form.submit()">
                <option value="all">Все поставщики</option>
                {% for s in suppliers %}
                <option value="{{ s.id }}" {% if current_supplier == s.id|stringformat:"i" %}selected{% endif %}>{{ s.name }}</option>
                {% endfor %}
            </select>
        </div>

        <div>
            <label>Сортировка (кол-во):</label><br>
            <select name="sort" onchange="this.form.submit()">
                <option value="">Без сортировки</option>
                <option value="asc" {% if current_sort == "asc" %}selected{% endif %}>По возрастанию</option>
                <option value="desc" {% if current_sort == "desc" %}selected{% endif %}>По убыванию</option>
            </select>
        </div>

        {% if user.role.name == 'admin' %}
        <div style="margin-left: auto;">
            <a href="{% url 'product_create' %}" class="btn">Добавить товар</a>
        </div>
        {% endif %}
    </form>

</div>
{% endif %}
<div>
    {% for product in products %}
    <div class="product-card 
        {% if product.discount > 15 %}sale{% endif %}
        {% if product.quantity == 0 %}out-of-stock{% endif %}">
        {% if product.photo %}
        <img src="{{ product.photo.url }}" class="image" alt="{{ product.name }}">
        {% else %}
        <img src="{% static 'images/picture.png' %}" class="image" alt="Заглушка">
        {% endif %}
        <div class="details">
            <strong>{{ product.category }} | {{ product.name }}</strong>
            <br />
            Описание товара: {{ product.description }}
            <br />
            Производитель: {{ product.manufacturer }}
            <br />
            Поставщик: {{ product.supplier.name }}
            <br />
            {% if product.discount > 0 %}
            Цена: <span class="old-price">{{ product.price }}</span> {{ product.final_price|floatformat:2 }} руб.
            {% else %}
            Цена: {{ product.price }} руб.
            {% endif %}
            <br />
            Единица измерения: {{ product.unit }}
            <br />
            Количество на складе: {{ product.quantity }}
            {% if user.role.name == "admin" %}
            <br><a href="{% url 'product_edit' product.id %}">Редактировать товар</a>
            {% endif %}
        </div>
        <div class="sale">{{ product.discount }}%</div>
    </div>
    {% empty %}
    <p>Товары не найдены.</p>
    {% endfor %}
</div>
{% endblock %}
```

---

### core/templates/core/product_form.html

```html
{% extends 'core/base.html' %}

{% block title %}
{% if is_edit %}Редактирование товара{% else %}Добавление товара{% endif %}
{% endblock %}

{% block h1 %}
{% if is_edit %}Редактирование товара: {{ object.article }}{% else %}Новый товар{% endif %}
{% endblock %}

{% block content %}
<div>
    <form method="post" enctype="multipart/form-data">
        {% csrf_token %}
        {{ form }}
        <button type="submit" class="btn">Сохранить</button>
    </form>
</div>
{% endblock %}
```

---

## 5. Полный CSS — static/css/style.css

```css
body {
  font-family: "Times New Roman", serif;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  align-content: center;
  background-color: #7fff00;
  margin: 10px;
}

.header-left {
  font-size: xxx-large;
  padding: 10px;
}

.header-left img {
  width: 50px;
  height: 50px;
}

.product-card {
  border: solid black 2px;
  display: flex;
  padding: 10px;
}

.product-card.sale {
  background-color: #2e8b57;
}

.product-card.out-of-stock {
  background-color: aqua;
}

.product-card .image {
  width: 30%;
  border: 2px gray solid;
}

.product-card .details {
  flex: 1;
  border: solid black 1px;
  margin: 0 10px;
  padding: 5px;
}

.product-card .sale {
  border: solid black 1px;
  font-weight: bold;
  font-size: x-large;
  padding: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 15%;
}

.old-price {
  text-decoration: line-through;
  color: red;
}
```

---

## 6. Условное форматирование карточек

| Условие | CSS-класс | Цвет фона |
|---------|-----------|-----------|
| `product.discount > 15` | `sale` | `#2e8b57` (тёмно-зелёный) |
| `product.quantity == 0` | `out-of-stock` | `aqua` (голубой) |
| Нет условий | — | Белый |

> Если оба условия выполняются (скидка > 15% И количество = 0), применяются оба класса. Цвет определяется порядком в CSS.

---

## 6. Шаблоны заказов (Модуль 4)

→ [Полный код с объяснением: orders-module.md](orders-module.md)

### core/templates/core/order_list.html

```html
{% extends 'core/base.html' %}

{% block title %}Список заказов - ООО «Обувь»{% endblock %}
{% block h1 %}Заказы{% endblock %}

{% block content %}
<div style="margin-bottom: 10px;">
    <a href="{% url 'product_list' %}" class="btn-secondary">← К товарам</a>
    {% if user.role.name == "admin" %}
    <a href="{% url 'order_create' %}" class="btn" style="margin-left: 10px;">Добавить заказ</a>
    {% endif %}
</div>

{% if orders %}
<table class="orders-table">
    <thead>
        <tr>
            <th>№</th><th>Клиент</th><th>Статус</th>
            <th>Дата заказа</th><th>Дата доставки</th>
            <th>Пункт выдачи</th><th>Код</th><th>Позиций</th>
            {% if user.role.name == "admin" %}<th>Действия</th>{% endif %}
        </tr>
    </thead>
    <tbody>
        {% for order in orders %}
        <tr>
            <td>{{ order.id }}</td>
            <td>{{ order.client_name|default:"—" }}</td>
            <td>{{ order.status }}</td>
            <td>{{ order.order_date|date:"d.m.Y H:i" }}</td>
            <td>{{ order.delivery_date|date:"d.m.Y H:i" }}</td>
            <td>{{ order.pickup_point.address|truncatechars:40 }}</td>
            <td>{{ order.pickup_code }}</td>
            <td>{{ order.items.count }}</td>
            {% if user.role.name == "admin" %}
            <td>
                <a href="{% url 'order_edit' order.id %}">Редактировать</a> |
                <form method="post" action="{% url 'order_delete' order.id %}" style="display: inline;"
                      onsubmit="return confirm('Удалить заказ №{{ order.id }}?')">
                    {% csrf_token %}
                    <button type="submit" style="color: red; background: none; border: none; cursor: pointer; font-family: inherit; font-size: inherit; padding: 0;">Удалить</button>
                </form>
            </td>
            {% endif %}
        </tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<p>Заказов пока нет.</p>
{% endif %}
{% endblock %}
```

### core/templates/core/order_form.html

```html
{% extends 'core/base.html' %}

{% block title %}
{% if is_edit %}Редактирование заказа{% else %}Новый заказ{% endif %}
{% endblock %}

{% block h1 %}
{% if is_edit %}Редактирование заказа №{{ object.pk }}{% else %}Новый заказ{% endif %}
{% endblock %}

{% block content %}
<div>
    <a href="{% url 'order_list' %}" class="btn-secondary">← Назад к заказам</a>
</div>
<br>
<div>
    {% if is_edit %}
    <p><strong>ID:</strong>
        <input type="text" value="{{ object.pk }}" disabled
               style="background: #eee; border: 1px solid #ccc; padding: 3px 6px;">
    </p>
    {% endif %}
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit" class="btn">Сохранить</button>
    </form>
</div>
{% endblock %}
```

---

## 7. Обновлённый style.css (полный)

```css
body {
  font-family: "Times New Roman", serif;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #7fff00;
  margin: 10px;
}

.header-left {
  font-size: xxx-large;
  padding: 10px;
}

.header-left img {
  width: 50px;
  height: 50px;
  object-fit: contain;
}

.btn {
  background-color: #00fa9a;
  border: 1px solid #ccc;
  padding: 5px 15px;
  cursor: pointer;
  font-family: "Times New Roman", serif;
  font-size: inherit;
  text-decoration: none;
  display: inline-block;
  color: black;
}

.btn-secondary {
  background-color: #e0e0e0;
  border: 1px solid #aaa;
  padding: 5px 15px;
  cursor: pointer;
  font-family: "Times New Roman", serif;
  font-size: inherit;
  text-decoration: none;
  display: inline-block;
  color: black;
}

.product-card {
  border: solid black 2px;
  display: flex;
  padding: 10px;
  margin-bottom: 5px;
}

.product-card.sale { background-color: #2e8b57; }
.product-card.out-of-stock { background-color: aqua; }
.product-card .image { width: 30%; border: 2px gray solid; }
.product-card .details { flex: 1; border: solid black 1px; margin: 0 10px; padding: 5px; }
.product-card .sale { border: solid black 1px; font-weight: bold; font-size: x-large; display: flex; align-items: center; justify-content: center; width: 15%; }
.old-price { text-decoration: line-through; color: red; }

.alert { padding: 10px 15px; margin: 5px 0; border: 1px solid; border-radius: 3px; }
.alert-success { background-color: #d4edda; border-color: #28a745; color: #155724; }
.alert-error, .alert-danger { background-color: #f8d7da; border-color: #dc3545; color: #721c24; }
.alert-warning { background-color: #fff3cd; border-color: #ffc107; color: #856404; }
.alert-info { background-color: #d1ecf1; border-color: #17a2b8; color: #0c5460; }

.orders-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
.orders-table th, .orders-table td { border: 1px solid black; padding: 6px 10px; text-align: left; }
.orders-table th { background-color: #7fff00; }
.orders-table tr:nth-child(even) { background-color: #f9f9f9; }
```
