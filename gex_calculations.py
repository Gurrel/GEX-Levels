import numpy as np

class GEXCalculator:
    """
    A class to calculate and manage Gamma Exposure (GEX) data for options contracts.

    Attributes:
    -----------
    data : pd.DataFrame
        A DataFrame containing options data with fields like 'strike', 'volume', 'open_interest', etc.
    underlying_price : float
        The current price of the underlying asset.
    contract_size : int, optional
        The number of underlying shares per contract (default is 100).
    vol_spot_GEXs : pd.Series or None
        Volume-based GEX aggregated by strike price (in billions).
    OI_spot_GEXs : pd.Series or None
        Open Interest-based GEX aggregated by strike price (in billions).
    net_OI_GEX : float or None
        Net GEX for open interest (in billions).
    net_vol_GEX : float or None
        Net GEX for volume (in billions).
    zero_gamma : float or None
        Strike price where GEX crosses zero for volume-based GEX.
    maj_pos_oi_gamma : float or None
        Strike price with the highest positive GEX for open interest.
    maj_pos_vol_gamma : float or None
        Strike price with the highest positive GEX for volume.
    maj_neg_oi_gamma : float or None
        Strike price with the highest negative GEX for open interest.
    maj_neg_vol_gamma : float or None
        Strike price with the highest negative GEX for volume.
    """

    def __init__(self, data, underlying_price, contract_size=100):
        """
        Initialize a GEXCalculator instance with options data and relevant attributes.

        Parameters:
        -----------
        data : pd.DataFrame
            Options data containing 'option_type', 'strike', 'expiration', 'volume', 'gamma', 'updated' data for each row (option contract)
        underlying_price : float
            The spot price of the underlying asset.
        contract_size : int, optional
            The quantity of underlying shares per contract (default is 100).
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
        """
        Calculate all GEX-related data, including values for volume and open interest.
        Populates attributes for net GEX, major gamma values, and zero gamma.
        """
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
        Aggregate GEX values by strike price and convert to billions.

        Parameters:
        GEX_type (str, optional): Type of GEX to calculate ('OI_GEX' or 'vol_GEX').

        Returns:
        pd.Series: GEX values aggregated by strike price in billions.
        """
        gex_by_strike = self.data.groupby('strike')[GEX_type].sum()
        gex_by_strike = round(gex_by_strike / 10**9, 3)
        return gex_by_strike
    
    def calculate_net_gex(self, GEX_type='OI_GEX'):
        """
        Calculates the net GEX for the specific GEX_type (either 'OI_GEX' or 'vol_GEX')
        Divides the results by a billion.

        Parameters:
        GEX_type (str, optional): Type of GEX to calculate ('OI_GEX' or 'vol_GEX').

        Returns:
        float: Net GEX value in billions.
        """
        net_gex = self.data[GEX_type].sum() 

        net_gex = round(net_gex / 10**9, 3)
        return net_gex        
    
    def calculate_zero_gamma(self):
        """
        Calculates the strike price where the gamma exposure crosses zero.

        Returns:
        float: The calculated zero gamma strike price.
                Returns None if no zero-crossing is found.
        """
        vol_spot_gex = np.array(self.vol_spot_GEXs)
        gex_strikes = np.array(self.vol_spot_GEXs.index)
        
        # Identify indices where GEX crosses zero (sign change from negative to positive)
        zero_cross_idx = np.where(np.diff(np.sign(vol_spot_gex)) == 2)[0]

        if len(zero_cross_idx) == 0:
            # No zero crossings found
            print("No zero-crossing found in gamma exposure data.")
            return None
        
        neg_gamma = vol_spot_gex[zero_cross_idx]
        pos_gamma = vol_spot_gex[zero_cross_idx+1]
        neg_strike = gex_strikes[zero_cross_idx]
        pos_strike = gex_strikes[zero_cross_idx+1]

        # Calculate zero gamma strike using linear interpolation
        zero_gamma = pos_strike - ((pos_strike - neg_strike) * pos_gamma/(pos_gamma - neg_gamma))
        return zero_gamma[0]


    def calculate_major_gamma(self):

        """
        Calculates the strike price of major negative and positive gamma for both volume and open interest.
        """

        if self.vol_spot_GEXs is None or self.OI_spot_GEXs is None:
            return
        
        self.maj_pos_oi_gamma = self.OI_spot_GEXs.idxmax()
        self.maj_pos_vol_gamma = self.vol_spot_GEXs.idxmax()
        self.maj_neg_oi_gamma = self.OI_spot_GEXs.idxmin()
        self.maj_neg_vol_gamma = self.vol_spot_GEXs.idxmin()


def calculate_gex_value(row, underlying_price, contract_size, quantity_type='open_interest'):
    """
    Calculate GEX for each row (option contract) in a DataFrame.
    If it's a put, the gamma is treated as negative.

    Parameters:
    row (pd.Series): A single row containing 'option_type', 'gamma', and the specified quantity_type.
    underlying_price (float): The spot price of the underlying security
    contract_size (int): The quantity of the underlying shares that corresponds to one option contract
    quantity_type (str): Classified either as 'open_interest' or 'volume' depending on which data point the GEX is calculated with.

    Returns:
    float: The Gamma Exposure (GEX) for this specific option contract.
    """
    gex = underlying_price * row['gamma'] * row[quantity_type] * contract_size * underlying_price * 0.01
    # Adjust for put options
    if row['option_type'] == 'put':
        gex = -gex
    return gex

