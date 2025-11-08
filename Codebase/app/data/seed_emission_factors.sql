-- Seed emission factors referenced by the raw materials scoring service.

INSERT INTO ingredient_emission_factors (
    ingredient_tag,
    ingredient_name,
    category,
    kg_co2_per_kg,
    data_source,
    confidence
)
VALUES
-- Animal-based products
('en:beef', 'Beef', 'animal', 25.0, 'Poore & Nemecek 2018', 'high'),
('en:lamb', 'Lamb', 'animal', 24.0, 'Poore & Nemecek 2018', 'high'),
('en:cheese', 'Cheese', 'animal', 21.0, 'Poore & Nemecek 2018', 'high'),
('en:pork', 'Pork', 'animal', 7.5, 'Poore & Nemecek 2018', 'high'),
('en:chicken', 'Chicken', 'animal', 6.0, 'Poore & Nemecek 2018', 'high'),
('en:egg', 'Eggs', 'animal', 4.5, 'Poore & Nemecek 2018', 'high'),
('en:milk', 'Dairy milk', 'animal', 2.8, 'Poore & Nemecek 2018', 'high'),
('en:fish', 'Fish (farmed)', 'animal', 5.0, 'Poore & Nemecek 2018', 'medium'),
('en:shrimp', 'Shrimp (farmed)', 'animal', 12.0, 'Poore & Nemecek 2018', 'medium'),

-- Plant-based products
('en:rice', 'Rice', 'plant', 1.31, 'Agribalyse 3.1', 'high'),
('en:tofu', 'Tofu', 'plant', 2.0, 'Poore & Nemecek 2018', 'high'),
('en:wheat-flour', 'Wheat flour', 'plant', 0.60, 'Agribalyse 3.1', 'high'),
('en:corn', 'Corn/Maize', 'plant', 0.50, 'Agribalyse 3.1', 'high'),
('en:potato', 'Potatoes', 'plant', 0.40, 'Agribalyse 3.1', 'high'),
('en:pea', 'Peas', 'plant', 0.40, 'Agribalyse 3.1', 'high'),
('en:bean', 'Beans', 'plant', 0.40, 'Agribalyse 3.1', 'high'),
('en:tomato', 'Tomatoes', 'plant', 0.30, 'Agribalyse 3.1', 'high'),
('en:sugar', 'Sugar (cane)', 'plant', 0.70, 'Agribalyse 3.1', 'high'),
('en:vegetable-oil', 'Vegetable oil', 'plant', 2.5, 'Agribalyse 3.1', 'medium'),
('en:palm-oil', 'Palm oil', 'plant', 7.5, 'Poore & Nemecek 2018', 'high'),
('en:nut', 'Nuts (average)', 'plant', 1.5, 'Agribalyse 3.1', 'medium'),
('en:cocoa', 'Cocoa', 'plant', 3.5, 'Agribalyse 3.1', 'high'),
('en:coffee', 'Coffee', 'plant', 4.0, 'Poore & Nemecek 2018', 'high')
ON CONFLICT (ingredient_tag) DO NOTHING;
