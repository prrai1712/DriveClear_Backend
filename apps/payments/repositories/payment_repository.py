from apps.payments.models import Payment, PaymentWebhookLog
from common.constants.enums import PaymentStatus
from common.database.base_repository import BaseRepository


class PaymentRepository(BaseRepository):
    def create_payment(self, **kwargs) -> Payment:
        return Payment.objects.create(**kwargs)

    def get_by_gateway_payment_id(self, gateway_payment_id: str) -> Payment | None:
        return Payment.objects.filter(gateway_payment_id=gateway_payment_id).first()

    def get_by_idempotency(self, key: str) -> Payment | None:
        return Payment.objects.filter(idempotency_key=key).first()

    def mark_success(self, payment: Payment, gateway_payment_id: str, signature: str, response: dict) -> Payment:
        payment.payment_status = PaymentStatus.SUCCESS
        payment.gateway_payment_id = gateway_payment_id
        payment.gateway_signature = signature
        payment.gateway_response = response
        payment.save(
            update_fields=[
                "payment_status",
                "gateway_payment_id",
                "gateway_signature",
                "gateway_response",
                "updated_at",
            ]
        )
        return payment

    def log_webhook(self, event_type: str, payload: dict, signature: str) -> PaymentWebhookLog:
        return PaymentWebhookLog.objects.create(
            event_type=event_type,
            payload=payload,
            signature=signature,
        )
