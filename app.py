import dash
import dash_core_components as dcc
import dash_html_components as html
from  dash.dependencies import Output, Input, State
import sympy
import numpy as np
import plotly.plotly as py
import plotly.graph_objs as go

DENSITY = 100
MAX_VARIABLES = 10


def slider_children(max_variables):
    children = []
    for i in range(max_variables):
        div = html.Div([
            html.Div(id = 's_{:d}_descr'.format(i)),
            dcc.Slider(min=0, max=1, value=0.5, step = 1/DENSITY, id='s_{:d}_slider'.format(i),
                       marks = dict((value, '{:.1f}'.format(value)) for value in np.linspace(0, 1, 11)))],
            id='s_{:d}_div'.format(i)
        )
        children.append(div)
    return children


app = dash.Dash(__name__)
app.config.supress_callback_exceptions = True
server = app.server


app.layout = html.Div(children=[
    html.H1("Let's visualize your multidimentional function."),
    html.Div([
        html.Div([
        html.Div('Define the function:'),
        html.Div('Use x0 .. xn as a variables and + - */ ** as operator, also brackets, numbers, constants etec'),
        dcc.Input(type='text',  placeholder='e.g. (x0+x1-2x2*x3)**x4', id='expression', value='x0-x1*x2+sin(2*pi*x3)',
                  style = {'width':'400px'}),
        html.Div('Define range for Colorscale'),
        dcc.Input(type='number', step=0.5, placeholder='minimum..', id='range_min', value=-2),
        dcc.Input(type='number', step=0.5, placeholder='maximum..', id ='range_max', value=2)],
            style={'flex': '50%'}
        ),
        html.Div(['Choose variables to show on X and Y axis',
        dcc.Dropdown(id='x_dropdown', value=None),
        dcc.Dropdown(id='y_dropdown', value=None)],
            style={'flex': '50%'}),
    ], style={'display':'flex'}),
    html.Div([html.Div(dcc.Graph(id='heatmap'), style={'flex': '50%'}),
              html.Div(id='sliders', style={'display': 'grid', 'flex': '50%'}, children=slider_children(MAX_VARIABLES))],
             style={'display': 'flex'}
             )
])


def input_validation(expression):
    expr = expression
    # add sanitize here
    return sympy.sympify(expr)


@app.callback([
    Output('x_dropdown', 'options'),
    Output('y_dropdown', 'options')],
    [Input('expression', 'value')]
)
def get_variables(expression):
    try:
        expr = input_validation(expression)
        symbols = [str(symbol) for symbol in expr.free_symbols]
        symbols.sort()
        options = [{'label': str(symbol), 'value': str(symbol)} for symbol in symbols]
        return [options, options]
    except:
        return [],[]


output_list = [Output('s_{:d}_div'.format(i), 'style') for i in range(MAX_VARIABLES)]
output_list += [Output('s_{:d}_descr'.format(i), 'children') for i in range(MAX_VARIABLES)]
@app.callback(output_list,
    [Input('x_dropdown', 'value'),
     Input('y_dropdown', 'value')],
    [State('expression', 'value')]
)
def return_sliders(x_symbol, y_symbol, expression):
    styles = []
    descrs = []
    for _ in range(MAX_VARIABLES):
        styles.append({'display':'none'})
        descrs.append('')
    if x_symbol and y_symbol:
        expr = input_validation(expression)
        for i, symbol in enumerate(expr.free_symbols):
            str_symb = str(symbol)
            if str_symb != x_symbol and str_symb != y_symbol:
                styles[i] = {'display':'block'}
                descrs[i] = str_symb
    return styles+descrs


input_list = [Input('x_dropdown', 'value'),
              Input('y_dropdown', 'value'),
              Input('expression', 'value'),
              Input('range_min', 'value'),
              Input('range_max', 'value')]
input_list += [Input('s_{:d}_slider'.format(i), 'value') for i in range(MAX_VARIABLES)]
@app.callback(
    Output('heatmap', 'figure'),
    input_list
)
def generate_heatmap(x_var, y_var, expression, range_min, range_max, *args):

    if not x_var or not y_var:
        return {}
    expr = input_validation(expression)
    symbols = expr.free_symbols
    sub_dict = dict([(str(symbol), args[i]) for i, symbol in enumerate(symbols)])
    f = sympy.lambdify([symbols], expr, 'numpy')
    grid = np.meshgrid(*[np.linspace(0,1, DENSITY) if (str(symbol)==x_var or str(symbol)==y_var)
                         else [sub_dict[str(symbol)]]
                         for symbol in symbols])
    z = f(grid).reshape([DENSITY, DENSITY])
    data = [go.Heatmap(z=z, x=np.linspace(0,1, DENSITY), y=np.linspace(0,1, DENSITY), zsmooth='fast',
                       zmin=range_min, zmax=range_max)]
    return {'data': data}

if __name__ == '__main__':
    app.run_server()