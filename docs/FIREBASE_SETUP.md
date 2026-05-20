# Firebase Phone Auth Setup

DriveClear uses **Firebase on the client** to send OTP to the user's phone, then **Django verifies** the Firebase ID token and issues JWT.

## 1. Firebase Console

1. [Firebase Console](https://console.firebase.google.com/) → your project
2. **Build → Authentication → Sign-in method → Phone** → Enable
3. **Authentication → Settings → Authorized domains** → add:
   - `localhost`
   - your Vercel domain (e.g. `your-app.vercel.app`)

## 2. Web app config (frontend)

Project settings → General → Your apps → **Web** → copy config.

Paste into `DriveClear_Frontend/.env.local`:

```env
NEXT_PUBLIC_FIREBASE_API_KEY=AIza...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=1:...
```

Restart: `npm run dev`

## 3. Service account (backend)

Project settings → **Service accounts** → Generate new private key → save JSON.

In `DriveClear_Backend/.env`:

```env
FIREBASE_CREDENTIALS_PATH=firebase/driveclear-service-account.json
```

Install dependency and restart Django:

```bash
cd DriveClear_Backend
.venv/bin/pip install firebase-admin
.venv/bin/python manage.py runserver
```

## 4. Development: test phone numbers (free, no Blaze)

Real Firebase SMS needs the **Blaze** plan. For local dev, use **test numbers** (no billing, no SMS):

1. Firebase Console → **Authentication** → **Sign-in method** → **Phone** → Enable
2. Same page → **Phone numbers for testing** → Add:
   - Phone: `+91 9876543210` (or your choice)
   - OTP: `123456`
3. Match `DriveClear_Frontend/.env.local`:

```env
NEXT_PUBLIC_FIREBASE_TEST_PHONE=9876543210
NEXT_PUBLIC_FIREBASE_TEST_OTP=123456
```

4. Login with that 10-digit number; enter the fixed OTP on `/verify-otp`

## 5. Production: real SMS (Blaze)

When you go live, upgrade the Firebase project to **Blaze** (pay-as-you-go for phone auth SMS). Remove or stop relying on test numbers; users get real OTPs on their phones.

## 6. Test flow (end-to-end)

1. Open http://localhost:3000/login
2. Enter name + test mobile (e.g. `9876543210`)
3. Enter the test OTP on `/verify-otp` (no SMS in dev)
4. App calls `POST /api/v1/auth/firebase/verify/` → JWT issued

## API

```
POST /api/v1/auth/firebase/verify/
{
  "id_token": "<firebase id token>",
  "name": "Rahul",
  "device_id": "optional-uuid",
  "device_platform": "web"
}
```

Legacy mock OTP (`123456`) still works via `/auth/otp/send/` when `SMS_PROVIDER=mock`.
