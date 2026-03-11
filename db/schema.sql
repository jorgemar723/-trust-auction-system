/*
Purpose:
This file defines the structure of the "users" table.
This table stores all user account information required
for authentication and identification in the TRUST system.

We are using SQLite for the MVP because:
- Easy to set up
- No server required
- Supports UNIQUE constraints
- Works well with Python
===========================================================
*/

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (

    /*
    user_id:
    - Unique identifier for each user
    - INTEGER PRIMARY KEY AUTOINCREMENT means:
        • Automatically assigns a unique number
        • Increases by 1 for each new user
        • Cannot be NULL
        • Used internally to identify users
    */
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),


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
    - NEVER store plain text passwords for security reasons
    - Will be generated using bcrypt or similar hashing algorithm
    - NOT NULL means password is required
    */
    password_hash TEXT NOT NULL,


    /*
    created_at:
    - Stores when the account was created
    - Automatically set using CURRENT_TIMESTAMP
    - Useful for tracking user registration date
    */
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,


    /*
    updated_at:
    - Stores last time user data was updated
    - Automatically set when user is created
    - Will be updated if user changes password or email
    */
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,


    /*
    is_active:
    - Indicates if the account is active
    - 1 = active
    - 0 = disabled
    - Allows disabling accounts without deleting them
    */
    is_active INTEGER NOT NULL DEFAULT 1

);

CREATE TABLE IF NOT EXISTS auctions (
    auction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    images JSONB DEFAULT '[]'::jsonb,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE TABLE IF NOT EXISTS bidding_history (
    bid_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    auction_id UUID NOT NULL REFERENCES auctions(auction_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    bid_amount DECIMAL(12, 2) NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    bid_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_bidding_auction_id ON bidding_history(auction_id);