from rest_framework import serializers
from .models import *

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'age', 'monthly_salary', 'phone_number']


class LoanEligibilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['customer_id', 'loan_amount', 'interest_rate', 'tenure']
class CreateandEligibilityLoanSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField()

    class Meta:
        model = Loan
        fields = ['customer_id', 'loan_amount', 'interest_rate', 'tenure']