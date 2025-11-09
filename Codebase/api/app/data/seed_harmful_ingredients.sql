-- Seed harmful and caution ingredients
-- Based on common food additives and their health classifications
-- Sources: EFSA, FDA, Health Canada evaluations

BEGIN;

-- Update common harmful additives (E-numbers)
-- These are ingredients with documented health concerns

-- Harmful: Strong evidence of health risks
UPDATE ingredients SET
  health_classification = 'harmful',
  is_additive = TRUE,
  additive_code = 'E102',
  health_concerns = 'May cause hyperactivity in children, allergic reactions'
WHERE tag = 'en:e102' OR name ILIKE '%tartrazine%' OR name ILIKE '%e102%';

UPDATE ingredients SET
  health_classification = 'harmful',
  is_additive = TRUE,
  additive_code = 'E621',
  health_concerns = 'May cause headaches, nausea in sensitive individuals'
WHERE tag = 'en:e621' OR name ILIKE '%monosodium glutamate%' OR name ILIKE '%msg%' OR name ILIKE '%e621%';

UPDATE ingredients SET
  health_classification = 'harmful',
  is_additive = TRUE,
  additive_code = 'E250',
  health_concerns = 'Potential carcinogen when cooked at high temperatures'
WHERE tag = 'en:e250' OR name ILIKE '%sodium nitrite%' OR name ILIKE '%e250%';

UPDATE ingredients SET
  health_classification = 'harmful',
  is_additive = TRUE,
  additive_code = 'E951',
  health_concerns = 'May cause headaches and dizziness in sensitive individuals'
WHERE tag = 'en:e951' OR name ILIKE '%aspartame%' OR name ILIKE '%e951%';

UPDATE ingredients SET
  health_classification = 'harmful',
  is_additive = TRUE,
  additive_code = 'E320',
  health_concerns = 'Possible endocrine disruptor, allergic reactions'
WHERE tag = 'en:e320' OR name ILIKE '%butylated hydroxyanisole%' OR name ILIKE '%bha%' OR name ILIKE '%e320%';

UPDATE ingredients SET
  health_classification = 'harmful',
  is_additive = TRUE,
  additive_code = 'E321',
  health_concerns = 'Possible endocrine disruptor, may affect liver'
WHERE tag = 'en:e321' OR name ILIKE '%butylated hydroxytoluene%' OR name ILIKE '%bht%' OR name ILIKE '%e321%';

-- Caution: Moderate concerns or uncertain effects
UPDATE ingredients SET
  health_classification = 'caution',
  is_additive = TRUE,
  additive_code = 'E330',
  health_concerns = 'May erode tooth enamel in high quantities'
WHERE tag = 'en:e330' OR name ILIKE '%citric acid%' OR name ILIKE '%e330%';

UPDATE ingredients SET
  health_classification = 'caution',
  is_additive = TRUE,
  additive_code = 'E412',
  health_concerns = 'May cause digestive issues in large amounts'
WHERE tag = 'en:e412' OR name ILIKE '%guar gum%' OR name ILIKE '%e412%';

UPDATE ingredients SET
  health_classification = 'caution',
  is_additive = TRUE,
  additive_code = 'E407',
  health_concerns = 'May cause digestive inflammation in sensitive individuals'
WHERE tag = 'en:e407' OR name ILIKE '%carrageenan%' OR name ILIKE '%e407%';

UPDATE ingredients SET
  health_classification = 'caution',
  is_additive = TRUE,
  additive_code = 'E433',
  health_concerns = 'May affect gut microbiome'
WHERE tag = 'en:e433' OR name ILIKE '%polysorbate%' OR name ILIKE '%e433%';

-- Mark common good/safe ingredients
UPDATE ingredients SET
  health_classification = 'good'
WHERE tag IN ('en:water', 'en:salt', 'en:sugar', 'en:flour', 'en:wheat-flour', 'en:oil', 'en:olive-oil')
  AND health_classification IS NULL;

-- Mark natural ingredients as good by default
UPDATE ingredients SET
  health_classification = 'good'
WHERE (vegan_status = 'yes' OR vegetarian_status = 'yes')
  AND is_from_palm_oil = FALSE
  AND health_classification IS NULL
  AND (name NOT ILIKE '%e%' OR name NOT SIMILAR TO '%E[0-9]+%');

COMMIT;
