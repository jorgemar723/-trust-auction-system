from db.repositories.user_repository import UserRepository
from db.repositories.auction_repository import AuctionRepository
from db.repositories.bid_repository import BidRepository
from db.repositories.watchlist_repository import WatchlistRepository


def get_user_repository():
    return UserRepository()


def get_auction_repository():
    return AuctionRepository()


def get_bid_repository():
    return BidRepository()


def get_watchlist_repository():
    return WatchlistRepository()