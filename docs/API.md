# DriveClear API Reference (v1)

Base URL: `https://api.driveclear.in/api/v1` (production)

## Headers

| Header | Required | Description |
|--------|----------|-------------|
| Authorization | Protected routes | `Bearer <access_token>` |
| X-Device-ID | Recommended | Unique device fingerprint |
| X-Device-Platform | Recommended | `web` \| `ios` \| `android` |
| X-Correlation-ID | Optional | Trace ID (auto-generated if omitted) |

## Auth

### Send OTP
`POST /auth/otp/send/`
```json
{ "phone_number": "9876543210", "name": "Rahul Sharma" }
```

### Verify OTP
`POST /auth/otp/verify/`
```json
{
  "phone_number": "9876543210",
  "otp": "123456",
  "name": "Rahul Sharma",
  "device_id": "uuid-device",
  "device_platform": "web"
}
```
Returns: `{ access, refresh, user }`

## Challans

### Fetch
`POST /challans/fetch/`
```json
{ "vehicle_number": "DL01AB1234", "vehicle_type": "private" }
```

## Orders

### Create
`POST /orders/create/`
```json
{
  "challan_uuid": "...",
  "order_type": "ONLINE_PAYMENT",
  "idempotency_key": "optional-client-key"
}
```

### My Orders
`GET /orders/`

### Order Detail
`GET /orders/{uuid}/`

## Payments

### Create Razorpay Order
`POST /payments/razorpay/create/`
```json
{ "order_uuid": "..." }
```

### Verify Payment (server-side only)
`POST /payments/razorpay/verify/`
```json
{
  "order_uuid": "...",
  "razorpay_order_id": "order_xxx",
  "razorpay_payment_id": "pay_xxx",
  "razorpay_signature": "..."
}
```
