-- Core extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('student', 'owner', 'makler', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    CREATE TYPE listing_target_gender AS ENUM ('erkak', 'ayol', 'aralash');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    CREATE TYPE listing_source AS ENUM ('owner', 'makler', 'exiting_student');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    CREATE TYPE payment_status AS ENUM ('tolangan', 'kutilmoqda', 'kechikkan');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    CREATE TYPE subscription_type AS ENUM ('owner_monthly', 'makler_s', 'makler_l');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    CREATE TYPE listing_payment_type AS ENUM ('oddiy', 'premium');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
    CREATE TYPE listing_payment_status AS ENUM ('tolangan', 'kutilmoqda');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ism VARCHAR(100) NOT NULL,
    telefon VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100),
    rol user_role NOT NULL,
    universitet VARCHAR(100),
    verified BOOLEAN DEFAULT FALSE,
    rasm_url TEXT,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    egasi_id UUID REFERENCES users(id),
    viloyat VARCHAR(100) NOT NULL,
    tuman VARCHAR(100) NOT NULL,
    manzil VARCHAR(255),
    dom_raqami VARCHAR(20),
    xona_raqami VARCHAR(20),
    qavat INTEGER,
    jami_qavat INTEGER,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    xonalar_soni INTEGER NOT NULL,
    maydon_m2 INTEGER,
    narx_usd INTEGER NOT NULL,
    jins listing_target_gender NOT NULL,
    manba listing_source NOT NULL,
    max_kishi INTEGER DEFAULT 1,
    bosh_joy INTEGER DEFAULT 1,
    qulayliklar JSONB DEFAULT '{}'::jsonb,
    rasmlar TEXT[] NOT NULL,
    tavsif TEXT,
    premium BOOLEAN DEFAULT FALSE,
    premium_tugash TIMESTAMP,
    faol BOOLEAN DEFAULT TRUE,
    korishlar INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rentals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID REFERENCES listings(id),
    talaba_id UUID REFERENCES users(id),
    boshlash DATE NOT NULL,
    tugash DATE,
    narx_usd INTEGER NOT NULL,
    faol BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rental_id UUID REFERENCES rentals(id),
    tolovchi_id UUID REFERENCES users(id),
    summa INTEGER NOT NULL,
    oy DATE NOT NULL,
    holat payment_status DEFAULT 'kutilmoqda',
    sana TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID REFERENCES listings(id),
    yozgan_id UUID REFERENCES users(id),
    baho INTEGER CHECK (baho BETWEEN 1 AND 5),
    matn TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (listing_id, yozgan_id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    tur subscription_type NOT NULL,
    boshlash DATE NOT NULL,
    tugash DATE NOT NULL,
    listing_limit INTEGER NOT NULL,
    ishlatilgan INTEGER DEFAULT 0,
    faol BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS listing_payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID REFERENCES listings(id),
    user_id UUID REFERENCES users(id),
    summa INTEGER NOT NULL,
    tur listing_payment_type NOT NULL,
    holat listing_payment_status DEFAULT 'kutilmoqda',
    created_at TIMESTAMP DEFAULT NOW()
);
