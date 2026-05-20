# Real OTP SMS — Free / Low Cost (India)

Firebase Phone Auth **cannot** send real SMS for free (requires Blaze billing).

**Recommended for DriveClear:** Backend OTP + **MSG91** (free trial credits when you sign up).

## Setup MSG91 (≈10 min)

### 1. Create account
1. https://msg91.com → Sign up (free trial SMS credits)
2. Complete KYC if prompted (needed for transactional SMS in India)

### 2. Get Auth Key
1. MSG91 Dashboard → **API** → copy **Authkey**

### 3. Configure backend `.env`
```env
SMS_PROVIDER=msg91
MSG91_AUTH_KEY=paste_your_auth_key_here
MSG91_SENDER_ID=DRCLEAR
MSG91_TEMPLATE_ID=
```

Leave `MSG91_TEMPLATE_ID` empty to use simple text SMS (works immediately).

### 4. Restart backend
```bash
cd backend
.venv/bin/python manage.py runserver
```

### 5. Test login
1. http://localhost:3000/login
2. Enter your real 10-digit number
3. OTP arrives via SMS (from MSG91, not Firebase)

---

## Costs (honest)

| Provider | Real SMS to any number |
|----------|------------------------|
| Firebase | Paid (Blaze) per SMS |
| MSG91 | Free trial credits, then ~₹0.10–0.20/SMS |
| Mock (`SMS_PROVIDER=mock`) | Free but OTP is always `123456`, no SMS |

There is **no unlimited free real OTP** to all Indian numbers at production scale.

---

## Firebase keys in `.env.local`

You can **keep** Firebase config for later, but login now uses **backend MSG91** only.
Remove `billing-not-enabled` errors by not using Firebase for OTP on the login page.
