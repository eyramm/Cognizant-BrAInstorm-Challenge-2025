#React App

A React application for displaying eco-friendly products with sustainability ratings, cart functionality, and wishlist features.

## Features

- 🛒 **Shopping Cart** - Add products to cart with quantity management
- ❤️ **Wishlist** - Save favorite products for later
- 🌱 **Sustainability Scoring** - Products rated 0-100 on sustainability
- 📊 **Sorting & Filtering** - Sort by price, health score, carbon emissions
- 💾 **Local Storage** - Cart and wishlist persist across sessions
- 🎨 **Tailwind CSS** - Modern, responsive design

## Installation

1. Clone the repository or create a new React app
2. Install dependencies:

npm install

3. Install Tailwind CSS dependencies:

npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p


4. Create a `.env` file in the root directory:
REACT_APP_API_BASE_URL=http://localhost:3000

## Configuration

### API Integration

Update `src/components/ProductList.jsx` to fetch from your actual API endpoint. Currently using mock data.

Your API should return products with these fields:
- `upc` (required)
- `brand`
- `name` or `product_name`
- `primary_category`
- `quantity`
- `manufacturing_places`
- `price` (number)
- `sustainabilityScore` (0-100)
- `carbonEmissions` (number)
- `ingredients` (array of strings)

## Running the App

npm start

Opens on [http://localhost:3000](http://localhost:3000)

## Project Structure

src/
├── components/
│ ├── ProductCard.jsx # Individual product display
│ ├── ProductList.jsx # Product grid with filtering
│ ├── Cart.jsx # Shopping cart sidebar
│ ├── Wishlist.jsx # Wishlist sidebar
│ ├── FilterSort.jsx # Sort/filter controls
│ └── SustainabilityBadge.jsx # Sustainability score display
├── context/
│ ├── CartContext.jsx # Cart state management
│ └── WishlistContext.jsx # Wishlist state management
├── utils/
│ ├── api.js # API utility functions
│ └── helpers.js # Helper functions
├── App.jsx # Main app component
├── App.css # Custom styles
├── index.js # App entry point
└── index.css # Tailwind imports

## Key Technologies

- **React 18** - UI framework
- **React Hooks** - State management (useState, useEffect, useContext)
- **Tailwind CSS** - Styling
- **Local Storage API** - Data persistence

## Customization

### Adding Real API Data

Replace mock data in `ProductList.jsx` with your API call:

const response = await fetch(${API_BASE_URL}/api/products);
const data = await response.json();

### Adjusting Health Score Calculation

Modify `src/utils/helpers.js` `calculateHealthScore()` function to match your ingredient analysis logic.

### Sustainability Scoring

Update sustainability thresholds in `getSustainabilityCategory()` function in `src/utils/helpers.js`.

## Notes

- Current implementation uses mock product data
- Health scores are calculated client-side based on ingredients
- Update the API endpoints in `src/utils/api.js` to match your backend
- Cart and wishlist data persists in browser localStorage

## Future Enhancements

- Backend integration for cart/wishlist
- User authentication
- Product search functionality
- Advanced filtering (multiple filters at once)
- Product detail pages
- Checkout flow
Setup Instructions
Create React App:

npx create-react-app eco-product-scanner
cd eco-product-scanner
Install Tailwind CSS:​

npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
Replace/Create Files: Copy all the files I provided above into your project structure

Create .env file in root:

REACT_APP_API_BASE_URL=http://localhost:3000
Start the app:

npm start
Important Notes
API Integration: The current ProductList.jsx uses mock data because your API returns individual products by UPC. You'll need to either:

Create an endpoint that returns all products (e.g., GET /api/products)

Or modify the component to fetch multiple products by their UPCs

Missing Fields: Your current API response doesn't include price, sustainabilityScore, carbonEmissions, or ingredients. Add these fields to your API response for full functionality.