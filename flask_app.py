from flask import Flask, render_template, jsonify

app = Flask(__name__)

#Tries to use real blockchain-backed state pipeline (backend.mainauction)
# In case it fails, (not deployed or missing dependencies)

try:
    from backend.mainauction import get_state  # Flask -> mainauction -> state.py -> Hardhat
except Exception as e:
    get_state = None
    _backend_import_error = str(e)

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
    # Find the auction by ID or return 404
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
        return jsonify({
            "error": "backend.mainauction import failed",
            "details": _backend_import_error
        }), 500

    try:
        state = get_state()
        return jsonify(state)
    except Exception as e:
        return jsonify({
            "error": "failed to fetch on-chain state",
            "details": str(e)
        }), 500
    

if __name__ == '__main__':
    app.run(debug=True)