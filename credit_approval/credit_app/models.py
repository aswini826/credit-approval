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
    customer = models.ForeignKey(User, related_name='loans', on_delete=models.CASCADE)


class UserLoan(models.Model):
    user = models.ForeignKey(User, related_name='user_loans', on_delete=models.CASCADE)
    loan = models.ForeignKey(Loan, related_name='loan_users', on_delete=models.CASCADE)


class Customer(models.Model):
    customer_id = models.IntegerField(unique=True)
    credit_score = models.IntegerField(default=0)
    monthly_salary = models.FloatField(default=0.0)

    def __str__(self):
        return f"Customer {self.customer_id}"

class LoanData(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    loan_amount = models.FloatField()
    interest_rate = models.FloatField()
    tenure = models.IntegerField()
    emi = models.FloatField(default=0.0)
    approval = models.BooleanField(default=False)
    corrected_interest_rate = models.FloatField(default=0.0)

    def __str__(self):
        return f"LoanData for Customer {self.customer.customer_id}"