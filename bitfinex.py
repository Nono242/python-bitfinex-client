# -*- coding: utf-8 -*-

#from functools import wraps
import hmac
import hashlib
import time
import warnings
import json
import base64

import requests

class BitfinexError(Exception):
    pass

"""
class TransRange(object):
"""
    #Enum like object used in transaction method to specify time range
    #from which to get list of transactions
"""
    HOUR = 'hour'
    MINUTE = 'minute'
"""
class BaseClient(object):
    """
    A base class for the API Client methods that handles interaction with
    the requests library.
    """
    api_url = 'https://api.bitfinex.com/v1/'
    exception_on_error = True
    symbols = []

    def __init__(self, proxydict=None, *args, **kwargs):
        self.proxydict = proxydict
        # Request available symbols
        self.symbols = self._get("symbols/", return_json=True)

    def _check_symbol(self, symbol):
        """
        Check if symbol is availble. If not raise a BitfinexError
        """
        if symbol.lower() in self.symbols:
            return True
        else:
            # Raise an error, the symbol is not avalaible.
            raise BitfinexError("Symbol not supported")
            return False

    def _get(self, *args, **kwargs):
        """
        Make a GET request.
        """
        return self._request(requests.get, *args, **kwargs)

    def _post(self, *args, **kwargs):
        """
        Make a POST request.
        """
        data = {}
        data['X-BFX-APIKEY'] = self.key

        msg={ 'request' : '/v1/' + args[0]}
        msg.update(self._default_data(*args, **kwargs))
        if 'data' in kwargs:
            msg.update(kwargs.pop('data'))
        data['X-BFX-PAYLOAD'] = base64.standard_b64encode(json.dumps(msg))

        signature = hmac.new(
            self.secret.encode('utf-8'), msg=data['X-BFX-PAYLOAD'].encode('utf-8'),
            digestmod=hashlib.sha384).hexdigest()
        data['X-BFX-SIGNATURE'] = signature

        kwargs['headers'] = data
        return self._request(requests.post, *args, **kwargs)

    def _default_data(self, *args, **kwargs):
        """
        Default data for a POST request.
        """
        return {}

    def _request(self, func, url, *args, **kwargs):
        """
        Make a generic request, adding in any proxy defined by the instance.
        Raises a ``requests.HTTPError`` if the response status isn't 200, and
        raises a :class:`BitfinexError` if the response contains a json encoded
        error message.
        """
        return_json = kwargs.pop('return_json', False)
        url = self.api_url + url
        
        response = func(url, *args, **kwargs)

        if 'proxies' not in kwargs:
            kwargs['proxies'] = self.proxydict

        # Check for error, raising an exception if appropriate.
        response.raise_for_status()

        try:
            json_response = response.json()
        except ValueError:
            json_response = None
        if isinstance(json_response, dict):
            error = json_response.get('error')
            if error:
                raise BitfinexError(error)

        if return_json:
            if json_response is None:
                raise BitfinexError(
                    "Could not decode json for: " + response.text)
            return json_response

        return response

class Public(BaseClient):

    def ticker(self, symbol ='BTCUSD'):
        """
        Returns dictionary.
        mid	[price]	(bid + ask) / 2
        bid	[price]	Innermost bid.
        ask	[price]	Innermost ask.
        last_price	[price]	The price at which the last order executed.
        low	[price]	Lowest trade price of the last 24 hours
        high	[price]	Highest trade price of the last 24 hours
        volume	[price]	Trading volume of the last 24 hours
        timestamp	[time]	The timestamp at which this information was valid.
        """
        if self._check_symbol (symbol):
            return self._get("pubticker/" + symbol.lower(), return_json=True)

    def stats(self, symbol ='BTCUSD'):
        """
        Returns dictionary.
        period	[integer]	period covered in days
        volume	[price]	volume
        """
        if self._check_symbol (symbol):
            return self._get("stats/" + symbol.lower(), return_json=True)

    def fundingbook(self, currency ='USD', limit_bids = None, limit_asks = None):
        """
        Returns dictionary.
        bids	[array of funding bids]	
            rate	[rate in % per 365 days]	
            amount	[decimal]	
            period	[days]	minimum period for the margin funding contract
            timestamp	[time]	
            frr	                [yes/no]	“Yes” if the offer is at Flash Return Rate, “No” if the offer is at fixed rate
        asks	[array of funding offers]	
            rate	[rate in % per 365 days]	
            amount	[decimal]	
            period	[days]	maximum period for the funding contract
            timestamp	[time]	
            frr	                [yes/no]	“Yes” if the offer is at Flash Return Rate, “No” if the offer is at fixed rate
        """
        params = {}
        if limit_bids is not None:
            params.update({'limit_bids': limit_bids})
        if limit_asks is not None:
            params.update({'limit_asks': limit_asks})
        return self._get("lendbook/" + currency.lower(), params = params, return_json=True)

    def orderbook(self, symbol ='BTCUSD', limit_bids = None, limit_asks = None, group = None):
        """
        Returns dictionary.
        bids	[array]
        price	[price]
        amount	[decimal]
        timestamp	[time]
        asks	[array]
        price	[price]
        amount	[decimal]
        timestamp	[time]        
        """
        if self._check_symbol (symbol):
            params = {}
            if limit_bids is not None:
                params.update({'limit_bids': limit_bids})
            if limit_asks is not None:
                params.update({'limit_asks': limit_asks})
            if limit_asks is not None:
                params.update({'group': group})
            return self._get("book/" + symbol.lower(), params = params, return_json=True)

    def trades(self, symbol ='BTCUSD', timestamp = None, limit_trades = None):
        """
        Returns dictionary.
        tid	[integer]	
        timestamp	[time]	
        price	[price]	
        amount	[decimal]	
        exchange	[string]	
        type	[string]	“sell” or “buy” (can be “” if undetermined)
        """
        if self._check_symbol (symbol):
            params = {}
            if timestamp is not None:
                params.update({'timestamp': timestamp})
            if limit_trades is not None:
                params.update({'limit_trades': limit_trades})
            return self._get("trades/" + symbol.lower(), params = params, return_json=True)

    def lends(self, currency ='USD', timestamp = None, limit_trades = None):
        """
        Returns dictionary.
        rate	[decimal, % by 365 days]	Average rate of total funding received at fixed rates, ie past Flash Return Rate annualized
        amount_lent	[decimal]	Total amount of open margin funding in the given currency
        amount_used	[decimal]	Total amount of open margin funding used in a margin position in the given currency
        timestamp	[time]        
        """
        params = {}
        if timestamp is not None:
            params.update({'timestamp': timestamp})
        if limit_trades is not None:
            params.update({'limit_trades': limit_trades})
        return self._get("lends/" + currency, params = params, return_json=True)

class Trading(Public):

    def __init__(self, username, key, secret, *args, **kwargs):
        """
        Stores the username, key, and secret which is used when making POST
        requests to Bitfinex.
        """
        super(Trading, self).__init__(
            username=username, key=key, secret=secret, *args, **kwargs)
        self.username = username
        self.key = key
        self.secret = secret

    def get_nonce(self):
        """
        Get a unique nonce for the bitfinex API.
        This integer must always be increasing, so use the current unix time.
        Every time this variable is requested, it automatically increments to
        allow for more than one API request per second.
        This isn't a thread-safe function however, so you should only rely on a
        single thread if you have a high level of concurrent API requests in
        your application.
        """
        nonce = getattr(self, '_nonce', 0)
        if nonce:
            nonce += 1
        # If the unix time is greater though, use that instead (helps low
        # concurrency multi-threaded apps always call with the largest nonce).
        self._nonce = max(int(time.time()), nonce)
        return self._nonce

    def _default_data(self, *args, **kwargs):
        """
        Generate a one-time signature and other data required to send a secure
        POST request to the Bitfinex API.
        """
        nonce = self.get_nonce()
        return { 'nonce' : str(nonce)}

    #def _expect_true(self, response):
        """
        A shortcut that raises a :class:`BitfinexError` if the response didn't
        just contain the text 'true'.
        """
        #if response.text == u'true':
            #return True
        #raise BitfinexError("Unexpected response")

    def account_info(self):
        """
        Return information about your account (trading fees).
        Input:
            NONE

        Output: List of dictionaries
            pairs	[string]	The currency included in the pairs with this fee schedule
            maker_fees	[decimal]	Your current fees for maker orders (limit orders not marketable, in percent)
            taker_fees	[decimal]	Your current fees for taker orders (marketable order, in percent)
        """
        return self._post("account_infos", return_json=True)

    def historical_balance(self, currency, since = None, until = None, limit = None, wallet = None):
        """
        Returns all of your balance ledger entries.

        Input:
            currency	[string]	The currency to look for.
            since	[time]	Optional. Return only the history after this timestamp.
            until	[time]	Optional. Return only the history before this timestamp.
            limit	[int]	Optional. Limit the number of entries to return. Default is 500.
            wallet	[string]	Optional. Return only entries that took place in this wallet. Accepted inputs are: trading, exchange, deposit.

        Output: List of dictionaries
            currency	[string]	Currency
            amount	[decimal]	Positive (credit) or negative (debit)
            balance	[decimal]	Wallet balance after the current entry
            description	[string]	Description of the entry. Includes the wallet in which the operation took place
            timestamp	[time]	Timestamp of the entry
        """
        data = {'currency': currency}
        if since is not None:
            data.update({'since': since})
        if until is not None:
            data.update({'until': until})
        if limit is not None:
            data.update({'limit': limit})
        if wallet is not None:
            data.update({'wallet': wallet})

        return self._post("history", data=data, return_json=True)

    def historical_movements(self, currency, method = None, since = None, until = None, limit = None):
        """
        Returns all of  your past deposits/withdrawals.

        Input:
            currency	[string]	The currency to look for.
            method	[string]	Optional. The method of the deposit/withdrawal (can be bitcoin, litecoin, darkcoin, wire).
            since	[time]	Optional. Return only the history after this timestamp.
            until	[time]	Optional. Return only the history before this timestamp.
            limit	[int]	Optional. Limit the number of entries to return. Default is 500.

        Output: List of dictionaries
            currency	[string]	
            method	[string]	
            type	[string]	
            amount	[decimal]	Absolute value of the movement
            description	[string]	Description of the movement (txid, destination address,,,,)
            status	[string]	Status of the movement
            timestamp	[time]	Timestamp of the movement
        """
        data = {'currency': currency}
        if method is not None:
            data.update({'method': method})
        if since is not None:
            data.update({'since': since})
        if until is not None:
            data.update({'until': until})
        if limit is not None:
            data.update({'limit': limit})

        return self._post("history/movements", data=data, return_json=True)
