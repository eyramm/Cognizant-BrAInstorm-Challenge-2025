import React from 'react';
import { useCart } from '../context/CartContext';
import { useWishlist } from '../context/WishlistContext';
import SustainabilityBadge from './SustainabilityBadge';
import { formatPrice } from '../utils/helpers';

const ProductCard = ({ product }) => {
  const { addToCart } = useCart();
  const { addToWishlist, removeFromWishlist, isInWishlist } = useWishlist();
  const inWishlist = isInWishlist(product.upc);

  const handleAddToCart = () => {
    addToCart(product);
  };

  const handleWishlistToggle = () => {
    if (inWishlist) {
      removeFromWishlist(product.upc);
    } else {
      addToWishlist(product);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden">
      <div className="p-5">
        {/* Product Header */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 mb-1 line-clamp-2">
              {product.name || product.product_name}
            </h3>
            <p className="text-sm text-gray-600">{product.brand}</p>
          </div>
          <button
            onClick={handleWishlistToggle}
            className={`ml-2 p-2 rounded-full transition-colors ${
              inWishlist
                ? 'bg-red-100 text-red-600 hover:bg-red-200'
                : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
            }`}
            aria-label={inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}
          >
            <svg
              className="w-5 h-5"
              fill={inWishlist ? 'currentColor' : 'none'}
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
              />
            </svg>
          </button>
        </div>

        {/* Product Details */}
        <div className="space-y-2 mb-4">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Category:</span>
            <span className="font-medium text-gray-900">{product.primary_category || 'N/A'}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Quantity:</span>
            <span className="font-medium text-gray-900">{product.quantity || 'N/A'}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Location:</span>
            <span className="font-medium text-gray-900 text-right">{product.manufacturing_places || 'N/A'}</span>
          </div>
        </div>

        {/* Sustainability Badge */}
        <div className="mb-4">
          <SustainabilityBadge score={product.sustainabilityScore || 50} />
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 gap-2 mb-4">
          <div className="bg-blue-50 rounded-lg p-2">
            <p className="text-xs text-gray-600">Health Score</p>
            <p className="text-lg font-bold text-blue-600">{product.healthScore || 'N/A'}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-2">
            <p className="text-xs text-gray-600">Carbon (kg)</p>
            <p className="text-lg font-bold text-green-600">{product.carbonEmissions || 'N/A'}</p>
          </div>
        </div>

        {/* Price and Add to Cart */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200">
          <span className="text-2xl font-bold text-gray-900">
            {formatPrice(product.price)}
          </span>
          <button
            onClick={handleAddToCart}
            className="bg-eco-green hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors duration-200 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            Add to Cart
          </button>
        </div>

        {/* UPC */}
        <p className="text-xs text-gray-400 mt-2 text-center">UPC: {product.upc}</p>
      </div>
    </div>
  );
};

export default ProductCard;
