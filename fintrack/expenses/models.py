from django.db import models
import calendar

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Charity', 'Charity'),
        ('Dining Out', 'Dining Out'),
        ('Discretionary', 'Discretionary'),
        ('Living Expenses', 'Living Expenses'),
        ('Medical', 'Medical'),
        ('Passive', 'Passive'),
        ('Salary', 'Salary'),
        ('Transport', 'Transport'),
    ]

    date = models.DateField()
    description = models.CharField(max_length=255)
    debit = models.FloatField(null=True, blank=True)
    credit = models.FloatField(null=True, blank=True)
    sub_category = models.CharField(max_length=100)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    category_type = models.CharField(max_length=50, blank=True)
    month_number = models.IntegerField(blank=True, null=True)
    weekday = models.CharField(max_length=10, blank=True)
    amount = models.FloatField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Extract month and weekday from date
        if self.date:
            self.month_number = self.date.month
            self.weekday = calendar.day_name[self.date.weekday()]

        # Compute amount and category type
        if self.debit:
            self.amount = -abs(self.debit)
            self.category_type = "Expense"
        elif self.credit:
            self.amount = abs(self.credit)
            self.category_type = "Income"
        else:
            self.amount = 0.0
            self.category_type = ""

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.date} - {self.description} - ${self.amount}"