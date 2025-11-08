-- Seed packaging materials with environmental scores and emission factors
-- Based on SUSTAINABILITY_SCORING_METHODOLOGY.md specifications

INSERT INTO packaging_materials (
    tag,
    name,
    slug,
    material_subtype,
    recyclability_score,
    recycling_rate_pct,
    biodegradability_score,
    transport_impact_score,
    environmental_score,
    score_adjustment,
    production_kg_co2_per_kg,
    recycling_code,
    biodegradation_time
)
VALUES
-- Cardboard/Paper (Best: 87/100 environmental score)
('en:cardboard', 'Cardboard', 'cardboard', 'paper-based', 95, 62.0, 100, 95, 87, 10, 0.7, NULL, '2-3 months'),
('en:paper', 'Paper', 'paper', 'paper-based', 95, 62.0, 100, 95, 87, 10, 0.5, NULL, '2-4 weeks'),

-- Aluminum (68/100 environmental score)
('en:aluminium', 'Aluminum', 'aluminum', 'metal', 100, 50.0, 0, 90, 68, 5, 8.5, '41', 'Does not biodegrade'),
('en:metal', 'Metal (general)', 'metal', 'metal', 100, 50.0, 0, 90, 68, 5, 6.0, NULL, 'Does not biodegrade'),

-- Steel/Tin (65/100 environmental score)
('en:steel', 'Steel', 'steel', 'metal', 100, 45.0, 0, 88, 65, 3, 2.0, '40', 'Does not biodegrade'),
('en:tin', 'Tin/Tinplate', 'tin', 'metal', 100, 45.0, 0, 88, 65, 3, 2.2, NULL, 'Does not biodegrade'),

-- Glass (51/100 environmental score)
('en:glass', 'Glass', 'glass', 'glass', 100, 31.0, 0, 20, 51, 0, 0.9, '70-79', '1 million years+'),

-- PET Plastic (28/100 environmental score)
('en:pet', 'PET Plastic', 'pet', 'plastic', 85, 29.0, 5, 95, 28, -8, 3.5, '1', '450+ years'),
('en:1-pet', 'PET #1', 'pet-1', 'plastic', 85, 29.0, 5, 95, 28, -8, 3.5, '1', '450+ years'),

-- HDPE Plastic (26/100 environmental score)
('en:hdpe', 'HDPE Plastic', 'hdpe', 'plastic', 80, 28.0, 5, 95, 26, -10, 2.8, '2', '450+ years'),
('en:2-hdpe', 'HDPE #2', 'hdpe-2', 'plastic', 80, 28.0, 5, 95, 26, -10, 2.8, '2', '450+ years'),

-- Composite/Tetra Pak (25/100 environmental score)
('en:tetra-pak', 'Tetra Pak', 'tetra-pak', 'composite', 40, 26.0, 10, 85, 25, -12, 1.8, NULL, '5+ years'),
('en:composite', 'Composite material', 'composite', 'composite', 40, 26.0, 10, 85, 25, -12, 2.0, NULL, '5+ years'),

-- Mixed/Other Plastics (23/100 environmental score - Worst)
('en:plastic', 'Plastic (mixed)', 'plastic', 'plastic', 30, 9.0, 0, 95, 23, -15, 4.0, NULL, '500+ years'),
('en:other-plastics', 'Other Plastics', 'other-plastics', 'plastic', 30, 9.0, 0, 95, 23, -15, 4.2, '7', '500+ years'),

-- PVC Plastic (20/100 environmental score)
('en:pvc', 'PVC Plastic', 'pvc', 'plastic', 25, 5.0, 0, 90, 20, -15, 4.5, '3', '1000+ years'),
('en:3-pvc', 'PVC #3', 'pvc-3', 'plastic', 25, 5.0, 0, 90, 20, -15, 4.5, '3', '1000+ years'),

-- LDPE Plastic (24/100 environmental score)
('en:ldpe', 'LDPE Plastic', 'ldpe', 'plastic', 60, 18.0, 5, 95, 24, -12, 2.5, '4', '450+ years'),
('en:4-ldpe', 'LDPE #4', 'ldpe-4', 'plastic', 60, 18.0, 5, 95, 24, -12, 2.5, '4', '450+ years'),

-- PP Plastic (27/100 environmental score)
('en:pp', 'PP Plastic', 'pp', 'plastic', 75, 25.0, 5, 95, 27, -10, 2.9, '5', '450+ years'),
('en:5-pp', 'PP #5', 'pp-5', 'plastic', 75, 25.0, 5, 95, 27, -10, 2.9, '5', '450+ years'),

-- PS Plastic (22/100 environmental score)
('en:ps', 'PS Plastic', 'ps', 'plastic', 40, 12.0, 0, 95, 22, -15, 3.8, '6', '500+ years'),
('en:6-ps', 'PS #6', 'ps-6', 'plastic', 40, 12.0, 0, 95, 22, -15, 3.8, '6', '500+ years'),

-- Bio-based/Compostable (Better alternatives)
('en:biodegradable-plastic', 'Biodegradable Plastic', 'biodegradable-plastic', 'bio-plastic', 50, 15.0, 80, 95, 45, -2, 2.2, NULL, '6-12 months'),
('en:pla', 'PLA (Polylactic Acid)', 'pla', 'bio-plastic', 60, 20.0, 90, 95, 50, 0, 1.8, NULL, '6-24 months'),

-- Wood/Natural fibers
('en:wood', 'Wood', 'wood', 'natural', 70, 40.0, 95, 80, 75, 8, 0.4, NULL, '1-3 years')

ON CONFLICT (tag) DO UPDATE SET
    name = EXCLUDED.name,
    slug = EXCLUDED.slug,
    material_subtype = EXCLUDED.material_subtype,
    recyclability_score = EXCLUDED.recyclability_score,
    recycling_rate_pct = EXCLUDED.recycling_rate_pct,
    biodegradability_score = EXCLUDED.biodegradability_score,
    transport_impact_score = EXCLUDED.transport_impact_score,
    environmental_score = EXCLUDED.environmental_score,
    score_adjustment = EXCLUDED.score_adjustment,
    production_kg_co2_per_kg = EXCLUDED.production_kg_co2_per_kg,
    recycling_code = EXCLUDED.recycling_code,
    biodegradation_time = EXCLUDED.biodegradation_time;
