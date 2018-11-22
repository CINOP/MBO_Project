import numpy as np
import copy
import pickle
import pandas as pd
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash
from utils_map import filter_location_df, create_buttons, create_edges, create_vertices
import dash_auth
import sys
sys.path.append("../data") # Append source directory to our Python path
sys.path.append("..")
with open('tokens.pickle', 'rb') as file:
    tokens = pickle.load(file)
mapbox_access_token = tokens[0]['MAPBOX_TOKEN']
VALID_USERNAME_PASSWORD_PAIRS = tokens[1]

STYLESHEETS = ['style.css']


class CustomIndexDash(dash.Dash):
    """Custom Dash class overriding index() method for local CSS support"""
    global STYLESHEETS

    def _generate_css_custom_html(self):
        link_str = '<link rel="stylesheet" href="{}/{}">'
        static_url_path = 'static'
        return '\n'.join(link_str.format(static_url_path, path)
                         for path in STYLESHEETS)

    def index(self, *args, **kwargs):
        scripts = self._generate_scripts_html()
        css = self._generate_css_dist_html()
        custom_css = self._generate_css_custom_html()
        config = self._generate_config_html()
        title = getattr(self, 'title', 'Dash')
        return f'''
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="UTF-8">
                <title>{title}</title>
                {css}
                {custom_css}
            </head>
            <body>
                <div id="react-entry-point">
                    <div class="_dash-loading">
                        Loading...
                    </div>
                </div>
                <footer>
                    {config}
                    {scripts}
                </footer>
            </body>
        </html>
        '''




app = CustomIndexDash(
    __name__,
    # Serve any files that are available in the `static` folder
    static_folder='static'
)

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
BACKGROUND = 'rgb(240,255,240)'
# Load data
df = pd.read_csv('lat_lot_colleges.csv', header=0)
df = filter_location_df(df)
with open('dropout_per_norm.pickle', 'rb') as file:
    drops = pickle.load(file)
with open('dropout_reference.pickle', 'rb') as file:
    drops_reference = pickle.load(file)

labels = pd.read_csv('labels_V1.csv')
college_options = [{'label': value, 'value': value} for key, value in df.college.to_dict().items()]
# all_sectors = dropout_per_sector['Sector'].unique()
with open('registered_per_norm_V2.pickle', 'rb') as file:
    enrolled_per_year = pickle.load(file)

# # Create colorscale for the different sectors
COLORSCALE_SECTORS = {'Bovensectoraal': '#19595b', 'Voedsel, groen en gastvrijheid': '#ae3415', 'Handel': '#110303',
                       'Techniek en gebouwde omgeving': '#feb24c', 'Zakelijke dienstverlening en veiligheid': '#fd8d3c',
                       'Zorg, welzijn en sport': '#fc4e2a',
                       'Mobiliteit, transport, logistiek, maritiem': '#e31a1c',
                       'Specialistisch vakmanschap ': '#bd0026',
                       'Creatieve industrie en ICT': '#800026'}
#
# # Create colorscale for the different sectors
# In[]
# Layouts
template_layout = dict(
    autosize=True,
    height=500,
    font=dict(color='#CCCCCC'),
    backgroundColor=BACKGROUND,
    titlefont=dict(color='#000000', size='15'),
    margin=dict(
        l=55,
        r=35,
        b=65,
        t=45,
        autoexpand=True
    ),
    hovermode="closest",
    plot_bgcolor="#E8E8E8",
    paper_bgcolor="#FFFFFF",
    legend=dict(font=dict(size=14), orientation='h'),
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        style="light",
        center=dict(
            lon=5.2913,
            lat=52.1326
        ),
        zoom=7,
    )
)

# In[]:
# Create app layout
app.layout = html.Div(
    [
        html.Div(
            [
                html.H1(
                    'MBOs and ROCs of the Netherlands',
                    className='eight columns',

                ),
                html.Img(
                    src='http://www.cinopadvies.nl/_images/user/logo/CINOP_Logo_Stichting_72dpi_RGB_def.jpg',
                    className='one columns',
                    style={
                        'height': '80',
                        'width': '225',
                        'float': 'right',
                        'position': 'relative',
                    },
                ),
            ],
            className='row'
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(children=[html.H4(children='Select a college:')]),
                        html.Div(dcc.Dropdown(
                            id='college_dropdown',
                            options=college_options,
                            value=None,
                            #clearable=False,
                            placeholder="Make a selection"
                        )),
                    ],
                    className='six columns'
                ),
            ],
            className='row'
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(
                            id='simple-map',
                            hoverData=None,
                        )
                    ],
                    className='eight columns',
                    style={'margin-top': '20', 'position': 'relative'}
                ),
                html.Div(
                    [
                        dcc.Graph(id='registered_graph'),
                    ],
                    className='four columns',
                    style={'margin-top': '20', 'position': 'relative'}
                ),

            ],
            className='row',
        ),
        html.Div(
            [html.Div([
                html.Div(dcc.Dropdown(id='category', placeholder='Select category', multi=False,
                                      options=[{'label': 'Positive', 'value': 'positive'},
                                               {'label': 'Negative', 'value': 'negative'},
                                               {'label': 'All', 'value': 'all'}]
                                      ),
                         ),
                html.Div(
                    id='output', style={'width': '90%',
                     'display': 'inline-block'}
                ),
                html.Div(
                    id='table-container'
                ),
                html.Div(dcc.Dropdown(id='sector', placeholder='Select a sector', multi=False,

                                      ),
                         ),
            ],
                className='four columns',
                style={'margin-top': '10', 'position': 'relative'}
            ),
                html.Div(
                    [
                        dcc.Graph(id='dropout_graph'),
                        html.Div(dcc.Slider(
                            id='year--slider',
                            min=2005,
                            max=2015,
                            value=2015,
                            step=1,
                            marks={str(year): str(year) for year in (range(2005, 2016, 1))},
                        ),
                            style={#'height': '7000',
                         'display': 'relative'}),

                    ],
                    className='eight columns',
                    style={'margin-top': '10', 'position': 'relative', 'display': 'inline-block'}
                ),
            ],
            className='row'
        ),
    ],
    className='ten columns offset-by-one',
)


# In[]:
# Helper functions
def generate_table(dataframe, max_rows=10):
    """Creates a table in HTML format
    Parameters
    ----------
    dataframe : pd.DataFrame
        The original reduced dataframe
    max_rows : int
        The maximum number of row
    Returns
    -------
    html object
        The same dataframe in html format
    """
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


def display_table(dropdown_value):
    """
    A helper function that bonds the value from the dropdown selection and the generate_table function
    Parameters
    ----------
    dropdown_value : str
        The value as returned by the dropdown selection tool
    Returns
    -------
    html object
        A table in html format
    """
    if dropdown_value is None:
        return generate_table(df)


def exception_handler(main_graph_hover, selection):
    """
    It handles the situation where no selection is made either from the map of the filtering option
        Parameters
    ----------
    main_graph_hover : str
        The value as returned by hovering on the map
    selection: str
        The values as returned by the filtering dropdown widget

    Returns
    -------
    str
        A college name
    """
    if main_graph_hover is None:
        main_graph_hover = {
            'points': [{'curveNumber': 0, 'pointNumber': 40, 'pointIndex': 40, 'lon': 5.801026, 'lat': 53.198069,
                        'text': 'Nordwin College'}]}
    if selection is None:
        try:
            college_name = [point['text'] for point in main_graph_hover['points']]
            college_name = college_name[0]
        except KeyError as e:
            college_name = 'Nordwin College'
    else:
        college_name = str(selection)
    return college_name


def html_text(text, **kwargs):
    return html.Div(children=[html.H4(children=text)], style=kwargs)

# # In[]:
# Create callbacks
@app.callback(
    Output('table-container', 'children'),
    [Input('category', 'value'),
     Input('simple-map', 'hoverData'),
     Input('college_dropdown', 'value')
     ])
def display_table(categ, main_graph_hover, selection):
    college_name = exception_handler(main_graph_hover, selection)
    subset = labels[labels['Institute'] == college_name]
    subset = subset[['Sector', 'Final Score']]
    # Change the name from Final Score to label
    subset = subset.rename(columns={'Final Score': 'Label'})
    if categ is None:
        pass
    if categ == 'positive':
        df = subset[subset['Label'] == 'Positive']
        if df.empty:
            text = 'There are no positively labelled sectors'
            layout = html_text(text, fontsize=14)
            return layout
        else:
            return generate_table(df)
    elif categ == 'negative':
        df = subset[subset['Label'] == 'Negative']
        if df.empty:
            text = 'There are no negatively labelled sectors'
            layout = html_text(text, fontsize=14)
            return layout
        else:
            return generate_table(df)
    elif categ == 'all':
        if subset.empty:
            text = 'There are no labelled sectors'
            layout = html_text(text, fontsize=14)
            return layout
        else:
            return generate_table(subset)
        return generate_table(subset)
    else:
        text = ''
        layout = html_text(text, fontsize=14)
        return layout


# Map, dropdown college -> dropdown sector
@app.callback(
    Output('sector', 'options'),
    [Input('simple-map', 'hoverData'),
     Input('college_dropdown', 'value'),
     ])
def set_cities_options(main_graph_hover, selection):
    college_name = exception_handler(main_graph_hover, selection)
    try:
        sub = drops[college_name]
    except KeyError as e:
        return []
    # Dictionary to dataframe
    sub = pd.DataFrame.from_dict(sub)
    # List with all the sectors that will be removed
    drop_list = []
    # Filter out the sector with total records smaller than the threshold. Ideally all sectors should have for
    # the whole duration 2005-2015
    threshold = 8
    for sector in sub.columns:
        if sub[sector].nunique() <= threshold:
            drop_list.append(sector)
    sub = sub.drop(drop_list, axis=1)
    return [{'label': key, 'value': key} for key in sub.columns]


# Map, dropdown college, dropdown label category->text
@app.callback(Output('output', 'children'),
              [Input('category', 'value'),
               Input('simple-map', 'hoverData'),
               Input('college_dropdown', 'value')
               ])
def prepare_data(categ, main_graph_hover, selection):
    college_name = exception_handler(main_graph_hover, selection)
    subset = labels[labels['Institute'] == college_name]
    subset = subset[['Sector', 'Final Score']]
    # Change the name from Final Score to label
    subset = subset.rename(columns={'Final Score': 'Label'})
    if categ == 'positive':
        text = 'Positive labelled sectors for {}'.format(college_name)
        layout = html_text(text, fontsize=14, color='rgb(0, 102, 51)')
    elif categ == 'negative':
        text = 'Negative labelled sectors for {}'.format(college_name)
        layout = html_text(text, fontsize=14, color='rgb(153,0,0)')
    elif categ == 'all':
        text = 'All labelled sectors for {}'.format(college_name)
        layout = html_text(text, fontsize=14)
    else:
        layout = html_text('', fontsize=14)
    return layout

# Dropdown->map
@app.callback(Output('simple-map', 'figure'),
              [
                  Input('college_dropdown', 'value'),
                  # Input('simple-map', 'hoverData')
              ],

              )
def update_map(college_name):
    map_layout = copy.deepcopy(template_layout)
    map_layout['margin'] = dict(
        l=0,
        r=0,
        b=0,
        t=0)
    if not college_name or college_name == []:
        figure = dict(
            data=[dict(
                lat=df['lat'],
                lon=df['lon'],
                text=df['college'],
                type='scattermapbox',
                hoverinfo='text',
                selected = {'color':'red'},
                marker=dict(size=10, opacity=10,  selectedcolor = 'red')
            )],
            layout=map_layout
        )
    else:
        coords = df[df['college'] == college_name]
        lat = coords['lat'].iloc[0]
        lon = coords['lon'].iloc[0]
        figure = dict(
            data=[dict(
                lat=[lat],
                lon=[lon],
                text=college_name,
                type='scattermapbox',
                hoverinfo='text',
                selected={'color': 'red'},
                marker=dict(size=20, color='red', opacity=100, selectedcolor = 'red'),
                annotations=[
                    dict(
                        lat=[lat],
                        lon=[lon],
                        xref='x',
                        yref='y',
                        text='dict Text',
                        showarrow=True,
                        arrowhead=7,
                        ax=0,
                        ay=-40,
                    )
                ]

            )],
            layout=map_layout,
        )
    return figure


# Dropdown, hover in the map->dropout figure
@app.callback(Output('dropout_graph', 'figure'),
              [Input('simple-map', 'hoverData'),
               Input('college_dropdown', 'value'),
               Input('year--slider', 'value'),
               Input('sector', 'value')
               ])
def update_dropout_figure(main_graph_hover, selection, year_slider, sector_drop):
    layout_dropout_graph = copy.deepcopy(template_layout)
    if main_graph_hover is None:
        main_graph_hover = {
            'points': [{'curveNumber': 0, 'pointNumber': 40, 'pointIndex': 40, 'lon': 5.801026, 'lat': 53.198069,
                        'text': 'Nordwin College'}]}
    if selection is None:
        try:
            college_name = [point['text'] for point in main_graph_hover['points']]
            college_name = college_name[0]
        except KeyError as e:
            college_name = 'Nordwin College'
    else:
        college_name = selection
    try:
        sub = drops[college_name]
    except KeyError as e:
        annotation = dict(
            text='No data available',
            x=0.5,
            y=0.5,
            align="center",
            showarrow=False,
            xref="paper",
            yref="paper",
            font={'size': 20},
        )
        layout_dropout_graph['annotations'] = [annotation]
        layout_dropout_graph['xaxis'] = dict(
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
            showticklabels=False,
        )
        layout_dropout_graph['yaxis'] = dict(
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
            showticklabels=False
        )
        data_drop = []
        figure = dict(data=data_drop, layout=layout_dropout_graph)
        return figure
    sub = pd.DataFrame.from_dict(sub)
    subset_ref = pd.DataFrame.from_dict(drops_reference)

    # Filter out the sector with a single year record
    drop_list = []
    # Filter out the sector with total records smaller than the threshold. Ideally all sectors should have for
    # the whole duration 2005-2015
    threshold = 8
    for sector in sub.columns:
        if sub[sector].nunique() <= threshold:
            drop_list.append(sector)
    data_drop = []
    if sector_drop:
        try:
            subset = sub[sector_drop].loc[:year_slider]
            subset_ref = subset_ref[sector_drop].loc[:year_slider]
            color = COLORSCALE_SECTORS[sector_drop]
            data_drop = [
                dict(
                    type='scatter',
                    mode='lines+markers',
                    name=college_name,
                    x=list(subset.index),
                    y=list(subset.values),
                    line=dict(
                        shape="spline",
                        smoothing=2,
                        width=1,
                        color=color
                    ),
                    marker=dict(symbol='diamond-open')
                ),
                dict(
                    type='scatter',
                    mode='lines+markers',
                    name='Average of all schools',
                    x=list(subset_ref.index),
                    y=list(subset_ref.values),
                    line=dict(
                        shape="spline",
                        smoothing=2,
                        width=1,
                        color='#0000cc'
                    ),
                    marker=dict(symbol='diamond-open')
                ),
            ]
            layout_dropout_graph['title'] = '<b>Percentage change of the dropout rate <br> of the {}</b>'.format(
                sector_drop)
            layout_dropout_graph['showlegend'] = True
            layout_dropout_graph['xaxis'] = dict(title='Year',  # anchor='y',
                                                 position=0.5,
                                                 # overlaying='y',
                                                 side='right',
                                                 titlefont=dict(
                                                     size=20,
                                                     color='#7f7f7f'
                                                 ),

                                                 tickfont=dict(
                                                     size=14,
                                                     color='black'
                                                 )
                                                 )
            layout_dropout_graph['yaxis'] = dict(title='Percentage (%)', titlefont=dict(
                size=20,
                color='#7f7f7f'),
                                                 tickfont=dict(
                                                     size=14,
                                                     color='black'
                                                 )
                                                 )
        except KeyError as e:
            annotation = dict(
                text='No data available',
                x=0.5,
                y=0.5,
                align="center",
                showarrow=False,
                xref="paper",
                yref="paper",
                font={'size': 20},
            )
            layout_dropout_graph['annotations'] = [annotation]
            layout_dropout_graph['xaxis'] = dict(
                autorange=True,
                showgrid=False,
                zeroline=False,
                showline=False,
                ticks='',
                showticklabels=False,
            )
            layout_dropout_graph['yaxis'] = dict(
                autorange=True,
                showgrid=False,
                zeroline=False,
                showline=False,
                ticks='',
                showticklabels=False
            )
            data_drop = []

    else:
        annotation = dict(
            text='No data available',
            x=0.5,
            y=0.5,
            align="center",
            showarrow=False,
            xref="paper",
            yref="paper",
            font={'size': 20},
        )
        layout_dropout_graph['annotations'] = [annotation]
        layout_dropout_graph['xaxis'] = dict(
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
            showticklabels=False,
        )
        layout_dropout_graph['yaxis'] = dict(
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
            showticklabels=False
        )
        data_drop = []
    figure = dict(data=data_drop, layout=layout_dropout_graph)
    return figure

# Dropdown, hovering in the map->registered figure
@app.callback(Output('registered_graph', 'figure'),
              [Input('simple-map', 'hoverData'),
               Input('college_dropdown', 'value')])
def update_registered_figure(main_graph_hover, selection):
    layout_registered = copy.deepcopy(template_layout)
    if main_graph_hover is None:
        main_graph_hover = {
            'points': [{'curveNumber': 0, 'pointNumber': 40, 'pointIndex': 40, 'lon': 5.801026, 'lat': 53.198069,
                        'text': 'Nordwin College'}]}
    if selection is None:
        try:
            college_name = [point['text'] for point in main_graph_hover['points']]
            college_name = college_name[0]
        except KeyError as e:
            college_name = 'Nordwin College'
    else:
        college_name = selection
    try:
        subset = enrolled_per_year[college_name]
        data = [
            dict(
                type='scatter',
                mode='lines+markers',
                name=college_name,
                x=list(subset.keys()),
                y=list(subset.values()),
                line=dict(
                    shape="spline",
                    smoothing=2,
                    width=1,
                    color='#FF8C00'
                ),
                marker=dict(symbol='diamond-open')
            ),
            dict(
                type='scatter',
                mode='lines+markers',
                name='Average of all schools',
                x=list(enrolled_per_year['reference'].keys()),
                y=list(enrolled_per_year['reference'].values()),
                line=dict(
                    shape="spline",
                    smoothing=2,
                    width=1,
                    color='#0000cc'
                ),
                marker=dict(symbol='diamond-open')
            ),
        ]
        layout_registered['title'] = '<b>Percentage change for the registered students <br> of the {}</b>'.format(
            college_name)
        layout_registered['showlegend'] = True
        layout_registered['xaxis'] = dict(title='Year',  # anchor='y',
                                          position=0.065,
                                          # overlaying='y',
                                          side='right',
                                          titlefont=dict(
                                              size=20,
                                              color='#7f7f7f'
                                          ),

                                          tickfont=dict(
                                              size=14,
                                              color='black'
                                          )
                                          )
        layout_registered['yaxis'] = dict(title='Percentage (%)', titlefont=dict(
            size=20,
            color='#7f7f7f'),
                                          tickfont=dict(
                                              size=14,
                                              color='black'
                                          )
                                          )
        layout_registered['vetricalAlign'] = 'middle'
    except KeyError as e:
        annotation = dict(
            text='No data available',
            x=0.5,
            y=0.5,
            align="center",
            showarrow=False,
            xref="paper",
            yref="paper",
            font={'size': 20}

        )
        layout_registered['annotations'] = [annotation]

        layout_registered['xaxis'] = dict(
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
            showticklabels=False,
        )
        layout_registered['yaxis'] = dict(
            autorange=True,
            showgrid=False,
            zeroline=False,
            showline=False,
            ticks='',
            showticklabels=False
        )
        data = []

    figure = dict(data=data, layout=layout_registered)
    return figure


if __name__ == '__main__':
    app.server.run(debug=True, threaded=True)