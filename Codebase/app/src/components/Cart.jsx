import React from 'react';
import { useCart } from '../context/CartContext';
import { formatPrice } from '../utils/helpers';

const Cart = ({ isOpen, onClose }) => {
  const { cartItems, removeFromCart, updateQuantity, getCartTotal, clearCart } = useCart();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-end">
      <div className="bg-white w-full max-w-md h-full overflow-y-auto shadow-xl">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Shopping Cart</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {cartItems.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
              <p className="text-gray-500 text-lg">Your cart is empty</p>
            </div>
          ) : (
            <>
              <div className="space-y-4 mb-6">
                {cartItems.map(item => (
                  <div key={item.upc} className="bg-gray-50 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h3 className="font-semibold text-gray-900">{item.name}</h3>
                        <p className="text-sm text-gray-600">{item.brand}</p>
                      </div>
                      <button
                        onClick={() => removeFromCart(item.upc)}
                        className="text-red-500 hover:text-red-700 ml-2"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                    
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => updateQuantity(item.upc, item.quantity - 1)}
                          className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold w-8 h-8 rounded"
                        >
                          -
                        </button>
                        <span className="font-semibold w-8 text-center">{item.quantity}</span>
                        <button
                          onClick={() => updateQuantity(item.upc, item.quantity + 1)}
                          className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-bold w-8 h-8 rounded"
                        >
                          +
                        </button>
                      </div>
                      <span className="font-bold text-gray-900">
                        {formatPrice((item.price || 0) * item.quantity)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="border-t border-gray-200 pt-4 mb-4">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-lg font-semibold text-gray-700">Total:</span>
                  <span className="text-2xl font-bold text-gray-900">{formatPrice(getCartTotal())}</span>
                </div>
                <button className="w-full bg-eco-green hover:bg-green-600 text-white font-bold py-3 px-4 rounded-lg transition-colors mb-2">
                  Checkout
                </button>
                <button
                  onClick={clearCart}
                  className="w-full bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg transition-colors"
                >
                  Clear Cart
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Cart;
