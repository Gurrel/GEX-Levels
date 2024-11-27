import plotly.graph_objects as go
import pandas as pd

class Visualizer:
    """
    Visualizes Gamma Exposure (GEX) data for options contracts.
    Generates interactive bar and scatter plots using Plotly to illustrate the relationship 
    between Gamma Exposure, strike prices, and other key metrics.

    Attributes:
    -----------
    fig (go.Figure): 
        The Plotly figure object that holds the visualization.
    vol_spot_GEXs (pd.Series): 
        Gamma Exposure values by volume for each strike price, adjusted for visualization limits.
    OI_spot_GEXs (pd.Series): 
        Gamma Exposure values by open interest for each strike price, adjusted for visualization limits.
    underlying_price (float): 
        Current price of the underlying security.
    zero_gamma (float): 
        The strike price where net gamma crosses zero.
    spot_price (float): 
        Current spot price of the underlying security.
    ticker (str): 
        The ticker symbol of the security being visualized.
    config (dict): 
        Configuration settings for the Plotly figure's interactive behavior.
    """

    def __init__(self, vol_spot_GEXs, OI_spot_GEXs, underlying_price, zero_gamma, spot_price, ticker):
        """
        Initializes the Visualizer class with data and settings for plotting.

        Parameters:
        -----------
        vol_spot_GEXs (pd.Series): Gamma exposure by volume for each strike price.
        OI_spot_GEXs (pd.Series): Gamma exposure by open interest for each strike price.
        underlying_price (float): The current price of the underlying asset.
        zero_gamma (float): The strike price where the gamma exposure crosses zero.
        spot_price (float): The current spot price of the underlying asset.
        ticker (str): The ticker symbol of the underlying asset.
        """
        self.fig = go.Figure()
        self.vol_spot_GEXs = limit_spot_GEX_for_plot(vol_spot_GEXs, underlying_price)
        self.OI_spot_GEXs =  limit_spot_GEX_for_plot(OI_spot_GEXs, underlying_price)
        self.underlying_price = underlying_price
        self.zero_gamma = zero_gamma
        self.spot_price = spot_price
        self.ticker = ticker

        self.config = {
            'displayModeBar': True,
            'scrollZoom': True,
            'displaylogo': False,
            'modeBarButtons': [['autoScale2d', 'resetScale2d']]
            }

    def add_bars(self):
        """
        Adds bars to the Plotly figure to visualize Gamma Exposure by volume and open interest.
        Adds positive and negative GEX values separately for volume and open interest.
        Also adds lines to mark zero gamma and spot price on the plot.
        """
        strikes = self.vol_spot_GEXs.index
        vol_positive_gex = self.vol_spot_GEXs.clip(lower=0)
        vol_negative_gex = self.vol_spot_GEXs.clip(upper=0)

        oi_positive_gex = self.OI_spot_GEXs.clip(lower=0)
        oi_negative_gex = self.OI_spot_GEXs.clip(upper=0)

          
        self.fig.add_trace(go.Bar(
            x=vol_positive_gex,
            y=strikes,
            base=0.3,
            orientation='h',
            name='vol GEX',
            marker_color='#C86C6A',
            marker_line_width=0
        ))

        self.fig.add_trace(go.Bar(
            x=vol_negative_gex,
            y=strikes,
            base=-0.3,
            orientation='h',
            name='vol GEX',
            showlegend=False,
            marker_color='#C86C6A',
            marker_line_width=0
        ))
        
        self.fig.add_trace(go.Bar(
            x=oi_positive_gex,
            y=strikes,
            base=0.3,
            orientation='h',
            name='OI GEX',
            marker_color='hsl(1.2,45.6%,44.3%)',
            marker_line_width=0
        ))

        self.fig.add_trace(go.Bar(
            x=oi_negative_gex,
            y=strikes,
            base=-0.3,
            orientation='h',
            name='Negative OI GEX',
            showlegend=False,
            marker_color='hsl(1.2,45.6%,44.3%)',
            marker_line_width=0
        ))

        self.fig.add_trace(go.Scatter(
            x=[-1, 1],
            y=[self.zero_gamma, self.zero_gamma],
            mode='lines',
            name='Zero Gamma',
            line=dict(
                color="orange",
                width=1
            )
        ))

        self.fig.add_trace(go.Scatter(
            x=[-1, 1],
            y=[self.spot_price, self.spot_price],
            mode='lines',
            name='Spot Price',
            line=dict(
                color='lightblue',
                width=1
            )
        ))
    

    def update_plot(self):
        """
        Updates the layout of the Plotly figure, including axis titles, gridlines, and annotations.
        This ensures the plot is visually clear and organized with customized labels and axes.
        """
        strikes = self.vol_spot_GEXs.index
        xaxis_pos_vals = [0, 2, 4, 6, 8, 10, 15, 20]
        tickvals = get_tickvals(xaxis_pos_vals, space_value=0.3)
        ticktext = get_ticktext(xaxis_pos_vals)


        self.fig.update_layout(

            title=dict(
                text=f'{self.ticker} Gamma By Strike',
                font=dict(
                    color='#BEC0C6'
                ),
                x=0.48,
                xanchor='center'
            ),
            margin=dict(l=65, r=65, t=65, b=65),
            xaxis_title='Gamma Exposure in (Bn)',
            yaxis_title='Spot Level ($)',
            paper_bgcolor='#0B111E',
            plot_bgcolor='#11131a',
            barmode='group',
            #bargroupgap=0,
            bargap=0.55,
            dragmode='pan',
            xaxis=dict(
                zeroline=False,  # Draw a line at x=0
                tickvals=tickvals,
                ticktext=ticktext,

            ),
        )
        self.fig.update_yaxes(
            dtick=5,
            showticklabels = False,
            color="#A7ABB4"
                       
        ),
        self.fig.update_xaxes(
            color="#A7ABB4",
            gridcolor="#42454D",
            range=[-8.5, 8.5]
        )

        # Add annotations to label each strike price on the chart in the middle
        for i, m in enumerate(strikes):
            self.fig.add_annotation(dict(font=dict(color='#A7ABB4',size=12),
                                                x=0,
                                                y=strikes[i],
                                                showarrow=False,
                                                text=str(strikes[i]),
                                                textangle=0,
                                                xref="x",
                                                yref="y"))
        
 
    def fetch_plot_in_json(self):
        """
        Converts the Plotly figure to a JSON format for easy embedding or sharing.

        Returns:
        plot_in_json (dict): JSON representation of the Plotly figure.
        """
        plot_in_json = self.fig.to_json()
        return plot_in_json

def get_ticktext(pos_tickvals):
    """
    Generates tick labels for the x-axis, including both positive and negative values.

    Parameters:
    pos_tickvals (list): List of positive tick values for the x-axis.

    Returns:
    tick_series (pd.Series): Series containing both negative and positive tick labels.
    """
    tick_series_pos = pd.Series(pos_tickvals)
    tick_series_neg = -tick_series_pos
    tick_series_neg = tick_series_neg.iloc[::-1]
    tick_series = pd.concat([tick_series_neg, tick_series_pos])
    tick_series = tick_series.reset_index(drop=True)
    return tick_series

def get_tickvals(pos_tickvals, space_value):
    """
    Generates tick positions for the x-axis, including both positive and negative values.

    Parameters:
    pos_tickvals (list): List of positive tick values for the x-axis.
    space_value (float): The spacing value between ticks on the x-axis.

    Returns:
    tick_series (pd.Series): Series containing both negative and positive tick positions.
    """
    tick_series_pos = pd.Series(pos_tickvals)
    tick_series_pos = tick_series_pos + space_value
    tick_series_neg = -tick_series_pos
    tick_series_neg = tick_series_neg.iloc[::-1] # Reverse the series
    tick_series = pd.concat([tick_series_neg, tick_series_pos])
    tick_series = tick_series.reset_index(drop=True)
    return tick_series

    
def limit_spot_GEX_for_plot(spot_GEX, underlying_price, limit_number=40):
    """
    Limits the Gamma Exposure data to a window around the underlying price for better visualization.

    Parameters:
    spot_GEX (pd.Series): The Gamma Exposure data.
    underlying_price (float): The price of the underlying asset.
    limit_number (int): The number of strikes to include around the underlying price.

    Returns:
    spot_GEX (pd.Series): Limited Gamma Exposure data centered around the underlying price.
    """
    strike_list = spot_GEX.index.tolist()
    strike_df = pd.DataFrame(strike_list, columns=["strike"])
    closest_index = (strike_df["strike"] - underlying_price).abs().argmin()
    # Return the range of strikes centered around the closest strike, limited by the limit_number
    spot_GEX = spot_GEX.iloc[closest_index - (limit_number//2) : closest_index + (limit_number//2)]
    return spot_GEX

