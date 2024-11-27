from dash_integration import DashController

def main():
    """main function that runs the entire application"""
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




