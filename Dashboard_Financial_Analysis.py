### Code Advanced Programming Project Spring 2024, HEC, UNIL 

# Isaac Graber, mail: isaac.graber@unil.ch
# Financial Analysis Dashboard 

### Install the necessary packages 

import dash
from dash import dcc, html, Output, Input, State, exceptions
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import dash_bootstrap_components as dbc
from rapidfuzz import process, fuzz
import os
import time
# Download the CSV file "companies.csv", this file contain tickers associated with their respective company names
# The user must place this file in the same place as the current python script 

dir_path = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(dir_path, 'companies.csv')
df = pd.read_csv(file_path)

# Creating a data frame with tickers and company name
company_to_ticker = pd.Series(df['ticker'].values, index=df['company name']).to_dict()

# Adding some additionnal tickers
additional_tickers={
    # European companies
    "Nestle SA": "NESN.SW", "Novartis AG": "NOVN.SW", "Roche Holding AG": "ROG.SW","HSBC Holdings plc": "HSBA.L", "Shell plc": "SHEL.L", "Unilever PLC": "ULVR.L",
    "Bayer AG": "BAYN.DE", "Siemens AG": "SIE.DE", "Volkswagen AG": "VOW.DE","SAP SE": "SAP.DE", "Allianz SE": "ALV.DE", "Adidas AG": "ADS.DE",
    # Swiss Companies
    "UBS Group AG": "UBSG.SW", "ABB Ltd": "ABBN.SW","Zurich Insurance Group": "ZURN.SW", "Swiss Re": "SREN.SW", "Lonza Group AG": "LONN.SW",
    # Global Stock Market Indexes
    "Dow Jones Industrial Average": "^DJI", "NASDAQ Composite": "^IXIC", "S&P 500": "^GSPC","FTSE 100": "^FTSE", "DAX": "^GDAXI", "CAC 40": "^FCHI", "IBEX 35": "^IBEX",
    "Euro Stoxx 50": "^STOXX50E", "FTSE MIB": "FTSEMIB.MI", "Hang Seng Index": "^HSI","Shanghai Composite": "000001.SS", "Nikkei 225": "^N225", "S&P/ASX 200": "^AXJO",
    "Bovespa Index": "^BVSP", "TSX Composite Index": "^GSPTSE", "KOSPI": "^KS11", "SENSEX": "^BSESN", "Nifty 50": "^NSEI", "MOEX Russia Index": "IMOEX.ME",
    "Swiss Market Index": "^SSMI", "TA-35": "TA35.TA" ,"US 10-Year Treasury Yield": "^TNX", "German 10-Year Bund Yield": "^DE10Y", 
    "UK 10-Year Gilt Yield": "^TNX", "Swiss 10-Year Bond Yield": "^TNX",
    # Cryptocurrencies
    "Bitcoin": "BTC-USD", "Ethereum": "ETH-USD", "Binance Coin": "BNB-USD","Cardano": "ADA-USD", "Tether": "USDT-USD", "Solana-USD": "SOL-USD",
    "XRP": "XRP-USD", "Polkadot": "DOT1-USD", "Dogecoin": "DOGE-USD","USD Coin": "USDC-USD", "Avalanche": "AVAX-USD", "Chainlink": "LINK-USD","Nvidia Corporation": "NVDA",  
    "Sony Corporation": "SONY",  "Intel Corporation": "INTC",  "Advanced Micro Devices": "AMD",  "Samsung Electronics": "005930.KS",  "Alphabet Inc.": "GOOGL", 
    }

company_to_ticker.update(additional_tickers)

# Creation of a function that access the company name based on the ticker provided 
def get_company_name(ticker):
        try:
            stock_info = yf.Ticker(ticker)
            return stock_info.info.get('longName', stock_info.info.get('shortName', ticker))
        except Exception as e:
            print(f"Failed to fetch name for ticker {ticker}: {e}")
            
            return ticker
    
# Creation of a function that access the currency in which the ticker is exprimed 
def get_currency(ticker):
        ticker_info = yf.Ticker(ticker).info
        currency = ticker_info['currency']
        
        return currency


### Creation of the FinancialAnalysis class 

# This class stocks the downloading of the datas and all the analysis available for the the user in the application
class FinancialAnalysis:
    def __init__(self):
        self.data = {}
        self.tickers = []

    def analysis(self, tickers, start_date, end_date):
        
        # Save the tickers provided as a list
        self.tickers = tickers
        self.data = {}
       
        # Determine if we need to include the S&P 500 for the regression purpose, if we provide one ticker not equal to one from the S&P 500
        include_spy = len(tickers) == 1 and tickers[0] != '^GSPC'        
        
        # Use the provided tickers
        tickers_to_fetch = tickers[:]  
        
        # Add S&P 500 for regression purpose
        if include_spy:
            tickers_to_fetch.append('^GSPC')  
        
        # Download the data with yfinance library
        for ticker in tickers_to_fetch:
            try:
                data = yf.download(ticker, start=start_date, end=end_date)
                
                if data.empty:
                    print(f"No data found for {ticker}, skipping.")
                    continue 

                self.data[ticker] = {
                    'dates': data.index,
                    'prices': data['Adj Close'],
                    'daily Returns': data['Adj Close'].pct_change(),
                    'daily volatility': data['Adj Close'].pct_change().rolling(window=20).std()
                }
            
            except Exception as e:
                print(f"An error occurred while processing {ticker}: {e}")
                continue

    ### Definition of our analysis 
    
    # Plot the index evolution and include currency information in the title
    def plot_index_evolution(self):
        fig = go.Figure()
        titles = []
        for ticker in self.tickers:
            if ticker in self.data:
                company_name = get_company_name(ticker)
                currency=get_currency(ticker)
                titles.append(f"{company_name}")
                
                fig.add_trace(go.Scatter(
                    x=self.data[ticker]['dates'],y=self.data[ticker]['prices'],mode='lines',name=f'{company_name} Prices ({currency})'))

        # Dynamic adaptation of titles
        if len(titles) == 1:
            title = f"Evolution of Index prices {titles[0]}"
        elif len(titles) > 1:
            title = " and ".join(titles)
            title = f"Evolution of Index for {title}"
        else:
            title = "Evolution of Index prices"
        fig.update_layout(title=title, xaxis_title='Date', yaxis_title='Adjusted Close Price')
        return fig

    # Define the returns distribution
    def plot_returns_distribution(self):
        fig = go.Figure()
        titles = []
        for ticker in self.tickers:
            company_name = get_company_name(ticker)  
            titles.append(company_name)
            daily_returns = self.data[ticker]['daily Returns'].dropna()
            fig.add_trace(go.Histogram(
                x=daily_returns,
                name=f'{company_name}',
                opacity=0.5,
                nbinsx=50,
                histnorm='probability'  
            ))

        if len(titles) == 1:
            title = f"Distribution of daily Returns for {titles[0]}"
        elif len(titles) > 1:
            title = " and ".join(titles)
            title = f"Distribution of daily Returns for {title}"
        else:
            title = "Distribution of daily Returns"

        fig.update_layout(
            title=title,
            xaxis_title='Daily Returns',
            yaxis_title='Probability', 
            barmode='overlay',
            bargap=0.1  
        )
        return fig


    # Define the volatility evolution 
    def plot_volatility_evolution(self):
        fig = go.Figure()
        titles = [] 
        for ticker in self.tickers:
            company_name = get_company_name(ticker)  
            titles.append(company_name)  
            fig.add_trace(go.Scatter(x=self.data[ticker]['dates'], y=self.data[ticker]['daily volatility'].dropna(), mode='lines', name=f'{company_name} Volatility'))
        
        if len(titles) == 1:
            title = f"Evolution of Daily Volatility for {titles[0]}"
        elif len(titles) > 1:
            title = " and ".join(titles)
            title = f"Evolution of Daily Volatility for {title}"
        else:
            title = "Evolution of Daily Volatility"

        fig.update_layout(title=title, xaxis_title='Date', yaxis_title='Volatility')
        return fig
    
    # Define the daily returns evolution
    def plot_daily_returns_evolution(self):
        fig = go.Figure()
        titles = [] 
        for ticker in self.tickers:
            company_name = get_company_name(ticker)  
            titles.append(company_name)  
            fig.add_trace(go.Scatter(
                x=self.data[ticker]['dates'],
                y=self.data[ticker]['daily Returns'],
                mode='lines',
                name=f'{company_name} Daily Returns'
            ))

        if len(titles) == 1:
            title = f"Evolution of Daily Returns for {titles[0]}"
        elif len(titles) > 1:
            title = " and ".join(titles)
            title = f"Evolution of Daily Returns for {title}"
        else:
            title = "Evolution of Daily Returns"

        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Daily Returns (%)',
            yaxis_tickformat='%',  
            legend_title='Company'
        )
        return fig

    # Define the weekly returns evolution 
    def plot_weekly_returns_evolution(self):
        fig = go.Figure()
        titles=[]
        for ticker in self.tickers:
            company_name = get_company_name(ticker) 
            titles.append(company_name)
            # Define the weekly prices and weekly returns
            if 'prices' in self.data[ticker]:
                # Resample the data to weekly frequency, using 'last' to get the last available price of the week
                weekly_prices = self.data[ticker]['prices'].resample('W').last()
                # Calculate weekly returns from these prices
                weekly_returns = weekly_prices.pct_change().dropna()
                fig.add_trace(go.Scatter(
                    x=weekly_returns.index,
                    y=weekly_returns,
                    mode='lines',
                    name=f'{company_name} Weekly Returns'
                ))
        if len(titles) == 1:
            title = f"Weekly Returns Evolution for {titles[0]}"
        elif len(titles) > 1:
            title = " and ".join(titles)
            title = f"Weekly Returns Evolution for {title}"
        else:
            title = "Weekly Returns Evolution"
        
        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Weekly Returns (%)',
            yaxis_tickformat='%',  
            legend_title='Company'
        )
        return fig
    
    # Define the linear regression 
    # We use the daily returns for the linear regression
    def perform_linear_regression(self):
        
        # If one ticker is provided, we use the S&P 500 for the linear regression 
        if len(self.tickers) == 1:
            ticker = self.tickers[0]
            market_data = self.data['^GSPC']['daily Returns'] if ticker != '^GSPC' else self.data[ticker]['daily Returns']
            asset_data = self.data[ticker]['daily Returns']
        
            # Align data by common dates and drop any NaN values
            common_data = pd.concat([market_data, asset_data], axis=1, join='inner').dropna()
            market_data_aligned = common_data.iloc[:, 0]
            asset_data_aligned = common_data.iloc[:, 1]

            # Check if lengths are equal after cleaning
            if len(market_data_aligned) != len(asset_data_aligned):
                print("Data alignment error: Arrays do not match in length.")
                return None

            # Perform linear regression
            slope, intercept = np.polyfit(market_data_aligned, asset_data_aligned, 1)
            beta = slope

            # Generate plot
            trace = go.Scatter(x=market_data_aligned, y=asset_data_aligned, mode='markers', name=get_company_name(ticker))
            regression_line = np.polyval([slope, intercept], market_data_aligned)
            regression_trace = go.Scatter(x=market_data_aligned, y=regression_line, mode='lines', name='Regression Line')
        
            figure = go.Figure(data=[trace, regression_trace])
            figure.update_layout(
                title=f'Linear Regression: {get_company_name(ticker)} on {"itself" if ticker == "^GSPC" else "S&P 500 index"}',
                xaxis_title='S&P 500 Returns' if ticker != '^GSPC' else get_company_name(ticker) + ' Returns',
                yaxis_title=get_company_name(ticker) + ' Returns'
            )
            # Display the beta value in the graph
            figure.add_annotation(x=max(market_data_aligned), y=max(asset_data_aligned), text=f'Beta: {beta:.2f}', showarrow=False, arrowhead=1)
            return figure
        
        # If two tickers are provided, we regress the first asset's daily returns on the second 
        elif len(self.tickers) == 2:
           asset1_data = self.data[self.tickers[0]]['daily Returns']
           asset2_data = self.data[self.tickers[1]]['daily Returns']

           # Align data by common dates and drop any NaN values
           common_data = pd.concat([asset1_data, asset2_data], axis=1, join='inner').dropna()
           asset2_data_aligned = common_data.iloc[:, 0]
           asset1_data_aligned = common_data.iloc[:, 1]

           # Check if lengths are equal after cleaning
           if len(asset1_data_aligned) != len(asset2_data_aligned):
            print("Data alignment error: Arrays do not match in length.")
            return None

           # Perform linear regression
           slope, intercept = np.polyfit(asset2_data_aligned, asset1_data_aligned, 1)
           beta = slope

           # Generate plot
           trace = go.Scatter(x=asset2_data_aligned, y=asset1_data_aligned, mode='markers', name=get_company_name(self.tickers[1]))
           regression_line = np.polyval([slope, intercept], asset2_data_aligned)
           regression_trace = go.Scatter(x=asset2_data_aligned, y=regression_line, mode='lines', name='Regression Line')
        
           figure = go.Figure(data=[trace, regression_trace])
           figure.update_layout(
               title=f'Linear Regression: {get_company_name(self.tickers[0])} on {get_company_name(self.tickers[1])}',
               xaxis_title=get_company_name(self.tickers[1]) + ' Returns',
               yaxis_title=get_company_name(self.tickers[0]) + ' Returns'
           )
           figure.add_annotation(x=max(asset2_data_aligned), y=max(asset1_data_aligned), text=f'Beta: {beta:.2f}', showarrow=True, arrowhead=1)
           return figure


### Creation of the Dashboard_Financial_Analysis class

# This class construct the dashboard with two central parts: the layout and the callbacks 
# The layout define the visual aspect of the dashboard and the callbacks define the interactivity of the dashboard 


# Define a common input style for some elements in the dashboard 
common_input_style = {'margin': '10px', 'font-size': '14px', 'margin-left': '0px'}  # Adjusted 'margin-left

# Definition of the overall class
class Dashboard_Financial_Analysis:
    def __init__(self, analysis_instance):
        self.analysis = analysis_instance
        # We define here the overall style of the dashboard with the library dash_bootstraps components
        self.app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.CERULEAN])
        
        ### Define the layout
        # We give "id" for all the components that will be used in the callback part
        
        # Use the command container to wrap the whole layout
        self.app.layout =dbc.Container([
            # Design the title part
            dbc.Row(
                dbc.Col(html.H1("Financial Analysis Dashboard", className="text-center mt-4", style={'font-size': '24px'}), width=12)
                ),
            html.Hr(style={'background-color': 'primary', 'height': '2px'}),
            dbc.Row([
                dbc.Col([
                    html.P("This dashboard provides financial analysis tools to explore stock data, visualize market trends, and conduct statistical analysis. Select a number of assets, the tickers, define a date range and choose the type of analysis to perform. In order to select assets, you will need to use the corresponding tickers from Yahoo Finance. You can find via the ticker researcher about seven thousands tickers. Otherwise, here's the link to find the tickers : https://finance.yahoo.com/", className="text-center mb-4", style={'font-size': '14px','font-family':'Segoe UI'})
                ], width=12)
            ]),
            # Design the ticker researcher part 
            dbc.Row([
    dbc.Col([
        html.H3("1 : Ticker Researcher ", className="mb-3", style={'margin-top':'20px','font-size': '16px'}),
        html.Div("You can search here the symbol (ticker) attributed to your company by entering its name. Then you can copy the ticker and paste it in the tickers fields. ", style={'margin-bottom':'15px','font-size': '14px'}),
        dbc.Row([ 
            dbc.Col([
                dcc.Input(
                    id='search-input', 
                    type='text', 
                    placeholder='Type a company...', 
                    style={
                        'width': '235px',  
                        'height': '25px',  
                        'font-size': 'smaller', 
                        'padding': '10px 5px',}
                ),
                # Dropdown for company suggestions placed directly below the input
                dcc.Dropdown(
                    id='company-suggestions',
                    placeholder="Open to select a company",
                    style={
                        'width': '235px',
                        'margin-top': '5px',
                        'font-size': 'smaller',},
                    options=[],
                    # Disable the ability to clear the selection
                    clearable=False,  
                    searchable=False,)
            ], width=2),
            
            dbc.Col([
                html.Div(
                    id='ticker-result', 
                    className="p-2 border bg-light", 
                    style={
                        'width': '160px', 
                        'height': '25px',  
                        'font-size': 'smaller',
                        'padding': '10px 5px',
                        'display': 'flex',
                        'align-items': 'center', 
                        'justify-content': 'center'
                    }
                ),
                # Add a copy button for the ticker 
                html.Button('Copy', id='copy-btn', n_clicks=0, className="btn btn-primary btn-sm", style={'display': 'inline-block','padding': '3px 6px','font-size': '12px'}),
                ], width=2), 
                    ]),
                html.Div(
                    id='search-results', 
                    style={'height': '50px', 'overflow-y': 'auto', 'width': '100%'}
                )], width=12)
        ], className="mb-3"),

            # Design the selection of assets 
            dbc.Row([
                dbc.Col([
                    html.H3("2 : Select the number of assets", style={'font-size': 'medium'}),
                    dbc.RadioItems(
                        id='num-assets',
                        options=[
                            {'label': 'One Asset', 'value': '1'},
                            {'label': 'Two Assets', 'value': '2'}
                        ],
                        value='1',
                        inline=True,
                        style=common_input_style
                    )], width=12)
            ], className="mb-5"),
            
            # Design the selection of tickers 
            dbc.Row([
                dbc.Col([
                    html.H3("3 : Enter the ticker(s) for your asset(s)", style={'font-size': 'medium'}),
                    dcc.Input(id='ticker-1', type='text', placeholder='Enter Ticker 1', style=common_input_style),
                    html.Div(id='ticker-2-container', children=[], style={'display': 'none'})  # Adjusted for initial hidden state
                ], width=12)
            ], className="mb-5"),

            # Design the selection of the dates 
            dbc.Row([
                dbc.Col([
                    html.H3("4 : Enter a date range for analysis", style={'font-size': 'medium'}),
                    dcc.Input(id='start-date', type='text', placeholder='Start Date (DD.MM.YYYY)', style={'margin': '5px 41px 5px 0', 'font-size': 'smaller'}),
                    dcc.Input(id='end-date', type='text', placeholder='End Date (DD.MM.YYYY)', style={'margin': '5px 0 5px 41px', 'font-size': 'smaller'})  # Added margin
                ], width=12)
            ], className="mb-5"),
            
            # Design the selection of the analysis
                        dbc.Row([
                dbc.Col([
                    html.H3("5 : Choose the analysis to perform", style={'font-size': 'medium'}),
                    # we create a section with a certain id containing an empty checklist that will adapt on the number of assets choosen
                    html.Div(id='dynamic-analysis-checklist-container', children=[
                        # The actual checklist is the return of a function in the callback
                        # We set it initially empty in order to be always present in the layout
                        dbc.Checklist(
                            id='analysis-checklist',
                            options=[],
                            value=[],
                            inline=True,
                            style=common_input_style
                        )
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Design the run analysis button
            dbc.Row(dbc.Col(
                html.Button('Run Analysis', id='run-analysis', n_clicks=0, className="mx-auto mb-2 btn btn-primary btn-sm", style=common_input_style), width=12)),
                html.Div("This button launches the analysis based on your parameters (number assets, tickers, dates, selected analysis). If you change your setup, don't forget to run again! ",style={'margin-top':'5px','font-size': '14px'}),
            
            # Design the dropdown to choose between the selected analysis 
            dbc.Row([      
            dbc.Col([
                html.H3("6 : Choose the analysis you want to display here", className="mt-5 mb-2", style={'font-size': 'medium'}),  # Increased margin-bottom
                dcc.Dropdown(id='analysis-dropdown', style={'width': '50%', 'font-size': 'smaller', 'margin-top': '15px'}, options=[], value=None)  # Added margin-top
            ], width=12)
            ], className="mb-4"),
            
            # Design the place where the selected analysis show up
            dbc.Row([
                dbc.Col(html.Div(id='selected-analysis-output'), width=12)
            ], className="mb-4"),
            # Design a place for a potential apparition of an error message
            dbc.Row([
                dbc.Col(html.Div(id='error-message', style={'color': 'red', 'margin': '5px', 'font-size': 'smaller'}), width=12)
            ], className="mb-4"),
            # Design and specify the place where the graphs of our analysis show up
            dbc.Row([
                dbc.Col(html.Div(id='output-container'), width=12)
            ], className="mb-4")
            # Specify the overall background color and font of the text
        ], fluid=True,style={'background-color': '#E0EEEE','font-family': 'Segoe UI'})
       
        ### Define the callbacks part 
        
        self.setup_callbacks()
    
    # Define all the callbacks in this method 
    # A callback has always two parts, the specification of output/inputs with id's and the function implementing that 
    def setup_callbacks(self):
        
        ### Callbacks for the ticker researcher 
        # Define the dynamic research of company name and return a list limited to five names
        @self.app.callback(
            Output('company-suggestions', 'options'),
            Input('search-input', 'value')
        )
        def update_suggestions(query):
            if query:
                matches = process.extract(query, company_to_ticker.keys(), scorer=fuzz.WRatio, limit=5)
                return [{'label': match[0], 'value': company_to_ticker[match[0]]} for match in matches]
            return []
        
        # Define the ticker result when you select a company 
        @self.app.callback(
            Output('ticker-result', 'children'),
            Input('company-suggestions', 'value')
        )
        def display_selected_ticker(ticker):
            if ticker:
                return f"{ticker}"
            return "" 
        
        # Define the apparition of ticker 2 input field when two assets are choosen 
        @self.app.callback(
            [Output('ticker-2-container', 'children'), Output('ticker-2-container', 'style')],
            Input('num-assets', 'value')
        )
        def manage_ticker_2_input(num_assets):
            if num_assets == '2':
                return [dcc.Input(id='ticker-2', type='text', placeholder='Enter Ticker 2', style=common_input_style)], {'display': 'block'}
            return [], {'display': 'none'}
        
        # Define a callback that update dynamically the options for analysis based on number of assets choosen 
        @self.app.callback(
            Output('dynamic-analysis-checklist-container', 'children'),
            Input('num-assets', 'value')
        )
        def update_analysis_checklist(num_assets):
            options = [
                {'label': 'Evolution of Index Prices', 'value': 'plot_index_evolution'},
                {'label': 'Distribution of Daily Returns', 'value': 'plot_returns_distribution'},
                {'label': 'Evolution of Daily Volatility', 'value': 'plot_volatility_evolution'},
                {'label': 'Evolution of Daily Returns', 'value': 'plot_daily_returns_evolution'},
                {'label': 'Evolution of Weekly Returns', 'value': 'plot_weekly_returns_evolution'}
            ]
            
            if num_assets == '1':
                options.append({'label': 'Linear Regression on S&P 500', 'value': 'perform_linear_regression'})
            else:
                options.append({'label': 'Linear Regression Analysis', 'value': 'perform_linear_regression'})

            return dbc.Checklist(
                id='analysis-checklist',
                options=options,
                value=['plot_index_evolution'],
                inline=True,
                style=common_input_style
            )
        
        ### Critical compoenent of the dashboard 
        # Propose : a list of the selected analysis, the default analysis value and the potential error message
        # This proposition is directly triggered by the "input" (Run-analysis button) and takes "states" of relevant components to display the correct output
        @self.app.callback(
            [Output('analysis-dropdown', 'options'), Output('analysis-dropdown', 'value'), Output('error-message', 'children')],
            Input('run-analysis', 'n_clicks'),
            [State('num-assets', 'value'), State('ticker-1', 'value'), State('ticker-2-container', 'children'),
             State('start-date', 'value'), State('end-date', 'value'), State('analysis-checklist', 'value')]
        )
        
        def perform_and_display_analysis(n_clicks, num_assets, ticker1, ticker2_container, start_date, end_date, analysis_options):
            # Prevent from running until user clicks on the run-analysis button 
            if n_clicks == 0:
                raise exceptions.PreventUpdate
           
            # calculate the time where the analyse starts 
            start_time = time.time()

            # More robust check for ticker2
            # start with an empty value for ticker 2 and assign a value if user has choosen two assets and provided two tickers
            ticker2 = None
            if num_assets == '2' and ticker2_container:
                input_component = ticker2_container[0] if ticker2_container else None
                if input_component and 'props' in input_component and 'value' in input_component['props']:
                    ticker2 = input_component['props']['value']
            # create tickers based on user's choices
            tickers = [ticker1 if ticker1 else None, ticker2 if ticker2 else None]

            # Check if the required number of tickers matches the number of assets selected
            if num_assets == '2' and (not tickers[0] or not tickers[1]):
                return [], None, "Please provide both tickers when two assets are selected."

            # Filter out None values for further processing
            tickers = [ticker for ticker in tickers if ticker]
            # Check if at least one ticker is provided to run the analysis
            if not tickers:
                return [], None, "Please provide at least one ticker."
            # Check if there are dates to run the analysis
            if not start_date or not end_date:
                return [], None, "Please ensure all date fields are filled out."
            # Check if the dates are specified properly (correct format and correct order)
            try:
                start_date = datetime.strptime(start_date, '%d.%m.%Y')
                end_date = datetime.strptime(end_date, '%d.%m.%Y')
                if start_date >= end_date:
                    return [], None, "Start date must be before end date."
            except ValueError:
                return [], None, "Invalid date format. Please use DD.MM.YYYY."
            
            # Create an empty valid ticker once the tickers are correctly handled
            valid_tickers = []
            error_message = ""
            # Download the data inside this method detect potential errors
            for ticker in tickers:
                try:
                    data = yf.download(ticker, start=start_date, end=end_date)
                    if data.empty:
                        error_message += f"No data found for {ticker}. Please check ticker names and try again.\n"
                    else:
                        self.analysis.data[ticker] = {
                            'dates': data.index,
                            'prices': data['Adj Close'],
                            'daily Returns': data['Adj Close'].pct_change(),
                            'daily volatility': data['Adj Close'].pct_change().rolling(window=20).std()
                        }
                        # Tickers (with valid data) go in valid_tickers
                        valid_tickers.append(ticker)
                except Exception as e:
                    error_message += f"Error downloading data for {ticker}: {str(e)}\n"
            # If error message, return empty valid_tickers and the appropriate error message
            if error_message:
                return [], None, error_message

            # Add S&P 500 data only for the linear regression analyse in the case of one asset choosen which isn't the S&P 500 itself
            if 'perform_linear_regression' in analysis_options and len(valid_tickers) == 1 and valid_tickers[0] != '^GSPC':
                try:
                    sp500_data = yf.download('^GSPC', start=start_date, end=end_date)
                    if not sp500_data.empty:
                        self.analysis.data['^GSPC'] = {
                            'dates': sp500_data.index,
                            'prices': sp500_data['Adj Close'],
                            'daily Returns': sp500_data['Adj Close'].pct_change(),
                            'daily volatility': sp500_data['Adj Close'].pct_change().rolling(window=20).std()
                        }
                except Exception as e:
                    error_message += f"Error downloading S&P 500 data: {str(e)}\n"
            
            # Assign the valid tickers as the tickers in the Financial_Analysis class 
            # Link the two classes
            self.analysis.tickers = valid_tickers
            # Return the different option in the dropdown
            options = [{'label': opt.replace('plot_', '').replace('_', ' ').title(), 'value': opt} for opt in analysis_options]
            if 'perform_linear_regression' in analysis_options:
                regression_label = 'Linear Regression on S&P 500' if len(valid_tickers) == 1 else 'Linear Regression Analysis'
                options = [{'label': regression_label, 'value': 'perform_linear_regression'} if opt['value'] == 'perform_linear_regression' else opt for opt in options]
            
            # calculate the run time 
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Runtime for updating dropdown with selected analysis: {elapsed_time:.2f} seconds")  
            
            return options, options[0]['value'] if options else None, ""
        
        # Define the apparition of the graph based on the user's selection in the dropdown of selected analysis
        @self.app.callback(
            Output('selected-analysis-output', 'children'),
            Input('analysis-dropdown', 'value')
        )
        def display_analysis_result(selected_analysis):
            # Verifies that the method to execute exists, preventing runtime errors
            if selected_analysis and hasattr(self.analysis, selected_analysis):
                # If the selected analysis method exists, this line retrieves the method from self.analysis
                analysis_function = getattr(self.analysis, selected_analysis)
                # Return the plotly figure created in self.analysis
                return dcc.Graph(figure=analysis_function())
            return "Select an analysis to display results."
        # This callback uses a JavaScript function to handle clipboard actions 
        self.app.clientside_callback(
            """
            function(n_clicks, ticker) {
                if (n_clicks > 0) {
                    navigator.clipboard.writeText(ticker).then(function() {
                        // Change button text temporarily to indicate success
                        setTimeout(function(){ document.getElementById('copy-btn').textContent = 'Copy'; }, 2000);  // Revert to 'Copy' after 2 seconds
                        return 'Copied!';
                    }, function(err) {
                        console.error('Could not copy text: ', err);
                        return 'Failed to copy!';
                    });
                }
                return 'Copy';  // Default text ensuring users know it's the copy button
            }
            """,
            Output('copy-btn', 'children'),
            [Input('copy-btn', 'n_clicks')],
            [State('ticker-result', 'children')]
        )

### This part makes the application running and create the server 
    def run(self):
        self.app.run_server(debug=True)

# When the app is created, it creates two instances of the class directly
# The app instance which represents the dashboard, utilizes the financial analysis functionalities directly !
if __name__ == '__main__':
    analysis_instance = FinancialAnalysis()
    app = Dashboard_Financial_Analysis(analysis_instance)
    app.run()

                                                            ### End of code

# This code is meant to be used with the csv file "companies", don't forget to download in the same place as this script 