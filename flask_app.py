from __future__ import annotations

from flask import Flask, render_template, jsonify

app = Flask(__name__)

get_state = None
_backend_import_error = None


#Tries to use real blockchain-backed state pipeline (backend.mainauction)
# In case it fails, /api/state will return a structured error response.
    
try:
    from backend.mainauction import get_state as _get_state  # Flask -> mainauction -> state.py -> Hardhat     
    get_state = _get_state
except Exception as e:
    _backend_import_error = str(e)


def error_json(code: str, message: str, details: str | None = None, http_status: int = 500):
    payload = {
        "ok": False,
        "error": {"code": code, "message": message},
    }
    if details:
        payload["details"] = details
    return jsonify(payload), http_status

# Mock Data: Simulating a database of active auctions
AUCTIONS = [
    {
        "id": 1,
        "title": "Vintage Rolex Submariner",
        "current_bid": "4.2 ETH",
        "image": "Rolex.jpg",
        "description": "Certified authentic 1970s diving watch."
    },
    {
        "id": 2,
        "title": "Unopened 1st Ed. Charizard",
        "current_bid": "12.5 ETH",
        "image": "Charizard.jpg",
        "description": "Mint condition, PSA 10 candidate."
    },
    {
        "id": 3,
        "title": "Bored Ape Yacht Club #772",
        "current_bid": "65.0 ETH",
        "image": "NFT.jpg",
        "description": "Rare gold fur trait. Smart contract verified."
    }
]

@app.route('/')
def index():
    return render_template('index.html', auctions=AUCTIONS)

@app.route('/auction/<int:auction_id>')
def detail(auction_id):
    auction = next((a for a in AUCTIONS if a['id'] == auction_id), None)
    return render_template('detail.html', auction=auction)

# PROJ-38: Real Auction state endpoint

@app.route("/api/state")
def api_state():
    """
    Returns live auction state from the backend wiring:
    Flask -> backend.mainauction -> backend.state -> Hardhat
    """
    if get_state is None:
        return error_json(
            "BACKEND_IMPORT_FAILED",
            "Backend import failed.",
            _backend_import_error,
            500,
        )

    try:
        state = get_state()
        # keep success shape simple for now (you can wrap later if you want)
        return jsonify(state)
    except Exception as e:
        return error_json(
            "CHAIN_CALL_FAILED",
            "Failed to fetch on-chain state.",
            str(e),
            500,
        )
    

if __name__ == '__main__':
    app.run(debug=True)