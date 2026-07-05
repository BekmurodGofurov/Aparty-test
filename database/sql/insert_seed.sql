-- Test users for Andijon region.
-- Password hash placeholder for local testing only.
INSERT INTO users (full_name, phone, email, role, university, is_verified, hashed_password)
VALUES
  ('Odilbek Ergashev', '+998901001001', 'odilbek.ergashev@gmail.com', 'owner', NULL, true, 'seed_hash_1'),
  ('Jasmina Raximova', '+998901001002', 'jasmina.raximova@gmail.com', 'owner', NULL, true, 'seed_hash_1'),
  ('Ulugbek Jo''rayev', '+998901001003', 'ulugbek.jorayev@gmail.com', 'owner', NULL, true, 'seed_hash_1'),
  ('Madina Yuldasheva', '+998901001004', 'madina.yuldasheva@gmail.com', 'owner', NULL, true, 'seed_hash_1'),
  ('Sardorbek Qo''chqorov', '+998901001005', 'sardorbek.qochqorov@gmail.com', 'owner', NULL, true, 'seed_hash_1'),
  ('Nodira Xasanova', '+998901001006', 'nodira.xasanova@gmail.com', 'owner', NULL, true, 'seed_hash_1'),
  ('Shoxrux Mirzayev', '+998901001007', 'shoxrux.mirzayev@gmail.com', 'owner', NULL, true, 'seed_hash_1'),
  ('Dildora Umarova', '+998901001008', 'dildora.umarova@gmail.com', 'owner', NULL, true, 'seed_hash_1'),
  ('Azamat Soliyev', '+998901001009', 'azamat.soliyev@gmail.com', 'owner', NULL, true, 'seed_hash_1'),
  ('Nilufar Teshaboyeva', '+998901001010', 'nilufar.teshaboyeva@gmail.com', 'owner', NULL, true, 'seed_hash_1'),
  ('Jasur Toshmatov', '+998902001001', 'jasur.toshmatov@gmail.com', 'makler', NULL, true, 'seed_hash_1'),
  ('Sherzod Karimov', '+998902001002', 'sherzod.karimov@gmail.com', 'makler', NULL, true, 'seed_hash_1'),
  ('Humoyun G''aniyev', '+998902001003', 'humoyun.ganiyev@gmail.com', 'makler', NULL, true, 'seed_hash_1'),
  ('Sevinch Nematova', '+998902001004', 'sevinch.nematova@gmail.com', 'makler', NULL, true, 'seed_hash_1'),
  ('Dilshod Rahmatov', '+998902001005', 'dilshod.rahmatov@gmail.com', 'makler', NULL, true, 'seed_hash_1')
ON CONFLICT (phone) DO NOTHING;

WITH owner_ads AS (
  SELECT * FROM (
    VALUES
      ('+998901001001', 'Andijon', 'Andijon shahri', 'Cho''lpon ko''chasi 12', 'B1', '12', 3, 9, 40.7822, 72.3442, 2, 58, 210, 'mixed', 3, 1, true, false, true, true, false, true, true, true, 'Yangi ta''mirlangan, transportga yaqin'),
      ('+998901001002', 'Andijon', 'Asaka tumani', 'Mustaqillik ko''chasi 45', 'A2', '4', 2, 5, 40.6413, 72.2387, 2, 54, 190, 'female', 2, 1, true, true, true, false, false, true, true, true, 'Sokin hudud, talaba qizlar uchun qulay'),
      ('+998901001003', 'Andijon', 'Shahrixon tumani', 'Navro''z ko''chasi 7', 'S3', '8', 1, 4, 40.7134, 72.0512, 3, 72, 240, 'male', 4, 2, true, true, true, true, true, true, true, true, 'Bozor va universitetga 10 daqiqa'),
      ('+998901001004', 'Andijon', 'Marhamat tumani', 'Bog''ishamol 19', 'M4', '3', 4, 9, 40.5007, 72.3130, 1, 41, 150, 'female', 2, 1, true, false, true, false, false, true, true, true, 'Issiq suv doimiy, yangi mebel bor'),
      ('+998901001005', 'Andijon', 'Baliqchi tumani', 'Ipak yo''li 88', 'BL5', '21', 5, 7, 40.9082, 72.1974, 2, 60, 175, 'mixed', 3, 1, true, true, true, true, false, true, true, true, 'Oilaviy mahalla, xavfsiz joy'),
      ('+998901001006', 'Andijon', 'Xo''jaobod tumani', 'Do''stlik 10', 'X6', '15', 2, 4, 40.6675, 72.5566, 2, 56, 165, 'male', 3, 2, true, true, true, false, false, true, true, true, 'Yotoqxona mebelli, shinam kvartira'),
      ('+998901001007', 'Andijon', 'Qo''rg''ontepa tumani', 'Yangi hayot 31', 'Q7', '2', 1, 2, 40.7310, 72.7613, 1, 38, 130, 'mixed', 2, 1, true, false, true, false, false, true, true, false, 'Byudjet variant, markazga marshrut bor'),
      ('+998901001008', 'Andijon', 'Paxtaobod tumani', 'Nurafshon 22', 'P8', '9', 3, 5, 40.9298, 72.4968, 2, 52, 170, 'female', 3, 1, true, true, true, true, false, true, true, true, 'Toza va yorug'' xona, derazalar katta'),
      ('+998901001009', 'Andijon', 'Izboskan tumani', 'Istiqlol 14', 'I9', '11', 2, 6, 40.9133, 72.2441, 3, 68, 220, 'male', 4, 2, true, true, true, false, true, true, true, true, 'Ko''p qavatli uy, lift ishlaydi'),
      ('+998901001010', 'Andijon', 'Andijon shahri', 'Temuriylar 5', 'AN10', '6', 6, 9, 40.7891, 72.3561, 2, 57, 205, 'mixed', 3, 1, true, true, true, true, true, true, true, true, 'Premium remont, markaziy joylashuv')
  ) AS t(phone, region, district, address, building_number, room_number, floor, total_floors, latitude, longitude, rooms_count, area_m2, price_usd, target_gender, max_guests, available_spaces, wifi, gas, water, tv, ac, washing_machine, refrigerator, kitchen_appliances, description)
)
INSERT INTO listings (
  owner_id, region, district, address, building_number, room_number, floor, total_floors,
  latitude, longitude, rooms_count, area_m2, price_usd, target_gender, source,
  max_guests, available_spaces, amenities, images, description, is_premium, premium_expires_at, is_active, views_count
)
SELECT
  u.id, a.region, a.district, a.address, a.building_number, a.room_number, a.floor, a.total_floors,
  a.latitude, a.longitude, a.rooms_count, a.area_m2, a.price_usd, a.target_gender::listing_target_gender, 'owner'::listing_source,
  a.max_guests, a.available_spaces,
  json_build_object(
    'wifi', a.wifi, 'gas', a.gas, 'water', a.water, 'tv', a.tv,
    'ac', a.ac, 'washing_machine', a.washing_machine,
    'refrigerator', a.refrigerator, 'kitchen_appliances', a.kitchen_appliances
  ),
  ARRAY[
    'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267',
    'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688'
  ]::text[],
  a.description,
  false,
  NULL,
  true,
  (100 + floor(random() * 200))::int
FROM owner_ads a
JOIN users u ON u.phone = a.phone
WHERE NOT EXISTS (
  SELECT 1 FROM listings l
  WHERE l.owner_id = u.id AND l.address = a.address
);

WITH makler_users AS (
  SELECT id, full_name, phone, row_number() OVER (ORDER BY phone) AS idx
  FROM users
  WHERE role = 'makler'::user_role
    AND phone IN ('+998902001001', '+998902001002', '+998902001003', '+998902001004', '+998902001005')
),
normal_ads AS (
  SELECT
    m.id AS owner_id,
    'Andijon'::text AS region,
    (ARRAY['Andijon shahri', 'Asaka tumani', 'Shahrixon tumani', 'Baliqchi tumani', 'Xo''jaobod tumani'])[(n % 5) + 1]::text AS district,
    format('Makler-%s oddiy e''lon %s, Andijon', m.idx, n)::text AS address,
    format('MK%s', m.idx)::text AS building_number,
    (10 + n)::text AS room_number,
    ((n % 6) + 1)::int AS floor,
    9::int AS total_floors,
    (40.76 + (m.idx * 0.02) + (n * 0.002))::float AS latitude,
    (72.30 + (m.idx * 0.015) + (n * 0.002))::float AS longitude,
    (1 + (n % 3))::int AS rooms_count,
    (42 + (n * 4))::int AS area_m2,
    (140 + (n * 18) + (m.idx * 5))::int AS price_usd,
    (ARRAY['male','female','mixed'])[(n % 3) + 1]::listing_target_gender AS target_gender,
    (2 + (n % 3))::int AS max_guests,
    (1 + (n % 2))::int AS available_spaces,
    json_build_object(
      'wifi', true, 'gas', true, 'water', true, 'tv', (n % 2 = 0),
      'ac', (n % 3 = 0), 'washing_machine', true,
      'refrigerator', true, 'kitchen_appliances', true
    ) AS amenities,
    format('Makler oddiy e''lon #%s. Broker: %s', n, m.full_name)::text AS description,
    false AS is_premium,
    NULL::timestamptz AS premium_expires_at
  FROM makler_users m
  CROSS JOIN generate_series(1, 5) AS n
),
premium_ads AS (
  SELECT
    m.id AS owner_id,
    'Andijon'::text AS region,
    (ARRAY['Andijon shahri', 'Asaka tumani', 'Shahrixon tumani', 'Marhamat tumani', 'Andijon shahri'])[(n % 5) + 1]::text AS district,
    format('Makler-%s PREMIUM e''lon %s, markaz', m.idx, n)::text AS address,
    format('PM%s', m.idx)::text AS building_number,
    (30 + n)::text AS room_number,
    ((n % 8) + 2)::int AS floor,
    10::int AS total_floors,
    (40.80 + (m.idx * 0.015) + (n * 0.003))::float AS latitude,
    (72.33 + (m.idx * 0.012) + (n * 0.003))::float AS longitude,
    (2 + (n % 2))::int AS rooms_count,
    (58 + (n * 6))::int AS area_m2,
    (240 + (n * 25) + (m.idx * 10))::int AS price_usd,
    'mixed'::listing_target_gender AS target_gender,
    4::int AS max_guests,
    1::int AS available_spaces,
    json_build_object(
      'wifi', true, 'gas', true, 'water', true, 'tv', true,
      'ac', true, 'washing_machine', true,
      'refrigerator', true, 'kitchen_appliances', true
    ) AS amenities,
    format('Premium kvartira. Broker: %s', m.full_name)::text AS description,
    true AS is_premium,
    (now() + interval '30 days')::timestamptz AS premium_expires_at
  FROM makler_users m
  CROSS JOIN generate_series(1, 2) AS n
),
all_makler_ads AS (
  SELECT * FROM normal_ads
  UNION ALL
  SELECT * FROM premium_ads
)
INSERT INTO listings (
  owner_id, region, district, address, building_number, room_number, floor, total_floors,
  latitude, longitude, rooms_count, area_m2, price_usd, target_gender, source,
  max_guests, available_spaces, amenities, images, description, is_premium, premium_expires_at, is_active, views_count
)
SELECT
  a.owner_id, a.region, a.district, a.address, a.building_number, a.room_number, a.floor, a.total_floors,
  a.latitude, a.longitude, a.rooms_count, a.area_m2, a.price_usd, a.target_gender, 'makler'::listing_source,
  a.max_guests, a.available_spaces, a.amenities,
  ARRAY[
    'https://images.unsplash.com/photo-1560185127-6ed189bf02f4',
    'https://images.unsplash.com/photo-1484154218962-a197022b5858'
  ]::text[],
  a.description, a.is_premium, a.premium_expires_at, true, (150 + floor(random() * 300))::int
FROM all_makler_ads a
WHERE NOT EXISTS (
  SELECT 1 FROM listings l
  WHERE l.owner_id = a.owner_id AND l.address = a.address
);
