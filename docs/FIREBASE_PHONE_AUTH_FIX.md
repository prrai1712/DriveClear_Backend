# Fix: Firebase Phone Auth errors

## `auth/billing-not-enabled` (BILLING_NOT_ENABLED)

Phone OTP **requires Blaze billing** on your Firebase/Google Cloud project.

### Option A — Enable Blaze (real SMS to any number)
1. [Firebase Console](https://console.firebase.google.com/) → project **driveclear-82af6**
2. Click **Upgrade** (bottom left) or ⚙️ → **Usage and billing**
3. Select **Blaze (Pay as you go)**
4. Add a billing account (credit card)
5. Retry login — SMS will work on real numbers

Typical cost: a few paise per SMS in India; testing is usually under ₹50/month.

### Option B — Test phone numbers (free, no billing)
1. **Authentication → Sign-in method → Phone**
2. **Phone numbers for testing** → Add:
   - Phone: `+91 9876543210`
   - OTP: `123456`
3. Use exactly that number in the app (no real SMS sent)

---

## `auth/operation-not-allowed` (OPERATION_NOT_ALLOWED)

This error means **Phone sign-in is disabled** in Firebase Console for project `driveclear-82af6`.

## Fix (5 minutes)

### 1. Enable Phone provider
1. Open https://console.firebase.google.com/
2. Select project **driveclear-82af6**
3. Go to **Build → Authentication**
4. Open **Sign-in method** tab
5. Click **Phone** → toggle **Enable** → **Save**

### 2. Upgrade billing (required for real SMS OTP)
Phone Authentication needs the **Blaze (pay as you go)** plan:
1. Firebase Console → **Upgrade** (bottom left) or Project settings → Usage and billing
2. Select **Blaze plan** (you only pay for SMS usage; free tier still applies to other products)

Without Blaze, Phone auth often returns `OPERATION_NOT_ALLOWED`.

### 3. Authorized domains
1. **Authentication → Settings → Authorized domains**
2. Ensure these exist:
   - `localhost`
   - `127.0.0.1` (optional)
   - Your Vercel domain when deployed

### 4. Test phone numbers (optional, no SMS cost)
1. **Authentication → Sign-in method → Phone**
2. Expand **Phone numbers for testing**
3. Add e.g. `+91 9876543210` with code `123456`
4. Use that number in the app — OTP is always `123456`

### 5. Retry
Hard refresh http://localhost:3000/login (Cmd+Shift+R) and send OTP again.

## Still stuck?

- Confirm `.env.local` `NEXT_PUBLIC_FIREBASE_PROJECT_ID=driveclear-82af6` matches the project where Phone is enabled.
- Check Google Cloud Console → APIs: **Identity Toolkit API** enabled (usually auto-enabled with Firebase Auth).
