from rest_framework import serializers


class EntitlementsSerializer(serializers.Serializer):
    unlimited_likes = serializers.BooleanField()
    see_likers = serializers.BooleanField()
    advanced_filters = serializers.BooleanField()
    rewind_pass = serializers.BooleanField()
    read_receipts = serializers.BooleanField()
    priority_profile = serializers.BooleanField()
    incognito_mode = serializers.BooleanField()
    priority_support = serializers.BooleanField()


class SubscriptionStateSerializer(serializers.Serializer):
    plan = serializers.CharField()
    plan_name = serializers.CharField()
    status = serializers.CharField()
    is_premium = serializers.BooleanField()
    starts_at = serializers.DateTimeField(allow_null=True)
    ends_at = serializers.DateTimeField(allow_null=True)
    auto_renew = serializers.BooleanField()
    entitlements = EntitlementsSerializer()


class PlanSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    features = serializers.ListField(child=serializers.CharField())
    price_label = serializers.CharField()
    amount_xaf = serializers.IntegerField(min_value=0)
    payment_available = serializers.BooleanField()


class PaymentMethodSerializer(serializers.Serializer):
    code = serializers.ChoiceField(
        choices=("airtel_money", "moov_money", "bank_card")
    )
    name = serializers.CharField()
    description = serializers.CharField()
    available = serializers.BooleanField()


class PremiumPrivacySerializer(serializers.Serializer):
    incognito_enabled = serializers.BooleanField()
    incognito_available = serializers.BooleanField()
    effective_incognito = serializers.BooleanField()


class PremiumPrivacyUpdateSerializer(serializers.Serializer):
    incognito_enabled = serializers.BooleanField(required=True)
