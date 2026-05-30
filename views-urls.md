# Views и URL-маршрутизация

← [Назад к пайплайну](README.md)

---

## 1. Классовые представления (CBV) — обзор

Django предоставляет готовые классы для типичных операций. Не нужно писать всё с нуля.

| Класс | Что делает | Обязательные атрибуты |
|-------|-----------|----------------------|
| `View` | Базовый класс | `get()` или `post()` методы |
| `TemplateView` | Показать шаблон | `template_name` |
| `ListView` | Список объектов | `model`, `template_name` |
| `DetailView` | Один объект по pk | `model`, `template_name` |
| `CreateView` | Форма создания | `model`, `form_class`, `success_url` |
| `UpdateView` | Форма редактирования | `model`, `form_class`, `success_url` |
| `DeleteView` | Удаление | `model`, `success_url` |
| `LoginView` | Страница входа | `template_name` |

---

## 2. ListView — список объектов

```python
from django.views.generic import ListView

class ProductListView(ListView):
    model = Product               # модель
    template_name = "core/product_list.html"
    context_object_name = "products"  # имя переменной в шаблоне
    
    def get_queryset(self):
        # Переопределяем queryset (фильтрация, сортировка)
        return Product.objects.all()
    
    def get_context_data(self, **kwargs):
        # Добавляем данные в контекст шаблона
        context = super().get_context_data(**kwargs)
        context["extra_data"] = "значение"
        return context
```

В шаблоне: `{% for product in products %}` (имя = `context_object_name`)

---

## 3. CreateView — форма создания

```python
from django.views.generic import CreateView
from django.urls import reverse_lazy

class ProductCreateView(CreateView):
    model = Product
    form_class = ProductForm          # какая форма использовать
    template_name = "core/product_form.html"
    success_url = reverse_lazy("product_list")  # куда редиректить после успеха
    
    def form_valid(self, form):
        # Вызывается когда форма валидна
        messages.success(self.request, "Товар успешно добавлен")
        return super().form_valid(form)
```

> `reverse_lazy` вместо `reverse` — потому что URL конфигурация ещё не загружена при импорте класса.

---

## 4. UpdateView — форма редактирования

```python
from django.views.generic import UpdateView

class ProductUpdateView(UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "core/product_form.html"
    success_url = reverse_lazy("product_list")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True   # для шаблона: знать что это редактирование
        return context
    
    def form_valid(self, form):
        messages.success(self.request, "Товар успешно обновлен")
        return super().form_valid(form)
```

URL для UpdateView должен содержать `<int:pk>` — Django сам подставит объект.

---

## 5. LoginView — страница входа

```python
from django.contrib.auth.views import LoginView

class UserLoginView(LoginView):
    template_name = "core/login.html"
    # После успешного входа → LOGIN_REDIRECT_URL из settings.py
```

Встроенный LoginView:
- Сам обрабатывает форму username/password
- Сам хеширует и проверяет пароль в БД
- Сам создаёт сессию

---

## 6. Миксины — добавление поведения

Миксины подмешиваются **перед** основным классом:
```python
class MyView(MixinA, MixinB, BaseView):
    ...
```

### UserPassesTestMixin — проверка произвольного условия

```python
from django.contrib.auth.mixins import UserPassesTestMixin

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        # Возвращает True = доступ разрешён, False = редирект на login
        return (
            self.request.user.is_authenticated
            and self.request.user.role
            and self.request.user.role.name == "admin"
        )
```

Использование:
```python
class ProductCreateView(AdminRequiredMixin, CreateView):
    ...  # Только для admin
```

### LoginRequiredMixin — только авторизованные

```python
from django.contrib.auth.mixins import LoginRequiredMixin

class SomeView(LoginRequiredMixin, ListView):
    ...
```

---

## 7. Q-объекты — сложные запросы с OR

```python
from django.db.models import Q

# Обычный AND (через запятую):
Product.objects.filter(name="boots", category="men")

# OR через Q-объекты:
Product.objects.filter(
    Q(name__icontains=query) | Q(description__icontains=query)
)

# Комбинация:
Product.objects.filter(
    Q(name__icontains=q) | Q(description__icontains=q),
    quantity__gt=0  # AND в конце
)
```

### Lookups (суффиксы фильтрации)

| Суффикс | Что делает | Пример |
|---------|-----------|--------|
| `__icontains` | Содержит (без учёта регистра) | `name__icontains="boot"` |
| `__contains` | Содержит (с учётом регистра) | |
| `__exact` | Равно | `status__exact="active"` |
| `__gt` / `__lt` | Больше / меньше | `price__gt=1000` |
| `__gte` / `__lte` | >= / <= | `quantity__gte=1` |
| `__in` | В списке | `id__in=[1,2,3]` |
| `__isnull` | Равно NULL | `photo__isnull=True` |

---

## 8. select_related — оптимизация JOIN

Без `select_related` каждый `product.supplier.name` = отдельный SQL-запрос:
```python
# N+1 проблема (30 товаров = 31 запрос):
products = Product.objects.all()
for p in products:
    print(p.supplier.name)  # каждый раз запрос к БД!

# С select_related (1 запрос с JOIN):
products = Product.objects.all().select_related("supplier")
for p in products:
    print(p.supplier.name)  # данные уже в памяти
```

---

## 9. Полный код — core/views.py

```python
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from .forms import ProductForm
from .models import Product, Supplier


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


class ProductCreateUpdateMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_suppliers"] = Supplier.objects.all()
        return context


class ProductCreateView(AdminRequiredMixin, ProductCreateUpdateMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "core/product_form.html"
    success_url = reverse_lazy("product_list")

    def form_valid(self, form):
        messages.success(self.request, "Товар успешно добавлен")
        return super().form_valid(form)


class ProductUpdateView(AdminRequiredMixin, ProductCreateUpdateMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "core/product_form.html"
    success_url = reverse_lazy("product_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, "Товар успешно обновлен")
        return super().form_valid(form)
```

---

## 10. Полный код — config/urls.py

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path

from core.views import (
    ProductCreateView,
    ProductListView,
    ProductUpdateView,
    UserLoginView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", UserLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("products/", ProductListView.as_view(), name="product_list"),
    path("products/add/", ProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/edit/", ProductUpdateView.as_view(), name="product_edit"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### URL-паттерны

| Паттерн | name | View |
|---------|------|------|
| `/` | `login` | UserLoginView |
| `/logout/` | `logout` | LogoutView |
| `/products/` | `product_list` | ProductListView |
| `/products/add/` | `product_create` | ProductCreateView |
| `/products/5/edit/` | `product_edit` | ProductUpdateView |

В шаблоне: `{% url 'product_edit' product.id %}` → `/products/5/edit/`

---

## 11. Матрица доступа по ролям

| Функция | Гость | Клиент | Менеджер | Администратор |
|---------|-------|--------|---------|---------------|
| Просмотр товаров | ✓ | ✓ | ✓ | ✓ |
| Поиск/фильтр/сортировка | — | — | ✓ | ✓ |
| Добавление товара | — | — | — | ✓ |
| Редактирование товара | — | — | — | ✓ |
| Удаление товара | — | — | — | ✓ |

В шаблоне реализуется через:
```html
{% if user.role.name == "admin" or user.role.name == "manager" %}
    <!-- поиск и фильтры -->
{% endif %}

{% if user.role.name == "admin" %}
    <!-- кнопки добавления/редактирования -->
{% endif %}
```
