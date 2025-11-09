# Setup Instructions for Judges

## Download the App (Quickest Option)

**Download the APK directly:** https://expo.dev/artifacts/eas/jgZbbG5FTL3o4sFyrcNpEN.apk

Install on your Android device and you're ready to go!

---

## Setup Backend (Flask API)

1. Navigate to the API directory:
   ```bash
   cd Codebase/api
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials if needed
   ```

4. Run the Flask server:
   ```bash
   flask run --host=0.0.0.0 --port=5001
   ```

The API will be available at `http://localhost:5001`

---

## Setup Chrome Extension

1. Navigate to the extension directory:
   ```bash
   cd Codebase/extension
   ```

2. Open Chrome and go to `chrome://extensions/`

3. Enable "Developer mode" (toggle in top right)

4. Click "Load unpacked"

5. Select the `Codebase/extension` folder

The extension is now installed and ready to use!

---

## Setup Expo Mobile App (Development)

1. Navigate to the app directory:
   ```bash
   cd Codebase/app
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Expo development server:
   ```bash
   npm start
   ```

4. Use the Expo Go app on your phone to scan the QR code, or run:
   - `npm run android` for Android emulator
   - `npm run ios` for iOS simulator

---

## Quick Links

- **Download APK:** https://expo.dev/artifacts/eas/jgZbbG5FTL3o4sFyrcNpEN.apk
- **Backend:** `http://localhost:5001`
- **Expo Dev Server:** Starts on `http://localhost:8081`
