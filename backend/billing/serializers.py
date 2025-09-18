from rest_framework import serializers
from .models import Bill, BillLineItem, DepartmentBudget, Payment, ServiceCatalog
class BillLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillLineItem
        fields = [
            "id",
            "bill",
            "hospital",
            "description",
            "quantity",
            "unit_price_cents",
            "amount_cents",
        ]
        read_only_fields = ["id", "amount_cents"]
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "bill",
            "hospital",
            "amount_cents",
            "method",
            "reference",
            "received_at",
        ]
        read_only_fields = ["id", "received_at"]
class BillSerializer(serializers.ModelSerializer):
    items = BillLineItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    class Meta:
        model = Bill
        fields = [
            "id",
            "hospital",
            "patient",
            "appointment",
            "total_cents",
            "discount_cents",
            "net_cents",
            "paid_cents",
            "status",
            "insurance_claim_status",
            "items",
            "payments",
        ]
        read_only_fields = ["id", "total_cents", "net_cents", "paid_cents", "status"]
class ServiceCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCatalog
        fields = ["id", "hospital", "code", "name", "price_cents", "active"]
        read_only_fields = ["id"]
class DepartmentBudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentBudget
        fields = [
            "id",
            "hospital",
            "department",
            "period",
            "budget_cents",
            "alerts_threshold_pct",
        ]
        read_only_fields = ["id"]