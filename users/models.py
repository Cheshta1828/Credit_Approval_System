
from django.db import models

class Customer(models.Model):
    customer_id = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    age= models.PositiveIntegerField()
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2)
    approved_limit = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Loan(models.Model):
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE,db_column='customer_id')
    loan_id = models.CharField(max_length=255, unique=True)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenure = models.PositiveIntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    monthly_repayment = models.DecimalField(max_digits=10, decimal_places=2)
    emis_paid_on_time = models.PositiveIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"Loan ID: {self.loan_id} - Customer: {self.customer_id.first_name} {self.customer_id.last_name}"
