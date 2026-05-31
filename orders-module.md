# Модуль 4 — Раздел заказов

← [Назад к пайплайну](README.md)

> Модуль 4 = «новый раздел» для менеджера и администратора. В нашем проекте это раздел заказов.
> Менеджер: просмотр. Администратор: полный CRUD.

---

## 1. Что нужно реализовать

| Что | Для кого | Файл |
|-----|---------|------|
| Кнопка "Заказы" в списке товаров | manager, admin | `product_list.html` |
| Список заказов | manager, admin | `order_list.html` + `OrderListView` |
| Форма добавления заказа | admin | `order_form.html` + `OrderCreateView` |
| Форма редактирования заказа | admin | `order_form.html` + `OrderUpdateView` |
| Удаление заказа с подтверждением | admin | `OrderDeleteView` |

---

## 2. OrderForm — форма заказа

```python
# core/forms.py — добавить:
from .models import Order

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["delivery_date", "pickup_point", "client_name", "pickup_code", "status"]
        labels = {
            "delivery_date": "Дата доставки",
            "pickup_point": "Пункт выдачи",
            "client_name": "ФИО клиента",
            "pickup_code": "Код получения",
            "status": "Статус",
        }
        widgets = {
            "delivery_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.delivery_date:
            self.initial["delivery_date"] = self.instance.delivery_date.strftime(
                "%Y-%m-%dT%H:%M"
            )

    def clean_pickup_code(self):
        code = self.cleaned_data.get("pickup_code")
        if code is not None and code < 0:
            raise forms.ValidationError("Код получения не может быть отрицательным")
        return code
```

**Поля формы:** дата доставки, пункт выдачи (выпадающий список), ФИО клиента, код получения, статус.
`order_date` — не в форме, ставится автоматически (`auto_now_add=True`).

---

## 3. Views для заказов

```python
# core/views.py — добавить:
from .forms import OrderForm
from .models import Order

class ManagerOrAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role
            and self.request.user.role.name in ("admin", "manager")
        )


class OrderListView(ManagerOrAdminMixin, ListView):
    model = Order
    template_name = "core/order_list.html"
    context_object_name = "orders"

    def get_queryset(self):
        return (
            Order.objects.all()
            .select_related("pickup_point", "user")
            .prefetch_related("items__product")
            .order_by("-id")
        )


class OrderCreateView(AdminRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = "core/order_form.html"
    success_url = reverse_lazy("order_list")

    def form_valid(self, form):
        messages.success(self.request, "Заказ успешно добавлен")
        return super().form_valid(form)


class OrderUpdateView(AdminRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = "core/order_form.html"
    success_url = reverse_lazy("order_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, "Заказ успешно обновлен")
        return super().form_valid(form)


class OrderDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        order_id = order.id
        order.delete()  # OrderItems удаляются каскадно
        messages.success(request, f"Заказ №{order_id} успешно удалён")
        return redirect("order_list")
```

---

## 4. URL-маршруты для заказов

```python
# config/urls.py — добавить импорты и пути:
from core.views import OrderListView, OrderCreateView, OrderUpdateView, OrderDeleteView

# в urlpatterns:
path("orders/", OrderListView.as_view(), name="order_list"),
path("orders/add/", OrderCreateView.as_view(), name="order_create"),
path("orders/<int:pk>/edit/", OrderUpdateView.as_view(), name="order_edit"),
path("orders/<int:pk>/delete/", OrderDeleteView.as_view(), name="order_delete"),
```

---

## 5. Кнопка "Заказы" в product_list.html

Добавить внутри `{% if user.role.name == "admin" or user.role.name == "manager" %}`:

```html
<div>
    <a href="{% url 'order_list' %}" class="btn" style="background-color: #5bc0de;">Заказы</a>
</div>
```

---

## 6. Шаблон order_list.html — полный код

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
            <th>№</th>
            <th>Клиент</th>
            <th>Статус</th>
            <th>Дата заказа</th>
            <th>Дата доставки</th>
            <th>Пункт выдачи</th>
            <th>Код</th>
            <th>Позиций</th>
            {% if user.role.name == "admin" %}
            <th>Действия</th>
            {% endif %}
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
                <a href="{% url 'order_edit' order.id %}">Редактировать</a>
                &nbsp;|&nbsp;
                <form method="post" action="{% url 'order_delete' order.id %}" style="display: inline;"
                      onsubmit="return confirm('Удалить заказ №{{ order.id }}?\nВсе позиции заказа будут удалены.')">
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

---

## 7. Шаблон order_form.html — полный код

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

## 8. CSS для таблицы заказов

Добавить в `static/css/style.css`:

```css
.orders-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.orders-table th,
.orders-table td {
  border: 1px solid black;
  padding: 6px 10px;
  text-align: left;
}

.orders-table th {
  background-color: #7fff00;
}

.orders-table tr:nth-child(even) {
  background-color: #f9f9f9;
}
```

---

## 9. Порядок реализации (пошагово)

1. Добавить `OrderForm` в `core/forms.py`
2. Добавить `ManagerOrAdminMixin`, `OrderListView`, `OrderCreateView`, `OrderUpdateView`, `OrderDeleteView` в `core/views.py`
3. Добавить URL-паттерны заказов в `config/urls.py` (обновить импорты)
4. Создать `core/templates/core/order_list.html`
5. Создать `core/templates/core/order_form.html`
6. В `product_list.html` раскомментировать/добавить кнопку "Заказы"
7. Добавить CSS для таблицы в `static/css/style.css`
8. Запустить сервер: `python manage.py runserver`
9. Зайти как admin → убедиться что кнопка "Заказы" появилась → перейти → проверить список

---

## 10. Чеклист Модуля 4

- [ ] `OrderForm` создан в forms.py
- [ ] `OrderListView` доступен менеджеру и администратору
- [ ] `OrderCreateView` доступен только администратору
- [ ] `OrderUpdateView` доступен только администратору
- [ ] `OrderDeleteView` запрашивает подтверждение (JS confirm в шаблоне)
- [ ] Кнопка "Заказы" видна в списке товаров для manager/admin
- [ ] Кнопки "Добавить"/"Редактировать"/"Удалить" видны только admin
- [ ] После удаления/добавления/редактирования список обновляется (redirect)
- [ ] ID показывается как readonly при редактировании
- [ ] Кнопка "Назад" присутствует в обоих шаблонах заказов
