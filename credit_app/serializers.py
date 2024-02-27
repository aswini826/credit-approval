from rest_framework import serializers

class LoanRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()

class LoanResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField()
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.FloatField()
