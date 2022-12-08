# Video: [Introduction to MongoDB with Plotly Dash](https://www.youtube.com/watch?v=2pWwSm6X24o)

import dash     # need Dash version 1.21.0 or higher
# import dash_core_components as dcc
# import dash_html_components as html
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_table

import pandas as pd
import plotly.express as px
import pymongo
from pymongo import MongoClient     # pip install pymongo
from bson import ObjectId           # pip install bson
					   
# [Examples of multi-page apps with Dash Pages](https://community.plotly.com/t/examples-of-multi-page-apps-with-dash-pages/66489/8):
# from .utils import id
def id(name, localid):
    return f"{name.replace('.', '-').replace(' ', '-').replace('_', '-').replace('.py', '').replace('/', '')}-{localid}"


dash.register_page(__name__, path="/mongo-dash-datatable")


# Connect to local server
client = MongoClient("mongodb://127.0.0.1:27017/")
# List available databases
database_names = [db["name"] for db in client.list_databases()]
database_selected = database_names[0]
database = client[database_selected]
print(f'{database_names=}')
# List available collections (tables)
collection_names = client[database_selected].list_collection_names()
collection_selected = collection_names[0]
print(f'{collection_names=}')


# app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])

# Choose database
database_dropdown = dbc.Row(
    [
        dbc.Label("Database", html_for="database-row", width=2),
        dbc.Col(
            dcc.Dropdown(database_names, None, id=id(__name__,"database-dropdown")),
            width=10,
        ),
    ],
    className="mb-3",
)
# Choose collection (table)
collection_dropdown = dbc.Row(
    [
        dbc.Label("Collection (table)", html_for="collection-row", width=2),
        dbc.Col(
            dcc.Dropdown(collection_names, None, id=id(__name__,"collection-dropdown")),
            width=10,
        ),
    ],
    className="mb-3",
)

layout = html.Div([

    dbc.Form([database_dropdown, collection_dropdown]),
    html.Div(id=id(__name__,"placeholder")),

    html.Div(id=id(__name__,"datatable-div"), children=[ # To be filled in
        # populate_datatable(n_itvl):
        #   return [ dash_table.DataTable(id=id(__name__,"datatable"), columns=[...], data=df.to_dict('records'), ...) ]
    ]),

    # activated once/week or when page refreshed
    dcc.Interval(id=id(__name__,"interval_db"), interval=86400000 * 7, n_intervals=0),

    html.Button("Save to Mongo Database", id=id(__name__,"save-it")),
    html.Button('Add Row', id=id(__name__,"adding-rows-btn"), n_clicks=0),

    html.Div(id=id(__name__,"show-graphs"), children=[]),
    html.Div(id=id(__name__,"placeholder"))

])

# rf.   [Cascading dropdowns](https://community.plotly.com/t/cascading-dropdowns/48635) and
#       [dash-three-cascading-dropdowns.py](https://github.com/plotly/dash-recipes/blob/master/dash-three-cascading-dropdowns.py)
@callback(
    Output(id(__name__,"collection-dropdown"), 'children'),
    Input(id(__name__,"database-dropdown"), 'value')
)
def select_database(value):
    # return f'You have selected database {value}'
    # TODO: update choices for collections (tables)

    return


# FIXME: In the callback for output(s):
#           pages-mongo-database-datatable-div.children
#       Output 0 (pages-mongo-database-datatable-div.children) is already in use.
#       Any given output can only have one callback that sets it.
#       To resolve this situation, try combining these into
#       one callback function, distinguishing the trigger
#       by using `dash.callback_context` if necessary.
#
# @callback(
#     Output(id(__name__,"datatable-div"), 'children'),
#     Input(id(__name__,"collection-dropdown"), 'value')
# )
# def select_database(value):
#     # return f'You have selected colletion (table) {value}'
#     # TODO: update table

#     return

def database_collection_by_names(database_name, collection_name):
    if not database_name:
        print(f'Unable to access database "{database_name}"')
        return None
    # Create database called f'{database_name}'
    database = client[database_name]
    if not collection_name:
        print(f'Unable to access collection "{collection_name}"')
        return None
    # Create Collection (table) called f'{collection_name}'
    collection = database[collection_name]
    print(f'selected collection "{collection_name}" of database "{database_name}"')
    return collection

# Display Datatable with data from Mongo database *************************
@callback(Output(id(__name__,"datatable-div"), 'children'),
          [
            Input(id(__name__,"database-dropdown"), 'value'),
            Input(id(__name__,"collection-dropdown"), 'value'),
            Input(id(__name__,"interval_db"), 'n_intervals'),
          ])
def populate_datatable(database_name, collection_name, n_intervals):
    print(n_intervals)
    collection = database_collection_by_names(database_name, collection_name)
    if collection==None:
        return None
    # FIXME: ValueError: Value of 'x' is not the name of a column in 'data_frame'. Expected one of [] but received: age
    #        Empty DataFrame
    #        Columns: []
    #        Index: []
    # Convert the Collection (table) date to a pandas DataFrame
    df = pd.DataFrame(list(collection.find()))
    #Drop the _id column generated automatically by Mongo
    df = df.iloc[:, 1:]
    print(df.head(20))

    return [
        dash_table.DataTable(
            id='my-table', # id(__name__,"datatable") # FIXME: ID not found in layout
            columns=[{
                'name': x,
                'id': x,
            } for x in df.columns],
            data=df.to_dict('records'),
            editable=True,
            row_deletable=True,
            filter_action="native",
            filter_options={"case": "sensitive"},
            sort_action="native",  # give user capability to sort columns
            sort_mode="single",  # sort across 'multi' or 'single' columns
            page_current=0,  # page number that user is on
            page_size=6,  # number of rows visible per page
            style_cell={'textAlign': 'left', 'minWidth': '100px',
                        'width': '100px', 'maxWidth': '100px'},
        )
    ]


# Add new rows to DataTable ***********************************************
@callback(
    Output('my-table', # id(__name__,"datatable")   # FIXME: ID not found in layout
           'data'),
    [Input(id(__name__,"adding-rows-btn"), 'n_clicks')],
    [State('my-table', # id(__name__,"datatable")   # FIXME: ID not found in layout
           'data'),
     State('my-table', # id(__name__,"datatable")   # FIXME: ID not found in layout
           'columns')],
)
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows


# Save new DataTable data to the Mongo database ***************************
@callback(
    Output(id(__name__,"placeholder"), "children"), # FIXME: ID not found in layout
    Input(id(__name__,"save-it"), "n_clicks"),      # FIXME: ID not found in layout
    State('my-table', # id(__name__,"datatable")    # FIXME: ID not found in layout
          "data"),
    prevent_initial_call=True
)
def save_data(n_clicks, data):
    dff = pd.DataFrame(data)
    collection.delete_many({})
    collection.insert_many(dff.to_dict('records'))
    return ""


# Create graphs from DataTable data ***************************************
@callback(
    Output(id(__name__,"show-graphs"), 'children'), # FIXME: ID not found in layout
    Input('my-table', # id(__name__,"datatable")   # FIXME: ID not found in layout
          'data')
)
def add_row(data):
    df_grpah = pd.DataFrame(data)
    fig_hist1 = px.histogram(df_grpah, x='age',color="animal")
    fig_hist2 = px.histogram(df_grpah, x="neutered")
    return [
        html.Div(children=[dcc.Graph(figure=fig_hist1)], className="six columns"),
        html.Div(children=[dcc.Graph(figure=fig_hist2)], className="six columns")
    ]

