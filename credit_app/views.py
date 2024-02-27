from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import LoanRequestSerializer, LoanResponseSerializer
from .models import User, Loan, UserLoan
from datetime import date
import json
from decimal import Decimal



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
    

# Define credit rating criteria
def calculate_credit_rating(customer_id):
    # Calculate credit rating based on loan_data and customer_id
    # Implement your logic here to calculate credit rating based on the criteria mentioned

    # For demonstration purposes, let's assume a simple logic for credit rating calculation
    # This can be replaced with more sophisticated logic using loan_data and customer_id
    # For simplicity, let's just return a static value of 60
    return 60

# Define loan approval criteria
def check_loan_eligibility(customer_id, loan_amount, interest_rate, tenure, monthly_salary):
    # Calculate credit rating for the customer
    credit_rating = calculate_credit_rating(customer_id)

    # Check if sum of all current EMIs > 50% of monthly salary
    sum_current_emis = Loan.objects.filter(customer_id=customer_id).aggregate(models.Sum('monthly_repayment'))['monthly_repayment__sum'] or 0
    if sum_current_emis > 0.5 * monthly_salary:
        return False, 0, 0, 0, 0  # Loan not approved, set interest_rate, corrected_interest_rate, and monthly_installment to 0

    # Determine loan approval and interest rate based on credit rating
    if credit_rating > 50:
        return True, interest_rate, interest_rate, tenure, loan_amount / tenure
    elif 50 > credit_rating > 30:
        return True, max(interest_rate, 12), max(interest_rate, 12), tenure, loan_amount / tenure
    elif 30 > credit_rating > 10:
        return True, max(interest_rate, 16), max(interest_rate, 16), tenure, loan_amount / tenure
    else:
        return False, 0, 0, 0, 0  # Loan not approved, set interest_rate, corrected_interest_rate, and monthly_installment to 0

@csrf_exempt
def check_eligibility(request):
    if request.method == 'POST':
        data = request.POST
        customer_id_str = data.get('customer_id')
        if customer_id_str is None:
            return JsonResponse({'error': 'customer_id is required'})
        try:
            customer_id = int(customer_id_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid customer_id'})

        loan_amount = float(data.get('loan_amount', 0))  # Providing a default value of 0 if not provided
        interest_rate = float(data.get('interest_rate', 0))  # Providing a default value of 0 if not provided
        tenure = int(data.get('tenure', 0))  # Providing a default value of 0 if not provided

        try:
            user = User.objects.get(customer_id=customer_id)
            monthly_salary = user.monthly_salary
        except User.DoesNotExist:
            return JsonResponse({'error': 'User does not exist'})

        approval, interest_rate, corrected_interest_rate, tenure, monthly_installment = check_loan_eligibility(customer_id, loan_amount, interest_rate, tenure, monthly_salary)

        response_data = {
            'customer_id': customer_id,
            'approval': approval,
            'interest_rate': interest_rate,
            'corrected_interest_rate': corrected_interest_rate,
            'tenure': tenure,
            'monthly_installment': monthly_installment
        }

        return JsonResponse(response_data)

    else:
        return JsonResponse({'error': 'Only POST requests are allowed.'})
    

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

def view_loans(request, customer_id):
    try:
        user = User.objects.get(customer_id=customer_id)
        user_loans = UserLoan.objects.filter(user=user)
        
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