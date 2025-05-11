from django.urls import path
from . import views

app_name = 'loyverse_integration'

urlpatterns = [
    path('connect/', views.connect_loyverse_view, name='connect_loyverse'),
    path('callback/', views.loyverse_callback_view, name='loyverse_callback'),
]
