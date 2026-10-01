from django.urls import path

from .views import (
    auth,
    clients,
    configuration,
    conversations,
    coupons,
    dashboard,
    orders,
    payments,
    products,
    kitchen,
)

urlpatterns = [
    path("login/", auth.LoginView.as_view(), name="login"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
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
    path("pedidos/cotizacion/", orders.wizard_quote, name="orders_quote"),
    path("pedidos/cupon/validar/", orders.wizard_validate_coupon, name="orders_validate_coupon"),
    path("pedidos/cliente/crear/", orders.orders_client_create, name="orders_client_create"),
    path("pedidos/nuevo/cupon/", orders.wizard_coupon, name="orders_new_coupon"),
    path("pedidos/nuevo/confirmar/", orders.wizard_confirm, name="orders_new_confirm"),
    path("pedidos/nuevo/producto/<str:product_id>/configurar/", orders.product_config_modal, name="orders_new_product_config"),

    path("pedidos/<str:order_id>/", orders.detail, name="order_detail"),
    path("pedidos/<str:order_id>/estado/", orders.change_status, name="order_change_status"),
    path("pedidos/<str:order_id>/cancelar/", orders.cancel, name="order_cancel"),
    path("cocina/", kitchen.index, name="kitchen"),

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

    path("productos/<str:product_id>/variantes/guardar/", products.variant_save, name="product_variant_save"),
    path("productos/<str:product_id>/opcionales/guardar/", products.modifier_group_save, name="product_modifier_group_save"),
    path("ingredientes/guardar/", products.ingredient_save, name="ingredient_save"),

    path("variantes/<str:variant_id>/ingredientes/guardar/", products.variant_ingredients_save, name="product_variant_ingredients_save"),
    path("variantes/<str:variant_id>/precio/guardar/", products.variant_price_save, name="product_variant_price_save"),

    path("opcionales/<str:group_id>/opcion/guardar/", products.modifier_option_save, name="product_modifier_option_save"),
    path("opcionales/<str:group_id>/actualizar/", products.modifier_group_update, name="product_modifier_group_update"),
    path("opcionales/<str:group_id>/eliminar/", products.modifier_group_delete, name="product_modifier_group_delete"),
    path("opcionales/opcion/<str:option_id>/eliminar/", products.modifier_option_delete, name="product_modifier_option_delete"),


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
    path("cupones/<str:coupon_id>/editar/", coupons.update, name="coupon_update"),
    path("cupones/<str:coupon_id>/estado/", coupons.toggle, name="coupon_toggle"),
    path("cupones/<str:coupon_id>/", coupons.detail, name="coupon_detail"),

    # Conversations
    path("conversaciones/", conversations.index, name="conversations"),
    path("conversaciones/<str:conversation_id>/", conversations.detail, name="conversation_detail"),
    path("conversaciones/<str:conversation_id>/cliente/", conversations.client_message, name="conversation_client_message"),
    path("conversaciones/<str:conversation_id>/humano/", conversations.operator_message, name="conversation_operator_message"),
    path("conversaciones/<str:conversation_id>/tomar/", conversations.takeover, name="conversation_takeover"),
    path("conversaciones/<str:conversation_id>/devolver/", conversations.release, name="conversation_release"),

    # Configuration
    path("configuracion/", configuration.index, name="configuration"),
    path("configuracion/direccion/", configuration.index, {"tab": "address"}, name="configuration_address_view"),
    path("configuracion/envios/", configuration.index, {"tab": "delivery"}, name="configuration_delivery_view"),
    path("configuracion/general/", configuration.save_general, name="configuration_general"),
    path("configuracion/direccion/crear/", configuration.create_address, name="configuration_address_create"),
    path("configuracion/direccion/<str:address_id>/eliminar/", configuration.delete_address, name="configuration_address_delete"),
    path("configuracion/envios/guardar/", configuration.save_delivery, name="configuration_delivery"),
]
