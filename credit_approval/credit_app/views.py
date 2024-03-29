from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import LoanRequestSerializer, LoanResponseSerializer
from .models import User, Loan, UserLoan, Customer, LoanData
from datetime import date
import json
from decimal import Decimal

from credit_app import models



@csrf_exempt
def register_customer(request):
    if request.method == 'POST':
        try:
            # Print request body for debugging
            print("Request POST data:", request.body)

            # Parse JSON data from request body
            data = json.loads(request.body)
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            monthly_salary = data.get('monthly_salary')
            if monthly_salary is None:
                raise ValueError("Monthly salary is required")

            # Convert monthly_salary to integer
            monthly_salary = int(monthly_salary)

            phone_number = data.get('phone_number')

            # Calculate the approved limit
            approved_limit = round(36 * monthly_salary)

            # Create a new User object
            user = User.objects.create(
                first_name=first_name,
                last_name=last_name,
                monthly_salary=monthly_salary,
                phone_number=phone_number,
                approved_limit=approved_limit
            )

            # Prepare response data
            response_data = {
                'customer_id': user.customer_id,
                'name': f"{user.first_name} {user.last_name}",
                'monthly_salary': user.monthly_salary,
                'approved_limit': user.approved_limit,
                'phone_number': user.phone_number,
            }

            return JsonResponse(response_data, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    

@api_view(['POST'])
def create_loan(request):
    serializer = LoanRequestSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        customer_id = data['customer_id']
        loan_amount = data['loan_amount']
        interest_rate = data['interest_rate']
        tenure = data['tenure']
        
        try:
            user = User.objects.get(customer_id=customer_id)
            if loan_amount <= user.approved_limit:
                # Loan approved
                # You can implement your loan approval logic here
                # For simplicity, let's assume the loan is approved
                loan_id = 123  # Generate a unique loan ID
                monthly_installment = calculate_monthly_installment(loan_amount, interest_rate, tenure)
                response_data = {
                    'loan_id': loan_id,
                    'customer_id': customer_id,
                    'loan_approved': True,
                    'message': 'Loan approved',
                    'monthly_installment': monthly_installment
                }
                return Response(LoanResponseSerializer(response_data).data)
            else:
                # Loan not approved due to exceeding approved limit
                response_data = {
                    'loan_id': None,
                    'customer_id': customer_id,
                    'loan_approved': False,
                    'message': 'Loan amount exceeds approved limit',
                    'monthly_installment': None
                }
                return Response(LoanResponseSerializer(response_data).data)
        except User.DoesNotExist:
            # User not found
            response_data = {
                'loan_id': None,
                'customer_id': customer_id,
                'loan_approved': False,
                'message': 'User not found',
                'monthly_installment': None
            }
            return Response(LoanResponseSerializer(response_data).data)
    else:
        # Invalid request data
        return Response(serializer.errors, status=400)



def calculate_monthly_installment(loan_amount, interest_rate, tenure):
    # Convert Decimal values to float
    loan_amount = float(loan_amount)
    interest_rate = float(interest_rate)
    tenure = float(tenure)

    # Implement your logic to calculate the monthly installment
    # For simplicity, let's assume a simple interest calculation
    monthly_interest_rate = interest_rate / 12 / 100
    monthly_installment = (loan_amount * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** (-tenure))
    return round(monthly_installment, 2)

def view_loan(request, customer_id):
    try:
        user = User.objects.get(customer_id=customer_id)
        user_loans = UserLoan.objects.filter(user=user)
        print("User:", user)

        
        loan_data = []
        for user_loan in user_loans:
            loan = user_loan.loan
            loan_item = {
                'loan_id': loan.loan_id,
                'loan_amount': loan.loan_amount,
                'interest_rate': loan.interest_rate,
                'monthly_installment': loan.monthly_repayment,
                'repayments_left': loan.tenure - loan.emis_paid_on_time
            }
            loan_data.append(loan_item)

        return JsonResponse(loan_data, safe=False)

    except User.DoesNotExist:
        return JsonResponse({'error': 'User does not exist'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    

@csrf_exempt
def check_eligibility(request):
    if request.method == 'POST':
        data = request.POST
        customer_id = data.get('customer_id')
        loan_amount_str = data.get('loan_amount')
        interest_rate_str = data.get('interest_rate')
        tenure_str = data.get('tenure')

        # Check if loan_amount, interest_rate, and tenure are provided
        if loan_amount_str is None or interest_rate_str is None or tenure_str is None:
            return JsonResponse({'error': 'Invalid request data'}, status=400)

        try:
            loan_amount = float(loan_amount_str)
            interest_rate = float(interest_rate_str)
            tenure = int(tenure_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid loan data format'}, status=400)

        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return JsonResponse({'error': 'Customer not found'}, status=404)

        # Check if sum of all current EMIs > 50% of monthly salary
        current_emis = LoanData.objects.filter(customer=customer, approval=True).aggregate(total_emi=models.Sum('emi'))['total_emi']
        if current_emis is None:
            current_emis = 0
        if current_emis + (loan_amount * interest_rate / 100 * tenure) > customer.monthly_salary * 0.5:
            return JsonResponse({'customer_id': customer_id, 'approval': False, 'message': 'Sum of all current EMIs > 50% of monthly salary'})

        # Check credit score and assign credit rating
        credit_score = customer.credit_score
        credit_rating = 0
        if credit_score > 50:
            credit_rating = 100
        elif 50 >= credit_score > 30:
            credit_rating = 50
        elif 30 >= credit_score > 10:
            credit_rating = 20

        # Correct interest rate based on credit rating
        if credit_rating == 100:
            corrected_interest_rate = interest_rate
        elif credit_rating == 50:
            corrected_interest_rate = max(interest_rate, 12.0)
        elif credit_rating == 20:
            corrected_interest_rate = max(interest_rate, 16.0)
        else:
            return JsonResponse({'customer_id': customer_id, 'approval': False, 'message': 'Credit rating too low'})

        # Check if interest rate matches the slab
        if corrected_interest_rate != interest_rate:
            interest_rate = corrected_interest_rate

        # Approve loan based on credit rating
        approval = True if credit_rating > 0 else False

        # Create LoanData entry
        loan_data = LoanData.objects.create(customer=customer, loan_amount=loan_amount, interest_rate=interest_rate, tenure=tenure, approval=approval)
        loan_data.emi = loan_amount * interest_rate / 100 / tenure
        loan_data.save()

        return JsonResponse({'customer_id': customer_id, 'approval': approval, 'interest_rate': interest_rate, 'corrected_interest_rate': corrected_interest_rate, 'tenure': tenure, 'monthly_installment': loan_data.emi})

    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    


@require_GET
def view_loan_details(request, loan_id):
    try:
        loan = Loan.objects.get(loan_id=loan_id)
        user_loans = UserLoan.objects.filter(loan=loan)
        if user_loans.exists():
            user_loan = user_loans.first()
            customer = user_loan.user

            response_data = {
                'loan_id': loan.loan_id,
                'customer': {
                    'customer_id': customer.customer_id,
                    'first_name': customer.first_name,
                    'last_name': customer.last_name,
                    'phone_number': customer.phone_number,
                    'monthly_salary': customer.monthly_salary,
                    'approved_limit': customer.approved_limit
                },
                'loan_amount': loan.loan_amount,
                'interest_rate': loan.interest_rate,
                'monthly_installment': loan.monthly_repayment,
                'tenure': loan.tenure
            }

            return JsonResponse(response_data)
        else:
            return JsonResponse({'error': 'Loan does not exist'}, status=404)
    except Loan.DoesNotExist:
        return JsonResponse({'error': 'Loan does not exist'}, status=404)
    

from django.http import JsonResponse
from .models import Loan

from django.http import JsonResponse
from .models import Loan

from django.http import JsonResponse
from .models import Loan


def view_loan_details(request, loan_id):
    try:
        loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
        loan_data = {
            'loan_id': loan.loan_id,
            'loan_amount': loan.loan_amount,
            'interest_rate': loan.interest_rate,
            'monthly_installment': loan.monthly_repayment,
            'tenure': loan.tenure,
            'customer': {
                'id': loan.customer.customer_id,
                'first_name': loan.customer.first_name,
                'last_name': loan.customer.last_name,
                'phone_number': loan.customer.phone_number,
            }
        }
        return JsonResponse(loan_data)
    except Loan.DoesNotExist:
        return JsonResponse({'error': 'Loan not found'}, status=404)
