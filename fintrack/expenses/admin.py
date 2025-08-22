from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'description', 'category', 'amount')
    list_filter = ('category_type', 'month_number', 'category')
    search_fields = ('description', 'sub_category', 'category')
