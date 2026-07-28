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
    profile_boost = serializers.BooleanField()
    boosts_per_window = serializers.IntegerField(min_value=0)
    super_like = serializers.BooleanField()
    super_likes_per_day = serializers.IntegerField(min_value=0)


class ProfileBoostStateSerializer(serializers.Serializer):
    entitled = serializers.BooleanField()
    active = serializers.BooleanField()
    active_until = serializers.DateTimeField(allow_null=True)
    duration_minutes = serializers.IntegerField(min_value=1)
    allowance_per_7_days = serializers.IntegerField(min_value=0)
    remaining = serializers.IntegerField(min_value=0)
    next_available_at = serializers.DateTimeField(allow_null=True)


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


class PaymentCheckoutCreateSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(choices=("plus", "prestige"))
    method = serializers.ChoiceField(
        choices=("airtel_money", "moov_money", "bank_card")
    )


class PaymentTransactionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    plan = serializers.CharField()
    plan_name = serializers.CharField()
    method = serializers.CharField()
    method_name = serializers.CharField()
    status = serializers.CharField()
    amount_xaf = serializers.IntegerField(min_value=0)
    currency = serializers.CharField()
    provider = serializers.CharField()
    provider_reference = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    verified_at = serializers.DateTimeField(allow_null=True)
    can_confirm_in_test_mode = serializers.BooleanField()


class PaymentConfirmationSerializer(serializers.Serializer):
    transaction_id = serializers.UUIDField()


class PaymentHistorySerializer(serializers.Serializer):
    transactions = PaymentTransactionSerializer(many=True)
