from django.urls import path

from .views import (
    clients,
    configuration,
    conversations,
    coupons,
    dashboard,
    orders,
    payments,
    products,
)

urlpatterns = [
    path("", dashboard.index, name="dashboard"),

    # Orders
    path("pedidos/", orders.index, name="orders"),
    path("pedidos/tabla/", orders.table, name="orders_table"),
    path("pedidos/listado/", orders.listing, name="orders_listing"),
    path("pedidos/listado/grid/", orders.listing_grid, name="orders_listing_grid"),
    path("pedidos/nuevo/", orders.new_order, name="orders_new"),
    path("pedidos/nuevo/cliente/buscar/", orders.wizard_client_search, name="orders_new_client_search"),
    path("pedidos/nuevo/cliente/crear/", orders.wizard_client_create, name="orders_new_client_create"),
    path("pedidos/nuevo/productos/buscar/", orders.wizard_product_search, name="orders_new_product_search"),
    path("pedidos/nuevo/carrito/", orders.wizard_cart, name="orders_new_cart"),
    path("pedidos/nuevo/cupon/", orders.wizard_coupon, name="orders_new_coupon"),
    path("pedidos/nuevo/confirmar/", orders.wizard_confirm, name="orders_new_confirm"),
    path("pedidos/<str:order_id>/", orders.detail, name="order_detail"),
    path("pedidos/<str:order_id>/estado/", orders.change_status, name="order_change_status"),
    path("pedidos/<str:order_id>/cancelar/", orders.cancel, name="order_cancel"),

    # Products & categories
    path("productos/", products.index, name="products"),
    path("productos/tabla/", products.table, name="products_table"),
    path("productos/categorias/", products.categories, name="categories"),
    path("productos/categorias/guardar/", products.save_category, name="category_save"),
    path("productos/nuevo/", products.form, name="product_new"),
    path("productos/guardar/", products.save, name="product_create"),
    path("productos/<str:product_id>/", products.detail, name="product_detail"),
    path("productos/<str:product_id>/eliminar/", products.delete, name="product_delete"),
    path("productos/<str:product_id>/editar/", products.form, name="product_edit"),
    path("productos/<str:product_id>/guardar/", products.save, name="product_save"),
    path("productos/<str:product_id>/disponibilidad/", products.toggle_availability, name="product_toggle"),
    path("productos/<str:product_id>/precio/", products.add_price, name="product_add_price"),

    # Payments
    path("pagos/", payments.index, name="payments"),
    path("pagos/tabla/", payments.table, name="payments_table"),
    path("pagos/<str:payment_id>/", payments.detail, name="payment_detail"),

    # Clients
    path("clientes/", clients.index, name="clients"),
    path("clientes/tabla/", clients.table, name="clients_table"),
    path("clientes/<str:client_id>/", clients.detail, name="client_detail"),
    path("clientes/<str:client_id>/eliminar/", clients.delete, name="client_delete"),

    # Coupons
    path("cupones/", coupons.index, name="coupons"),
    path("cupones/nuevo/", coupons.form, name="coupon_new"),
    path("cupones/guardar/", coupons.save, name="coupon_save"),
    path("cupones/<str:coupon_id>/", coupons.detail, name="coupon_detail"),

    # Conversations
    path("conversaciones/", conversations.index, name="conversations"),
    path("conversaciones/<str:conversation_id>/", conversations.detail, name="conversation_detail"),

    # Configuration
    path("configuracion/", configuration.index, name="configuration"),
    path("configuracion/general/", configuration.save_general, name="configuration_general"),
    path("configuracion/envios/", configuration.save_delivery, name="configuration_delivery"),
]
