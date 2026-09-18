# Historical data loader

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from utils.config_loader import logger

api_key = "PKOZXTHYCD7VTBXATV5WOBVDCB"
api_secret = "8MMU6kSyGfebWUYmZYKNQkegNfPhMqRS1QkPBTh7JoQ6"

client = StockHistoricalDataClient(api_key, api_secret)

# multi symbol request - single symbol is similar
multisymbol_request_params = StockLatestQuoteRequest(symbol_or_symbols=["SPY", "GLD", "TLT"])

latest_multisymbol_quotes = client.get_stock_latest_quote(multisymbol_request_params)
logger.info(latest_multisymbol_quotes)



