from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token 
from rest_framework.pagination import PageNumberPagination
from rest_framework import generics, permissions
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import NotFound
from .models import MenuItem, Cart, Order, OrderItem, Category
from .serializers import CartSerializer, MenuItemSerializer, UserSerializer, OrderSerializer, OrderItemSerializer, UpdateOrderSerializer, DeliveryUpdateSerializer, CategorySerializer
from datetime import datetime
import random


class UserTypeCheck(permissions.BasePermission):
    """
    Custom permission to only allow managers to create, update, or delete objects.
    """
    def has_permission(self, request, view):
        # Allow read-only permissions for non-manager users
        if request.method == 'GET':
            return True
        
        # Allow create, update, or delete actions only for managers
        return request.user.groups.filter(name='Manager').exists()

    def has_object_permission(self, request, view, obj):
        # Allow read-only permissions for non-manager users
        if request.method == 'GET':
            return True
        
        # Allow create, update, or delete actions only for managers
        return request.user.groups.filter(name='Manager').exists()



class OnlyManager(permissions.BasePermission):
    """
    Custom permission to only allow only managers to do operation.
    """

    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name='Manager').exists()


class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [UserTypeCheck]
    throttle_classes = [UserRateThrottle]



class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [UserTypeCheck]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        queryset =  super().get_queryset()
        title = self.request.query_params.get('title')
        ordering = self.request.query_params.get('ordering')

        if title:
            queryset = queryset.filter(title__icontains=title)

        if ordering:
            ordering_list = ordering.split(',')
            queryset = queryset.order_by(*ordering_list)
        
        return queryset


class MenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [UserTypeCheck]
    throttle_classes = [UserRateThrottle]


class ManagerView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [OnlyManager]
    throttle_classes = [UserRateThrottle]

    def list(self, request, *args, **kwargs):
        users = self.queryset.filter(groups__name='Manager') 
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
    
  
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')

        if not username:
            return Response({'detail': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'detail': 'There is no user with the given username'}, status=status.HTTP_404_NOT_FOUND)

        manager_group = Group.objects.get(name='Manager')
        if manager_group in user.groups.all():
            return Response({'detail': 'The user is already a manager'}, status=status.HTTP_400_BAD_REQUEST)

        user.groups.add(manager_group)
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RemoveFromManagerGroup(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [OnlyManager]
    throttle_classes = [UserRateThrottle]


    def delete(self, request, pk):
        
        user = get_object_or_404(User, pk=pk)

        if user:
            manager_group = Group.objects.get(name='Manager')
            user.groups.remove(manager_group)
            return Response({'message': 'done'}, status=status.HTTP_204_NO_CONTENT)

        return Response({'message': 'the user is not found'}, status=status.HTTP_404_NOT_FOUND)
    



class DeliveryView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [OnlyManager]

    def list(self, request, *args, **kwargs):
        users = self.queryset.filter(groups__name='Delivery crew') 
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)

      
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')

        if not username:
            return Response({'detail': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'detail': 'There is no user with the given username'}, status=status.HTTP_404_NOT_FOUND)

        manager_group = Group.objects.get(name='Delivery crew')
        if manager_group in user.groups.all():
            return Response({'detail': 'The user is already a Delivery crew'}, status=status.HTTP_400_BAD_REQUEST)

        user.groups.add(manager_group)
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)



class RemoveFromDeliveryGroup(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [OnlyManager]
    throttle_classes = [UserRateThrottle]

    def delete(self, request, pk):
        
        user = get_object_or_404(User, pk=pk)

        if user:
            manager_group = Group.objects.get(name='Delivery crew')
            user.groups.remove(manager_group)
            return Response({'message': 'done'}, status=status.HTTP_204_NO_CONTENT)

        return Response({'message': 'the user is not found'}, status=status.HTTP_404_NOT_FOUND)
    

class CartsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get(self, request, *args, **kwargs):
        user = Token.objects.get(key=request.auth).user
        carts =Cart.objects.filter(user=user)
        serializer = CartSerializer(carts, many=True)
        return Response(serializer.data)
    

    def post(self, request, *args, **kwargs):
        user = Token.objects.get(key=request.auth).user
        request.data['user_id'] = user.id
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

    def delete(self, request, *args, **kwargs):
        user = Token.objects.get(key=request.auth).user
        
        carts = Cart.objects.filter(user=user)
        if not carts.exists():
            raise NotFound("No carts found for this user")
        carts.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderView(APIView, PageNumberPagination):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request, *args, **kwargs):
        user = Token.objects.get(key=request.auth).user
        
        if user.groups.filter(name='Manager').exists():
            # If the user is a manager, return all orders
            orders = Order.objects.all()
        
        elif user.groups.filter(name='Delivery crew').exists():
            orders = Order.objects.filter(delivery_crew=user)

        else:
            # Otherwise, return only the orders of the user
            orders = Order.objects.filter(user=user)
        

        # Collecting order ids
        order_ids = orders.values_list('id', flat=True)
        # Retrieving order items related to collected order ids
        order_items = OrderItem.objects.filter(order__id__in=order_ids)


        # Applying sorting
        ordering = request.query_params.get('ordering')
        if ordering:
            ordering_list = ordering.split(',')
            orders = orders.order_by(*ordering_list)


        # Paginated data
        order_results = self.paginate_queryset(orders, request, view=self)
        order_item_results = self.paginate_queryset(order_items, request, view=self)

        
        order_serializer = OrderSerializer(order_results, many=True)
        order_item_serializer = OrderItemSerializer(order_item_results, many=True)

        return Response({'Order':order_serializer.data, 'Order items':order_item_serializer.data})


    def post(self, request, *args, **kwargs):
        user = Token.objects.get(key=request.auth).user


        # Get current items for the user
        cart_items = Cart.objects.filter(user=user)

        if not cart_items.exists():
            return Response({'detail': 'No items in cart'}, status=status.HTTP_400_BAD_REQUEST)
        
        
        # Select a delivery crew member randomly
        delivery_group = Group.objects.get(name='Delivery crew')
        delivery_crew_members  = User.objects.filter(groups=delivery_group)

        if not delivery_crew_members.exists():
            return Response({'detail': 'No delivery crew available'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery_crew = random.choice(delivery_crew_members)

        # Calculate total price
        total = sum(cart_item.price for cart_item in cart_items)

        # Create new order
        order = Order.objects.create(
            user=user,
            delivery_crew=delivery_crew,
            status=False,
            total=total,
            date=datetime.now().date()
        )


        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=cart_item.menuitem,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price,
                price=cart_item.price
            )

        # Clear the user's cart
        cart_items.delete()

        # Return the created order
        order_serializer = OrderSerializer(order)           

        return Response(order_serializer.data, status=status.HTTP_201_CREATED)
    



class GetSpeceficOrder(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    
    def get(self, request, pk, *args, **kwargs):    
        user = Token.objects.get(key=request.auth).user
        
        # Get order 
        user_order = get_object_or_404(Order, pk=pk)
        
        if user_order.user != user:
            return Response({'detail': 'the order does not belong to authenticated user'}, status=status.HTTP_403_FORBIDDEN)
        
        order_items = OrderItem.objects.filter(order=user_order)

        order_item_serializer = OrderItemSerializer(order_items, many=True)

        return Response(order_item_serializer.data, status=status.HTTP_200_OK)
    

    def put(self, request, pk, *args, **kwargs):
        user = Token.objects.get(key=request.auth).user

        # Check if the user is part of the 'Delivery crew' group
        if user.groups.filter(name='Delivery crew').exists():
            return Response({'detail': 'Delivery crew members are not allowed to update orders.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if the user is a manager
        if user.groups.filter(name='Manager').exists():
            # Manager can access and update all orders
            order = get_object_or_404(Order, pk=pk)
        else:
            # Regular user can only access and update their own orders
            order = get_object_or_404(Order, pk=pk, user=user)

        serializer = UpdateOrderSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

    def patch(self, request, pk, *args, **kwargs):
        user = Token.objects.get(key=request.auth).user

        if user.groups.filter(name='Delivery crew').exists():
            order = get_object_or_404(Order, pk=pk, delivery_crew=user)
            serializer_class = DeliveryUpdateSerializer
        
        elif user.groups.filter(name='Manager').exists():
            order = get_object_or_404(Order, pk=pk)
            serializer_class = UpdateOrderSerializer
    
        else:
            return Response({'detail':'The user does not have permission to update'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = serializer_class(order, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        user = Token.objects.get(key=request.auth).user

        if user.groups.filter(name='Manager').exists():
            order = get_object_or_404(Order, pk=pk)
            order.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response({'detail':'The user does not have permission to delete'}, status=status.HTTP_403_FORBIDDEN)