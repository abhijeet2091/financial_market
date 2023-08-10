
import yfinance as yf
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Fetch and Prepare Data (similar to your previous code)

# List of Nifty 50 stock symbols
nifty50_stocks = [
    'RELIANCE.NS', 'HDFCBANK.NS', 'INFY.NS', 'TCS.NS', 'HINDUNILVR.NS',  # Add the rest of the symbols...
]

# Create an empty list to store DataFrame objects
stock_data_frames = []

# Fetch historical stock price data for each Nifty 50 stock
for stock_symbol in nifty50_stocks:
    stock_data = yf.download(stock_symbol, start='2019-01-01', end='2023-08-01')
    stock_name = stock_symbol.split('.')[0]  # Extract stock name from symbol
    stock_data['Stock_Name'] = stock_name
    stock_data_frames.append(stock_data)

# Combine data frames into a single DataFrame
combined_data = pd.concat(stock_data_frames, axis=0)

# Reset index to move date to a column
combined_data.reset_index(inplace=True)

# Calculate daily returns
combined_data['Daily_Return'] = combined_data.groupby('Stock_Name')['Adj Close'].pct_change() * 100

# Calculate average returns and volatility
average_returns_volatility = combined_data.groupby('Stock_Name')['Daily_Return'].agg(['mean', 'std'])
average_returns_volatility.columns = ['Average_Return', 'Volatility']
average_returns_volatility.reset_index(inplace=True)

# Calculate 50-day and 200-day moving averages
combined_data['50MA'] = combined_data.groupby('Stock_Name')['Adj Close'].rolling(window=50).mean().reset_index(level=0, drop=True)
combined_data['200MA'] = combined_data.groupby('Stock_Name')['Adj Close'].rolling(window=200).mean().reset_index(level=0, drop=True)

# Merge average returns, volatility, and moving averages data
combined_data = pd.merge(combined_data, average_returns_volatility, on='Stock_Name')

# Reorder the columns
column_order = ['Stock_Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume',
                'Daily_Return', 'Average_Return', 'Volatility', '50MA', '200MA']
combined_data = combined_data.reindex(columns=column_order)
################################################################

# Create a Dash app
app = dash.Dash(__name__)

# Define the layout of the dashboard
app.layout = html.Div([
    html.H1('Nifty 50 Stock Data Dashboard', style={'text-align': 'center'}),
    
    html.Div([
        # Dropdown for stock selection
        dcc.Dropdown(
            id='stock-dropdown',
            options=[{'label': stock, 'value': stock} for stock in nifty50_stocks],
            value=nifty50_stocks[:5],  # Initial selection (first 5 stocks)
            multi=True
        )
    ], style={'text-align': 'left', 'width': '50%', 'margin-bottom': '5px'}),
    
    # Wrap each graph in an html.Div with border styling
    html.Div([
        dcc.Graph(id='stock-price-chart'),
    ], style={'width': '49%', 'display': 'inline-block', 'border': '1px solid gray',
              'padding': '2px', 'margin-right': '5px', 'margin-left':'6px'}),
    
    html.Div([
        dcc.Graph(id='daily-returns-chart'),
    ], style={'width': '49%', 'display': 'inline-block', 'border': '1px solid gray', 'padding': '2px'}),
    
    html.Div([
        dcc.Graph(id='average-returns-volatility-chart'),
    ], style={'width': '49%', 'display': 'inline-block', 'border': '1px solid gray',
              'padding': '2px', 'margin-right': '5px', 'margin-left':'6px'}),
    
    html.Div([
        dcc.Graph(id='moving-averages-chart'),
    ], style={'width': '49%', 'display': 'inline-block', 'border': '1px solid gray', 'padding': '2px'})
])

# Create callback functions for each chart

def create_line_chart(x, y, mode, title, xaxis_title, yaxis_title, selected_stocks, filtered_data):
    fig = go.Figure()
    for stock_name in selected_stocks:
        stock_data = filtered_data[filtered_data['Stock_Name'] == stock_name]
        fig.add_trace(go.Scatter(x=stock_data[x], y=stock_data[y], mode=mode, name=stock_name))
    
    fig.update_layout(
        title={'text': title, 'font': {'size': 16}},
        xaxis_title={'text': xaxis_title, 'font': {'size': 10}},
        yaxis_title={'text': yaxis_title, 'font': {'size': 10}},
        legend={'title':'Stock Name','font':{'size':9}},
        height=350,
        xaxis_tickfont={'size': 9},
        yaxis_tickfont={'size': 9},
        plot_bgcolor='white',
        paper_bgcolor='#F9F9F9',
        margin=dict(t=40, b=20),

    )
    
    return fig

@app.callback(
    [Output('stock-price-chart', 'figure'),
     Output('daily-returns-chart', 'figure'),
     Output('average-returns-volatility-chart', 'figure'),
     Output('moving-averages-chart', 'figure')],
    [Input('stock-dropdown', 'value')]
)
def update_charts(selected_stocks):
    
    combined_data['Stock_Name'] = combined_data['Stock_Name'].str.replace('.NS', '')
    
    # Remove '.NS' from the selected stock names
    selected_stocks = [stock.replace('.NS', '') for stock in selected_stocks]

    filtered_data = combined_data[combined_data['Stock_Name'].isin(selected_stocks)]

    stock_price_chart = create_line_chart('Date', 'Adj Close', 'lines', 'Adj Close Price Over Time',
                                          'Date', 'Adjusted Close Price', selected_stocks, filtered_data)
    
    daily_returns_chart = create_line_chart('Date', 'Daily_Return', 'lines', 'Daily Returns Over Time',
                                            'Date', 'Daily Return (%)', selected_stocks, filtered_data)
    
    average_returns_volatility_chart = create_line_chart('Volatility', 'Average_Return', 'markers', 'Average Returns vs. Volatility',
                                                        'Volatility', 'Average Return (%)', selected_stocks, filtered_data)
    
    moving_averages_chart = create_line_chart('Date', '50MA', 'lines', 'Moving Averages Over Time',
                                              'Date', 'Price', selected_stocks, filtered_data)
    
    return stock_price_chart, daily_returns_chart, average_returns_volatility_chart, moving_averages_chart

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)