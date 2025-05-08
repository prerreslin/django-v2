from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field, OpenApiTypes
from rest_framework import serializers

from ..models import Product


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(read_only=True)
    discount_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'stock', 'price', 'available', 'category', 'nomenclature', 'created_at', 'rating', 'discount', 'attributes', 'discount_price']
    
    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_discount_price(self, obj):
        return obj.discount_price