import re

with open("api/modules/catalog/infrastructure/adapters/driver/rest/views.py", "r") as f:
    content = f.read()

replacement = """        query = ListProductsQuery(category_id=category_id, state=state)
        container = get_app_catalog_container()
        results = container.list_products.execute(query)

        response_data = []
        for r in results:
            snapshot = container.product_query.find_product(r.id)
            d = dataclasses.asdict(r)
            if snapshot:
                d['variants'] = [dataclasses.asdict(v) for v in snapshot.variants]
                d['modifierGroups'] = [dataclasses.asdict(g) for g in snapshot.modifier_groups]
            else:
                d['variants'] = []
                d['modifierGroups'] = []
            response_data.append(d)

        return Response(response_data)"""

content = re.sub(r'        query = ListProductsQuery.*?return Response\(\[dataclasses\.asdict\(r\) for r in results\]\)', replacement, content, flags=re.DOTALL)

with open("api/modules/catalog/infrastructure/adapters/driver/rest/views.py", "w") as f:
    f.write(content)
