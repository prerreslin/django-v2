from django.urls import path, include
from .views.views import index, about, product_details, cart_add, cart_detail, cart_delete, checkout
from rest_framework.routers import DefaultRouter
from .views.product import ProductViewSet
from .views.category import CategoryViewSet

app_name = 'products'
router = DefaultRouter()
router.register(r"products", viewset=ProductViewSet)
router.register(r"categories", viewset=CategoryViewSet)

urlpatterns = [
    path('', index, name='index'),
    path('about/', about, name='about'),
    path('product/<int:product_id>/', product_details, name='product_details'),
    path('cart_add/<int:product_id>/', cart_add, name='cart_add'),
    path("cart_detail/", cart_detail, name="cart_detail"),
    path('cart_delete/<int:product_id>/', cart_delete, name="cart_delete"),
    path("checkout/", checkout, name="checkout"),
    
]

urlpatterns += router.urls