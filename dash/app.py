from dash import Dash, dcc, html, Input, Output, clientside_callback
import plotly.express as px
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
from utils import *

connection = get_connection()
recipes = execute_fetch_query("SELECT * FROM recipes", connection)
df_recipes = pd.DataFrame(recipes)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

fig_bar_matplotlib = None

app.layout = dbc.Container([

    html.H1('Postrecito Dash', className='mb-2', style={'textAlign': 'center'}),
    html.Br(),
    html.Div([
        html.H3('Checkout our Database', className='mb-2', style={'textAlign': 'center'}),
        dbc.Row([
            dbc.Col([
                dag.AgGrid(
                id = 'recipes',
                rowData =df_recipes.to_dict("recipes"),
                columnDefs=[{"field": i} for i in df_recipes.columns],
                columnSize="sizeToFit"
                )
            ]),
        ], className = 'mt-4'),
    ],style={'marginBottom': 50, 'marginTop': 25}),
    html.H3('See our charts', className='mb-2', style={'textAlign': 'center'}),
    html.Div([
        dcc.Dropdown(id = "hearts_by_column_scatter",
                    options=[
                    {"label": "Total time", "value": "totaltime"},
                    {"label": "Prep time", "value": "preptime"}],
                    multi = False,
                    value = "totaltime",
                    style = {"width": "50%"}
                ),
        html.Div(id = 'output_container', children = []),
        html.P('Scatter: hearts by Totaltime/Preptime', className= 'mb-2', style = {'textAlign': 'center'}),
        dcc.Graph(id = 'graf_1', figure = {}),
        html.Br(),
        dcc.Dropdown(id = "hearts_by_column_bar_time",
                     options=[{"label": "Cuisine", "value": "cuisine"},
                             {"label": "Category", "value": "category"}],
                     multi = False,
                     value = "cuisine",
                     style = {"width": "50%"}
                    ),
        html.P('Bar: hearts by Cuisine/Category', className= 'mb-2', style = {'textAlign': 'center'}),
        html.Div(id = 'output_container_2', children = []),
        html.Br(),
        dcc.Graph(id = 'graf_2', figure = {}),
        html.Br(),
        #dcc.Dropdown(id = "hearts_by_column_bar",
        #             options=[{"label": "Prep time", "value": "preptime"},
        #                     {"label": "Total time", "value": "totaltime"}],
        #             multi = False,
        #             value = "preptime",
        #             style = {"width": "50%"}
        #            ),
        #html.P('Bar: hearts by Totaltime/Preptime', className= 'mb-2', style = {'textAlign': 'center'}),
        #html.Div(id = 'output_container_3', children = []),
        #html.Br(),
        #dcc.Graph(id = 'graf_3', figure = {})
    ],style={'marginBottom': 50, 'marginTop': 25}),
    html.Div([
        dbc.Row([
            dbc.Col([
                html.P('Pie: Cuisine by likes', className= 'mb-2', style = {'textAlign': 'center'}),
                html.Div(id = 'output_container_3', children = []),
                html.Br(),
                dcc.Graph(id = 'graf_3', figure = {})
            ]),
            dbc.Col([
                html.P('Pie: Cuisine by time', className= 'mb-2', style = {'textAlign': 'center'}),
                html.Div(id = 'output_container_4', children = []),
                html.Br(),
                dcc.Graph(id = 'graf_4', figure = {})
            ])
        ]),
    ] , style = {'marginBottom':50 , 'marginTop': 50})

])

@app.callback(
    [Output(component_id='graf_1', component_property='figure'),
     Output(component_id='graf_2', component_property='figure'),
     Output(component_id = 'graf_3', component_property = 'figure'),
     Output(component_id = 'graf_4', component_property = 'figure')],
    [Input('hearts_by_column_scatter', 'value'),
    Input('hearts_by_column_bar_time', 'value')]
)

def update_figure_scatter(selected_column_scatter, selected_column_bar_time):
    df_filter_positive_hearts = df_recipes[df_recipes["hearts"]>0]

    fig_scatter = px.scatter(df_recipes, x="hearts", y=selected_column_scatter, color=selected_column_scatter, hover_data={'name': True})

    fig_bar_time = px.bar(df_filter_positive_hearts, x="hearts", y=selected_column_bar_time, color="cuisine", hover_data={'name': True})

    fig_pie = px.sunburst(df_filter_positive_hearts, color = "category" , values = "hearts", path = ["category"])

    fig_pie_time = px.sunburst(df_filter_positive_hearts, color = "category" , values = "totaltime", path = ["category"])

    #other option to first scatter
    #fig_bar = px.bar(df_recipes, x=selected_column_bar, y="hearts", color=selected_column_bar)
    return fig_scatter, fig_bar_time , fig_pie, fig_pie_time



if __name__ == '__main__':
    app.run_server(debug = True)
