import React from 'react';
import { getSustainabilityCategory } from '../utils/helpers';

const SustainabilityBadge = ({ score }) => {
  const category = getSustainabilityCategory(score);

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700">Sustainability</span>
          <span className={`text-sm font-bold ${category.color}`}>{score}/100</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full ${
              score >= 80 ? 'bg-green-600' :
              score >= 60 ? 'bg-lime-500' :
              score >= 40 ? 'bg-yellow-500' :
              score >= 20 ? 'bg-orange-500' : 'bg-red-500'
            }`}
            style={{ width: `${score}%` }}
          ></div>
        </div>
      </div>
      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${category.bgColor} ${category.color}`}>
        {category.label}
      </span>
    </div>
  );
};

export default SustainabilityBadge;
