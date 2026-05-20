# DriveClear — Production Architecture

> Modular monolith backend · Next.js web · Expo mobile · MySQL · Redis · Razorpay

---

## 1. System Context

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Next.js    │     │ Expo Mobile │     │ Django Admin│
│  (Vercel)   │     │ iOS/Android │     │  (Railway)  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │ HTTPS/JWT         │                   │
       └───────────────────┼───────────────────┘
                           ▼
              ┌────────────────────────┐
              │   Django REST API      │
              │   (Railway)            │
              │   Modular Monolith     │
              └───────────┬────────────┘
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐   ┌──────────┐   ┌──────────────┐
    │  MySQL   │   │  Redis   │   │ challanpay   │
    │ Railway  │   │ Upstash  │   │ External API │
    └──────────┘   └──────────┘   └──────────────┘
                           │
                    ┌──────┴──────┐
                    │   Celery    │
                    │   Workers   │
                    └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  Razorpay   │
                    └─────────────┘
```

**Critical rule:** External challan API is **never** called from frontend. All flows: `Client → Django → External API`.

---

## 2. Backend Layer Architecture

```
View (Controller)     → HTTP, auth, serializer validation only
    ↓
Service               → Business logic, orchestration, transactions
    ↓
Repository            → DB queries, upserts, no business rules
    ↓
Model                 → Schema + constraints
```

### Folder structure (implemented)

```
backend/
├── apps/
│   ├── auth/          # OTP, JWT, device sessions
│   ├── users/         # User profile
│   ├── vehicles/      # Vehicle registry per user
│   ├── challans/      # Fetch, normalize, master table
│   ├── orders/        # Order lifecycle + timeline
│   ├── payments/      # Razorpay + webhooks
│   ├── notifications/ # Celery push/SMS
│   ├── support/       # Tickets
│   └── core/          # Health, base models
├── common/
│   ├── middleware/    # Logging, rate limit, device, security
│   ├── permissions/   # USER, ADMIN, OPERATIONS, SUPPORT
│   ├── exceptions/    # DriveClearException + DRF handler
│   ├── responses/     # Standardized envelope
│   ├── validators/    # Phone, vehicle
│   └── logging/       # Correlation ID, JSON logs
└── config/
    ├── settings/
    ├── celery.py
    └── urls.py
```

---

## 3. API Routes (v1)

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| POST | `/api/v1/auth/otp/send/` | Public | Send OTP |
| POST | `/api/v1/auth/otp/verify/` | Public | Verify OTP → JWT |
| POST | `/api/v1/auth/token/refresh/` | Public | Rotate refresh token |
| POST | `/api/v1/auth/logout/` | JWT | Blacklist + device deactivate |
| GET | `/api/v1/users/me/` | JWT | Profile |
| POST | `/api/v1/challans/fetch/` | JWT | Fetch challans (proxy) |
| GET | `/api/v1/challans/` | JWT | List stored challans |
| POST | `/api/v1/orders/create/` | JWT | Create order |
| GET | `/api/v1/orders/` | JWT | My Orders |
| GET | `/api/v1/orders/{uuid}/` | JWT | Order detail + timeline |
| POST | `/api/v1/payments/razorpay/create/` | JWT | Create Razorpay order |
| POST | `/api/v1/payments/razorpay/verify/` | JWT | Verify signature + capture |
| POST | `/api/v1/payments/razorpay/webhook/` | Webhook | Async reconciliation |
| POST | `/api/v1/support/create/` | JWT | Support ticket |
| GET | `/api/v1/health/` | Public | Health check |

### Standard response envelope

All endpoints return:

```json
{
  "success": true,
  "message": "...",
  "data": {},
  "meta": {},
  "error": null
}
```

Implemented in `common/responses/api_response.py` + `common/exceptions/handlers.py`.

---

## 4. Authentication Flow

```
1. POST /auth/otp/send/     { phone_number, name }
   → Redis: otp:{phone}, cooldown, daily limit
   → SMS provider (MSG91 in prod, mock in dev)

2. POST /auth/otp/verify/   { phone_number, otp, name, device_id }
   → Verify Redis OTP
   → Create/update User, mark is_phone_verified
   → Issue access (15m) + refresh (30d) with rotation + blacklist
   → DeviceSession touch for fraud tracking

3. Authorization: Bearer <access>
   Headers: X-Device-ID, X-Device-Platform, X-Correlation-ID

4. POST /auth/logout/       { refresh } + blacklist
```

**Security controls:**
- OTP: 5 attempts, 300s TTL, 60s resend cooldown, 10/day per phone
- Refresh token rotation + blacklist (`rest_framework_simplejwt.token_blacklist`)
- Device session deactivation on logout

---

## 5. Challan Fetch Flow

```
POST /challans/fetch/ { vehicle_number, vehicle_type }
│
├─ validate_vehicle_number()
├─ VehicleRepository.get_or_create_for_user()
├─ ChallanFetchRequest created (audit log)
├─ ExternalChallanClient.post()  [45s timeout, httpx]
│     Payload: { name, phone, vehicleNo, vehicleType, utmSource }
├─ ChallanNormalizer.normalize_list()
├─ @transaction.atomic upsert challan_details (unique: user+challan+vehicle)
└─ Return normalized challans to frontend

On failure:
├─ Mark fetch request FAILED
└─ Celery retry_challan_fetch (max 3, exponential backoff)
```

**Normalized format (canonical):**

```json
{
  "challan_number": "",
  "vehicle_number": "",
  "amount": "",
  "status": "",
  "issue_date": "",
  "state": "",
  "offences": [],
  "source": "challanpay"
}
```

---

## 6. Payment Flow (Razorpay) — Trust-First

```
NEVER mark success from frontend callback alone.

1. User selects challan → POST /orders/create/
   - convenience_fee: ₹99 (online) | ₹999 (court)
   - idempotency_key prevents duplicate orders
   - timeline: "Order Created" → PAYMENT_PENDING

2. POST /payments/razorpay/create/
   - Razorpay order created server-side
   - Payment record INITIATED
   - timeline: "Payment Initiated"

3. Frontend opens Razorpay Checkout (key_id from backend only)

4. User pays → frontend receives razorpay_payment_id + signature

5. POST /payments/razorpay/verify/
   - Idempotency lock on payment_id
   - HMAC signature verification
   - razorpay.Client.payment.fetch() — confirm "captured"
   - Update payment + order atomically
   - timeline: "Payment Successful"

6. Celery: verify_payment_async
   - Online → UNDER_REVIEW → COMPLETED
   - Court → COURT_PROCESSING → SETTLEMENT_IN_PROGRESS

7. Webhook backup: payment.captured → verify_payment_from_webhook

8. Celery: generate_receipt_async
```

**Race condition prevention:**
- `idempotency_key` on orders and payments
- Redis `acquire_idempotency_lock()` on verify
- Unique `gateway_payment_id` check before success

---

## 7. Order Lifecycle

```
CREATED
  → PAYMENT_PENDING
  → PAYMENT_SUCCESS
  → UNDER_REVIEW (online) | COURT_PROCESSING (court)
  → SETTLEMENT_IN_PROGRESS (court only)
  → COMPLETED

Failure paths:
  → FAILED (stale pending > 24h via Celery)
  → REFUNDED (admin-initiated)
```

**My Orders page data model:**

```json
{
  "uuid": "...",
  "order_type": "ONLINE_PAYMENT",
  "order_status": "PAYMENT_SUCCESS",
  "payment_status": "SUCCESS",
  "settlement_status": "IN_PROGRESS",
  "payable_amount": "500.00",
  "convenience_fee": "99.00",
  "total_amount": "599.00",
  "timeline": [
    { "status": "CREATED", "message": "Order created", "created_at": "..." },
    { "status": "PAYMENT_SUCCESS", "message": "Payment successful", "created_at": "..." }
  ],
  "challan": { "challan_number": "...", "vehicle_number": "..." }
}
```

---

## 8. Celery Task Architecture

| Task | Queue | Retry | Purpose |
|------|-------|-------|---------|
| `retry_challan_fetch` | default | 3x | External API retry |
| `verify_payment_async` | default | - | Post-payment workflow |
| `generate_receipt_async` | default | - | PDF receipt |
| `reconcile_pending_payments` | beat/10m | - | Stuck payments |
| `cleanup_stale_pending_orders` | beat/daily | - | Fail old pending |
| `send_order_status_notification` | default | 3x | Push/SMS |

**Dead letter:** Log to `payments.log` / `external_api.log` with correlation_id; alert on 3 failures.

---

## 9. Redis Usage

| Key pattern | TTL | Purpose |
|-------------|-----|---------|
| `otp:{phone}` | 300s | OTP value |
| `otp_cooldown:{phone}` | 60s | Resend block |
| `otp_daily:{phone}` | 24h | Daily limit counter |
| `rl:otp_send:{hash}` | 1h | Rate limit |
| `rl:challan_fetch:{user}` | 1h | Fetch limit |
| `idempotency:{key}` | 300-600s | Duplicate prevention |
| Celery broker | - | Task queue |

---

## 10. Middleware Stack (order matters)

1. `SecurityMiddleware` + WhiteNoise
2. `CorsMiddleware`
3. `SecurityHeadersMiddleware` — HSTS, X-Frame-Options
4. `RequestLoggingMiddleware` — correlation ID, duration, IP
5. `DeviceTrackingMiddleware` — X-Device-ID
6. `RateLimitMiddleware` — OTP + challan fetch
7. `ExceptionMiddleware` — non-DRF exceptions

---

## 11. Logging Strategy

| Logger | File | Events |
|--------|------|--------|
| `driveclear` | app.log | Requests, auth, orders |
| `driveclear.payments` | payments.log | Verify, webhooks, refunds |
| `driveclear.external` | external_api.log | Challan API req/res |

Every log includes `correlation_id` from `X-Correlation-ID` header.

---

## 12. Frontend Architecture (Next.js)

```
web/src/
├── app/
│   ├── (marketing)/page.tsx      # Landing
│   ├── (auth)/login/page.tsx
│   ├── (auth)/verify-otp/page.tsx
│   ├── (app)/vehicle/page.tsx
│   ├── (app)/challans/page.tsx
│   ├── (app)/pay/[challanId]/page.tsx
│   ├── (app)/court-settlement/[id]/page.tsx
│   ├── (app)/orders/page.tsx       # My Orders
│   └── (app)/orders/[id]/page.tsx
├── components/
│   ├── ui/                         # shadcn-style primitives
│   ├── challan/ChallanCard.tsx
│   ├── order/OrderTimeline.tsx
│   └── payment/RazorpayCheckout.tsx
├── lib/
│   ├── api/client.ts               # Axios + interceptors
│   ├── auth/token.ts               # Secure storage
│   └── hooks/useOrders.ts
└── store/
    └── authStore.ts                # Zustand
```

**API client pattern:**

```typescript
// All responses typed as ApiResponse<T>
const res = await api.post('/challans/fetch/', { vehicle_number });
if (!res.success) throw new ApiError(res.error);
return res.data;
```

**Razorpay integration:** Load script dynamically; never store secret on frontend; only `key_id` from backend.

---

## 13. Mobile Architecture (Expo)

```
mobile/src/
├── navigation/RootNavigator.tsx
├── screens/
│   ├── Auth/LoginScreen.tsx
│   ├── Challan/ChallanListScreen.tsx
│   ├── Payment/PaymentScreen.tsx
│   └── Orders/OrderDetailScreen.tsx
├── services/api.ts                 # Same envelope as web
├── storage/secureStore.ts          # expo-secure-store for JWT
└── hooks/useRazorpay.ts          # react-native-razorpay
```

Shared API contract with web — single backend, identical JWT flow.

---

## 14. Admin Workflows

Django Admin (`/admin/`) for MVP operations:

- **Users:** search by phone, verify status
- **Challans:** inspect raw_api_response, normalized_response
- **Orders:** inline timeline, update settlement_status manually
- **Support tickets:** admin_notes, status transitions
- **Payments:** gateway_response audit

Phase 2: Custom ops dashboard with role `OPERATIONS` + `SUPPORT`.

---

## 15. Deployment

| Service | Platform | Notes |
|---------|----------|-------|
| API | Railway | `railway.toml`, gunicorn |
| Celery worker | Railway (separate service) | Same image, `worker` process |
| Celery beat | Railway | `beat` process |
| MySQL | Railway MySQL | utf8mb4 |
| Redis | Upstash | TLS URL in env |
| Web | Vercel | `NEXT_PUBLIC_API_URL` |
| Mobile | EAS Build | env per channel |

### CI/CD (GitHub Actions suggestion)

```yaml
# .github/workflows/backend.yml
- lint (ruff)
- migrate --check
- test
- deploy Railway on main
```

---

## 16. Environment Variables

See `backend/.env.example` and `web/.env.example`.

Production checklist:
- [ ] `DEBUG=False`
- [ ] Strong `SECRET_KEY`
- [ ] Razorpay live keys + webhook secret
- [ ] SMS provider configured
- [ ] CORS limited to production domains
- [ ] Upstash Redis TLS

---

## 17. Security Checklist

- [x] JWT + refresh rotation + blacklist
- [x] OTP rate limiting (middleware + service)
- [x] Payment signature verification server-side
- [x] Webhook HMAC verification
- [x] Idempotency keys on orders/payments
- [x] External API hidden from clients
- [x] Correlation ID tracing
- [x] Security headers middleware
- [ ] WAF on Railway (phase 2)
- [ ] PII encryption at rest (phase 2)

---

## 18. Pricing (Business Logic)

| Service | Fee | Code constant |
|---------|-----|---------------|
| Online challan payment | ₹99 | `ONLINE_CHALLAN_SERVICE_FEE_PAISE` |
| Court settlement | ₹999 | `COURT_SETTLEMENT_SERVICE_FEE_PAISE` |

`total_amount = challan_amount + convenience_fee`

---

## 19. Scalability Path (Post-MVP)

1. **Read replicas** for My Orders / challan list
2. **Separate Celery queues:** `payments`, `challans`, `notifications`
3. **Event outbox** for order timeline → websocket (Pusher/Ably)
4. **S3** for receipts instead of local media
5. **API gateway** only if splitting services

Current modular monolith supports 50k+ MAU without microservices.
