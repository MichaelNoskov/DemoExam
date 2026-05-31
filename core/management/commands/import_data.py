import csv
import os
from typing import Any

from django.core.management.base import BaseCommand

from core.models import Order, OrderItem, PickupPoint, Product, Role, Supplier, User


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        base_path = "part_1/add_2/import/"

        # pickup points
        with open(os.path.join(base_path, "pp.csv")) as f:
            reader = csv.DictReader(f, ["address"])
            for row in reader:
                print(row)
                PickupPoint.objects.get_or_create(address=row["address"])

        # products and suppliers
        with open(os.path.join(base_path, "products.csv"), encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(row)
                if not row:
                    continue

                sup_obj, _ = Supplier.objects.get_or_create(name=row["supplier"])
                row["supplier"] = sup_obj
                
                if row.get("photo") and not row["photo"].startswith("products/"):
                    row["photo"] = f"products/{row['photo']}"
                
                Product.objects.update_or_create(article=row["article"], defaults=row)

        # users
        with open(os.path.join(base_path, "users.csv"), encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(row)
                if not row:
                    continue

                role_obj, _ = Role.objects.get_or_create(name=row["role"])
                if not User.objects.filter(username=row["login"]).exists():
                    user = User.objects.create(
                        username=row["login"], full_name=row["full_name"], role=role_obj
                    )
                    user.set_password(str(row["password"]).strip())
                    user.save()

        # orders
        with open(os.path.join(base_path, "orders.csv"), encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(row)
                if not row:
                    continue

                pp_obj = (
                    PickupPoint.objects.get(id=row["pp"])
                    if PickupPoint.objects.filter(id=row["pp"]).exists()
                    else PickupPoint.objects.first()
                )
                order, created = Order.objects.get_or_create(
                    id=row["id"],
                    defaults={
                        "order_date": row["order_date"],
                        "delivery_date": row["delivery_date"],
                        "client_name": row["client_name"],
                        "pickup_code": row["pickup_code"],
                        "status": row["status"],
                        "pickup_point": pp_obj,
                    },
                )
                if created:
                    items = row["items"].split(",")
                    for i in range(0, len(items), 2):
                        art = items[i].strip()
                        try:
                            prod = Product.objects.get(article=art)
                            OrderItem.objects.create(
                                order=order, product=prod, count=int(items[i + 1])
                            )
                        except Exception:
                            pass


