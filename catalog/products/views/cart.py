from rest_framework.viewsets import ReadOnlyModelViewSet, ViewSet
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.response import Response
from serializers.product_serializer import ProductSerializer

from ...utils.email import send_order_confirmation_email
from ..models import Cart, CartItem, Product, Payment, Order
from ..serializers.cart_serializer import CartSerializer, CartItemSerializer
from ..forms import OrderCreateForm
from ..models import OrderItem


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
    
    @action(detail=False, methods=['post'], url_path='cart-checkout/')
    def checkout(self, request):
        if request.user.is_authenticated:
            cart = request.user.cart

            if not cart or cart.items.count() == 0:
                return Response({'status': 'cart is empty'}, status=400)
        
        else:
            cart = request.session.get(settings.CART_SESSION_ID, default={})
            if not cart:
                return Response({'status': 'cart is empty'}, status=400)
            
        form = OrderCreateForm(request.data)

        if not form.is_valid():
            return Response({'errors': form.errors}, status=400)
        
        order = form.save(commit=False)

        if request.user.is_authenticated:
            form.user = request.user

        order.save()

        if request.user.is_authenticated:
            cart_items = order.user.cart.items.select_related('product').all()
        
        else:
            cart_items = [{'product' : Product.objects.get(id=int(p_id)), 'amount' : a} for p_id, a in cart.items()]
            items = OrderItem.objects.bulk_create([
                OrderItem(order = order, 
                        product = item.product, 
                        amount = item.amount,
                        price = item.discount_price or item.price)
                for item in cart_items]
            )
        
        method = form.cleaned_data.get('method')
        total = sum(item.item_total for item in cart_items)
        if method != "cash":
            Payment.objects.create(
                order = order,
                provider = method,
                amount = total
            )
        else:
            order.status = Order.Status.PROCESSING
            order.save()

        if request.user.is_authenticated:
            request.user.cart.items.all().delete()
        
        else:
            cart.clear()
        
        send_order_confirmation_email(order)
        
        return Response({'status': f'Order {order.id} is created'}, status=200)
