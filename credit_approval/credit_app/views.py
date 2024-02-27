from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, require_POST
from .models import User, Loan

import json


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