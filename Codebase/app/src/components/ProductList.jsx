import React, { useState, useEffect } from 'react';
import ProductCard from './ProductCard';
import FilterSort from './FilterSort';
import { calculateHealthScore } from '../utils/helpers';

const ProductList = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortOption, setSortOption] = useState('default');

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      
      // IMPORTANT: Replace this with your actual API endpoint
      // For now, using mock data since your API returns individual products by UPC
      const mockProducts = [
        {
          upc: '0064100238220',
          brand: 'Sample Foods',
          name: 'Organic Wheat Crackers',
          product_name: 'Organic Wheat Crackers',
          primary_category: 'Crackers',
          quantity: '560 g',
          manufacturing_places: 'Mississauga, Ontario',
          price: 4.99,
          sustainabilityScore: 78,
          carbonEmissions: 1.2,
          ingredients: ['organic wheat', 'water', 'salt', 'yeast'],
        },
        {
          upc: '0064100238221',
          brand: 'Green Valley',
          name: 'Organic Almond Milk',
          product_name: 'Organic Almond Milk',
          primary_category: 'Beverages',
          quantity: '1 L',
          manufacturing_places: 'Vancouver, BC',
          price: 5.49,
          sustainabilityScore: 85,
          carbonEmissions: 0.8,
          ingredients: ['organic almonds', 'water', 'natural vitamin E'],
        },
        {
          upc: '0064100238222',
          brand: 'Nature\'s Best',
          name: 'Whole Grain Bread',
          product_name: 'Whole Grain Bread',
          primary_category: 'Bakery',
          quantity: '675 g',
          manufacturing_places: 'Toronto, Ontario',
          price: 3.99,
          sustainabilityScore: 72,
          carbonEmissions: 1.5,
          ingredients: ['whole wheat flour', 'water', 'yeast', 'salt'],
        },
      ];

      // Calculate health scores for each product
      const productsWithHealthScores = mockProducts.map(product => ({
        ...product,
        healthScore: calculateHealthScore(product.ingredients),
      }));

      setProducts(productsWithHealthScores);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const sortProducts = (productsToSort, option) => {
    const sorted = [...productsToSort];
    
    switch (option) {
      case 'price-low':
        return sorted.sort((a, b) => (a.price || 0) - (b.price || 0));
      case 'price-high':
        return sorted.sort((a, b) => (b.price || 0) - (a.price || 0));
      case 'sustainability':
        return sorted.sort((a, b) => (b.sustainabilityScore || 0) - (a.sustainabilityScore || 0));
      case 'health':
        return sorted.sort((a, b) => (b.healthScore || 0) - (a.healthScore || 0));
      case 'carbon':
        return sorted.sort((a, b) => (a.carbonEmissions || 0) - (b.carbonEmissions || 0));
      default:
        return sorted;
    }
  };

  const sortedProducts = sortProducts(products, sortOption);

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-eco-green"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="bg-red-100 border border-red-400 text-red-700 px-6 py-4 rounded-lg">
          <p className="font-bold">Error loading products</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <FilterSort onSortChange={setSortOption} currentSort={sortOption} />
      
      {sortedProducts.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">No products available</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedProducts.map(product => (
            <ProductCard key={product.upc} product={product} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ProductList;
