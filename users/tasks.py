
from celery import shared_task
import pandas as pd
from .models import Customer, Loan

@shared_task
def process_customer_data():
    customer_data = pd.read_excel('customer_data.xlsx')
    for index, row in customer_data.iterrows():
        Customer.objects.create(
            customer_id=row['Customer ID'],
            first_name=row['First Name'],
            last_name=row['Last Name'],
            age=row['Age'],
            phone_number=row['Phone Number'],
            monthly_salary=row['Monthly Salary'],
            approved_limit=row['Approved Limit']
        )

@shared_task
def process_loan_data():
    loan_data = pd.read_excel('loan_data.xlsx')
    
    for index, row in loan_data.iterrows():
        
        try:
            customer = Customer.objects.get(customer_id=row['Customer ID'])
        except Customer.DoesNotExist:
            print(f"Customer with ID {row['Customer ID']} does not exist.")
            continue 
        
        existing_loan = Loan.objects.filter(loan_id=row['Loan ID']).first()
        if existing_loan:
            print(f"Loan with ID {row['Loan ID']} already exists. Skipping.")
            continue  

       
        Loan.objects.create(
            customer_id=customer,
            loan_id=row['Loan ID'],
            loan_amount=row['Loan Amount'],
            tenure=row['Tenure'],
            interest_rate=row['Interest Rate'],
            monthly_repayment=row['Monthly payment'],
            emis_paid_on_time=row['EMIs paid on Time'],
            start_date=row['Date of Approval'],
            end_date=row['End Date']
        )

