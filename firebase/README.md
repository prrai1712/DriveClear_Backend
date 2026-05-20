# Firebase service account (backend)

Required for `POST /api/v1/auth/firebase/verify/` after the user completes Firebase phone OTP in the browser.

1. [Firebase Console](https://console.firebase.google.com/) → project **driveclear-82af6**
2. **Project settings** → **Service accounts** → **Generate new private key**
3. Save the downloaded JSON as:

   `DriveClear_Backend/firebase/driveclear-service-account.json`

4. In `DriveClear_Backend/.env`:

   ```env
   FIREBASE_CREDENTIALS_PATH=firebase/driveclear-service-account.json
   ```

5. Restart Django: `.venv/bin/python manage.py runserver`

This file is gitignored — do not commit it.
