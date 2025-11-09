import React from 'react';
import { useWishlist } from '../context/WishlistContext';
import { useCart } from '../context/CartContext';
import { formatPrice } from '../utils/helpers';

const Wishlist = ({ isOpen, onClose }) => {
  const { wishlistItems, removeFromWishlist, clearWishlist } = useWishlist();
  const { addToCart } = useCart();

  const handleMoveToCart = (item) => {
    addToCart(item);
    removeFromWishlist(item.upc);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-end">
      <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-xl">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Wishlist</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {wishlistItems.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
              <p className="text-gray-500 text-lg">Your wishlist is empty</p>
            </div>
          ) : (
            <>
              <div className="space-y-4 mb-6">
                {wishlistItems.map(item => (
                  <div key={item.upc} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{item.name}</h3>
                        <p className="text-sm text-gray-600">{item.brand}</p>
                        <p className="text-lg font-bold text-gray-900 mt-1">
                          {formatPrice(item.price)}
                        </p>
                      </div>
                      <button
                        onClick={() => removeFromWishlist(item.upc)}
                        className="text-red-500 hover:text-red-700 ml-2"
                      >
                        <svg className="w-5 h-5" fill="currentColor" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                        </svg>
                      </button>
                    </div>
                    
                    <div className="flex items-center gap-2 text-sm mb-3">
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded">
                        Sustainability: {item.sustainabilityScore || 'N/A'}
                      </span>
                    </div>

                    <button
                      onClick={() => handleMoveToCart(item)}
                      className="w-full bg-eco-green hover:bg-green-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
                    >
                      Move to Cart
                    </button>
                  </div>
                ))}
              </div>

              <button
                onClick={clearWishlist}
                className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition-colors"
              >
                Clear Wishlist
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Wishlist;
