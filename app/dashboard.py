"""Professional Dashboard with Authentication - Fixed"""

import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from wordcloud import WordCloud
import base64
from io import BytesIO
from loguru import logger
from dotenv import load_dotenv
from flask import Flask, session
import secrets

from app.data_collector import DataCollector
from app.sentiment_analyzer import SentimentAnalyzer
from app.auth import check_auth, is_authenticated, get_current_user

load_dotenv()

# Flask server
server = Flask(__name__)
server.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))

# Dash app
app = Dash(__name__, server=server, external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME], suppress_callback_exceptions=True)

data_collector = DataCollector()
sentiment_analyzer = SentimentAnalyzer()

# Login Page Layout
login_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-lock fa-4x mb-4", style={'color': '#3498db'}),
                        html.H2("Login", className="mb-4", style={'font-weight': '700', 'color': '#2c3e50'}),
                        
                        dbc.Alert(id="login-alert", is_open=False, duration=4000, color="danger"),
                        
                        dbc.Input(
                            id="username-input",
                            placeholder="Username",
                            type="text",
                            className="mb-3",
                            style={'font-size': '1rem', 'padding': '12px'}
                        ),
                        
                        dbc.Input(
                            id="password-input",
                            placeholder="Password",
                            type="password",
                            className="mb-3",
                            style={'font-size': '1rem', 'padding': '12px'}
                        ),
                        
                        dbc.Button(
                            [html.I(className="fas fa-sign-in-alt me-2"), "Login"],
                            id="login-button",
                            color="primary",
                            className="w-100 mb-3",
                            style={'padding': '12px', 'font-size': '1.1rem', 'font-weight': '600'}
                        ),
                        
                        html.Div([
                            html.P("Demo Credentials:", style={'color': '#7f8c8d', 'font-weight': '600', 'margin-bottom': '10px'}),
                            html.P("Username: admin | Password: admin123", style={'color': '#7f8c8d', 'font-size': '0.9rem', 'margin': '0'}),
                            html.P("Username: demo | Password: demo123", style={'color': '#7f8c8d', 'font-size': '0.9rem'})
                        ], className="text-center mt-3")
                        
                    ], className="text-center")
                ])
            ], className="shadow", style={'border': 'none', 'border-radius': '15px'})
        ], width=4)
    ], justify="center", align="center", style={'min-height': '100vh'})
], fluid=True, style={'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'})


# Dashboard Layout
dashboard_layout = dbc.Container([
    # Header with Logout
    dbc.Row([
        dbc.Col([
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.H1([
                            html.I(className="fas fa-chart-line me-3", style={'color': '#2c3e50'}),
                            "Sentiment Analysis Dashboard"
                        ], style={'color': '#2c3e50', 'font-weight': '700', 'font-size': '2.5rem', 'margin': '0'})
                    ], width=8),
                    dbc.Col([
                        html.Div([
                            html.Span([
                                html.I(className="fas fa-user-circle me-2"),
                                html.Span(id="current-user", style={'font-weight': '600'})
                            ], style={'color': '#2c3e50', 'margin-right': '20px'}),
                            dbc.Button(
                                [html.I(className="fas fa-sign-out-alt me-2"), "Logout"],
                                id="logout-button",
                                color="danger",
                                size="sm",
                                style={'font-weight': '600'}
                            )
                        ], className="text-end", style={'padding-top': '10px'})
                    ], width=4)
                ]),
                html.P("AI-Powered Real-Time News Sentiment Analysis", 
                       style={'color': '#7f8c8d', 'font-size': '1.1rem', 'margin-top': '10px'})
            ], className="mb-4 mt-4")
        ])
    ]),
    
    # Search Panel
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label([html.I(className="fas fa-search me-2"), "Search Query"], 
                                    style={'font-weight': '600', 'color': '#2c3e50'}),
                            dbc.Input(id="search-query", placeholder="e.g., artificial intelligence", 
                                    value="artificial intelligence", style={'font-size': '1rem'})
                        ], width=8),
                        dbc.Col([
                            dbc.Label([html.I(className="fas fa-sliders-h me-2"), "Max Results"], 
                                    style={'font-weight': '600', 'color': '#2c3e50'}),
                            dbc.Input(id="max-results", type="number", value=40, min=10, max=100, 
                                    style={'font-size': '1rem'})
                        ], width=4)
                    ], className="mb-3"),
                    dbc.Button([html.I(className="fas fa-rocket me-2"), "Analyze Sentiment"], 
                             id="analyze-btn", color="primary", size="lg", className="w-100",
                             style={'font-size': '1.1rem', 'font-weight': '600', 'padding': '12px'})
                ])
            ], className="shadow-sm", style={'border': 'none', 'border-radius': '10px'})
        ])
    ], className="mb-4"),
    
    dcc.Loading(id="loading", type="circle", children=html.Div(id="loading-output"), color="#3498db"),
    
    # Stats Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-database fa-3x mb-3", style={'color': '#3498db'}),
                        html.H2(id="total-items", style={'font-weight': '700', 'color': '#2c3e50', 'margin-bottom': '5px'}),
                        html.P("Total Items", style={'color': '#7f8c8d', 'font-size': '0.95rem', 'margin': '0'})
                    ], className="text-center")
                ])
            ], className="shadow-sm h-100", style={'border': 'none', 'border-radius': '10px', 
                                                    'background': 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)'})
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-smile-beam fa-3x mb-3", style={'color': '#27ae60'}),
                        html.H2(id="positive-count", style={'font-weight': '700', 'color': '#27ae60', 'margin-bottom': '5px'}),
                        html.P("Positive", style={'color': '#7f8c8d', 'font-size': '0.95rem', 'margin': '0'})
                    ], className="text-center")
                ])
            ], className="shadow-sm h-100", style={'border': 'none', 'border-radius': '10px',
                                                    'background': 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)'})
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-meh fa-3x mb-3", style={'color': '#f39c12'}),
                        html.H2(id="neutral-count", style={'font-weight': '700', 'color': '#f39c12', 'margin-bottom': '5px'}),
                        html.P("Neutral", style={'color': '#7f8c8d', 'font-size': '0.95rem', 'margin': '0'})
                    ], className="text-center")
                ])
            ], className="shadow-sm h-100", style={'border': 'none', 'border-radius': '10px',
                                                    'background': 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)'})
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-frown fa-3x mb-3", style={'color': '#e74c3c'}),
                        html.H2(id="negative-count", style={'font-weight': '700', 'color': '#e74c3c', 'margin-bottom': '5px'}),
                        html.P("Negative", style={'color': '#7f8c8d', 'font-size': '0.95rem', 'margin': '0'})
                    ], className="text-center")
                ])
            ], className="shadow-sm h-100", style={'border': 'none', 'border-radius': '10px',
                                                    'background': 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)'})
        ], width=3)
    ], className="mb-4"),
    
    # Visualizations
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Tabs([
                        dbc.Tab(dcc.Graph(id="pie-chart", config={'displayModeBar': True}), 
                              label="📊 Sentiment Distribution"),
                        dbc.Tab(dcc.Graph(id="timeline", config={'displayModeBar': True}), 
                              label="📈 Sentiment Timeline"),
                        dbc.Tab(dcc.Graph(id="histogram", config={'displayModeBar': True}), 
                              label="📉 Score Distribution"),
                        dbc.Tab(html.Div(id="wordcloud", className="p-4"), 
                              label="☁️ Word Cloud")
                    ])
                ])
            ], className="shadow-sm", style={'border': 'none', 'border-radius': '10px'})
        ])
    ], className="mb-4")
    
], fluid=True, style={'maxWidth': '1400px', 'background': '#f8f9fa', 'padding': '30px', 'min-height': '100vh'})


# Main app layout
app.layout = html.Div([
    dcc.Store(id='login-state', storage_type='session'),
    dcc.Interval(id='interval', interval=1000, n_intervals=0, max_intervals=1),
    html.Div(id='page-content')
])


# Initial page load
@app.callback(
    Output('page-content', 'children'),
    Input('interval', 'n_intervals')
)
def display_page(n):
    if is_authenticated():
        return dashboard_layout
    else:
        return login_layout


# Login callback
@app.callback(
    [Output('login-state', 'data'),
     Output('login-alert', 'children'),
     Output('login-alert', 'is_open')],
    Input('login-button', 'n_clicks'),
    [State('username-input', 'value'),
     State('password-input', 'value')],
    prevent_initial_call=True
)
def login(n_clicks, username, password):
    if check_auth(username, password):
        session['logged_in'] = True
        session['username'] = username
        return {'logged_in': True, 'trigger': n_clicks}, '', False
    else:
        return {'logged_in': False}, 'Invalid username or password', True


# Logout callback
@app.callback(
    Output('login-state', 'data', allow_duplicate=True),
    Input('logout-button', 'n_clicks'),
    prevent_initial_call=True
)
def logout(n_clicks):
    session.clear()
    return {'logged_in': False, 'trigger': n_clicks}


# Update page on login/logout
@app.callback(
    Output('page-content', 'children', allow_duplicate=True),
    Input('login-state', 'data'),
    prevent_initial_call=True
)
def update_page(login_data):
    if is_authenticated():
        return dashboard_layout
    else:
        return login_layout


# Display current user
@app.callback(
    Output('current-user', 'children'),
    Input('login-state', 'data')
)
def display_user(login_data):
    return get_current_user()


# Dashboard update callback
@app.callback(
    [Output("total-items", "children"),
     Output("positive-count", "children"),
     Output("neutral-count", "children"),
     Output("negative-count", "children"),
     Output("pie-chart", "figure"),
     Output("timeline", "figure"),
     Output("histogram", "figure"),
     Output("wordcloud", "children"),
     Output("loading-output", "children")],
    Input("analyze-btn", "n_clicks"),
    [State("search-query", "value"),
     State("max-results", "value")],
    prevent_initial_call=True
)
def update_dashboard(n_clicks, query, max_results):
    try:
        df = data_collector.collect_data(query, max_results)
        if df.empty:
            empty_fig = create_empty_figure()
            return "0", "0", "0", "0", empty_fig, empty_fig, empty_fig, "No data found", ""
        
        df = sentiment_analyzer.analyze_dataframe(df)
        stats = sentiment_analyzer.get_summary_statistics(df)
        
        return (
            str(stats['total_items']),
            f"{stats['positive_count']} ({stats['positive_ratio']:.1f}%)",
            f"{stats['neutral_count']}",
            f"{stats['negative_count']} ({stats['negative_ratio']:.1f}%)",
            create_pie_chart(df),
            create_timeline(df),
            create_histogram(df),
            create_wordcloud(df),
            ""
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        empty_fig = create_empty_figure()
        return "Error", "Error", "Error", "Error", empty_fig, empty_fig, empty_fig, f"Error: {str(e)}", ""


def create_empty_figure():
    fig = go.Figure()
    fig.update_layout(template="plotly_white", paper_bgcolor='white', plot_bgcolor='white', 
                     height=500, font=dict(color='#2c3e50'))
    return fig


def create_pie_chart(df):
    counts = df['sentiment_category'].value_counts()
    colors = {'Positive': '#27ae60', 'Neutral': '#f39c12', 'Negative': '#e74c3c'}
    fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values, hole=0.4,
                                 marker=dict(colors=[colors.get(label, '#95a5a6') for label in counts.index]),
                                 textposition='outside', textinfo='label+percent',
                                 textfont=dict(size=14, color='#2c3e50'))])
    fig.update_layout(title=dict(text="<b>Sentiment Distribution</b>", 
                                font=dict(size=22, color='#2c3e50'), x=0.5),
                     template="plotly_white", height=500)
    return fig


def create_timeline(df):
    df_sorted = df.sort_values('created_at')
    colors = {'Positive': '#27ae60', 'Neutral': '#f39c12', 'Negative': '#e74c3c'}
    fig = px.scatter(df_sorted, x='created_at', y='sentiment', color='sentiment_category',
                    color_discrete_map=colors, title="<b>Sentiment Timeline</b>")
    fig.update_traces(marker=dict(size=10))
    fig.update_layout(template="plotly_white", height=500, 
                     title=dict(font=dict(size=22, color='#2c3e50'), x=0.5))
    return fig


def create_histogram(df):
    fig = px.histogram(df, x='sentiment', nbins=25, color_discrete_sequence=['#3498db'],
                      title="<b>Sentiment Score Distribution</b>")
    fig.update_layout(template="plotly_white", height=500,
                     title=dict(font=dict(size=22, color='#2c3e50'), x=0.5))
    return fig


def create_wordcloud(df):
    text = ' '.join(df['text'].astype(str))
    if not text:
        return html.Div("No text data available", className="text-center")
    wordcloud = WordCloud(width=1200, height=600, background_color='white', 
                         colormap='viridis').generate(text)
    img = BytesIO()
    wordcloud.to_image().save(img, format='PNG')
    img.seek(0)
    encoded = base64.b64encode(img.read()).decode()
    return html.Img(src=f"data:image/png;base64,{encoded}", style={'width': '100%', 'border-radius': '10px'})


if __name__ == "__main__":
    port = int(os.getenv('PORT', 8050))
    host = os.getenv('HOST', '127.0.0.1')
    logger.info(f"🚀 Starting dashboard with authentication on http://{host}:{port}")
    app.run_server(debug=True, host=host, port=port)