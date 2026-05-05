description = '''
Budgeting Dashboard
Version 0.1
By Matthew Ian Connor
'''

future = '''
Future Workflow:
1.  done - mom chart drilldown
2.  done - adjust titles and labels
3.  done - add descriptive statistics tab
4.  done - incorporate income
5.  done - cash flow tab
6.  done - add sub-category dropdown for descriptive statistics
7.  done - add exit button
8.  done - automatic window launch on script run
9.  done - finish budgeting tab
10. done - month-over-month divide-by-zero error
11. clean for release
12. a seperate python file that automatically cleans new data and appends it to old data
13. a total row for descriptive statistics
14. export button for budget review
'''

# Initial setup for the dashboard app, including importing necessary packages and loading the data.

## Imported packages
import dash
from dash import dash_table, html, dcc, Input, Output, callback, State, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import threading, os, signal
import webbrowser

## Imported .csv file
df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'budgeting_data.csv'))

## A little bit of data cleaning
df['Transaction Date'] = pd.to_datetime(df['Transaction Date'])
df = df.drop(columns=['Transaction Type'])

# Data manipulation for dashboard

## Get unique months
df['Month'] = df['Transaction Date'].dt.to_period('M').astype(str)
months = sorted(df['Month'].unique())

### Actual data for the dashboard, where we filter out income and convert spending to positive values for better visualization.

#### Spending amounts are multiplied by -1 to convert them to positive values, 
spending_df = df[df['Category name'] != 'Income'].copy()
spending_df['Amount'] = spending_df['Amount'] * -1

#### while income remains unchanged. 
income_df = df[df['Category name'] == 'Income'].copy()

#### creating a new 'df' with edited 'spending_df'
df = pd.concat([spending_df, income_df]).sort_values('Transaction Date').reset_index(drop=True)

### Group by month, create month column for both spending and income
spending_df['Month'] = spending_df['Transaction Date'].dt.to_period('M').astype(str)
income_df['Month'] = income_df['Transaction Date'].dt.to_period('M').astype(str)
df['Month'] = df['Transaction Date'].dt.to_period('M').astype(str)

# Charts for dashboard
# All of the charts are created within the callbacks except for the initial pie chart
# I may want to change the pie chart callback to generate the chart for the first time as well, but for now this is fine

## Pie chart of checking account
pie_chart = px.pie(spending_df, values='Amount', names='Category name')

print(spending_df[spending_df['Category name'] == 'Home']['Sub-category name'].unique())

# App setup

## Set dashboard app layout and theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

## Used to automatically close the browser tab when the exit button is clicked
@app.server.route('/shutdown')
def shutdown_page():
    return '<script>window.close();</script><p>You may close this tab.</p>'

## Physical layout of the dashboard
app.layout = html.Div([
    ### Title of the dashboard
    html.H1('Budgeting Dashboard'),
    html.Button('Exit', id='exit_button', n_clicks=0, style={'float': 'right'}),
    dcc.Location(id='url', refresh=True),
    dcc.Tabs([
        ### First tab for spending by category
        dcc.Tab(label='Spending by Proportion', children=[
            #### Toggle for income vs spending
            dcc.RadioItems(
                id='income_spending_toggle',
                options=[
                    {'label': 'Spending', 'value': 'Spending'},
                    {'label': 'Income', 'value': 'Income'}
                ],
                value='Spending',
                inline=True,
                labelStyle={'color': 'white'}
            ),
            #### Radio items for month selection
            dcc.RadioItems(
                id='month_filter',
                options=[{'label': 'Total', 'value': 'Total'}] + [{'label': m, 'value': m} for m in months],
                value='Total',
                inline=True,
                labelStyle={'color': 'white'}
            ),
            dcc.Graph(id='pie_chart'),
            dcc.Graph(id='drilldown_chart')
        ]),
        ### Second tab for month-over-month comparison
        dcc.Tab(label='Month over Month', children=[
            dcc.RadioItems(
                id='mom_category_filter',
                options=[{'label': 'Total Spending', 'value': 'Total'}] + [{'label': c, 'value': c} for c in sorted(df['Category name'].unique())],
                value='Total',
                inline=True,
                labelStyle={'color': 'white'}
            ),
            # This chart will show month-over-month spending trends. 
            dcc.Graph(id='mom_chart'),
            html.Div(id='mom_drilldown_container', children=[
                dcc.Graph(id='mom_drilldown_chart')
            ])
        ]),
        ### Third tab for descriptive statistics
        dcc.Tab(label='Descriptive Statistics', children=[
            dcc.RadioItems(
                id='stats_income_spending_toggle',
                options=[
                    {'label': 'Spending', 'value': 'Spending'},
                    {'label': 'Income', 'value': 'Income'}
                ],
                value='Spending',
                inline=True,
                labelStyle={'color': 'white'}
            ),
            dcc.RadioItems(
                id='stats_month_filter',
                options=[{'label': 'Total', 'value': 'Total'}] + [{'label': m, 'value': m} for m in months],
                value='Total',
                inline=True,
                labelStyle={'color': 'white'}
            ),
            dash_table.DataTable(
                id='stats_table',
                style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left'},
            )
        ]),
        ### Fourth tab for spending/income over time
        dcc.Tab(label='Over Time', children=[
            dcc.Graph(id='over_time_chart')
        ]),
        ### Fifth tab for budgeting
        dcc.Tab(label='Budget', children=[
            dcc.RadioItems(
                id='budget_view_toggle',
                options=[
                    {'label': 'Expenses', 'value': 'Expenses'},
                    {'label': 'Income', 'value': 'Income'},
                    {'label': 'Review', 'value': 'Review'}
                ],
                value='Expenses',
                inline=True,
                labelStyle={'color': 'white'}
            ),
            html.Div(id='budget_planning', children=[
                html.Div(id='budget_inputs'),
            ]),
            html.Div(id='budget_income_planning', children=[
                html.Div(id='budget_income_inputs'),
            ]),
            html.Div(id='budget_review', children=[])
        ])
    ])
])

## Callbacks

### App Callbacks

#### Callback to exit the app when the exit button is clicked
@callback(
    Output('url', 'href'),
    Input('exit_button', 'n_clicks'),
    prevent_initial_call=True
)
def exit_app(n_clicks):
    def shutdown():
        import time
        time.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)
    threading.Thread(target=shutdown).start()
    return '/shutdown'
 
### Pie chart callbacks

#### This callback updates the main pie chart based on the selected month and whether the user is viewing income or spending. 
#### It also updates the drilldown pie chart when a category is clicked
@callback(
    # Inputs and Outputs for pie chart
    Output('pie_chart', 'figure'),
    Output('drilldown_chart', 'figure'),
    Input('month_filter', 'value'),
    Input('pie_chart', 'clickData'),
    Input('income_spending_toggle', 'value')
)

def update_pie(selected_month, clickData, toggle):
    if toggle == 'Spending':
        base_df = spending_df
    else:
        base_df = df[df['Category name'] == 'Income'].copy()
        base_df['Month'] = base_df['Transaction Date'].dt.to_period('M').astype(str)

    if selected_month == 'Total':
        filtered_df = base_df
    else:
        filtered_df = base_df[base_df['Month'] == selected_month]

    if toggle == 'Income':
        main_fig = px.pie(filtered_df, values='Amount', names='Sub-category name')
        return main_fig, {}
    else:
        main_fig = px.pie(filtered_df, values='Amount', names='Category name')

    if clickData is None:
        top_category = filtered_df.groupby('Category name')['Amount'].sum().idxmax()
        drilldown_df = filtered_df[filtered_df['Category name'] == top_category]
        drilldown_fig = px.pie(drilldown_df, values='Amount', names='Sub-category name', title=f'{top_category} Breakdown')
        return main_fig, drilldown_fig

    label = clickData['points'][0]['label']
    if toggle == 'Spending':
        drilldown_df = filtered_df[filtered_df['Category name'] == label]
        drilldown_fig = px.pie(drilldown_df, values='Amount', names='Sub-category name', title=f'{label} Breakdown')
    else:
        return main_fig, {}

    return main_fig, drilldown_fig

#### Callback to hide drilldown chart when income is selected
@callback(
    Output('drilldown_chart', 'style'),
    Input('income_spending_toggle', 'value')
)
def toggle_pie_drilldown(toggle):
    if toggle == 'Income':
        return {'display': 'none'}
    return {'display': 'block'}

### Month-over-month (MoM callbacks)

#### Callback to update the month-over-month chart
@callback(
    Output('mom_chart', 'figure'),
    Input('mom_category_filter', 'value')
)
def update_mom_chart(selected_category):
    if selected_category == 'Total':
        filtered_df = spending_df
        title = 'Month over Month Total Spending Change'
    elif selected_category == 'Income':
        filtered_df = income_df
        title = 'Month over Month Total Income Change'
    else:
        filtered_df = spending_df[spending_df['Category name'] == selected_category]
        title = f'Month over Month {selected_category} Change'

    all_months = sorted(spending_df['Month'].unique())
    monthly = filtered_df.groupby('Month')['Amount'].sum().reset_index()
    monthly = monthly.set_index('Month').reindex(all_months, fill_value=0).reset_index()
    monthly = monthly.sort_values('Month')
    monthly['Change'] = monthly['Amount'].diff()

    fig = px.bar(monthly, x='Month', y='Change', title=title,
                 labels={'Change': '$ Change', 'Month': 'Month'},
                 color='Change',
                 color_continuous_scale=['green', 'red'])
    fig.update_layout(yaxis_tickprefix='$')
    fig.update_xaxes(type='category')
    return fig

#### Callback to update the month-over-month chart for drilldown
@callback(
    Output('mom_drilldown_chart', 'figure'),
    Input('mom_category_filter', 'value')
)
def update_mom_drilldown(selected_category):
    if selected_category == 'Total':
        return {}
    elif selected_category == 'Income':
        filtered_df = income_df
    else:
        filtered_df = spending_df[spending_df['Category name'] == selected_category]

    monthly = filtered_df.groupby(['Month', 'Sub-category name'])['Amount'].sum().reset_index()
    all_months = sorted(spending_df['Month'].unique())
    all_subs = monthly['Sub-category name'].unique()
    full_index = pd.MultiIndex.from_product([all_months, all_subs], names=['Month', 'Sub-category name'])
    monthly = monthly.set_index(['Month', 'Sub-category name']).reindex(full_index, fill_value=0).reset_index()
    monthly = monthly.sort_values('Month')
    monthly['Change'] = monthly.groupby('Sub-category name')['Amount'].diff()

    fig = px.bar(monthly, x='Month', y='Change', color='Sub-category name',
                 title=f'{selected_category} — Sub-category Month over Month Change',
                 labels={'Change': '$ Change', 'Month': 'Month'},
                 barmode='group')
    fig.update_layout(yaxis_tickprefix='$')
    fig.update_xaxes(type='category')
    return fig

#### Callback to hide drilldown chart when 'Total' is selected in month-over-month tab
@callback(
    Output('mom_drilldown_container', 'style'),
    Input('mom_category_filter', 'value')
)
def toggle_mom_drilldown_visibility(selected_category):
    if selected_category == 'Total':
        return {'display': 'none'}
    return {'display': 'block'}

### Callback to update the descriptive statistics table

@callback(
    Output('stats_table', 'data'),
    Output('stats_table', 'columns'),
    Input('stats_income_spending_toggle', 'value'),
    Input('stats_month_filter', 'value')
)
def update_stats_table(toggle, selected_month):
    if toggle == 'Income':
        filtered_df = income_df if selected_month == 'Total' else income_df[income_df['Month'] == selected_month]
        group_col = 'Sub-category name'
        rename_col = 'Income Source'
    else:
        filtered_df = spending_df if selected_month == 'Total' else spending_df[spending_df['Month'] == selected_month]
        group_col = 'Category name'
        rename_col = 'Category'

    df_stats = filtered_df.groupby(group_col)['Amount'].agg(
        Mean='mean', Median='median', Std='std',
        Min='min', Max='max', Count='count', Total='sum'
    ).round(2).reset_index()
    df_stats['Range'] = (df_stats['Max'] - df_stats['Min']).round(2)
    df_stats = df_stats.rename(columns={group_col: rename_col})

    columns = [{'name': c, 'id': c} for c in df_stats.columns]
    data = df_stats.to_dict('records')
    return data, columns

### Callback for over time chart
@callback(
    Output('over_time_chart', 'figure'),
    Input('over_time_chart', 'id')
)
def update_over_time_chart(_):
    daily_spending = spending_df.groupby('Transaction Date')['Amount'].sum().reset_index()
    daily_spending = daily_spending.rename(columns={'Amount': 'Spending'})

    daily_income = income_df.groupby('Transaction Date')['Amount'].sum().reset_index()
    daily_income = daily_income.rename(columns={'Amount': 'Income'})

    combined = pd.merge(daily_spending, daily_income, on='Transaction Date', how='outer').fillna(0)
    combined = combined.sort_values('Transaction Date')
    combined['Net Cash Flow'] = combined['Income'] - combined['Spending']
    combined['Net Cash Flow'] = combined['Net Cash Flow'].cumsum()

    fig = px.line(combined, x='Transaction Date', y='Net Cash Flow',
                  title='Daily Net Cash Flow Over Time',
                  labels={'Net Cash Flow': '$', 'Transaction Date': 'Date'})
    fig.add_hline(y=0, line_dash='dash', line_color='grey')
    return fig

### Budget Tab Callbacks

#### Callback to update budget inputs based on stored budgets and actual spending data
@callback(
    Output('budget_inputs', 'children'),
    Input('budget_inputs', 'id')
)
def update_budget_inputs(stored_budgets):
    months_count = spending_df['Month'].nunique()

    header = html.Div([
        html.Span('Sub-category',  style={'display': 'inline-block', 'width': '200px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Budget $',      style={'display': 'inline-block', 'width': '160px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Avg/Month',     style={'display': 'inline-block', 'width': '120px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Min/Month',     style={'display': 'inline-block', 'width': '120px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Max/Month',     style={'display': 'inline-block', 'width': '120px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Over/Under',    style={'display': 'inline-block', 'width': '120px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Min. Mandatory',style={'display': 'inline-block', 'width': '120px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
    ], style={'marginBottom': '6px', 'marginLeft': '20px'})

    inputs = [header]

    for category in sorted(spending_df['Category name'].unique()):
        inputs.append(html.H4(category, style={'color': 'white', 'marginTop': '14px'}))
        subs = sorted(spending_df[spending_df['Category name'] == category]['Sub-category name'].unique())

        for sub in subs:
            key = f'{category}||{sub}'
            budget_val = None
            avg_actual = spending_df[
                (spending_df['Category name'] == category) &
                (spending_df['Sub-category name'] == sub)
            ]['Amount'].sum() / months_count
            avg_actual = round(avg_actual, 2)

            monthly_sub = spending_df[
                (spending_df['Category name'] == category) &
                (spending_df['Sub-category name'] == sub)
            ].groupby('Month')['Amount'].sum()
            min_month = round(monthly_sub.min(), 2)
            max_month = round(monthly_sub.max(), 2)

            mandatory = spending_df[
                (spending_df['Category name'] == category) &
                (spending_df['Sub-category name'] == sub) &
                (spending_df['Regular occurance'] == True)
            ]['Amount'].sum() / months_count
            mandatory = round(mandatory, 2)

            over_under = round(0 - avg_actual, 2)
            ou_color = 'green' if over_under >= 0 else 'red'

            inputs.append(html.Div([
                html.Span(f'→ {sub}', style={'display': 'inline-block', 'width': '200px', 'color': 'lightgrey', 'marginLeft': '20px'}),
                dcc.Input(
                    id={'type': 'budget_input', 'index': key},
                    type='number', min=0, placeholder='$',
                    value=budget_val,
                    style={'width': '120px', 'marginRight': '40px', 'color': 'black', 'backgroundColor': 'white'}
                ),
                html.Span(f'${avg_actual:,.2f}', style={'display': 'inline-block', 'width': '120px', 'color': 'white'}),
                html.Span(f'${min_month:,.2f}', style={'display': 'inline-block', 'width': '120px', 'color': 'white'}),
                html.Span(f'${max_month:,.2f}', style={'display': 'inline-block', 'width': '120px', 'color': 'white'}),
                html.Span(f'${over_under:,.2f}', style={'display': 'inline-block', 'width': '120px', 'color': ou_color},
                    id={'type': 'over_under', 'index': key}),
                html.Span(f'${mandatory:,.2f}', style={'display': 'inline-block', 'width': '120px', 'color': 'white'}),
                html.Button('▼ Fixed Expenses', id={'type': 'expand_btn', 'index': key},
                    n_clicks=0,
                    style={'marginLeft': '10px', 'backgroundColor': 'transparent', 'color': 'white', 'border': 'none', 'cursor': 'pointer'}
                ) if mandatory > 0 else html.Button('', id={'type': 'expand_btn', 'index': key},
                    n_clicks=0,
                    style={'display': 'none'}),
            ], style={'marginBottom': '4px', 'display': 'flex', 'alignItems': 'center'}))

            inputs.append(html.Div(
                id={'type': 'expand_content', 'index': key},
                style={'display': 'none', 'marginLeft': '20px', 'marginBottom': '8px'}
            ))
            
    return inputs

#### Callback to expand/collapse merchant details
@callback(
    Output({'type': 'expand_content', 'index': ALL}, 'children'),
    Output({'type': 'expand_content', 'index': ALL}, 'style'),
    Input({'type': 'expand_btn', 'index': ALL}, 'n_clicks'),
    State({'type': 'expand_btn', 'index': ALL}, 'id'),
)
def toggle_expand(n_clicks_list, ids):
    children = []
    styles = []
    for n_clicks, id_dict in zip(n_clicks_list, ids):
        category, sub = id_dict['index'].split('||')
        if n_clicks % 2 == 1:
            sub_df = spending_df[
                (spending_df['Category name'] == category) &
                (spending_df['Sub-category name'] == sub) &
                (spending_df['Regular occurance'] == True)
            ][['Transaction Date','Merchant name', 'Full description', 'Amount']].drop_duplicates()
            table = dash_table.DataTable(
                data=sub_df.to_dict('records'),
                columns=[{'name': c, 'id': c} for c in sub_df.columns],
                style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left'},
            )
            children.append(html.Div([
                html.H6('Fixed Expenses', style={'color': 'lightgrey', 'marginBottom': '4px'}),
                table
            ]))
            styles.append({'display': 'block', 'marginLeft': '20px', 'marginBottom': '8px'})
        else:
            children.append(None)
            styles.append({'display': 'none', 'marginLeft': '20px', 'marginBottom': '8px'})
    return children, styles

#### Callback to update over/under spans when budget inputs change
@callback(
    Output({'type': 'over_under', 'index': ALL}, 'children'),
    Output({'type': 'over_under', 'index': ALL}, 'style'),
    Input({'type': 'budget_input', 'index': ALL}, 'value'),
    State({'type': 'budget_input', 'index': ALL}, 'id'),
)
def update_over_under(values, ids):
    months_count = spending_df['Month'].nunique()
    children = []
    styles = []
    for val, id_dict in zip(values, ids):
        category, sub = id_dict['index'].split('||')
        avg_actual = spending_df[
            (spending_df['Category name'] == category) &
            (spending_df['Sub-category name'] == sub)
        ]['Amount'].sum() / months_count
        avg_actual = round(avg_actual, 2)
        over_under = round((val or 0) - avg_actual, 2)
        ou_color = 'green' if over_under >= 0 else 'red'
        children.append(f'${over_under:,.2f}')
        styles.append({'display': 'inline-block', 'width': '120px', 'color': ou_color})
    return children, styles

@callback(
    Output({'type': 'income_over_under', 'index': ALL}, 'children'),
    Output({'type': 'income_over_under', 'index': ALL}, 'style'),
    Input({'type': 'budget_income_input', 'index': ALL}, 'value'),
    State({'type': 'budget_income_input', 'index': ALL}, 'id'),
)
def update_income_over_under(values, ids):
    months_count = income_df['Month'].nunique()
    children = []
    styles = []
    for val, id_dict in zip(values, ids):
        _, sub = id_dict['index'].split('||')
        avg_actual = income_df[income_df['Sub-category name'] == sub]['Amount'].sum() / months_count
        avg_actual = round(avg_actual, 2)
        over_under = round((val or 0) - avg_actual, 2)
        ou_color = 'green' if over_under >= 0 else 'red'
        children.append(f'${over_under:,.2f}')
        styles.append({'display': 'inline-block', 'width': '120px', 'color': ou_color})
    return children, styles

#### Callback to toggle between expenses, income and review views
@callback(
    Output('budget_planning', 'style'),
    Output('budget_income_planning', 'style'),
    Output('budget_review', 'style'),
    Input('budget_view_toggle', 'value')
)
def toggle_budget_view(view):
    if view == 'Expenses':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}
    elif view == 'Income':
        return {'display': 'none'}, {'display': 'block'}, {'display': 'none'}
    return {'display': 'none'}, {'display': 'none'}, {'display': 'block'}

#### Callback to update review tables
@callback(
    Output('budget_review', 'children'),
    Input({'type': 'budget_input', 'index': ALL}, 'value'),
    State({'type': 'budget_input', 'index': ALL}, 'id'),
    Input({'type': 'budget_income_input', 'index': ALL}, 'value'),
    State({'type': 'budget_income_input', 'index': ALL}, 'id'),
)
def update_budget_review(exp_values, exp_ids, inc_values, inc_ids):
    ##### --- Expenses table ---
    rows = []
    category_totals = {}
    for val, id_dict in zip(exp_values, exp_ids):
        category, sub = id_dict['index'].split('||')
        budget = val or 0
        rows.append({'Category': category, 'Sub-category': sub, 'Budget': f'${budget:,.2f}'})
        category_totals[category] = category_totals.get(category, 0) + budget

    exp_table_rows = []
    for category in sorted(category_totals.keys()):
        exp_table_rows.append({'Category': category, 'Sub-category': '', 'Budget': f'${category_totals[category]:,.2f}'})
        for row in [r for r in rows if r['Category'] == category]:
            exp_table_rows.append({'Category': '', 'Sub-category': f'  → {row["Sub-category"]}', 'Budget': row['Budget']})

    total_expenses = sum(category_totals.values())
    exp_table_rows.append({'Category': 'Total', 'Sub-category': '', 'Budget': f'${total_expenses:,.2f}'})

    expenses_table = dash_table.DataTable(
        data=exp_table_rows,
        columns=[{'name': c, 'id': c} for c in ['Category', 'Sub-category', 'Budget']],
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
        style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{Category} != ""'},
                'backgroundColor': 'rgb(0, 30, 80)',
                'color': 'white',
                'fontWeight': 'bold',
            },
            {
                'if': {'filter_query': '{Category} = "Total"'},
                'backgroundColor': 'rgb(130, 30, 30)',
                'color': 'white',
                'fontWeight': 'bold',
            }
        ],
    )

    ##### --- Income table ---
    inc_table_rows = []
    total_income = 0
    for val, id_dict in zip(inc_values, inc_ids):
        _, sub = id_dict['index'].split('||')
        budget = val or 0
        total_income += budget
        inc_table_rows.append({'Income Source': f'  → {sub}', 'Budget': f'${budget:,.2f}'})

    inc_table_rows.append({'Income Source': 'Total', 'Budget': f'${total_income:,.2f}'})

    income_table = dash_table.DataTable(
        data=inc_table_rows,
        columns=[{'name': c, 'id': c} for c in ['Income Source', 'Budget']],
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
        style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{Income Source} = "Total"'},
                'backgroundColor': 'rgb(10, 90, 10)',
                'color': 'white',
                'fontWeight': 'bold',
            }
        ],
    )

    ##### --- Net table ---
    net = total_income - total_expenses
    net_color = 'rgb(0, 60, 0)' if net >= 0 else 'rgb(100, 0, 0)'
    net_table = dash_table.DataTable(
        data=[
            {'Label': 'Total Income',   'Amount': f'${total_income:,.2f}'},
            {'Label': 'Total Expenses', 'Amount': f'${total_expenses:,.2f}'},
            {'Label': 'Net',            'Amount': f'${net:,.2f}'},
        ],
        columns=[{'name': c, 'id': c} for c in ['Label', 'Amount']],
        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
        style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white', 'textAlign': 'left'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{Label} = "Net"'},
                'backgroundColor': net_color,
                'color': 'white',
                'fontWeight': 'bold',
            }
        ],
    )

    return html.Div([
        html.H4('Expenses', style={'color': 'white', 'marginTop': '16px'}),
        expenses_table,
        html.H4('Income', style={'color': 'white', 'marginTop': '24px'}),
        income_table,
        html.H4('Income - Expenses', style={'color': 'white', 'marginTop': '24px'}),
        net_table,
    ])

#### Callback to update income button
@callback(
    Output('budget_income_inputs', 'children'),
    Input('budget_income_inputs', 'id')
)
def update_budget_income_inputs(_):
    months_count = income_df['Month'].nunique()

    header = html.Div([
        html.Span('Income Source', style={'display': 'inline-block', 'width': '200px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Budget $',      style={'display': 'inline-block', 'width': '160px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Avg/Month',     style={'display': 'inline-block', 'width': '120px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Min/Month',     style={'display': 'inline-block', 'width': '120px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Max/Month',     style={'display': 'inline-block', 'width': '120px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
        html.Span('Over/Under',    style={'display': 'inline-block', 'width': '120px', 'color': 'lightgrey', 'fontWeight': 'bold'}),
    ], style={'marginBottom': '6px', 'marginLeft': '20px'})

    inputs = [header]

    for sub in sorted(income_df['Sub-category name'].unique()):
        key = f'Income||{sub}'

        avg_actual = income_df[income_df['Sub-category name'] == sub]['Amount'].sum() / months_count
        avg_actual = round(avg_actual, 2)

        monthly_sub = income_df[income_df['Sub-category name'] == sub].groupby('Month')['Amount'].sum()
        min_month = round(monthly_sub.min(), 2)
        max_month = round(monthly_sub.max(), 2)

        over_under = round(0 - avg_actual, 2)
        ou_color = 'green' if over_under >= 0 else 'red'

        inputs.append(html.Div([
            html.Span(f'→ {sub}', style={'display': 'inline-block', 'width': '200px', 'color': 'lightgrey', 'marginLeft': '20px'}),
            dcc.Input(
                id={'type': 'budget_income_input', 'index': key},
                type='number', min=0, placeholder='$',
                value=None,
                style={'width': '120px', 'marginRight': '40px', 'color': 'black', 'backgroundColor': 'white'}
            ),
            html.Span(f'${avg_actual:,.2f}', style={'display': 'inline-block', 'width': '120px', 'color': 'white'}),
            html.Span(f'${min_month:,.2f}',  style={'display': 'inline-block', 'width': '120px', 'color': 'white'}),
            html.Span(f'${max_month:,.2f}',  style={'display': 'inline-block', 'width': '120px', 'color': 'white'}),
            html.Span(f'${over_under:,.2f}', style={'display': 'inline-block', 'width': '120px', 'color': ou_color},
                id={'type': 'income_over_under', 'index': key}),
        ], style={'marginBottom': '4px', 'display': 'flex', 'alignItems': 'center'}))

    return inputs

### definition to open a browser
def open_browser():
    import time
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:8050')

# Start the app in a separate thread to allow automatic browser launch
threading.Thread(target=open_browser).start()

# Run the app
app.run()