from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.contrib.auth import login, authenticate
from rest_framework.response import Response
from django.conf import settings

from ..forms import RegisterForm, LoginForm
from ...utils.email import send_email_confirm
from products.models import Cart, Product, CartItem




class AccountViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        form = RegisterForm(request.data)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save()
            login(request, user)
            send_email_confirm(request, user, user.email)
            return Response({'status': 'User was registered'}, status=201)
        else:
            return Response({"errors":form.errors}, status=400)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        form = LoginForm(request.data)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                login(request, user)
                session_cart = request.session.get(settings.CART_SESSION_ID, default={})
                if session_cart:
                    cart = request.user.cart
                    for p_id, amount in session_cart.items():
                        product = Product.objects.get(id=p_id)
                        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                        cart_item.amount = cart_item + amount if not created else amount
                        cart_item.save()
                    session_cart.clear()
                    return Response({"message":"Successfully logged in"}, status=200)
                
            return Response({"error":"Invalid credentials"}, status=400)