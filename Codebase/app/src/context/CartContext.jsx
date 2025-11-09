import React, { createContext, useContext, useState, useEffect } from 'react';
import { saveToLocalStorage, loadFromLocalStorage } from '../utils/helpers';

const CartContext = createContext();

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState([]);

  // Load cart from localStorage on mount
  useEffect(() => {
    const savedCart = loadFromLocalStorage('cart');
    if (savedCart) {
      setCartItems(savedCart);
    }
  }, []);

  // Save cart to localStorage whenever it changes
  useEffect(() => {
    saveToLocalStorage('cart', cartItems);
  }, [cartItems]);

  const addToCart = (product) => {
    setCartItems(prevItems => {
      const existingItem = prevItems.find(item => item.upc === product.upc);
      if (existingItem) {
        return prevItems.map(item =>
          item.upc === product.upc
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      return [...prevItems, { ...product, quantity: 1 }];
    });
  };

  const removeFromCart = (upc) => {
    setCartItems(prevItems => prevItems.filter(item => item.upc !== upc));
  };

  const updateQuantity = (upc, quantity) => {
    if (quantity <= 0) {
      removeFromCart(upc);
      return;
    }
    setCartItems(prevItems =>
      prevItems.map(item =>
        item.upc === upc ? { ...item, quantity } : item
      )
    );
  };

  const clearCart = () => {
    setCartItems([]);
  };

  const getCartTotal = () => {
    return cartItems.reduce((total, item) => total + (item.price || 0) * item.quantity, 0);
  };

  const getCartCount = () => {
    return cartItems.reduce((count, item) => count + item.quantity, 0);
  };

  return (
    <CartContext.Provider
      value={{
        cartItems,
        addToCart,
        removeFromCart,
        updateQuantity,
        clearCart,
        getCartTotal,
        getCartCount,
      }}
    >
      {children}
    </CartContext.Provider>
  );
};
