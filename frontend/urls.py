from django.urls import path

from frontend.views import home, auth_login, auth_logout, register, cart, add_to_cart, increase_quantity, \
    decrease_quantity, remove_from_cart, clear_cart, proceed_to_checkout, place_order

urlpatterns = [
    path('', home, name="home"),
    path('login', auth_login, name='login'),
    path('logout/', auth_logout, name='logout'),
    path('register', register, name='register'),
    path('cart', cart, name='cart'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/increase/<int:id>/', increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:id>/', decrease_quantity, name='decrease_quantity'),
    path('cart/remove/<int:id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', clear_cart, name='clear_cart'),
    path('proceed_to_checkout/', proceed_to_checkout, name='proceed_to_checkout'),
    path('place-order/', place_order, name='place_order'),
]