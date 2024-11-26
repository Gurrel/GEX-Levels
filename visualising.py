import plotly.graph_objects as go
import pandas as pd

class Visualizer:

    def __init__(self, vol_spot_GEXs, OI_spot_GEXs, underlying_price, zero_gamma, spot_price, ticker):

        """
        self.fig:  The graph object that will render the chart
        vol_spot_GEXs: a DataFrame of volume GEX for each strike price
        OI_spot_GEXs: a DataFrame of open interest GEX for each strike price
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
            #hoverlabel='vol GEX',
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
            #hoverlabel='vol GEX',
            marker_color='#C86C6A',
            marker_line_width=0
        ))
        
        self.fig.add_trace(go.Bar(
            x=oi_positive_gex,
            y=strikes,
            base=0.3,
            orientation='h',
            name='OI GEX',
            #hoverlabel='OI GEX',
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
            #hoverlabel='OI GEX',
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
            #paper_bgcolor='gray',
            #plot_bgcolor='gray',
            xaxis=dict(
                zeroline=False,  # Draw a line at x=0
                #zerolinecolor='black',  # Color of the zero line
                #zerolinewidth=2,  # Width of the zero line
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

        for i, m in enumerate(strikes):
            self.fig.add_annotation(dict(font=dict(color='#A7ABB4',size=12),
                                                x=0,
                                                y=strikes[i],
                                                showarrow=False,
                                                text=str(strikes[i]),
                                                textangle=0,
                                                xref="x",
                                                yref="y"))
        
        


    def show_plot(self):
        self.fig.write_json('plot.json')
        #self.fig.show(config=self.config)
    
    def fetch_plot_in_json(self):
        plot_in_json = self.fig.to_json()
        return plot_in_json

def get_ticktext(pos_tickvals):

    tick_series_pos = pd.Series(pos_tickvals)
    tick_series_neg = -tick_series_pos
    tick_series_neg = tick_series_neg.iloc[::-1]
    tick_series = pd.concat([tick_series_neg, tick_series_pos])
    tick_series = tick_series.reset_index(drop=True)
    return tick_series

def get_tickvals(pos_tickvals, space_value):

    tick_series_pos = pd.Series(pos_tickvals)
    tick_series_pos = tick_series_pos + space_value
    tick_series_neg = -tick_series_pos
    tick_series_neg = tick_series_neg.iloc[::-1] # Reverse the series
    tick_series = pd.concat([tick_series_neg, tick_series_pos])
    tick_series = tick_series.reset_index(drop=True)
    return tick_series

    



def limit_spot_GEX_for_plot(spot_GEX, underlying_price, limit_number=40):

    strike_list = spot_GEX.index.tolist()
    strike_df = pd.DataFrame(strike_list, columns=["strike"])
    closest_index = (strike_df["strike"] - underlying_price).abs().argmin()
    spot_GEX = spot_GEX.iloc[closest_index - (limit_number//2) : closest_index + (limit_number//2)]
    return spot_GEX

