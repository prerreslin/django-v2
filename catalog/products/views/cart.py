from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet
from rest_framework.decorators import action
from ..models import Cart, CartItem, Product
from ..serializers.cart_serializer import CartSerializer, CartItemSerializer
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.response import Response
from serializers.product_serializer import ProductSerializer


class CartViewSet(ViewSet):
    @action(detail=False, methods=['post'], url_path='add-product/<int:product_id>')
    def add_product(self, request, product_id=None):
        product = get_object_or_404(Product, id=product_id)
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=request.user)
            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            if created:
                cart_item.amount = 1
            else:
                cart_item.amount += 1
            cart_item.save()
        else:
            cart = request.session.get(settings.CART_SESSION_ID, default={})
            cart[str(product_id)] = cart.get(str(product_id), 0) + 1
        return Response({'status': f'product with id {product_id} was added to cart'},status=200)
    
    @action(detail=False, methods=['get'], url_path='get-caart-items/')
    def details(self, request):
        if request.user.is_authenticated:
            cart = request.user.cart
            return CartSerializer(cart).data
        else:
            cart = request.session.get(settings.CART_SESSION_ID, default={})
            products = Product.objects.filter(id__in=cart.keys())
            items = []
            total = 0
            for product in products:
                data = ProductSerializer(product).data
                amount = cart.get(str(product.id))
                item_total = (product.discount_price or product.price) * amount
                items.append({
                    'product': data,
                    'amount': amount,
                    'item_total': item_total,
                    'cart': None,
                })
                total += item_total
            return Response({'items': items, 'total': total}, status=200)