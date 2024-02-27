from django.db import models


# Create your models here.
class User(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    monthly_salary = models.DecimalField(max_digits=15, decimal_places=2)
    approved_limit = models.DecimalField(max_digits=10, decimal_places=2)


class Loan(models.Model):
    loan_id = models.CharField(max_length=20, unique=True)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenure = models.IntegerField()  # In months
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    monthly_repayment = models.DecimalField(max_digits=10, decimal_places=2)
    emis_paid_on_time = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()
