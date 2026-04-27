# Unit Testing Plan: PostgresDB Read Methods

## Overview
This document outlines the testing strategy for data retrieval methods located in `db/PostgresDB.py`. These tests verify that Python interacts correctly with the `psycopg2` driver to retrieve PostgreSQL records.

## Target Components
* **Class:** `PostgresDB`
* **File Path:** `db/PostgresDB.py`

## Tests to be Executed

### 1. `test_get_auctions`
* **Description:** Mocks the cursor `fetchall()` method to supply dummy auction rows.
* **Assertions:** Verifies the `cursor.execute()` is fired to run a query, the connection is safely closed, and the fields returned perfectly map to a 2D list array containing all rows.

### 2. `test_get_users`
* **Description:** Mocks the cursor `fetchall()` method to return mocked user tuples. 
* **Assertions:** Verifies that the precise SQL literal `SELECT * FROM users` is used, tests the iteration over the tuples, and verifies fields map directly to user emails and wallet addresses.

### 3. `test_get_starting_bid_for_auction`
* **Description:** Validates parameterized query binding. Supplies a mocked `fetchone()` return object resembling `(50.5,)`.
* **Assertions:** Verifies the target parameter `%s` binding takes `(auction_id,)` tuple, and that it extracts the scalar value properly (index 0) returning a raw float object instead of a tuple.
