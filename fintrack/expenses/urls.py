from django.urls import path
from . import views

urlpatterns = [
    path('transactions/', views.expense_list, name='transactions'),
    path('upload/', views.upload_expenses, name='upload'),
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_expense, name='add_expense'),
    path('forecast/', views.expenses_forecast, name='forecast'),
]