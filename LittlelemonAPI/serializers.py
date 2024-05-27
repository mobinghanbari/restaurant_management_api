from rest_framework import serializers
from .models import Category, MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token 

class UserSerializer (serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class CategorySerializer (serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug','title']


class MenuItemSerializer (serializers.ModelSerializer):
    category_id = serializers.IntegerField(write_only=True)

    category = CategorySerializer(read_only=True)

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id']



class CartSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    user = UserSerializer(read_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.IntegerField(write_only=True)


    class Meta:
        model = Cart
        fields = ['id', 'user', 'user_id', 'menuitem', 'menuitem_id', 'quantity', 'unit_price', 'price']
        extra_kwargs = {
            'price': {'read_only': True},
            'unit_price': {'read_only': True}
        }
        
    def create(self, validated_data):
        menuitem = MenuItem.objects.get(id=validated_data['menuitem_id'])
        validated_data['unit_price'] = menuitem.price  # مقدار unit_price از MenuItem دریافت می‌شود
        validated_data['price'] = validated_data['quantity'] * validated_data['unit_price']
        return super().create(validated_data)

    def update(self, instance, validated_data):
        menuitem = MenuItem.objects.get(id=validated_data['menuitem_id'])
        validated_data['unit_price'] = menuitem.price
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.unit_price = validated_data.get('unit_price', instance.unit_price)
        instance.price = instance.quantity * instance.unit_price
        instance.save()
        return instance


class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    delivery_crew = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date']


class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    menuitem = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'quantity', 'unit_price', 'price']


class UpdateOrderSerializer(serializers.ModelSerializer):

    class Meta:
        model = Order
        fields = ['status', 'delivery_crew']



class DeliveryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']