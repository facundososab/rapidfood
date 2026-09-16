import re

with open("ui/panel/services/mock_client.py", "r") as f:
    content = f.read()

replacement = """        p = dtos.Product(id=db.next_id("prod"), name=payload["name"],
                         description=payload["description"],
                         available=payload.get("available", True),
                         categoryId=payload["category_id"], imageUrl=payload.get("image_url"))
        import uuid
        from decimal import Decimal as D
        default_var = dtos.Variant(id=str(uuid.uuid4()), name="Default", available=True, currentPrice=D(str(payload.get("price") or 0)))
        p.variants = [default_var]
        self.variants.append(default_var)
        p.category = next((c for c in db.categories if c.id == p.categoryId), None)
        if payload.get("price"):
            pr = dtos.Price(id=db.next_id("price"), productId=p.id,
                            sinceDate=datetime.now(), price=D(str(payload["price"])))
            db.prices.append(pr)
        db.products.append(p)
        return p"""

content = re.sub(r'        p = dtos\.Product\(id=db\.next_id\("prod"\).*?return p', replacement, content, flags=re.DOTALL)

with open("ui/panel/services/mock_client.py", "w") as f:
    f.write(content)
