import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objects as go
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:imgongetit10@nps-demo-instance.ciamrvvkkat5.us-east-2.rds.amazonaws.com/strategy')
df = pd.read_sql("SELECT * from trades", engine.connect(), parse_dates=('Entry time'))
df['YearMonth'] = df['Entry time'].apply(lambda x: x.strftime('%Y-%m'))


app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])

app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['Exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            # Leverage Selector
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': str(label), 'value': str(label)} for label in df['Margin'].unique()
                                        ],
                                        value='1',
                                        labelStyle={'display': 'inline-block'}
                                    ),
                                ]
                            ),
                            html.Div(
                                className="three columns card",
                                children=[
                                    html.H6("Select a Date Range"),
                                    dcc.DatePickerRange(
                                        id="date-range-select",
                                        display_format="MMM YY",
                                        start_date=df['Entry time'].min(),
                                        end_date=df['Entry time'].max()
                                    ),
                                ]
                            ),
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                        'data': []
                    }
                )
            ]
        ),
        html.Div(
            className="padding row",
            children=[
                html.Div(
                    className="six columns card",
                    children=[
                        dash_table.DataTable(
                            id='table',
                            columns=[
                                {'name': 'Number', 'id': 'Number'},
                                {'name': 'Trade type', 'id': 'Trade type'},
                                {'name': 'Exposure', 'id': 'Exposure'},
                                {'name': 'Entry balance', 'id': 'Entry balance'},
                                {'name': 'Exit balance', 'id': 'Exit balance'},
                                {'name': 'Pnl (incl fees)', 'id': 'Pnl (incl fees)'},
                            ],
                            style_cell={'width': '50px'},
                            style_table={
                                'maxHeight': '450px',
                                'overflowY': 'scroll'
                            },
                        )
                    ]
                ),
                dcc.Graph(
                    id="pnl-types",
                    className="six columns card",
                    figure={},
                    style={"height" : "450px"}
                )
            ]
        ),
        html.Div(
            className="padding row",
            children=[
                dcc.Graph(
                    id="daily-btc",
                    className="six columns card",
                    figure={},
                    style={"height" : "450px"}
                ),
                dcc.Graph(
                    id="balance",
                    className="six columns card",
                    figure={},
                    style={"height" : "450px"}
                )
            ]
        )
    ])        
])

@app.callback(
    dash.dependencies.Output('daily-btc', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)
def daily_btc_line_chart(exchange, leverage, start_date, end_date):
    data = []
    df = filter_df(exchange, leverage, start_date, end_date)
    data.append(go.Scatter(x=df['Entry time'], y=df['BTC Price']))
    return {
        'data': data,
        'layout': { 
            'title': 'Daily BTC Price' 
        }
    }

@app.callback(
    dash.dependencies.Output('balance', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)
def balance_line_chart(exchange, leverage, start_date, end_date):
    data = []
    df = filter_df(exchange, leverage, start_date, end_date)
    data.append(go.Scatter(x=df['Entry time'], y=df['Exit balance']))
    return {
        'data': data,
        'layout': { 
            'title': 'Balance overtime' 
        }
    }


@app.callback(
    dash.dependencies.Output('pnl-types', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)
def update_bar_chart(exchange, leverage, start_date, end_date):
    dff = filter_df(exchange, leverage, start_date, end_date)
    dff_short = dff[dff['Trade type'] == 'Short']
    dff_long = dff[dff['Trade type'] == 'Long']
    trace1 = go.Bar(x=dff_short['Entry time'], y=dff_short['Pnl (incl fees)'], name='Short')
    trace2 = go.Bar(x=dff_long['Entry time'], y=dff_long['Pnl (incl fees)'], name='Long')
    return {
        'data': [trace1, trace2],
        'layout': { 
            'title': 'PnL vs Trade type' 
        }
    }


@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date'),
    )
)
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(exchange, leverage, start_date, end_date)
    return dff.to_dict('records')

@app.callback(
    [   
        dash.dependencies.Output('date-range-select', 'start_date'),
        dash.dependencies.Output('date-range-select', 'end_date')
    ],
    [
        dash.dependencies.Input('exchange-select', 'value')
    ]
)
def update_date_range(exchange):
    min_date = df[df['Exchange'] == exchange]['Entry time'].min()
    max_date = df[df['Exchange'] == exchange]['Entry time'].max()
    return min_date, max_date

@app.callback(
    [
        dash.dependencies.Output('monthly-chart', 'figure'),
        dash.dependencies.Output('market-returns', 'children'),
        dash.dependencies.Output('strat-returns', 'children'),
        dash.dependencies.Output('strat-vs-market', 'children'),
    ],
    [
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range-select', 'start_date'),
        dash.dependencies.Input('date-range-select', 'end_date')
    ]
)
def update_monthly(exchange, leverage, start_date, end_date):
    filtered_data = filter_df(exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(filtered_data)
    btc_returns = calc_btc_returns(filtered_data)
    strat_returns = calc_strat_returns(filtered_data)
    strat_vs_market = strat_returns - btc_returns

    return {
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }, f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'

def filter_df(exchange, leverage, start_date, end_date):
    leverage = int(leverage) 
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    return df[(df['Exchange'] == exchange) & (df['Margin'] == leverage) & (df['Entry time'] >= start_date) & (df['Entry time'] <= end_date)]

def calc_returns_over_month(df):
    out = []
    for name, group in df.groupby('YearMonth'):
        
        exit_balance = group.head(1)['Exit balance'].values[0]
        entry_balance = group.tail(1)['Entry balance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': name,
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out

def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['BTC Price'].values[0]
    btc_end_value = dff.head(1)['BTC Price'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['Exit balance'].values[0]
    end_value = dff.head(1)['Entry balance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns


if __name__ == "__main__":
    app.run_server(debug=True, port=8080)