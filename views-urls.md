# Views и URL-маршрутизация

← [Назад к пайплайну](README.md) | → [Запросы к БД](orm-queries.md)

---

## 1. Классовые представления (CBV) — обзор

| Класс | Что делает | Обязательные атрибуты |
|-------|-----------|----------------------|
| `ListView` | Список объектов | `model`, `template_name` |
| `CreateView` | Форма создания | `model`, `form_class`, `success_url` |
| `UpdateView` | Форма редактирования | `model`, `form_class`, `success_url` |
| `View` | Базовый (get/post методы вручную) | `get()` или `post()` |
| `LoginView` | Страница входа | `template_name` |

---

## 2. ListView — список объектов

```python
class ProductListView(ListView):
    model = Product
    template_name = "core/product_list.html"
    context_object_name = "products"  # имя переменной в шаблоне
    
    def get_queryset(self):
        # Переопределяем queryset (фильтрация, поиск, сортировка)
        return Product.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["extra"] = "значение"
        return context
```

### `get_queryset()` — как он работает

`ListView` вызывает `get_queryset()` один раз и кладёт результат в контекст под именем `context_object_name`. По умолчанию возвращает `Model.objects.all()`.

**Главное:** queryset — ленивый. Методы `.filter()`, `.order_by()`, `.select_related()` не выполняют SQL — они строят описание запроса. SQL выполняется один раз, когда Django рендерит шаблон и начинает итерацию по объектам.

```python
def get_queryset(self):
    # Шаг 1 — начало
    queryset = Product.objects.all().select_related("supplier", "category", "manufacturer")

    # Шаг 2 — поиск (если передан GET-параметр)
    search_query = self.request.GET.get("search", "")
    if search_query:
        queryset = queryset.filter(          # добавляет WHERE к queryset
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(manufacturer__name__icontains=search_query)
            | Q(category__name__icontains=search_query)
            | Q(article__icontains=search_query)
            | Q(supplier__name__icontains=search_query)
        )

    # Шаг 3 — фильтр по поставщику (если выбран)
    supplier_id = self.request.GET.get("supplier", "")
    if supplier_id and supplier_id != "all":
        queryset = queryset.filter(supplier_id=supplier_id)   # AND

    # Шаг 4 — сортировка (если выбрана)
    sort = self.request.GET.get("sort", "")
    if sort == "asc":
        queryset = queryset.order_by("quantity")
    elif sort == "desc":
        queryset = queryset.order_by("-quantity")

    return queryset  # SQL ещё не выполнен — всё ещё queryset
```

Каждый шаг — дополнительное условие к одному финальному SQL-запросу. Если пользователь ничего не ввёл, queryset остаётся `Product.objects.all()`.

### `select_related` в get_queryset

Без `select_related` при рендере шаблона `{{ product.supplier.name }}` выполнился бы отдельный SQL-запрос для **каждого** товара. С `select_related` всё загружается одним JOIN.

```python
# Без оптимизации (N+1 проблема):
Product.objects.all()
# → 1 запрос: SELECT * FROM product
# → N запросов: SELECT * FROM supplier WHERE id=? (для каждого товара)

# С оптимизацией:
Product.objects.all().select_related("supplier", "category", "manufacturer")
# → 1 запрос с тремя JOIN-ами
```

Для заказов используется `prefetch_related` — т.к. `items` это обратная FK (один заказ → много позиций):

```python
Order.objects.all()
    .select_related("pickup_point", "user")    # FK прямые → JOIN
    .prefetch_related("items__product")         # обратная FK → отдельный SELECT
    .order_by("-id")
```

`items__product` означает: prefetch `OrderItem`-ы через `items`, и для каждого из них select_related `Product`. Django делает это за 3 запроса вместо 1 + N + N×M.

### `get_context_data()` — дополнительные переменные для шаблона

`get_queryset()` кладёт результат только в одну переменную (`products`). Если шаблону нужно больше данных — используем `get_context_data()`:

```python
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)  # ← обязательно! иначе products не попадёт
    context["suppliers"] = Supplier.objects.all()     # список для фильтра-дропдауна
    context["current_search"] = self.request.GET.get("search", "")   # вернуть в инпут
    context["current_supplier"] = self.request.GET.get("supplier", "")
    context["current_sort"] = self.request.GET.get("sort", "")
    return context
```

Без `super()` в контексте не окажется ни `products`, ни стандартных переменных CBV.

---

## 3. CreateView / UpdateView

```python
class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm
    template_name = "core/product_form.html"
    success_url = reverse_lazy("product_list")  # куда редиректить после успеха
    
    def form_valid(self, form):
        messages.success(self.request, "Добавлено!")
        return super().form_valid(form)


class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "core/product_form.html"
    success_url = reverse_lazy("product_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True  # флаг для шаблона
        return context
```

---

## 3.1 get_context_data в CreateView/UpdateView

`get_context_data` работает одинаково во всех CBV. В `CreateView` он особенно полезен для передачи предварительного ID:

```python
class ProductCreateView(AdminRequiredMixin, CreateView):
    ...
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # MAX(id) из БД + 1 → предварительный ID для отображения в форме
        max_id = Product.objects.aggregate(Max("id"))["id__max"] or 0
        context["next_id"] = max_id + 1
        return context
```

`or 0` — защита от пустой таблицы: если товаров нет, `aggregate` вернёт `{"id__max": None}`.

---

## 4. View — кастомное представление (для удаления)

```python
from django.views import View
from django.shortcuts import get_object_or_404, redirect

class ProductDeleteView(View):
    def post(self, request, pk):         # только POST (из формы с CSRF)
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        return redirect("product_list")
```

Почему `View` а не `DeleteView`: нужен ручной контроль — перехват `ProtectedError` при удалении товара, который есть в заказах.

```python
class ProductDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            if product.photo:
                product.photo.delete(save=False)   # удалить файл с диска
            product.delete()                        # удалить из БД
            messages.success(request, f"Товар «{product.name}» успешно удалён")
        except ProtectedError:
            # Срабатывает когда ForeignKey(on_delete=PROTECT) запрещает удаление
            messages.error(request, f"Нельзя удалить «{product.name}»: есть связанные заказы")
        return redirect("product_list")
```

`product.photo.delete(save=False)` — удаляет файл с диска, `save=False` значит «не пересохранять объект в БД после удаления файла» (объект всё равно сейчас удалится).

---

## 5. Миксины — добавление поведения

Миксины ставятся **первыми** в списке родителей:
```python
class MyView(MixinA, MixinB, BaseView):
    ...
```

### AdminRequiredMixin — только администратор

```python
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role
            and self.request.user.role.name == "admin"
        )
```

### ManagerOrAdminMixin — менеджер или администратор

```python
class ManagerOrAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role
            and self.request.user.role.name in ("admin", "manager")
        )
```

---

## 6. Q-объекты — поиск по нескольким полям

```python
from django.db.models import Q

queryset.filter(
    Q(name__icontains=query)
    | Q(description__icontains=query)
    | Q(article__icontains=query)
    | Q(supplier__name__icontains=query)  # через JOIN на связанную FK-таблицу
)
```

`icontains` — содержит строку без учёта регистра (`ILIKE '%query%'` в PostgreSQL).

`|` — OR между условиями. Все `Q(...)` в одном `filter()` соединяются через OR, если между ними стоит `|`. Без `|` — через AND.

Поиск по FK-полям через `__`: `supplier__name__icontains` автоматически добавляет JOIN с таблицей `core_supplier`.

Подробнее о Q-объектах и всех lookup expressions → [Запросы к БД](orm-queries.md#5-q-объекты--or-и-and-в-одном-запросе)

---

## 6.1 Inline formset — форма с вложенными объектами

Используется в `OrderCreateView` / `OrderUpdateView` для добавления позиций заказа (OrderItem) прямо в форме заказа.

**Почему нельзя просто CreateView:**  
При создании заказа нужно сохранить сам `Order` И несколько `OrderItem`. `CreateView` умеет только одну форму. Поэтому переопределяем `get()` и `post()` вручную.

```python
class OrderCreateView(AdminRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = "core/order_form.html"
    success_url = reverse_lazy("order_list")

    def get(self, request, *args, **kwargs):
        self.object = None       # сигнал для CBV: объект ещё не создан
        form = self.get_form()   # пустая OrderForm
        item_formset = OrderItemFormSet()           # пустой формсет (extra=1 пустая строка)
        max_id = Order.objects.aggregate(Max("id"))["id__max"] or 0
        return self.render_to_response(
            self.get_context_data(form=form, item_formset=item_formset, next_id=max_id + 1)
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()                         # OrderForm с данными из POST
        item_formset = OrderItemFormSet(request.POST)  # формсет с данными из POST
        if form.is_valid() and item_formset.is_valid():
            self.object = form.save()          # 1. сохранить заказ → получаем Order с id
            item_formset.instance = self.object  # 2. привязать формсет к этому заказу
            item_formset.save()                 # 3. сохранить все OrderItem
            messages.success(request, "Заказ успешно добавлен")
            return redirect(self.success_url)
        # Если форма невалидна — вернуть с ошибками
        return self.render_to_response(
            self.get_context_data(form=form, item_formset=item_formset)
        )
```

**При редактировании** формсет передаёт `instance=self.object` — тогда он загружает существующие позиции и позволяет их менять или удалять (`can_delete=True`):

```python
def get(self, request, *args, **kwargs):
    self.object = self.get_object()   # получаем существующий заказ
    form = self.get_form()
    item_formset = OrderItemFormSet(instance=self.object)  # загружает текущие позиции
    return self.render_to_response(
        self.get_context_data(form=form, item_formset=item_formset, is_edit=True)
    )
```

**В шаблоне** формсет рендерится через таблицу:

```html
{{ item_formset.management_form }}  {# скрытые поля с количеством строк — обязательно! #}
{% for item_form in item_formset %}
<tr>
    <td>{{ item_form.product }}</td>   {# дропдаун из Product #}
    <td>{{ item_form.count }}</td>
    <td>{% if item_form.instance.pk %}{{ item_form.DELETE }}{% endif %}</td>
    {{ item_form.id }}   {# скрытый id для UPDATE, а не INSERT #}
</tr>
{% endfor %}
```

`management_form` — это скрытые поля `TOTAL_FORMS`, `INITIAL_FORMS`, `MIN_NUM_FORMS`, `MAX_NUM_FORMS`. Без них Django не поймёт сколько строк формсета было отправлено и выдаст ошибку.

---

## 7. messages — три типа уведомлений

```python
from django.contrib import messages

messages.success(request, "Операция выполнена успешно")  # зелёный
messages.error(request, "Ошибка: нельзя удалить")        # красный
messages.warning(request, "Внимание: ...")               # жёлтый
messages.info(request, "Информация: ...")                 # синий
```

В шаблоне (base.html):
```html
{% for message in messages %}
<div class="alert alert-{{ message.tags }}">{{ message }}</div>
{% endfor %}
```

---

## 8. Матрица доступа по ролям

| Функция | Гость | Клиент | Менеджер | Администратор |
|---------|-------|--------|---------|---------------|
| Просмотр товаров | ✓ | ✓ | ✓ | ✓ |
| Поиск/фильтр/сортировка | — | — | ✓ | ✓ |
| Просмотр заказов | — | — | ✓ | ✓ |
| Добавление товара | — | — | — | ✓ |
| Редактирование товара | — | — | — | ✓ |
| Удаление товара | — | — | — | ✓ |
| CRUD заказов | — | — | — | ✓ |

---

## 9. Полный код — core/views.py

```python
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Max, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from .forms import OrderForm, OrderItemFormSet, ProductForm
from .models import Order, Product, Supplier


class UserLoginView(LoginView):
    template_name = "core/login.html"


class ProductListView(ListView):
    model = Product
    template_name = "core/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        queryset = Product.objects.all().select_related("supplier")
        search_query = self.request.GET.get("search", "")
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(description__icontains=search_query)
                | Q(manufacturer__icontains=search_query)
                | Q(category__icontains=search_query)
                | Q(article__icontains=search_query)
                | Q(supplier__name__icontains=search_query)
            )
        supplier_id = self.request.GET.get("supplier", "")
        if supplier_id and supplier_id != "all":
            queryset = queryset.filter(supplier_id=supplier_id)
        sort = self.request.GET.get("sort", "")
        if sort == "asc":
            queryset = queryset.order_by("quantity")
        elif sort == "desc":
            queryset = queryset.order_by("-quantity")
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["suppliers"] = Supplier.objects.all()
        context["current_search"] = self.request.GET.get("search", "")
        context["current_supplier"] = self.request.GET.get("supplier", "")
        context["current_sort"] = self.request.GET.get("sort", "")
        return context


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role
            and self.request.user.role.name == "admin"
        )


class ManagerOrAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return (
            self.request.user.is_authenticated
            and self.request.user.role
            and self.request.user.role.name in ("admin", "manager")
        )


class ProductCreateUpdateMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_suppliers"] = Supplier.objects.all()
        return context


class ProductCreateView(AdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "core/product_form.html"
    success_url = reverse_lazy("product_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Вычисляем предварительный ID для отображения в форме
        max_id = Product.objects.aggregate(Max("id"))["id__max"] or 0
        context["next_id"] = max_id + 1
        return context

    def form_valid(self, form):
        messages.success(self.request, "Товар успешно добавлен")
        return super().form_valid(form)


class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "core/product_form.html"
    success_url = reverse_lazy("product_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, "Товар успешно обновлён")
        return super().form_valid(form)


class ProductDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        try:
            if product.photo:
                product.photo.delete(save=False)
            product.delete()
            messages.success(request, f"Товар «{product.name}» успешно удалён")
        except ProtectedError:
            # ForeignKey(on_delete=PROTECT) не даст удалить товар из заказа на уровне БД
            messages.error(
                request,
                f"Невозможно удалить товар «{product.name}»: он используется в заказах. "
                "Сначала удалите связанные заказы.",
            )
        return redirect("product_list")


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

    def get(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        item_formset = OrderItemFormSet()
        max_id = Order.objects.aggregate(Max("id"))["id__max"] or 0
        return self.render_to_response(
            self.get_context_data(form=form, item_formset=item_formset, next_id=max_id + 1)
        )

    def post(self, request, *args, **kwargs):
        self.object = None
        form = self.get_form()
        item_formset = OrderItemFormSet(request.POST)
        if form.is_valid() and item_formset.is_valid():
            self.object = form.save()
            item_formset.instance = self.object  # привязываем позиции к заказу
            item_formset.save()
            messages.success(request, "Заказ успешно добавлен")
            return redirect(self.success_url)
        return self.render_to_response(
            self.get_context_data(form=form, item_formset=item_formset)
        )


class OrderUpdateView(AdminRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = "core/order_form.html"
    success_url = reverse_lazy("order_list")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        item_formset = OrderItemFormSet(instance=self.object)
        return self.render_to_response(
            self.get_context_data(form=form, item_formset=item_formset, is_edit=True)
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        item_formset = OrderItemFormSet(request.POST, instance=self.object)
        if form.is_valid() and item_formset.is_valid():
            form.save()
            item_formset.save()
            messages.success(request, "Заказ успешно обновлён")
            return redirect(self.success_url)
        return self.render_to_response(
            self.get_context_data(form=form, item_formset=item_formset, is_edit=True)
        )


class OrderDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        order_id = order.id
        order.delete()
        messages.success(request, f"Заказ №{order_id} успешно удалён")
        return redirect("order_list")
```

---

## 10. Полный код — config/urls.py (финальный)

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path

from core.views import (
    OrderCreateView, OrderDeleteView, OrderListView, OrderUpdateView,
    ProductCreateView, ProductDeleteView, ProductListView, ProductUpdateView,
    UserLoginView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("products/", ProductListView.as_view(), name="product_list"),
    path("products/add/", ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product_delete"),
    path("orders/", OrderListView.as_view(), name="order_list"),
    path("orders/add/", OrderCreateView.as_view(), name="order_create"),
    path("orders/<int:pk>/edit/", OrderUpdateView.as_view(), name="order_edit"),
    path("orders/<int:pk>/delete/", OrderDeleteView.as_view(), name="order_delete"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### Все URL-паттерны

| URL | name | Доступ |
|-----|------|--------|
| `/` | `login` | все |
| `/logout/` | `logout` | все (POST) |
| `/products/` | `product_list` | все |
| `/products/add/` | `product_create` | admin |
| `/products/<pk>/edit/` | `product_edit` | admin |
| `/products/<pk>/delete/` | `product_delete` | admin (POST) |
| `/orders/` | `order_list` | manager, admin |
| `/orders/add/` | `order_create` | admin |
| `/orders/<pk>/edit/` | `order_edit` | admin |
| `/orders/<pk>/delete/` | `order_delete` | admin (POST) |

В шаблоне: `{% url 'product_edit' product.id %}` → `/products/5/edit/`
