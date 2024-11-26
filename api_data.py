import os
from dotenv import load_dotenv
import requests
import json
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timezone, timedelta
import tzlocal

load_dotenv()
api_key = os.getenv('API_KEY')

class API_Handler:

    def __init__(self, api_key, ticker, security_type, strike_limit):
        self.api_key = api_key
        self.ticker = ticker
        self.security_type = security_type
        self.strike_limit = strike_limit

        # Setting up the headers for authentication
        self.headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        self.options_data = None
        self.spot_price = None
        self.options_data_date = None
        self.options_data_time = None
        

    def fetch_all_data_to_attributes(self):

        spot_price = self.fetch_security_quote()
        
        # The API endpoint for retrieving stock quotes for SPY
        today = datetime.today().strftime("%Y-%m-%d")
        date_6_months_later = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")

        url = f'https://api.marketdata.app/v1/options/chain/{self.ticker}/?from={today}&to={date_6_months_later}&strike_limit={self.strike_limit}&minOpenInterest=1&minVolume=1'

        response = requests.get(url, headers=self.headers)


        if response_successful(response):
            data = response.json()

            options_df = create_df_from_api_data(data)
            self.options_data = options_df
            self.spot_price = spot_price

            options_data_timestamp = options_df['updated'].iloc[0] # Takes any date from when the data was fetched
            options_data_date = options_data_timestamp.strftime("%d/%m/%Y")
            options_data_time = options_data_timestamp.strftime("%H:%M:%S %p")
            self.options_data_date = options_data_date
            self.options_data_time = options_data_time          
        else:
            print(f'Failed to retrieve data: {response.status_code}')        

    def fetch_security_quote(self):

        """
        Fetches the API data for the security of the ticker
        returns: quote, ticker 
        """

        url = f'https://api.marketdata.app/v1/{self.security_type}/quotes/{self.ticker}/'

        # Making the GET request to the API
        response = requests.get(url, headers=self.headers)

        if response_successful(response):
            data = response.json()
            quote = data['last'][0]
            return quote
        else:
            print(f'Failed to retrieve data: {response.status_code}')


def create_df_from_api_data(data):

    number_of_contracts = len(data["optionSymbol"])

    with open(f'data_files/data2.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=5)

    option_dict = {
        "option_type": [],
        "strike": [],
        "expiration": [],
        "open_interest": [],
        "volume": [],
        "gamma": [],
        "updated": []

    }

    for i in range(number_of_contracts):

        contract_type = data["side"][i]
        strike_price = data["strike"][i]
        expiration_date = data["expiration"][i]
        expiration_date = convert_unix_to_date(expiration_date, exact_time=False)
        
        volume = data["volume"][i]
        open_interest = data["openInterest"][i]
        gamma = data["gamma"][i]
        updated = data["updated"][i]
        updated = convert_unix_to_date(updated, exact_time=True)
        updated = convert_datetime_to_local_time(updated)


        # Avoid this contract if it misses some data
        if any(var is None for var in [volume, open_interest,gamma]):
            continue
            #open_interest = 0
            #gamma = 0
            #volume = 0

        option_dict["option_type"].append(contract_type)
        option_dict["strike"].append(strike_price)
        option_dict["expiration"].append(expiration_date)
        option_dict["open_interest"].append(open_interest)
        option_dict["volume"].append(volume)
        option_dict["gamma"].append(gamma)
        option_dict["updated"].append(updated)

    options_df = pd.DataFrame(option_dict)
    return options_df

def format_ticker_for_api(ticker, security_type):

    """
    Makes sure to reformat the ticker if it is a indice so it works with the MarketData API
    returns: ticker
    """
    if security_type == 'indices':
        return 'I:' + ticker
    else:
        return ticker

        
def response_successful(response):

    if response.status_code in (200, 203):
        return True
    else:
        print(f'Failed to retrieve data: {response.status_code}')


def get_security_type(ticker):

    security_info = yf.Ticker(ticker).info
    security_type = security_info.get('quoteType')

    if security_type in ('INDEX', 'MUTUALFUND'):
        return 'indices'
    elif security_type in ('EQUITY', 'ETF'):  # Changed 'EFT' to 'ETF'
        return 'stocks'
    else:
        print(f'This is not a valid ticker {ticker}')
        return 'not_a_stock_or_index'

def convert_unix_to_date(unix_time, exact_time=False):

    date = datetime.fromtimestamp(unix_time, tz=timezone.utc)

    if exact_time:
        return date
    else:
        return date.strftime("%Y-%m-%d") 

def convert_datetime_to_local_time(datetime_object):
    # Get the local timezone
    local_timezone = tzlocal.get_localzone()

    # Check if the datetime object is naive
    if datetime_object.tzinfo is None:
        # Localize the naive datetime to UTC timezone
        utc_datetime = pytz.utc.localize(datetime_object)
    else:
        # If it's already timezone-aware, convert it to UTC if necessary
        utc_datetime = datetime_object.astimezone(pytz.utc)

    # Convert to local timezone
    local_datetime = utc_datetime.astimezone(local_timezone)

    return local_datetime


'''
new_api= API_Handler(api_key, "AAPL", "stocks", 10)

new_api.fetch_all_data_to_attributes()

print(new_api.options_data)
'''