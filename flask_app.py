from flask import Flask, render_template, request, redirect, url_for, flash
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

WATCHLIST = []

@app.route('/')
def index():
    return render_template('index.html', auctions=AUCTIONS)

@app.route('/auction/<int:auction_id>', methods=['GET', 'POST'])
def detail(auction_id):
    # Find the specific auction from our mock data list
    auction = next((a for a in AUCTIONS if a['id'] == auction_id), None)
    if not auction:
        return "Auction not found", 404
    
    # Mock bid history for the table
    history = [
        {"user": "0x71C...a2E", "amount": "4.1 ETH", "time": "2 hours ago", "status": "Verified"},
        {"user": "0x32B...f11", "amount": "3.8 ETH", "time": "5 hours ago", "status": "Verified"},
        {"user": "0x99A...c43", "amount": "3.5 ETH", "time": "1 day ago", "status": "Verified"},
    ]
    
    if request.method == 'POST':
        new_bid = float(request.form.get('bid_amount', 0))
        
        # Validation: Is the bid high enough?
        if new_bid > auction['current_bid']:
            auction['current_bid'] = new_bid
            flash(f"Success! Your bid of {new_bid} ETH has been placed.", "success")
        else:
            flash(f"Bid failed. You must bid higher than {auction['current_bid']} ETH.", "danger")
        
        return redirect(url_for('detail', auction_id=auction_id))

    is_watched = auction_id in WATCHLIST
    return render_template('detail.html', auction=auction, is_watched=is_watched)

@app.route('/watchlist')
def view_watchlist():
    # Filter AUCTIONS to only show those whose ID is in WATCHLIST
    watched_items = [a for a in AUCTIONS if a['id'] in WATCHLIST]
    return render_template('watchlist.html', auctions=watched_items)

@app.route('/toggle-watchlist/<int:auction_id>')
def toggle_watchlist(auction_id):
    if auction_id in WATCHLIST:
        WATCHLIST.remove(auction_id)
        flash("Removed from watchlist.", "info")
    else:
        WATCHLIST.append(auction_id)
        flash("Added to watchlist.", "success")
    return redirect(request.referrer or url_for('index'))

if __name__ == '__main__':
    app.run(port=8000, debug=True)