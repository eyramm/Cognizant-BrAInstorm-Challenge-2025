import React from 'react';

const FilterSort = ({ onSortChange, currentSort }) => {
  const sortOptions = [
    { value: 'default', label: 'Default' },
    { value: 'price-low', label: 'Price: Low to High' },
    { value: 'price-high', label: 'Price: High to Low' },
    { value: 'sustainability', label: 'Best Sustainability' },
    { value: 'health', label: 'Healthiest' },
    { value: 'carbon', label: 'Lowest Carbon' },
  ];

  return (
    <div className="bg-white rounded-lg shadow-md p-4 mb-6">
      <div className="flex items-center gap-4">
        <label htmlFor="sort" className="text-sm font-medium text-gray-700 whitespace-nowrap">
          Sort by:
        </label>
        <select
          id="sort"
          value={currentSort}
          onChange={(e) => onSortChange(e.target.value)}
          className="flex-1 block w-full px-4 py-2 text-base border border-gray-300 focus:outline-none focus:ring-2 focus:ring-eco-green focus:border-transparent rounded-lg"
        >
          {sortOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
};

export default FilterSort;
