import React, { createContext, useContext, useState, useEffect } from 'react';
import { saveToLocalStorage, loadFromLocalStorage } from '../utils/helpers';

const WishlistContext = createContext();

export const useWishlist = () => {
  const context = useContext(WishlistContext);
  if (!context) {
    throw new Error('useWishlist must be used within WishlistProvider');
  }
  return context;
};

export const WishlistProvider = ({ children }) => {
  const [wishlistItems, setWishlistItems] = useState([]);

  // Load wishlist from localStorage on mount
  useEffect(() => {
    const savedWishlist = loadFromLocalStorage('wishlist');
    if (savedWishlist) {
      setWishlistItems(savedWishlist);
    }
  }, []);

  // Save wishlist to localStorage whenever it changes
  useEffect(() => {
    saveToLocalStorage('wishlist', wishlistItems);
  }, [wishlistItems]);

  const addToWishlist = (product) => {
    setWishlistItems(prevItems => {
      const exists = prevItems.find(item => item.upc === product.upc);
      if (exists) {
        return prevItems;
      }
      return [...prevItems, product];
    });
  };

  const removeFromWishlist = (upc) => {
    setWishlistItems(prevItems => prevItems.filter(item => item.upc !== upc));
  };

  const isInWishlist = (upc) => {
    return wishlistItems.some(item => item.upc === upc);
  };

  const clearWishlist = () => {
    setWishlistItems([]);
  };

  return (
    <WishlistContext.Provider
      value={{
        wishlistItems,
        addToWishlist,
        removeFromWishlist,
        isInWishlist,
        clearWishlist,
      }}
    >
      {children}
    </WishlistContext.Provider>
  );
};
