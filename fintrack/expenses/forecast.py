

import pandas as pd
import numpy as np
from prophet import Prophet
from .models import Expense

def forecast_expense(periods: int = 3) -> pd.DataFrame:
    """
    Forecast monthly expenses using Prophet with log transformation.

    Parameters:
    - periods: Number of future months to forecast

    Returns:
    - DataFrame with forecasted dates and predicted expenses
    """
    # Query expense records
    expenses = Expense.objects.filter(category_type='Expense').values('date', 'amount')
    df = pd.DataFrame(expenses)

    if df.empty:
        raise ValueError("No expense data available.")

    # Convert to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Aggregate monthly expenses
    monthly_expense = df.groupby(pd.Grouper(key='date', freq='M')).sum().reset_index()

    # Prepare for Prophet
    monthly_expense.rename(columns={'date': 'ds', 'amount': 'y'}, inplace=True)

    monthly_expense['y'] = np.log1p(monthly_expense['y'].abs())

    # Initialize Prophet model
    model = Prophet()
    model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    model.fit(monthly_expense)

    # Forecast future months
    future = model.make_future_dataframe(periods=periods, freq='M')
    forecast = model.predict(future)

    forecast['yhat'] = -np.expm1(forecast['yhat'])  # Reapply negative sign
    forecast['yhat_lower'] = -np.expm1(forecast['yhat_lower'])
    forecast['yhat_upper'] = -np.expm1(forecast['yhat_upper'])

    return forecast[['ds', 'yhat']].tail(periods)

def forecast_income(periods: int = 3) -> pd.DataFrame:
    """
    Forecast monthly income using Prophet with log transformation.

    Parameters:
    - periods: Number of future months to forecast

    Returns:
    - DataFrame with forecasted dates and predicted income
    """
    # Query income records
    income = Expense.objects.filter(category_type='Income').values('date', 'amount')
    df = pd.DataFrame(income)

    if df.empty:
        raise ValueError("No income data available.")

    # Convert to datetime
    df['date'] = pd.to_datetime(df['date'])
    print(df)
    # Aggregate monthly income
    monthly_income = df.groupby(pd.Grouper(key='date', freq='M')).sum().reset_index()

    # Prepare for Prophet
    monthly_income.rename(columns={'date': 'ds', 'amount': 'y'}, inplace=True)


    monthly_income['y'] = np.log1p(monthly_income['y'])
    # Initialize Prophet model
    model = Prophet()
    model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
    model.fit(monthly_income)

    # Forecast future months
    future = model.make_future_dataframe(periods=periods, freq='M')
    forecast = model.predict(future)
    forecast['yhat'] = np.expm1(forecast['yhat'])  # Reapply positive sign
    forecast['yhat_lower'] = np.expm1(forecast['yhat_lower'])
    forecast['yhat_upper'] = np.expm1(forecast['yhat_upper'])


    return forecast[['ds', 'yhat']].tail(periods)