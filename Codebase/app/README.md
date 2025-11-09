# Eco Product Scanner - Mobile App

A React Native mobile app for scanning product barcodes and viewing sustainability information, ingredient analysis, and product recommendations.

## Features

- **Barcode Scanning**: Use your phone's camera to scan product barcodes (EAN-13, EAN-8, UPC-A, UPC-E)
- **Sustainability Scores**: View overall sustainability scores including:
  - Packaging impact
  - Transportation emissions
  - Ingredient sustainability
- **Ingredient Health Analysis**: See ingredient classifications:
  - ✓ Good ingredients
  - ⚠ Ingredients to use with caution
  - ✗ Harmful ingredients
- **AI-Powered Summaries**: Get comprehensive product analysis powered by Google Gemini
- **Better Alternatives**: Discover more sustainable product recommendations

## Tech Stack

- **React Native** with **Expo**
- **Expo Router** for file-based navigation
- **Expo Camera** for barcode scanning
- **TypeScript** for type safety
- **NativeWind** for Tailwind CSS styling

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create environment file:
   ```bash
   cp .env.example .env
   ```

3. Update `.env` with your API URL:
   ```
   EXPO_PUBLIC_API_URL=http://your-api-url:5000
   ```

## Running the App

### Development Mode

```bash
# Start Expo dev server
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android

# Run on web
npm run web
```

### Testing

```bash
npm test
```

## Project Structure

```
app/
├── app/                    # Expo Router screens
│   ├── _layout.tsx        # Root layout
│   ├── index.tsx          # Scanner screen
│   └── product/
│       └── [barcode].tsx  # Product details screen
├── components/            # Reusable components
├── config/               # Configuration files
│   └── constants.ts      # API configuration
├── assets/               # Images, fonts, etc.
├── app.json             # Expo configuration
├── package.json         # Dependencies
└── README.md           # This file
```

## API Integration

The app connects to the Eco Product Scanner API (located in `../api/`) which provides:
- Product data from Open Food Facts
- Sustainability score calculations
- Ingredient health analysis
- AI-powered summaries
- Product recommendations

## Permissions

The app requires camera permission to scan barcodes. The permission request is handled automatically on first use.

## Building for Production

```bash
# Build for iOS
expo build:ios

# Build for Android
expo build:android
```

## Environment Variables

- `EXPO_PUBLIC_API_URL`: Base URL for the API backend (default: `http://localhost:5000`)

## Contributing

This app was built for the Cognizant BrAInstorm Challenge 2025 to promote sustainable product choices through technology.
