import os
from dotenv import load_dotenv
from dash_integration import DashController

load_dotenv()
api_key = os.getenv('API_KEY')
#ticker = 'SPX'
strike_limit = 200
contract_size = 100




def main():

    dash_controller = DashController()
    dash_controller.create_layout()
    dash_controller.handle_data_fetching()
    dash_controller.handle_slider()
    dash_controller.handle_ticker()
    dash_controller.handle_slider_btns()    
    dash_controller.display_gex_data()

    dash_controller.run_server()


    
if __name__ == '__main__':
    main()




