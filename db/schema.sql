/*
===========================================================
Purpose:
This file defines the structure of the database tables
for the TRUST system.

This version is designed for PostgreSQL.

Features:
- Unique email constraint
- Auto-incrementing primary key for users
- Timestamp tracking
- Account status flag
===========================================================
*/

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    wallet_address TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS auctions (
    auction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    images JSONB DEFAULT '[]'::jsonb,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    starting_bid DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    highest_bid DECIMAL(12, 2) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS bidding_history (
    bid_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auction_id UUID NOT NULL REFERENCES auctions(auction_id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    bid_amount DECIMAL(12, 2) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    bid_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    wallet_address TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    auction_id UUID NOT NULL REFERENCES auctions(auction_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, auction_id)
);

CREATE INDEX IF NOT EXISTS idx_bidding_auction_id ON bidding_history(auction_id);