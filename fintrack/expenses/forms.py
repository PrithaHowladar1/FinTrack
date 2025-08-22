from django import forms
from .models import Expense

class UploadFileForm(forms.Form):
    file = forms.FileField()

class AddExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'description', 'debit', 'credit', 'sub_category', 'category']
