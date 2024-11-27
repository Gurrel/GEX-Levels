import os
from dotenv import load_dotenv
import dash
from dash import html, dcc, ctx, DiskcacheManager
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.io as pio
import diskcache
import json
import datetime as dt
import yfinance as yf
from api_data import API_Handler
from gex_calculations import GEXCalculator # Custom module to handle API data fetching
from visualising import Visualizer # Custom module for GEX calculations
from dash.exceptions import PreventUpdate # Custom module for visualizing data

load_dotenv()
api_key = os.getenv('API_KEY')
STRIKE_LIMIT = 200
CONTRACT_SIZE = 100

# Diskcache for non-production apps when developing locally
cache = diskcache.Cache("./cache")
background_callback_manager = DiskcacheManager(cache)


# Config for the plotly chart
config = {
            'displayModeBar': True,
            'scrollZoom': True,
            'displaylogo': False,
            'modeBarButtons': [['autoScale2d', 'resetScale2d']]
            }

# External stylesheets for the app (uses Font Awesome icons for buttons)
external_stylesheets=[dbc.icons.FONT_AWESOME]

class DashController:
    """
    DashController class to manage the entire Dash app.
    Includes layout creation, callback handling, and running the server.
    """

    def __init__(self):
        # Initialize the Dash app with specific settings
        self.app = dash.Dash(
            background_callback_manager=background_callback_manager, 
            suppress_callback_exceptions=True,
            external_stylesheets=external_stylesheets,
            )
        self.plot_config = {
            'displayModeBar': True,
            'scrollZoom': True,
            'displaylogo': False,
            'modeBarButtons': [['autoScale2d', 'resetScale2d']]
            }
        

    def create_layout(self):
        """
        Defines the layout of the Dash app, which includes stores for managing state,
        interval components for periodic updates, and the main content of the app.
        """
        self.app.layout = html.Div([
            dcc.Store(id="options-data-store", data=[]),
            dcc.Store(id="ticker-store", data=["SPX", "indices"]),
            dcc.Store(id="slider-max-value-store", data=0),
            html.Div(id="interval-container", children=dcc.Interval(id='interval-component', interval=30*1000, n_intervals=0, max_intervals=0)),
            dcc.Interval(id="slider-play-interval", interval=2*1000, n_intervals=0, disabled=True),
            main_content
            ], style={"display": "flex", "height": "100vh"})
        
    def run_server(self):
        """Runs the Dash app server with debugging enabled."""
        self.app.run_server(debug=True)


    def handle_data_fetching(self):
        """
        Callback to fetch new GEX data every minute and update the app's state.
        It fetches a new snapshot of GEX data for the selected ticker.
        """
        @self.app.callback(
            Output("options-data-store", "data"),
            Output("interval-container", "children"),
            Output("slider-max-value-store", "data"),
            Input("interval-component", "n_intervals"),
            State("options-data-store", "data"),
            State("interval-component", "interval"),
            State("ticker-store", "data"),
            State("slider-max-value-store", "data"),                
            background=True,
        )
        def update_data_every_minute(n_intervals, gex_record_list, interval, ticker_data, slider_max_value):

            print(interval)
            ticker = ticker_data[0]
            security_type = ticker_data[1]

            print("time sleep done")

            gex_minute_snapshot = fetch_new_gex_snapshot(ticker, security_type)
            print("gex_minute_snapshot")
            gex_record_list.append(gex_minute_snapshot)

            slider_max_value = len(gex_record_list)-1
            print(f"slider max value: {slider_max_value}")

            new_interval = dcc.Interval(id="interval-component", interval=(seconds_until_next_utc_minute()*1000), n_intervals=0, max_intervals=1)
            return gex_record_list, new_interval, slider_max_value


    def handle_slider(self):
        """
        Callback to handle slider interactions (e.g., play, pause, step forward, step backward).
        Controls the value of the slider and the play/pause functionality.
        """
        @self.app.callback(
            Output("slider-comp", "max"),
            Output("slider-comp", "value"),
            Output("slider-play-interval", "disabled"),
            Output("play-pause-btn", "n_clicks"),
            Input("slider-max-value-store", "data"),
            Input("slider-comp", "value"),
            Input("backward-step-btn", "n_clicks"),
            Input("forward-step-btn", "n_clicks"),
            Input("play-pause-btn", "n_clicks"),
            Input("slider-play-interval", "n_intervals"),
            Input("forward-btn", "n_clicks"),
            Input("backward-btn", "n_clicks"),
            State("slider-comp", "max"),
            prevent_initial_call=True,
            #State("interval-component", "n_intervals"),
            
        )
        def change_slider(new_slider_max, slider_value, bkwrd_step_clicks, frwrd_step_clicks, play_pause_clicks, playing_intervals, frwrd_clicks, bkwrd_clicks, current_slider_max):

            #print("interval SLIDER")
            input_triggered_id = ctx.triggered_id

            print(f"pause_clicks {play_pause_clicks}")
            playing = (play_pause_clicks % 2 == 1)
            print(f"playing: {playing}")

            # Handle play/pause button click
            if input_triggered_id == "play-pause-btn" and not playing:
                print("first if statement")
                return dash.no_update, dash.no_update, True, dash.no_update

            # Handle slider value and play state updates
            if playing and (slider_value != current_slider_max):
                
                print("if statement: playing and (slider_value != slider_max)")
                slider_value += 1

                if slider_value == current_slider_max:
                    print("second if statement")
                    play_pause_clicks += 1
                    return dash.no_update, slider_value, True, play_pause_clicks

                return dash.no_update, slider_value, False, dash.no_update

            
            # Handle slider max and forward/backward step changes
            if input_triggered_id == "slider-max-value-store" or input_triggered_id == "slider-comp":

                if slider_value < current_slider_max:
                    return new_slider_max, slider_value, True, dash.no_update
                
                return new_slider_max, new_slider_max, True, dash.no_update
            
            # Handle forward step and backward step button clicks
            if input_triggered_id == "backward-step-btn":
                slider_value = 0
                return dash.no_update, slider_value, True, dash.no_update
            
            if input_triggered_id == "forward-step-btn":
                slider_value = new_slider_max
                return dash.no_update, slider_value, True, dash.no_update
            
            # Handle forward and backward button clicks
            if input_triggered_id == "forward-btn":
                slider_value += 1
                return dash.no_update, slider_value, True, dash.no_update
            
            if input_triggered_id == "backward-btn":
                slider_value -= 1
                return dash.no_update, slider_value, True, dash.no_update            
                
    
    def handle_ticker(self):
        """
        Callback to handle ticker input changes, fetch the corresponding security type,
        and update the ticker data.
        """
        @self.app.callback(
                Output("ticker-store", "data"),
                Input("search-btn", "n_clicks"),
                State("ticker-input", "value"),
                State("ticker-store", "data")
        )
        def check_new_ticker(n_clicks, new_ticker, old_ticker_data):

            old_ticker = old_ticker_data[0]

            if new_ticker == old_ticker:
                return dash.no_update
            
            security_type = get_security_type(new_ticker)

            if security_type == 'not_a_stock_or_index':
                return dash.no_update

            return [new_ticker, security_type]
        
    def handle_slider_btns(self):
        """
        Callback to change the play/pause button icon based on the number of clicks.
        """
        @self.app.callback(
            Output("play-pause-btn", "children"),
            Input("play-pause-btn", "n_clicks"),
        )
        def change_play_pause_icon(n_clicks):

            if n_clicks % 2 == 0:
                return play_icon
            else:
                return pause_icon
            

    def display_gex_data(self):
        """
        Callback to update the GEX graph and display relevant data such as date, time,
        spot price, gamma values, and open interest.
        """
        @self.app.callback(
            Output("gex-graph", "figure"),
            Output("date-var", "children"),
            Output("time-var", "children"),
            Output("spot-var", "children"),
            Output("zero-gamma-var", "children"),
            Output("maj-pos-vol-var", "children"),
            Output("maj-neg-vol-var", "children"),
            Output("net-vol-gex-var", "children"),
            Output("maj-pos-oi-var", "children"),
            Output("maj-neg-oi-var", "children"),
            Output("net-oi-gex-var", "children"),
            Input("slider-comp", "drag_value"),
            State("options-data-store", "data"),
            State("gex-graph", "relayoutData"),
            State("slider-max-value-store", "data"),
        )
        def display_data(drag_value, data, relayoutData, slider_max):

            print(f"display data: {drag_value}")

            if slider_max == 0:
                raise PreventUpdate

            gex_snapshot = data[drag_value]

            #print(relayoutData)

            print(drag_value, "display data activated")
            
            
            plot = gex_snapshot["plot"]
            plot = update_plot_axis_range(plot, relayoutData)
            plot = json.loads(plot)

            date = gex_snapshot["date"]
            time = gex_snapshot["time"]
            spot = gex_snapshot["spot"]
            net_vol_gex = gex_snapshot["net_vol_gex"]
            net_oi_gex = gex_snapshot["net_oi_gex"]
            zero_gamma = gex_snapshot["zero_gamma"]
            maj_pos_vol_gex = gex_snapshot["maj_pos_vol_gamma"]
            maj_neg_vol_gex = gex_snapshot["maj_neg_vol_gamma"]
            maj_pos_oi_gex = gex_snapshot["maj_pos_oi_gamma"]
            maj_neg_oi_gex = gex_snapshot["maj_neg_oi_gamma"]

            return (
                plot, date, time, spot, zero_gamma, 
                maj_pos_vol_gex, maj_neg_vol_gex, net_vol_gex, 
                maj_pos_oi_gex, maj_neg_oi_gex, net_oi_gex
            )



""" ALL THE HTML COMPONENTS SAVED AS VARIABLES """

ticker_input = dcc.Input(
    className="ticker_input",
    id="ticker-input",
    type="text",
    value="SPX",
    )

search_icon = html.I(className='fas fa-search', style={"size": "100px"})

search_btn = dbc.Button(
    children=search_icon,
    id="search-btn", 
    n_clicks=0, 
    style=dict(backgroundColor="lightblue", margin="2px", flex="1")
    )

navbar = html.Div(className="top_nav_bar", children=
        [    
        html.H1(className="top_nav_bar_header", children="GEX Levels"),
        html.Div(className='search_bar', children=[
            ticker_input, 
            search_btn
            ]),
        
        ]
    )


def sidebar_information(info_name, info, id):
    sidebar_info = html.Div(className="sidebar_info", children=[
            html.P(className="left_sidebar_text", children=info_name), 
            html.P(className="right_sidebar_text", children=info, id=id)
            ])
    return sidebar_info

slider = dcc.Slider(min=0, max=0, step=1, value=0, id="slider-comp")

play_icon = html.I(className="fa-solid fa-play")
pause_icon = html.I(className="fa-solid fa-pause")
play_pause_btn = dbc.Button(
    children=play_icon,
    className="play_pause_btn",
    id="play-pause-btn",
    n_clicks=0,
)

forward_icon = html.I(className="fa-solid fa-forward")
forward_btn = dbc.Button(
    children=forward_icon,
    className="forward_btn",
    id="forward-btn",
    n_clicks=0,
)

forward_step_icon = html.I(className="fa-solid fa-forward-step")
forward_step_btn = dbc.Button(
    children=forward_step_icon,
    className="forward_step_btn",
    id="forward-step-btn",
    n_clicks=0,
)

backward_icon = html.I(className="fa-solid fa-backward")
backward_btn = dbc.Button(
    children=backward_icon,
    className="backward_btn",
    id="backward-btn",
    n_clicks=0,
)

backward_step_icon = html.I(className="fa-solid fa-backward-step")
backward_step_btn = dbc.Button(
    children=backward_step_icon,
    className="backward_step_btn",
    id="backward-step-btn",
    n_clicks=0,
)

slider_control_btn_container = html.Div(
    className="slider_control_btn_container",
    children=[backward_step_btn, backward_btn, play_pause_btn, forward_btn, forward_step_btn]
)

# Sidebar on the right
sidebar = html.Div(className="sidebar", id="sidebar", children=[
    html.Div([
        html.P(["FAQ"], style={"height": "70px","color": "white", "background": "gray", "margin": "0", "padding": "0"}),
        html.Div(className="sidebar_header_container_update", children=html.H3(className="sidebar_section_header", children=["Update"])),
        html.Div([
            sidebar_information("Date", "16/10/2024", "date-var"),
            sidebar_information("Time", "12:37:48 PM", "time-var"),
            sidebar_information("Spot", "5800.15", "spot-var")
        ]) 
    ]),
    html.Div([
        html.Div(className="sidebar_header_container", children=html.H3(className="sidebar_section_header", children=["Volume"])),
        html.Div([
            sidebar_information("Zero Gamma", "4080.234", "zero-gamma-var"),
            sidebar_information("Major Positive", "4099.54", "maj-pos-vol-var"),
            sidebar_information("Major Negative", "4068.22", "maj-neg-vol-var"),
            sidebar_information("Net GEX", "-2.512", "net-vol-gex-var")
        ]) 
    ]),
    html.Div([
        html.Div(className="sidebar_header_container", children=html.H3(className="sidebar_section_header", children=["Open Interest"])),
        html.Div([
            sidebar_information("Major Positive", "4150", "maj-pos-oi-var"),
            sidebar_information("Major Negative", "4000", "maj-neg-oi-var"),
            sidebar_information("Net GEX", "-18.322", "net-oi-gex-var")
        ]) 
    ]),
    html.Div([
        html.Div(className="sidebar_header_container", children=html.H3(className="sidebar_section_header", children=["History"])),
        html.Div(slider) 
    ]),
    slider_control_btn_container,
])

gex_graph = dcc.Graph(
    className="gex_plot_graph",
    id='gex-graph',
    #figure=plot,
    config=config,
    responsive=True  # Make the graph responsive
    )

data_container = html.Div(className="data_container", children=[
    navbar,
    gex_graph,
    
    ])

main_content = html.Div(className="main_container", children=[
    data_container,
    sidebar
    ])
        


def seconds_until_next_utc_minute():
    """
    Calculates the number of seconds until the next UTC minute.

    This function determines the time difference between the current time 
    (in UTC) and the start of the next minute. It returns the difference 
    in seconds, which can be used to set timers or delays that sync with 
    the next minute boundary.

    Returns:
    int: The number of seconds until the next UTC minute.
    """
    now = dt.datetime.now(dt.timezone.utc)
    next_minute = (now + dt.timedelta(minutes=1)).replace(second=0, microsecond=0)
    delta = next_minute - now
    return int(delta.total_seconds()) 

def get_security_type(ticker):
    """
    Checks if the ticker is an index or a stock.

    Parameters:
    ticker (str): The ticker of a security (e.g., 'AAPL' for Apple Inc.)

    Returns:
    str:
        - 'indices' if the security is classified as an INDEX or MUTUALFUND
        - 'stocks' if the security is classified as an EQUITY or ETF
        - 'not_a_stock_or_index' if it doesn't match with these classifications
    """
    try:
        # Get security info using yfinance
        security_info = yf.Ticker(ticker).info
        security_type = security_info.get('quoteType')

        # Check the type of security
        if security_type in ('INDEX', 'MUTUALFUND'):
            return 'indices'
        elif security_type in ('EQUITY', 'ETF'):
            return 'stocks'
        else:
            print(f'This ticker "{ticker}" is neither an index nor a stock.')
            return 'not_a_stock_or_index'

    except Exception as e:
        # Handle potential errors (e.g., invalid ticker, network issues)
        print(f"Error retrieving information for ticker {ticker}: {e}")
        return 'not_a_stock_or_index'

def update_plot_axis_range(plot, relayoutData):
    """
    Updates the plot's axis ranges based on the zoom or pan state from the relayout data.

    Parameters:
    plot (str): The plot represented as a JSON string.
    relayoutData (dict): A dictionary containing the new axis ranges, 
                          such as the range for x and y axes, or autorange options.

    Returns:
    str: The updated plot in JSON format with adjusted axis ranges.
    """
    if relayoutData is None:
        return plot
    
    # Extract axis range values from relayoutData
    xaxis_left = relayoutData.get("xaxis.range[0]")
    xaxis_right = relayoutData.get("xaxis.range[1]")
    yaxis_bottom = relayoutData.get("yaxis.range[0]")
    yaxis_top = relayoutData.get("yaxis.range[1]")

    # Check if the axes have been zoomed or panned
    zoomed_or_panned = (xaxis_left != None and xaxis_right != None and yaxis_bottom != None and yaxis_top != None)

    if zoomed_or_panned:

        fig = pio.from_json(plot)

        fig.update_yaxes(
            range=[yaxis_bottom, yaxis_top]
        )
        fig.update_xaxes(
            range=[xaxis_left, xaxis_right]
        )
        return pio.to_json(fig)

    # Check if axes are set to autorange
    xaxis_autorange = relayoutData.get("xaxis.autorange")
    yaxis_autorange = relayoutData.get("yaxis.autorange")
    autoranged = (xaxis_autorange == True and yaxis_autorange == True and len(relayoutData) == 2)

    if autoranged:

        fig = pio.from_json(plot)

        fig.update_yaxes(
            autorange=True
        )
        fig.update_xaxes(
            autorange=True
        )
        return pio.to_json(fig)

    xaxis_range = relayoutData.get("xaxis.range")
    xaxis_showspikes = relayoutData.get("xaxis.showspikes")
    yaxis_showspikes = relayoutData.get("yaxis.showspikes")

    # Check if axes are reset (showspikes is False)
    axis_is_reset = (xaxis_showspikes == False and yaxis_showspikes == False)

    if axis_is_reset:

        fig = pio.from_json(plot)

        fig.update_yaxes(
            autorange=True,
            showspikes=False
        )
        fig.update_xaxes(
            range=[-8.5, -8.5],
            showspikes=False
        )
        return pio.to_json(fig)

    return plot
    
def fetch_new_gex_snapshot(ticker, security_type):
    """
    Fetches the latest GEX (Gamma Exposure) snapshot for a given ticker and security type.

    This function retrieves data from an API, calculates the GEX values for 
    the given ticker, and generates a snapshot of the key GEX metrics along 
    with the corresponding plot.

    Parameters:
    ticker (str): The ticker of the security.
    security_type (str): The type of security (e.g., 'stocks' or 'indices').

    Returns:
    dict: A dictionary containing the GEX snapshot, including the plot and 
          various GEX-related metrics.
    """
    api_handler = API_Handler(api_key, ticker, security_type, STRIKE_LIMIT)

    api_handler.fetch_all_data_to_attributes()

    options_data = api_handler.options_data
    spot_price = api_handler.spot_price
    fetched_date = api_handler.options_data_date
    fetched_time = api_handler.options_data_time

    gex_calculator =  GEXCalculator(options_data, spot_price, CONTRACT_SIZE)
    gex_calculator.calculate_gex_data()
    net_vol_gex = gex_calculator.net_vol_GEX
    net_oi_gex = gex_calculator.net_OI_GEX
    vol_spot_GEXs = gex_calculator.vol_spot_GEXs
    OI_spot_GEXs = gex_calculator.OI_spot_GEXs
    zero_gamma = gex_calculator.zero_gamma
    maj_pos_vol_gamma = gex_calculator.maj_pos_vol_gamma
    maj_neg_vol_gamma = gex_calculator.maj_neg_vol_gamma
    maj_pos_oi_gamma = gex_calculator.maj_pos_oi_gamma
    maj_neg_oi_gamma = gex_calculator.maj_neg_oi_gamma    

    visualizer =  Visualizer(vol_spot_GEXs, OI_spot_GEXs, spot_price, zero_gamma, spot_price, ticker)

    visualizer.add_bars()
    visualizer.update_plot()
    plot_in_json = visualizer.fetch_plot_in_json()

    gex_minute_snapshot = dict(
        plot = plot_in_json,
        date = fetched_date,
        time = fetched_time,
        spot = spot_price,
        net_vol_gex = net_vol_gex,
        net_oi_gex = net_oi_gex,
        zero_gamma = zero_gamma,
        maj_pos_vol_gamma = maj_pos_vol_gamma,
        maj_neg_vol_gamma = maj_neg_vol_gamma,
        maj_pos_oi_gamma = maj_pos_oi_gamma,
        maj_neg_oi_gamma = maj_neg_oi_gamma,
        ticker = ticker
    )

    return gex_minute_snapshot





    






    




