import pandas as pd
from api_data import API_Handler
import numpy as np

class GEXCalculator:

    def __init__(self, data, underlying_price, contract_size=100):
        """
        (data) takes in a DataFrame as attribute
        """
        self.data = data
        self.updated = data['updated'].iloc[0]
        self.underlying_price = underlying_price
        self.contract_size = contract_size
        self.vol_spot_GEXs = None
        self.OI_spot_GEXs = None
        self.net_OI_GEX = None
        self.net_vol_GEX = None
        self.zero_gamma = None
        self.maj_pos_oi_gamma = None
        self.maj_pos_vol_gamma = None
        self.maj_neg_oi_gamma = None
        self.maj_neg_vol_gamma = None

    def calculate_gex_data(self):

        # Adds GEX values to each contract in the DataFrame
        self.apply_gex_values_to_df()

        # Calculates the open interest and volume GEX for each strike price
        self.vol_spot_GEXs = self.calculate_gex_by_strike(GEX_type='vol_GEX')
        self.OI_spot_GEXs = self.calculate_gex_by_strike(GEX_type='OI_GEX')

        # Calculates major negative and positive gamma for open interest and Volume
        self.calculate_major_gamma()

        # Calculates net open interest and volume GEX
        self.net_OI_GEX = self.calculate_net_gex(GEX_type='OI_GEX')
        self.net_vol_GEX = self.calculate_net_gex(GEX_type='vol_GEX')

        # Calculates the volume zero gamma
        self.zero_gamma = self.calculate_zero_gamma()


    def apply_gex_values_to_df(self):

        """
        Applies the open interest (OI) GEX and volume (vol) GEX to new columns in the dataframe (df) for each contract
        """
        self.data['OI_GEX'] = self.data.apply(lambda row: calculate_gex_value(row, self.underlying_price, self.contract_size, quantity_type="open_interest"), axis=1)
        self.data['vol_GEX'] = self.data.apply(lambda row: calculate_gex_value(row, self.underlying_price, self.contract_size, quantity_type="volume"), axis=1)
    
    def calculate_gex_by_strike(self, GEX_type='OI_GEX'):

        """
        Calculates the total GEX for a strike.
        Returns it in billions (bn)
        """
        gex_by_strike = self.data.groupby('strike')[GEX_type].sum()
        gex_by_strike = round(gex_by_strike / 10**9, 3)
        return gex_by_strike
    
    def calculate_net_gex(self, GEX_type='OI_GEX'):

        net_gex = self.data[GEX_type].sum() 

        #if GEX_type == "OI_GEX":
            #net_gex = net_gex * 5

        net_gex = round(net_gex / 10**9, 3)
        return net_gex        
    
    def calculate_zero_gamma(self):


        gex_data = np.array(self.vol_spot_GEXs)
        gex_strikes = np.array(self.vol_spot_GEXs.index)
        

        zero_cross_idx = np.where(np.diff(np.sign(gex_data)) == 2)[0]


        print(zero_cross_idx)
        neg_gamma = gex_data[zero_cross_idx]
        pos_gamma = gex_data[zero_cross_idx+1]
        neg_strike = gex_strikes[zero_cross_idx]
        pos_strike = gex_strikes[zero_cross_idx+1]

        zero_gamma = pos_strike - ((pos_strike - neg_strike) * pos_gamma/(pos_gamma - neg_gamma))
        return zero_gamma[0]


    def calculate_major_gamma(self):

        if self.vol_spot_GEXs is None or self.OI_spot_GEXs is None:
            return
        
        self.maj_pos_oi_gamma = self.OI_spot_GEXs.idxmax()
        self.maj_pos_vol_gamma = self.vol_spot_GEXs.idxmax()
        self.maj_neg_oi_gamma = self.OI_spot_GEXs.idxmin()
        self.maj_neg_vol_gamma = self.vol_spot_GEXs.idxmin()


def interpolate_zero_gammma(strike_1, strike_2, spot_gex_1, spot_gex_2):

    zero_gamma = strike_1 + ( abs(spot_gex_1) / (abs(spot_gex_1) + abs(spot_gex_2)) ) * (strike_1 - strike_2)
    return zero_gamma
        

    
def get_closest_zero_gamma_indexes(gex_data):

    first_index = 0
    second_index = 0
    first_data = 0
    second_data = 0        
    for index in range(len(gex_data)):

        first_index = index
        second_index = first_index + 1
        first_data = gex_data.iloc[first_index]
        second_data = gex_data.iloc[second_index]

        if (first_data < 0 and second_data > 0) or (first_data > 0 and second_data < 0):
            return first_index, second_index


def calculate_gex_value(row, underlying_price, contract_size, quantity_type='open_interest'):
    """
    Calculate GEX for each row (option contract).
    If it's a put, the gamma is treated as negative.
    """
    gex = underlying_price * row['gamma'] * row[quantity_type] * contract_size * underlying_price * 0.01
    # Adjust for put options
    if row['option_type'] == 'put':
        gex = -gex
    return gex

