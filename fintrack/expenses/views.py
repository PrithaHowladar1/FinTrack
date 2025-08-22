import io
import pandas as pd
import seaborn as sns
import numpy as np
import base64
import matplotlib.pyplot as plt
import chardet
from io import StringIO

from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import UploadFileForm, AddExpenseForm
from .models import Expense
from .utils import clean_dataframe

def upload_expenses(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = request.FILES['file']
            filename = uploaded_file.name.lower()

            try:
                # Load file
                if filename.endswith('.csv'):
                    raw_bytes = uploaded_file.read()
                    encoding = chardet.detect(raw_bytes).get('encoding') or 'utf-8'
                    decoded_text = raw_bytes.decode(encoding, errors='ignore')
                    df = pd.read_csv(StringIO(decoded_text), engine='python', on_bad_lines='skip')
                elif filename.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(uploaded_file)
                else:
                    form.add_error(None, "Unsupported file format.")
                    return render(request, 'expenses/upload.html', {'form': form})

                # Clean data
                df = clean_dataframe(df)

                # Allowed fields
                allowed_fields = [field.name for field in Expense._meta.fields if field.name != 'id']

                # Save entries
                for _, row in df.iterrows():
                    data = {key: row[key] for key in allowed_fields if key in row}
                    Expense.objects.create(**data)

                return redirect('dashboard')

            except Exception as e:
                form.add_error(None, f"Error processing file: {str(e)}")

    else:
        form = UploadFileForm()

    return render(request, 'expenses/upload.html', {'form': form})


def add_expense(request):
    if request.method == 'POST':
        form = AddExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)  # Don't save to DB yet
            expense.save()  # Triggers model.save() to auto-fill fields
            return redirect('expense_list')  # Or your desired redirect
    else:
        form = AddExpenseForm()
    return render(request, 'expenses/add_expense.html', {'form': form})

def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    return render(request, 'expenses/expense_list.html', {'expenses': expenses})


def dashboard(request):
    expenses = Expense.objects.all()
    df = pd.DataFrame(list(expenses.values()))

    if df.empty:
        context = {
            'total_income': 0,
            'total_expense': 0,
            'monthly_income': {},
            'monthly_expense': {},
            'yearly_income': 0,
            'yearly_expense': 0,
            'expense_pie': None,
            'income_pie': None,
            'trend_chart': None,
            'top_expense_categories': [],
        }
        return render(request, 'expenses/dashboard.html', context)

    # Normalize expense amounts to positive values
    df['amount'] = df.apply(
        lambda row: abs(row['amount']) if row['category_type'] == 'Expense' else row['amount'],
        axis=1
    )

    # Convert date field to datetime if available
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M').astype(str)
        df['year'] = df['date'].dt.year
    else:
        df['month'] = df['month_number'].astype(str)
        df['year'] = 'Unknown'

    # Monthly totals
    monthly_income = df[df['category_type'] == 'Income'].groupby('month')['amount'].sum().sort_index()
    monthly_expense = df[df['category_type'] == 'Expense'].groupby('month')['amount'].sum().sort_index()

    # Yearly totals
    yearly_income = df[df['category_type'] == 'Income']['amount'].sum()
    yearly_expense = df[df['category_type'] == 'Expense']['amount'].sum()

    # Top expense categories
    top_expense_categories = df[df['category_type'] == 'Expense'].groupby('category')['amount'].sum().sort_values(ascending=False).head(5)

    # Generate charts
    def generate_chart(fig):
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return f'data:image/png;base64,{encoded}'

    # Time series trend chart
    fig1, ax1 = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=monthly_income, label='Income', marker='o', ax=ax1)
    sns.lineplot(data=monthly_expense, label='Expense', marker='o', ax=ax1)
    ax1.set_title('Monthly Income vs Expense Trend')
    ax1.set_ylabel('Amount')
    ax1.set_xlabel('Month')
    ax1.legend()
    trend_chart = generate_chart(fig1)

    # Time series trend chart
    # Time series trend chart
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    sns.lineplot(data=monthly_income, label='Income', marker='o', ax=ax1)
    sns.lineplot(data=monthly_expense, label='Expense', marker='o', ax=ax1)

    # Larger axis labels and title
    ax1.set_title('Monthly Income vs Expense Trend', fontsize=15)
    ax1.set_ylabel('Amount', fontsize=15)
    ax1.set_xlabel('Month', fontsize=15)
    ax1.legend()

    trend_chart = generate_chart(fig1)

    # Expense pie chart
    expense_pie_data = df[df['category_type'] == 'Expense'].groupby('category')['amount'].sum()
    fig2, ax2 = plt.subplots()
    ax2.pie(expense_pie_data, labels=expense_pie_data.index, autopct='%1.1f%%', startangle=140)
    ax2.set_title('Expense Breakdown by Category', fontsize=10)
    expense_pie = generate_chart(fig2)

    # Income pie chart
    income_pie_data = df[df['category_type'] == 'Income'].groupby('category')['amount'].sum()
    fig3, ax3 = plt.subplots()
    ax3.pie(income_pie_data, labels=income_pie_data.index, autopct='%1.1f%%', startangle=140)
    ax3.set_title('Income Breakdown by Category')
    income_pie = generate_chart(fig3)

    context = {
        'total_income': yearly_income,
        'total_expense': yearly_expense,
        'monthly_income': monthly_income.to_dict(),
        'monthly_expense': monthly_expense.to_dict(),
        'yearly_income': yearly_income,
        'yearly_expense': yearly_expense,
        'expense_pie': expense_pie,
        'income_pie': income_pie,
        'trend_chart': trend_chart,
        'top_expense_categories': top_expense_categories.to_dict(),
    }

    return render(request, 'expenses/dashboard.html', context)

# views.py
from django.http import JsonResponse
from .forecast import forecast_expense, forecast_income
from django.db.models import Sum


def expenses_forecast(request):

    records = Expense.objects.all()

        # Calculate totals
    total_income = records.filter(category_type='Income').aggregate(total=Sum('amount'))['total'] or 0
    total_expense = records.filter(category_type='Expense').aggregate(total=Sum('amount'))['total'] or 0
    current_savings = total_income + total_expense

    try:
            # Forecast income and expense
        income_df = forecast_income(periods=3)
        expense_df = forecast_expense(periods=3)
    except ValueError as e:
        return render(request, 'expenses/forecast.html', {'error': str(e)})

        # Merge forecasts on date
    income_df = income_df.rename(columns={'yhat': 'income'})
    expense_df = expense_df.rename(columns={'yhat': 'expense'})
    forecast_df = pd.merge(income_df[['ds', 'income']], expense_df[['ds', 'expense']], on='ds')

        # Calculate savings
    forecast_df['savings'] = forecast_df['income'] + forecast_df['expense']  # expense is negative

        # Format for template
    monthly_forecast = [
            {
                'month': pd.to_datetime(row['ds']).strftime('%B %Y'),
                'yhat': row['savings']
            } for _, row in forecast_df.iterrows()
        ]
    total_forecasted_savings = sum(row['savings'] for _, row in forecast_df.iterrows())

    context = {
            'total_income': total_income,
            'total_expense': total_expense,
            'current_savings': current_savings,
            'monthly_forecast': monthly_forecast,
            'total_forecasted_savings': total_forecasted_savings,
        }

    return render(request, 'expenses/forecast.html', context)