import os
from dotenv import load_dotenv
import requests
import json
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timezone, timedelta
import tzlocal
import logging

load_dotenv()
api_key = os.getenv('API_KEY')

class API_Handler:
    """
    Handles fetching options data from an external API for a specific ticker symbol.

    Attributes:
    api_key (str): The API key required for authentication with the MarketData App API.
    ticker (str): The ticker symbol of the security for which options data is fetched.
    security_type (str): The type of security ('stocks', 'indices', or 'not_a_stock_or_index').
    strike_limit (int): The maximum number of strikes to be considered in the data request.
    headers (dict): The headers used to authenticate the API requests from the MarketData App API
    options_data (pd.DataFrame): Contains 'option_type', 'strike', 'expiration', 'volume', 'gamma', 'updated' data for each option contract
    spot_price (float): The price of a ticker fetched by the yfinance API
    options_data_date (str): The date (DD/MM/YYY) of when the options data was fetched from the MarketData App API
    options_data_time (str); The time (H:M:S AM/PM) of when the options data was fetched from the MarketData App API

    Methods:
    __init__(self, api_key, ticker, security_type, strike_limit):
        Initializes the API_Handler instance with provided API key, ticker, security type, and strike limit.
    fetch_all_data_to_attributes(self):
        Fetches options data and updates the class attributes with the retrieved information.
    """

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
        """
        Fetches options data for the given ticker and stores it as class attributes.

        This method fetches the spot price of the ticker, calculates the range of dates for 6 months ahead,
        and retrieves the options chain from the API. It then processes the data and updates relevant class 
        attributes like options data, spot price, and timestamp of the fetched data.

        Returns:
        None: This method updates internal attributes, but does not return anything.
        """

        spot_price = self.fetch_security_quote()
        
        # Set date range for the API request: today and 6 months later
        today = datetime.today().strftime("%Y-%m-%d")
        date_6_months_later = (datetime.now() + timedelta(days=180)).strftime("%Y-%m-%d")

        url = f'https://api.marketdata.app/v1/options/chain/{self.ticker}/?from={today}&to={date_6_months_later}&strike_limit={self.strike_limit}&minOpenInterest=1&minVolume=1'

        response = requests.get(url, headers=self.headers)


        if not response_successful(response):
            print(f'Failed to retrieve data: {response.status_code}')     
            return
        
        data = response.json()
        options_df = create_df_from_api_data(data)

        # Update the class attributes with the fetched data
        self.options_data = options_df
        self.spot_price = spot_price

        # Extract the timestamp of the fetched data and format it
        options_data_timestamp = options_df['updated'].iloc[0] # Takes any date from when the data was fetched
        options_data_date = options_data_timestamp.strftime("%d/%m/%Y")
        options_data_time = options_data_timestamp.strftime("%H:%M:%S %p")
        self.options_data_date = options_data_date
        self.options_data_time = options_data_time          

               

    def fetch_security_quote(self):
        """
        Fetches the API data for the security of the ticker from yfinance

        Returns:
        float: The quote of the ticker if the response was successful (status code 200 or 203)
        none: If the response was not successfull
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
    """
    Create a DataFrame from the API response data, processing option contracts.
    
    Parameters:
    data (dict): The raw API data containing option contracts information.
    
    Returns:
    pd.DataFrame: The DataFrame containing the processed option contract data.
    """
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
        # Process contract data for each option
        contract_data = process_contract_data(data, i)
        contract_type, strike_price, expiration_date, volume, open_interest, gamma, updated = contract_data

        # Avoid this contract if it misses some data
        if any(var is None for var in [volume, open_interest,gamma]):
            continue

        # Append the valid data to the respective lists
        option_dict["option_type"].append(contract_type)
        option_dict["strike"].append(strike_price)
        option_dict["expiration"].append(expiration_date)
        option_dict["open_interest"].append(open_interest)
        option_dict["volume"].append(volume)
        option_dict["gamma"].append(gamma)
        option_dict["updated"].append(updated)

    options_df = pd.DataFrame(option_dict)
    return options_df

def process_contract_data(data, index):
    """Helper function to process data for a single contract."""
    contract_type = data["side"][index]
    strike_price = data["strike"][index]
    expiration_date = convert_unix_to_date(data["expiration"][index], exact_time=False)
    volume = data["volume"][index]
    open_interest = data["openInterest"][index]
    gamma = data["gamma"][index]
    updated = data["updated"][index]
    
    # Convert the updated date to local time
    updated = convert_unix_to_date(updated, exact_time=True)
    updated = convert_datetime_to_local_time(updated)

    return contract_type, strike_price, expiration_date, volume, open_interest, gamma, updated

        
def response_successful(response):
    """
    Checks if the response has a status code of 200 or 203, indicating success.

    Parameters:
    response (requests.models.Response): The response object to check.

    Returns:
    bool: True if the status code is 200 or 203, False otherwise
    """

    if response.status_code in (200, 203):
        return True
    else:
        print(f'Failed to retrieve data: {response.status_code}')
        return False

def convert_unix_to_date(unix_time, exact_time=False):
    """
    Converts unix time to a date in str format.

    Parameters:
    unix_time (int): The time in Unix format (seconds since the Unix epoch).
    exact_time (bool): If True, return the exact datetime, otherwise return just the date (default is False).

    Returns:
    datetime: The full datetime object if 'exact_time' is True
    str: The string of the datetime object restricted to YYYY-MM-DD if 'exact_time' is False
    """
    date = datetime.fromtimestamp(unix_time, tz=timezone.utc)

    if exact_time:
        return date
    else:
        return date.strftime("%Y-%m-%d") 

def convert_datetime_to_local_time(datetime_object):
    """
    Converts a datetime object's time to the computer's local time.

    Parameters:
    datetime_object (datetime): The input datetime object, which can be naive or timezone-aware.

    Returns:
    datetime: The datetime object converted to the local timezone. 
              If the input is naive, it is assumed to be UTC and localized to local time.
    """

    # Ensure the input is a datetime object
    if not isinstance(datetime_object, datetime):
        raise ValueError("The input must be a valid datetime object.")

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