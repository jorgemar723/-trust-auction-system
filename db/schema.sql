/*
===========================================================
Purpose:
This file defines the structure of the "users" table.
This table stores all user account information required
for authentication and identification in the TRUST system.

This version is designed for PostgreSQL.

Features:
- Unique email constraint
- Auto-incrementing primary key
- Timestamp tracking
- Account status flag
===========================================================
*/

CREATE TABLE IF NOT EXISTS users (

    /*
    user_id:
    - Unique identifier for each user
    - SERIAL automatically generates incrementing IDs
    - Primary key ensures uniqueness
    */
    user_id SERIAL PRIMARY KEY,

    /*
    email:
    - User's email address
    - Used for login
    - MUST be unique (no duplicate accounts allowed)
    - NOT NULL means user must provide email
    */
    email TEXT NOT NULL UNIQUE,

    /*
    password_hash:
    - Stores the encrypted password
    - NEVER store plain text passwords
    - Will be generated using bcrypt or similar hashing algorithm
    */
    password_hash TEXT NOT NULL,

    /*
    created_at:
    - Stores when the account was created
    - Automatically set using CURRENT_TIMESTAMP
    */
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    /*
    updated_at:
    - Stores last time user data was updated
    - Initially same as created_at
    */
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    /*
    is_active:
    - Indicates if the account is active
    - TRUE = active
    - FALSE = disabled
    */
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    /*
    wallet_address:
    - Stores the user's cryptocurrency wallet address
    - Used for transactions and bidding in the TRUST system
    - MUST be unique to prevent multiple accounts sharing the same wallet
    - NOT NULL means user must provide a wallet address
    */
    wallet_address TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS auctions (
    auction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    images JSONB DEFAULT '[]'::jsonb,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    starting_bid DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    highest_bid DECIMAL(12, 2) DEFAULT NULL,
    contract_address TEXT UNIQUE
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

-- Indexes
CREATE INDEX IF NOT EXISTS idx_bidding_auction_id ON bidding_history(auction_id);