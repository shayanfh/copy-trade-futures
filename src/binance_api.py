import json
import datetime
from datetime import datetime
from lib2to3.pygram import Symbols
# from binance.futures import Futures as Client
from binance.um_futures import UMFutures as Client
import logging
from binance.lib.utils import config_logging
from binance.error import ClientError
import decimal


class Order():
    BUY = 'BUY'
    SELL = 'SELL'

    TYPE_LIMIT = 'LIMIT'
    TYPE_STOP = 'STOP'
    TYPE_STOP_MARKET = 'STOP_MARKET'
    TYPE_TAKE_PROFIT = 'TAKE_PROFIT'
    TYPE_TRAILING_STOP_MARKET = 'TRAILING_STOP_MARKET'
    TYPE_MARKET = 'MARKET'


class Binance():

    def __init__(self, key: str = "", secret: str = "", testnet=False, proxy: str = None):
        proxies = None
        if proxy:
            proxies = {'https': 'http://'+proxy}

        if testnet:
            base_url = 'https://testnet.binancefuture.com'
            self.client = Client(base_url=base_url)
        else:
            base_url = None
            self.client = Client(key, secret, proxies=proxies)

        self.order = Order()

    def get_balance(self):
        response = self.client.balance()
        for asset in response:
            if asset['asset'] == 'USDT':
                balance = asset['balance']
        return float(balance)

    def min_amount_trade(self, symbol):
        response = self.client.exchange_info()

        # Get all symbols
        symbols = response['symbols']
        # Get one symbol
        symbol = [_symbol for _symbol in symbols if _symbol['symbol'] == symbol][0]
        # Choose LOT_SIZE filter and get stepSize
        step_size = [_filter for _filter in symbol['filters']
                     if _filter['filterType'] == 'LOT_SIZE'][0]['stepSize']

        return float(step_size)

    def min_amount_trade_usdt(self, symbol):
        min_amount_trade = self.min_amount_trade(symbol)
        price = self.get_price(symbol)

        return price*min_amount_trade

    def get_order(self, symbol, ClientOrderId):
        response = self.client.get_all_orders(
            symbol=symbol,
        )
        currect_order = [
            order for order in response if order['clientOrderId'] == ClientOrderId]
        if len(currect_order) != 0:
            currect_order = currect_order[0]
        else:
            currect_order = None
        return currect_order

    def get_price(self, symbol):
        response = self.client.ticker_price(
            symbol=symbol)
        price = float(response['price'])

        return price

    def set_leverage(self, symbol, leverage):
        response = self.client.change_leverage(
            symbol=symbol,
            leverage=leverage)
        return response

    def cancel_order(self, symbol, kind):
        # price = binance.get_price(symbol)
        position = self.get_position(symbol)
        print(position)
        size = abs(float(position['positionAmt']))
        print(size)

        if kind == 'long':
            side = self.order.SELL
        else:
            side = self.order.BUY

        params = {
            "symbol": symbol,
            "side": side,
            "type": self.order.TYPE_MARKET,
            "quantity": size,
            # "timeInForce": "GTC",
            "reduceOnly": 'true',
            "priceProtect": 'true',
        }

        response = self.client.new_order(**params)
        return response

    def cancel_open_order(self, symbol, ClientOrderId, orderId):
        response = self.client.cancel_order(
            symbol=symbol,
            origClientOrderId=ClientOrderId,
            orderId=orderId)

        return response

    def stoplimit_long(self, symbol, stop_price, price, size, ClientOrderId=None):
        price_now = self.get_price(symbol)
        # choose STOP or TAKE_PROFIT type for BUY
        if price_now < stop_price:
            type = self.order.TYPE_STOP
        else:
            type = self.order.TYPE_TAKE_PROFIT

        params = {
            "symbol": symbol,
            "side": self.order.BUY,
            "type": type,
            "price": price,
            "stopPrice": stop_price,
            "quantity": size,
            "newClientOrderId": ClientOrderId
        }

        response = self.client.new_order(**params)
        return response

    def stoplimit_short(self, symbol, stop_price, price, size, ClientOrderId=None):
        price_now = self.get_price(symbol)
        # choose STOP or TAKE_PROFIT type for BUY
        if price_now > stop_price:
            type = self.order.TYPE_STOP
        else:
            type = self.order.TYPE_TAKE_PROFIT

        params = {
            "symbol": symbol,
            "side": self.order.SELL,
            "type": type,
            "price": price,
            "stopPrice": stop_price,
            "quantity": size,
            "newClientOrderId": ClientOrderId
        }

        response = self.client.new_order(**params)
        return response

    def market_long(self, symbol, size, ClientOrderId=None):
        params = {
            "symbol": symbol,
            "side": self.order.BUY,
            "type": self.order.TYPE_MARKET,
            "quantity": size,
            "newClientOrderId": ClientOrderId
        }

        response = self.client.new_order(**params)
        return response

    def market_short(self, symbol, size, ClientOrderId=None):
        params = {
            "symbol": symbol,
            "side": self.order.SELL,
            "type": self.order.TYPE_MARKET,
            "quantity": size,
            "newClientOrderId": ClientOrderId
        }

        response = self.client.new_order(**params)
        return response

    def limit_long(self, symbol, price, size, ClientOrderId=None):
        params = {
            "symbol": symbol,
            "side": self.order.BUY,
            "type": self.order.TYPE_LIMIT,
            "price": price,
            "reduceOnly": "true",
            "timeInForce": "GTC",
            "quantity": size,
            "newClientOrderId": ClientOrderId
        }

        response = self.client.new_order(**params)
        return response

    def limit_short(self, symbol, price, size, ClientOrderId=None):
        params = {
            "symbol": symbol,
            "side": self.order.SELL,
            "type": self.order.TYPE_LIMIT,
            "price": price,
            "reduceOnly": "true",
            "timeInForce": "GTC",
            "quantity": size,
            "newClientOrderId": ClientOrderId
        }

        response = self.client.new_order(**params)
        return response

    def stoploss_long(self, symbol, stop_price, ClientOrderId=None):
        params = {
            "symbol": symbol,
            "side": self.order.BUY,
            "type": self.order.TYPE_STOP_MARKET,
            "stopPrice": stop_price,
            "timeInForce": "GTC",
            "closePosition": 'true',
            "priceProtect": 'true',
            "newClientOrderId": ClientOrderId
        }

        response = self.client.new_order(**params)
        return response

    def stoploss_short(self, symbol, stop_price, ClientOrderId=None):
        params = {
            "symbol": symbol,
            "side": self.order.SELL,
            "type": self.order.TYPE_STOP_MARKET,
            "stopPrice": stop_price,
            "timeInForce": "GTC",
            "closePosition": 'true',
            "priceProtect": 'true',
            "newClientOrderId": ClientOrderId
        }

        response = self.client.new_order(**params)
        return response

    def trailing_stop_long(self, symbol, activation_price, size):
        params = {
            "symbol": symbol,
            "side": self.order.BUY,
            "type": self.order.TYPE_TRAILING_STOP_MARKET,
            "activationPrice": activation_price,
            "callbackRate": 0.4,
            "quantity": size,
            "reduceOnly": "true",
        }

        response = self.client.new_order(**params)
        return response

    def trailing_stop_short(self, symbol, activation_price, size):
        params = {
            "symbol": symbol,
            "side": self.order.SELL,
            "type": self.order.TYPE_TRAILING_STOP_MARKET,
            "activationPrice": activation_price,
            "callbackRate": 0.4,
            "quantity": size,
            "reduceOnly": "true",
        }

        response = self.client.new_order(**params)
        return response

    def get_decimal_coin(self, symbol):
        response = self.client.historical_trades(symbol=symbol, limit=1)
        # print(response)
        qty = response[0]['qty']

        # if not decimal
        if float(qty) % 1 == 0.0:
            qty = int(float(qty))

        _decimal = decimal.Decimal(str(qty)).as_tuple().exponent

        return abs(_decimal)

    def get_decimal_coin_price(self, symbol):
        response = self.client.historical_trades(symbol=symbol, limit=1)
        qty = float(response[0]['price'])

        _decimal = decimal.Decimal(str(qty)).as_tuple().exponent

        return abs(_decimal)

    def get_position(self, symbol):
        response = self.client.get_position_risk(symbol=symbol)
        return response[0]

    def change_margin_type(self, symbol, type="CROSSED"):
        response = self.client.change_margin_type(symbol, type)
        return response

    def get_last_pnl(self, symbol, start_time, end_time):
        # params = {
        #     "symbol": "TOMOUSDT",
        #     "incomeType": "REALIZED_PNL",
        #     "startTime": 1660219800000,
        #     "endTime": 1660224600000,
        # }
        params = {
            "symbol": symbol,
            "incomeType": "REALIZED_PNL",
            "startTime": start_time,
            "endTime": end_time,
        }
        response = self.client.get_income_history(**params)
        pnls = 0
        for trade in response:
            # print(trade)
            # if trade['side'] == 'SELL':
            # pnls += float(trade['realizedPnl'])
            pnls += float(trade['income'])
        return pnls

    def test(self):
        params = {
            "symbol": "TOMOUSDT",
            "startTime": 1660219800000,
            "endTime": 1660224600000,
        }
        req = self.client.get_account_trades(**params)
        return req


# Example usage:
# binance = Binance(key="your_api_key", secret="your_secret", proxy="http://proxy:port")
# balance = binance.get_balance()
# print(balance)
