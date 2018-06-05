import numpy as np
import copy
import pickle
import pandas as pd
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
from utils_map import CustomIndexDash, filter_location_df, create_buttons, create_edges, create_vertices

app = CustomIndexDash(
    __name__,
    # Serve any files that are available in the `static` folder
    static_folder='static'
)

BACKGROUND = 'rgb(230, 230, 230)'
# Load data
df = pd.read_csv('data\lat_lot_colleges.csv', header=0)
df = filter_location_df(df)
drops_per_sctrs = pd.read_csv('data\dropout_sector_grouped_V4.csv')
drops_per_sctrs['College'] = drops_per_sctrs['College'].str.strip()
pd.to_datetime(drops_per_sctrs.Graduated, format='%Y')
labels = pd.read_csv('data\labels_V1.csv')
college_options = [{'label': value, 'value': value} for key, value in df.college.to_dict().items()]
all_sectors = drops_per_sctrs['Sector'].unique()
with open('data\enrolled_per_year.pickle', 'rb') as file:
    enrolled_per_year = pickle.load(file)
with open('data/tokens.pickle', 'rb') as file:
    tokens = pickle.load(file)

mapbox_access_token = tokens['MAPBOX_TOKEN']
COLORSCALE_NORMAL = ['#fac1b7', '#f7fcb9', '#d9f0a3', '#addd8e', '#78c679', '#41ab5d', '#238443', '#006837', '#99d8c9']
COLORSCALE_DROPOUTS = ['#ffffcc', '#ffeda0', '#fed976', '#feb24c', '#fd8d3c', '#fc4e2a', '#e31a1c', '#bd0026',
                       '#800026']

# Create controls
college_options = [{'label': i, 'value': i} for i in df.college.unique()]
# Create colorscale for the different sectors
colorscale_sector_normal = {key: value for key, value in zip(all_sectors, COLORSCALE_NORMAL)}
colorscale_sector_drops = {key: value for key, value in zip(all_sectors, COLORSCALE_DROPOUTS)}
# In[]:
# Layouts
layout = dict(
    autosize=True,
    height=500,
    font=dict(color='#CCCCCC'),
    backgroundcolor=BACKGROUND,
    titlefont=dict(color='#CCCCCC', size='14'),
    margin=dict(
        l=55,  # noqa E741
        r=35,
        b=65,
        t=45,
        autoexpand=True
    ),
    hovermode="closest",
    plot_bgcolor="#191A1A",
    paper_bgcolor="#020202",
    legend=dict(font=dict(size=10), orientation='h'),
    title='Satellite Overview',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="dark",
        center=dict(
            lon=5.2913,
            lat=52.1326
        ),
        zoom=6,
    )
)


def label_layout(all_shapes, college_name):
    indie_layout = dict(
        autosize=True,
        height=500,
        font=dict(color='#CCCCCC'),
        # backgroundcolor = BACKGROUND,
        titlefont=dict(color='#CCCCCC', size='14'),
        margin=dict(
            l=35,  # noqa E741
            r=35,
            b=35,
            t=45
        ),
        hovermode="closest",
        plot_bgcolor="#191A1A",
        paper_bgcolor="#020202",
        legend=dict(font=dict(size=10), orientation='h'),
        shapes=all_shapes,
        annotations=[
            dict(
                x=2.3,
                y=0.2,
                xref='x',
                yref='y',
                yshift=7,
                text=college_name,
                align="center",
                showarrow=False,
                arrowhead=7,
                ax=0,
                ay=-40
            )],
        title='Labels per institute',
        xaxis=dict(showbackground=False,
                   showgrid=False,
                   showline=False,
                   showticklabels=False,
                   title="",
                   zeroline=False,
                   range=[0, 4]),
        yaxis=dict(showbackground=False,
                   showgrid=False,
                   showline=False,
                   showticklabels=False,
                   title="",
                   zeroline=False,
                   range=[-3.5, 0.5]),
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style="dark",
            center=dict(
                lon=5.2913,
                lat=52.1326
            ),
            zoom=6,
        )
    )
    return indie_layout


marker_layout_normal = dict(type='scatter',
                            mode='lines+markers',
                            x=[],
                            y=[],
                            visible=True,
                            line=dict(
                                shape="spline",
                                smoothing=2,
                                width=1
                                # color='#fac1b7'
                                # color=[]
                            ),
                            marker=dict(symbol='diamond-open')
                            )
marker_layout_drops = dict(type='scatter',
                           mode='lines+markers',
                           x=[],
                           y=[],
                           visible=True,
                           line=dict(
                               shape="spline",
                               smoothing=2,
                               width=1
                               # color='#a9bb95'
                           ), marker=dict(symbol='diamond-open')
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
                html.H4(
                    'Number of colleges:{}'.format(len(df.college.unique())),
                    id='well_text',
                    className='two columns',
                    style={'text-align': 'left'}
                )
            ],
            className='row'
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P('Filter by college:'),
                        dcc.Dropdown(
                            id='college_dropdown',
                            options=college_options,
                            value=None
                        ),
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
                        )],
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
            [
                html.Div(
                    [
                        dcc.Graph(id='label_graph',
                                  ),
                    ],
                    className='three columns',
                    style={'margin-top': '10', 'position': 'relative'}
                ),
                html.Div(
                    [
                        dcc.Graph(id='dropout_graph')
                    ],
                    className='nine columns',
                    style={'margin-top': '10', 'position': 'relative'}
                ),
            ],
            className='row'
        ),
        # html.Div(id='output-container'),
    ],
    className='ten columns offset-by-one',
)


# # In[]:
# Create callbacks


# Dropdown->map
@app.callback(Output('simple-map', 'figure'),
              [Input('college_dropdown', 'value')])
def update_map(college_name):
    map_layout = copy.deepcopy(layout)
    if not college_name or college_name == []:
        figure = dict(
            data=[dict(
                lat=df['lat'],
                lon=df['lon'],
                text=df['college'],
                type='scattermapbox',
                hoverinfo='text',
                marker=[dict(size=50, color='green', opacity=0)]
            )],
            title='Satelite view',
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
                marker=[dict(size=50, color='green', opacity=0)]
            )],
            title='Satellite view',
            layout=map_layout,
        )
    return figure


# Dropdown, hover in the map->dropout figure
@app.callback(Output('dropout_graph', 'figure'),
              [Input('simple-map', 'hoverData'),
               Input('college_dropdown', 'value')])
def update_dropout_figure(main_graph_hover, selection):
    layout_dropout_graph = copy.deepcopy(layout)
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
    sub = drops_per_sctrs[drops_per_sctrs['College'] == college_name]
    data_drop = []
    for sector in sub['Sector'].unique():
        for selection in [0, 1]:
            if selection == 1:
                trace_drop = copy.deepcopy(marker_layout_drops)
                trace_drop['x'] = sub['Graduated'].loc[(sub['Dropout'] == selection) & (sub['Sector'] == sector)]
                trace_drop['y'] = sub['Dropout.1'].loc[(sub['Dropout'] == selection) & (sub['Sector'] == sector)]
                trace_drop['name'] = 'Dropout {}'.format(sector)
                trace_drop['line']['color'] = colorscale_sector_drops[sector]
                data_drop.append(trace_drop)
            else:
                trace_normal = copy.deepcopy(marker_layout_normal)
                trace_normal['x'] = sub['Graduated'].loc[(sub['Dropout'] == selection) & (sub['Sector'] == sector)]
                trace_normal['y'] = sub['Dropout.1'].loc[(sub['Dropout'] == selection) & (sub['Sector'] == sector)]
                trace_normal['name'] = 'Graduate {}'.format(sector)
                trace_normal['line']['color'] = colorscale_sector_normal[sector]
                data_drop.append(trace_normal)
    data_drop = np.array(data_drop)
    data_drop = data_drop.ravel()
    if data_drop.size:
        all_buttons = create_buttons(sub)
        updatemenus = list([dict(type='buttons', active=0, buttons=all_buttons, direction='center', showactive=True,
                                 yanchor='top', pad={'r': 40, 't': 10, 'l': 0}, font=dict(size=9))])
        layout_dropout_graph['title'] = 'Dropouts per sector for the {}'.format(college_name)
        layout_dropout_graph['yaxis'] = dict(title='Number of Students')
        layout_dropout_graph['updatemenus'] = updatemenus
        layout_dropout_graph['showlegend'] = True
        layout_dropout_graph['xaxis'] = dict(type='date')
        layout_dropout_graph['xaxis']['tickformat'] = '%Y'
    else:
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
        layout_dropout_graph['annotations'] = [annotation]
        data_drop = []
    figure = dict(data=data_drop, layout=layout_dropout_graph)
    return figure


# Dropout, hovering in the map->label figure
@app.callback(Output('label_graph', 'figure'),
              [Input('simple-map', 'hoverData'),
               Input('college_dropdown', 'value')])
def update_label_graph(main_graph_hover, selection):
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
    subset = labels[labels['Institute'] == college_name]
    no_labelled_data = False
    try:
        trace_1, trace_2, trace_3 = create_vertices(subset, college_name=college_name, criteria='Final Score')
    except TypeError:
        no_labelled_data = True
        pass
    if no_labelled_data:
        print('No info', college_name)
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
        label_lay = copy.deepcopy(layout)
        label_lay['annotations'] = [annotation]
        data = []
        fig = dict(data=data, layout=label_lay)
        return fig
    data = [trace_1, trace_2, trace_3]
    all_shapes = []
    if trace_2 and trace_3:
        data = data
        shape_1 = create_edges(trace_1['x'][0], trace_1['y'][0], trace_2['x'][-1], trace_2['y'][-1], offset=1.5)
        shape_2 = create_edges(trace_1['x'][0], trace_1['y'][0], trace_3['x'][-1], trace_3['y'][-1], offset=1.5)
        all_shapes.append(shape_1)
        all_shapes.append(shape_2)
        for x, y in zip(trace_2['x'][:-1], trace_2['y'][:-1]):
            shape = create_edges(trace_2['x'][-1], trace_2['y'][-1], x, y, offset=2.5)
            all_shapes.append(shape)
        for x, y in zip(trace_3['x'][:-1], trace_3['y'][:-1]):
            shape = create_edges(trace_3['x'][-1], trace_3['y'][-1], x, y, offset=2.5)
            all_shapes.append(shape)
    elif trace_3 and not trace_2:
        data = [data[0], data[-1]]
        for x, y in zip(trace_3['x'][:], trace_3['y'][:]):
            shape = create_edges(trace_1['x'][0], trace_1['y'][0], x, y, offset=2.5)
            all_shapes.append(shape)
        for x, y in zip(trace_3['x'][:-1], trace_3['y'][:-1]):
            shape = create_edges(trace_1['x'], trace_1['y'], x, y, offset=2.5)
            all_shapes.append(shape)
    elif trace_2 and not trace_3:
        data = data[:-1]
        for x, y in zip(trace_2['x'][:], trace_2['y'][:]):
            shape = create_edges(trace_1['x'][0], trace_1['y'][0], x, y, offset=2.5)
            all_shapes.append(shape)
    else:
        pass
    label_lay = label_layout(all_shapes, college_name)
    fig = dict(data=data, layout=label_lay)
    return fig


# dropdown, hovering in the map->registered figure
@app.callback(Output('registered_graph', 'figure'),
              [Input('simple-map', 'hoverData'),
               Input('college_dropdown', 'value')])
def update_registered_figure(main_graph_hover, selection):
    layout_registered = copy.deepcopy(layout)
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
                x=list(subset.keys()),
                y=list(subset.values()),
                line=dict(
                    shape="spline",
                    smoothing=2,
                    width=1,
                    color='#fac1b7'
                ),
                marker=dict(symbol='diamond-open')
            )]
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
        data = []
    layout_registered['title'] = 'Registered students for the {}'.format(college_name)
    layout_registered['showlegend'] = False
    layout_registered['xaxis'] = dict(title='Year')
    layout_registered['yaxis'] = dict(title='Number of Students')
    # layout_registered['vetricalAlign'] = 'middle'
    figure = dict(data=data, layout=layout_registered)
    return figure


if __name__ == '__main__':
    app.server.run(debug=True, threaded=True)
