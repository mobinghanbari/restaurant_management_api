from django.urls import path
from djoser.views import UserViewSet
from rest_framework.throttling import AnonRateThrottle
from .views import MenuItemsView, MenuItemView, ManagerView, RemoveFromManagerGroup, DeliveryView, RemoveFromDeliveryGroup, CartsView, OrderView, GetSpeceficOrder, CategoryView


class AnonRateThrottleMixin:
    default_throttle_classes = [AnonRateThrottle]

urlpatterns = [
    # Login System
    path('users/', UserViewSet.as_view({'post': 'create'}), name='register'),
    path('users/users/me/', UserViewSet.as_view({'get': 'me'}), name='me'),
    path('categories', CategoryView.as_view()),    
    path('menu-items/', MenuItemsView.as_view()),
    path('menu-items/<str:pk>', MenuItemView.as_view()),
    path('groups/manager/users', ManagerView.as_view()),
    path('groups/manager/users/<str:pk>', RemoveFromManagerGroup.as_view()),
    path('groups/delivery-crew/users', DeliveryView.as_view()),
    path('groups/delivery-crew/users/<str:pk>', RemoveFromDeliveryGroup.as_view()),
    path('cart/menu-items', CartsView.as_view()),
    path('orders', OrderView.as_view()),
    path('orders/<str:pk>', GetSpeceficOrder.as_view()),
]

urlpatterns[0].default_throttle_classes = [AnonRateThrottleMixin]
urlpatterns[1].default_throttle_classes = [AnonRateThrottleMixin]