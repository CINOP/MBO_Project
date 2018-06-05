import logging
import dash
import numpy as np


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# create a file handler
handler = logging.FileHandler('LOGGING.log')
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)


# Helper functions
def filter_location_df(df):
        dff = df.copy()
        dff['BRIN'].replace('', np.nan, inplace=True)
        dff.dropna(subset=['BRIN'], inplace=True)
        return dff

def create_vertices(subset, college_name, criteria=None):
    # Axis limits of the graph and x coordinate of the top level of the tree
    x_axis_min = 1
    x_axis_max = 3
    x_top_level = 2.0
    # Coordinate of the intermediate level of the tree for both positive and negative leaves.
    intermediate_x_pos = 1.5
    intermediate_y = [-2]
    intermediate_x_neg = 2.75
    bottom_level_y = [-3]
    try:
        subset.iloc[0]
    except IndexError:
        print('We have an empty list here', college_name)
        logger.error('We have an empty list here {}'.format(college_name), exc_info=True)
        return None
    top_level_vrts = dict(x=[x_top_level + 0.01], y=[0],
                          marker=dict(color='yellow', line=dict(color='rgb(255,255,255)', width=0.5), size=11,
                                      symbol='dot'),
                          mode='markers', name='Institute', text=[college_name],
                          hoverinfo='text'
                          )
    if 'Positive' in subset[criteria].unique() and 'Negative' in subset[criteria].unique():
        # Number of positive and negative points in the bottom level of the tree
        num_pos = subset[criteria].value_counts()['Positive']
        num_neg = subset[criteria].value_counts()['Negative']
        all_x_coords = np.linspace(x_axis_min, x_axis_max, num=num_pos + num_neg)
        pos_x_coords = list(all_x_coords[:num_pos])
        pos_x_coords.append(intermediate_x_pos)
        pos_y_coords = bottom_level_y * num_pos + intermediate_y
        neg_x_coords = list(all_x_coords[num_pos:])
        neg_x_coords.append(intermediate_x_neg)
        neg_y_coords = bottom_level_y * num_neg + intermediate_y
        vrts_pos = dict(x=pos_x_coords, y=pos_y_coords,
                        marker=dict(color='green', line=dict(color='rgb(100,100,100))', width=1), size=11,
                                    symbol='dot'),
                        mode='markers', name='Positive',
                        text=subset['Sector'][subset['Final Score'] == 'Positive'], hoverinfo='text'
                        )
        vrts_neg = dict(x=neg_x_coords, y=neg_y_coords,
                        marker=dict(color='red', line=dict(color='rgb(100,100,100))', width=1), size=11, symbol='dot'),
                        mode='markers', name='Negative', text=subset['Sector'][subset['Final Score'] == 'Negative'],
                        hoverinfo='text'
                        )
        return top_level_vrts, vrts_pos, vrts_neg
    elif 'Positive' in subset[criteria].unique():
        print(subset[criteria].value_counts()[0], college_name)
        num_pos = subset[criteria].value_counts()[0]
        x_coords = list(np.linspace(x_axis_min, x_axis_max, num=num_pos))
        y_coords = bottom_level_y * num_pos
        vrts_pos = dict(x=x_coords, y=y_coords,
                        marker=dict(color='green', line=dict(color='rgb(100,100,100))', width=1), size=11,
                                    symbol='dot'),
                        mode='markers', name='Positive', text=subset['Sector'], hoverinfo='text'
                        )

        vrts_neg = False
        return top_level_vrts, vrts_pos, vrts_neg
    elif 'Negative' in subset[criteria].unique():
        num_neg = subset[criteria].value_counts()[0]
        x_coords = list(np.linspace(x_axis_min, x_axis_max, num=num_neg))
        y_coords = bottom_level_y * num_neg
        vrts_neg = dict(x=x_coords, y=y_coords,
                        marker=dict(color='red', line=dict(color='rgb(100,100,100))', width=1), size=11, symbol='dot'),
                        mode='markers', name='Negative', text=subset['Sector'], hoverinfo='text'
                        )
        vrts_pos = False
        return top_level_vrts, vrts_pos, vrts_neg
    else:
        pass


def create_edges(x_1, y_1, x_2, y_2, offset=None):
    if not offset:
        offset = 0.5
    shape = dict(
        layer="below",
        line=dict(
            color='rgb(255,255,255)',
            width=1),
        path="M{0} {2}, C{0} -{offset}, {1} -{offset}, {1} {3}".format(x_1, x_2, y_1, y_2, offset=offset),
        type="path"
    )
    return shape


def create_buttons(dataframe):
    try:
        sectors = dataframe.Sector.unique()
    except KeyError:
        pass
    buttons = []
    for sector, idx in zip(sectors, range(0, 2 * len(sectors), 2)):
        visibility = len(sectors) * 2 * [False]
        visibility[idx] = True
        visibility[idx + 1] = True
        button = dict(label='{}'.format(sector),
                      method='update',
                      args=[
                          {'visible': visibility},
                          {'title': '{}'.format(sector)}])
        buttons.append(button)
    reset_button = dict(label='Reset',
                        method='update',
                        args=[
                            {'visible': len(sectors) * [True]},
                            {'title': 'All sectors'}])
    buttons.append(reset_button)
    buttons = np.array(buttons)
    buttons = buttons.ravel()
    return buttons

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



