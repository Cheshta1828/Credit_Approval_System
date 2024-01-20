
from django.http import JsonResponse
from celery.result import AsyncResult
from .tasks import process_customer_data, process_loan_data
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from django.db.models import Sum
from django.db.models.functions import Coalesce
from datetime import datetime
import uuid



def ingest_data(request):
    
    process_customer_data_result = process_customer_data.delay()
    try:
        process_customer_data_result.get()
        if process_customer_data_result.successful():
            process_loan_data.delay()
            return JsonResponse({'message': 'Data ingestion started'})
        else:
            return JsonResponse({'error': 'Failed to ingest customer data'})

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return JsonResponse({'error': 'An error occurred during data ingestion'})


@api_view(['POST'])
def register_customer(request):
    if request.method == 'POST':
        serializer = CustomerSerializer(data=request.data)
        if serializer.is_valid():
            monthly_salary = serializer.validated_data['monthly_salary']
            approved_limit = round(36 * monthly_salary, -5) 
            customer_id = generate_unique_id()  
            customer = Customer.objects.create(customer_id=customer_id,approved_limit=approved_limit, **serializer.validated_data)
            response_data = {
                'customer_id': customer.customer_id,
                'name': f"{customer.first_name} {customer.last_name}",
                'age': customer.age,
                'monthly_income': customer.monthly_salary,
                'approved_limit': customer.approved_limit,
                'phone_number': customer.phone_number,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
def check_eligibility(request):
    print("request",request.data)
    if request.method == 'POST':
        serializer=CreateandEligibilityLoanSerializer(data=request.data)
        
        if serializer.is_valid():
            customer_id=request.data['customer_id']
            interest_rate=request.data['interest_rate']
            loan_amount=request.data['loan_amount']
            tenure=request.data['tenure']
            
        
            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except customer.DoesNotExist:
                    return Response({'error': f'Customer with id {customer_id} not found.'}, status=status.HTTP_404_NOT_FOUND)
            
            credit_rating = int(calculate_credit_rating(customer))
            if credit_rating > 50:
                    approval = True
            elif 30 < credit_rating <= 50:
                    approval = int(interest_rate) > 12
            elif 10 < credit_rating <= 30:
                    approval = int(interest_rate) > 16
            else:
                    approval = False
            total_emis = Loan.objects.filter(customer_id=customer).aggregate(Sum('tenure'))['tenure__sum']
            monthly_salary = float(customer.monthly_salary)
            if total_emis > 0.5 * monthly_salary:
                    approval = False
            
                
            corrected_interest_rate = min(int(interest_rate), calculate_corrected_interest_rate(credit_rating))
            monthly_installment = calculate_monthly_installment(loan_amount, corrected_interest_rate, tenure) 
            response_data = {
                    'customer_id': customer.customer_id,
                    'approval': approval,
                    'interest_rate': interest_rate,
                    'corrected_interest_rate': corrected_interest_rate,
                    'tenure': tenure,
                    'monthly_installment': monthly_installment,
                }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
def calculate_credit_rating(customer):
    loan_set=Loan.objects.filter(customer_id=customer)
    
    #component 1 :past loans paid on time
    loans_paid_on_time=[]
    for loan in loan_set:
        if loan.emis_paid_on_time==loan.tenure and (loan.end_date<datetime.now().date()):
            loans_paid_on_time.append(loan)
    
    component_i_percentage = (len(loans_paid_on_time) / loan_set.count()) * 100 if loan_set.count() > 0 else 0
    
    #component 2 :no of loans taken in past 
    past_loans = loan_set.filter(end_date__lt=datetime.now())
    total_past_loans = past_loans.count()    
    component_ii_count = total_past_loans
    
    #Component iii: Loan Activity in Current Year
    current_year_loans = loan_set.filter(start_date__year=datetime.now().year)
    
    component_iii_count = current_year_loans.count()
    
    #component iv :loan approved volume
    loans_approved_in_past = []
    current_datetime = datetime.now().date()
    
    for loan in loan_set:
        if loan.end_date < current_datetime:
            loans_approved_in_past.append(loan)
    component_iv_percentage = (len(loans_approved_in_past) / loan_set.count()) * 100 if loan_set.count() > 0 else 0
    
    #component v :sum of current loans vs approved limit
    sum_of_current_loans = 0
    for loan in loan_set:
        sum_of_current_loans += loan.loan_amount
    
    approved_limit = 36 * (customer.monthly_salary // 100000)
    component_v_score = 0 if sum_of_current_loans > approved_limit else 100
    
    weights = {
        'component_i': 0.2,
        'component_ii': 0.2,
        'component_iii': 0.2,
        'component_iv': 0.2,
        'component_v': 0.2,
    }
    overall_credit_rating = (
        weights['component_i'] * component_i_percentage +
        weights['component_ii'] * component_ii_count +
        weights['component_iii'] * component_iii_count +
        weights['component_iv'] *  component_iv_percentage+
        weights['component_v'] * component_v_score
    )
    print("overall_credit_rating",overall_credit_rating*100%100)
    return overall_credit_rating*100%100

    

def calculate_corrected_interest_rate(credit_rating):
    if credit_rating > 50:
        return 10
    elif 30 < credit_rating <= 50:
        return 12
    elif 10 < credit_rating <= 30:
        return 16
    else:
        return 20


def calculate_monthly_installment(loan_amount, interest_rate, tenure):
    monthly_installment = (int(loan_amount) * int(interest_rate) / 100) / 12
    return round(monthly_installment, 2)


@api_view(['POST'])
def create_loan(request):
    if request.method == 'POST':
        serializer=CreateandEligibilityLoanSerializer(data=request.data)
        if serializer.is_valid():
            customer_id=request.data['customer_id']
            interest_rate=request.data['interest_rate']
            loan_amount=request.data['loan_amount']
            tenure=request.data['tenure']
            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except customer.DoesNotExist:
                    return Response({'error': f'Customer with id {customer_id} not found.'}, status=status.HTTP_404_NOT_FOUND)
            
            credit_rating = int(calculate_credit_rating(customer))
            if credit_rating > 50:
                    approval = True
            elif 30 < credit_rating <= 50:
                    approval = int(interest_rate) > 12
            elif 10 < credit_rating <= 30:
                    approval = int(interest_rate) > 16
            else:
                    approval = False

            
            total_emis = Loan.objects.filter(customer_id=customer).aggregate(Sum('tenure'))['tenure__sum']
            
            monthly_salary = float(customer.monthly_salary)
            if total_emis > 0.5 * monthly_salary:
                    approval = False
            corrected_interest_rate = min(int(interest_rate), calculate_corrected_interest_rate(credit_rating))
            monthly_installment = calculate_monthly_installment(request.data['loan_amount'],corrected_interest_rate, request.data['tenure']) 
            response_data = {
                    'customer_id': customer.customer_id,
                    'loan_approved': approval,
                    'monthly_installment': monthly_installment,
                }
            if approval:
                loan_id = generate_unique_id() 
        
                
                loan = Loan.objects.create(customer_id=customer, loan_id=loan_id,loan_amount=request.data['loan_amount'], interest_rate=interest_rate, tenure=request.data['tenure'], monthly_repayment=monthly_installment, emis_paid_on_time=0, start_date=datetime.now().date(), end_date=datetime.now().date())
                response_data['loan_id'] = loan.loan_id
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                response_data['loan_id'] = None
                response_data['Message']="Loan not approved due to low credit rating"
                
                return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def generate_unique_id():
    random_str = str(uuid.uuid4().int)[:8] 
    return f'{random_str}'


@api_view(['GET'])
def view_loan(request, loan_id):
    try:
        loan = Loan.objects.get(loan_id=loan_id)
    except Loan.DoesNotExist:
        return Response({'error': 'Loan not found.'}, status=status.HTTP_404_NOT_FOUND)

    
    customer_data = {
        'customer_id': loan.customer_id.customer_id,
        'first_name': loan.customer_id.first_name,
        'last_name': loan.customer_id.last_name,
        'phone_number': loan.customer_id.phone_number,
        'age': loan.customer_id.age,
    }
    loan_data = {
        'loan_id': loan.loan_id,
        'customer': customer_data,
        'loan_amount': loan.loan_amount,
        'interest_rate': loan.interest_rate,
        'monthly_installment': loan.monthly_repayment,
        'tenure': loan.tenure,
    }

    return Response(loan_data, status=status.HTTP_200_OK)



@api_view(['GET'])
def view_loans_by_customer(request, customer_id):
    try:
        customer_data=Customer.objects.get(customer_id=customer_id)
        loans = Loan.objects.filter(customer_id=customer_data)
    except Loan.DoesNotExist:
        return Response({'error': 'Loans not found.'}, status=status.HTTP_404_NOT_FOUND)
    loan_list = []
    for loan in loans:
        loan_data = {
            'loan_id': loan.loan_id,
            'loan_amount': loan.loan_amount,
            'interest_rate': loan.interest_rate,
            'monthly_installment': loan.monthly_repayment,
            'repayments_left': loan.tenure - loan.emis_paid_on_time,
        }
        loan_list.append(loan_data)

    return Response(loan_list, status=status.HTTP_200_OK)
