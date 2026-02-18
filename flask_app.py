from flask import Flask, render_template

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)