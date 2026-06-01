# Views и URL-маршрутизация

← [Назад к пайплайну](README.md)

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

Почему `View` а не `DeleteView`: нужен ручной контроль — проверка ссылочной целостности перед удалением.

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
    | Q(supplier__name__icontains=query)  # через JOIN на связанную таблицу
)
```

`icontains` — содержит строку (без учёта регистра).

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
