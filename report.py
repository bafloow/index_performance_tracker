import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from metrics import get_market_summary

def plot_index_treemap(index_data, selected_index):

    df_tree = index_data['company_performance'].copy()
    df_tree['label'] = (df_tree['symbol'] + "<br>" + (df_tree['total_return']*100).map('{:+.1f}%'.format))

    sec_df = index_data['sector_performance'].copy()
    if 'sector' in sec_df.columns:
        sec_df = sec_df.set_index('sector')

    color_list = [
        [0.0, "#E63946"],
        [0.5, "#1E1E2E"],
        [1.0, "#06D6A0"]
    ]

    tree = px.treemap(data_frame=df_tree,
                      path=[px.Constant(selected_index),'sector','symbol'],
                      values='weight',
                      color='total_return',color_continuous_scale=color_list,color_continuous_midpoint=0,
                      custom_data=df_tree[['contribution','gk_vol','total_return']],
                      labels={'total_return': 'Return'}
                      )

    for i, node in enumerate(tree.data[0].labels):
        if node == selected_index:
            tree.data[0].customdata[i] = [index_data['index_performance']['total_return'],index_data['index_performance']['gk_vol'],index_data['index_performance']['total_return']]
            tree.data[0].marker.colors[i] = index_data['index_performance']['total_return'].iloc[0]
        elif node in sec_df.index:
            tree.data[0].customdata[i] = [sec_df.loc[node,'contribution'],sec_df.loc[node,'gk_vol'],sec_df.loc[node,'total_return']]
            tree.data[0].marker.colors[i] = sec_df.loc[node,'total_return']

    tree.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[2]:+.1%}",
        textposition="middle center",
        textfont=dict(size=14, family="Inter, sans-serif", color="white"),
        marker=dict(
            cornerradius=4,
            pad=dict(t=20,l=4,r=4,b=4)
        ),
        hovertemplate="""
            <b>%{label}</b><br>
            Index weight: %{value:.2%}<br>
            Total return: %{color:.2%}<br>
            Index contribution: %{customdata[0]:.3%}<br>
            Volatility (GK): %{customdata[1]:.1%}
            <extra></extra>
            """
    )

    tree.update_layout(
        coloraxis=dict(
            colorbar=dict(
                tickformat="+.0%",
                thickness=14,
                len=0.75,
                outlinewidth=0
            ),
            colorscale=color_list,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=0,b=0)
    )

    return tree


def plot_return_contribution_barchart(index_data, view_option):

    is_return = view_option == 'Total return (%)'
    val_col = 'total_return' if is_return else 'contribution'
    hover_unit = '%' if is_return else 'pp'

    sector_data = index_data['sector_performance'].copy()
    df_sorted = sector_data.sort_values(by=val_col,ascending=True)

    df_sorted[['total_return','contribution','weight']] =df_sorted[['total_return','contribution','weight']]*100

    color_list = ['#00E676' if val >= 0 else "#FF5252" for val in df_sorted[val_col]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(y=df_sorted['sector'],x=df_sorted[val_col],
               orientation='h',
               marker=dict(color=color_list,line=dict(width=0)),
               text=[f"{v:+.2f}{hover_unit}" for v in df_sorted[val_col]],
               textposition='outside',
               customdata=df_sorted[['weight','total_return','contribution']],
               hovertemplate=("""
                              <b>%{y}</b><br>
                              Index weight: %{customdata[0]:.2f}%<br>
                              Total return: %{customdata[1]:.2f}%<br>
                              Index contribution: %{customdata[2]:.3f}%
                              <extra></extra>
                              """
                        )
                )
    )
    max_val = max(abs(df_sorted[val_col].min()), abs(df_sorted[val_col].max())) * 1.25
    if max_val == 0:
        max_val = 1.0

    fig.update_layout(
        template='plotly_dark',
        height=480,
        margin=dict(l=10,r=30,t=20,b=20),
        xaxis=dict(
                    range=[-max_val,max_val],
                    tickfont=dict(size=14),
                    zeroline=True,
                    zerolinecolor='#555555',
                    zerolinewidth=1.5,
                    gridcolor='#2A2E39',
                    title=None
                ),
                yaxis=dict(
                            tickfont=dict(size=13),
                            title=None
                        ),
    )
    return fig
    


def plot_sector_breadth_barchart(index_data,period):

    sector_breadth = index_data['market_breadth']['sector_breadth'].copy()

    is_sma50 = period == 'SMA50'
    val_col = 'pct_above50' if is_sma50 else 'pct_above200'
    above_count = 'above50' if is_sma50 else 'above200'

    df_sorted = sector_breadth.sort_values(by=val_col, ascending=True)
    df_sorted['below_count'] = df_sorted['total_stocks'] - df_sorted[above_count]

    color_list=[[0.0, '#FF3B30'],
                [0.35, '#FF9500'],
                [0.5,"#DAE55D"],
                [0.65, '#30D158'],
                [1.0, "#035E32"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=df_sorted['sector'], x=df_sorted[val_col],
            orientation='h',
            marker=dict(color=df_sorted[val_col], cmin=0, cmax=100,
                        colorscale=color_list, showscale=False),
            text=[f"{v:.2f}%" for v in df_sorted[val_col]],
            textposition='outside',
            customdata=df_sorted[['total_stocks',above_count,'below_count']],
            hovertemplate=("""
                        <b>%{y}</b><br>
                        Stocks above sma: %{customdata[1]}<br>
                        Stocks below sma: %{customdata[2]}<br> 
                        Total stocks: %{customdata[0]}
                        <extra></extra>
                        """)
        )
    )

    fig.update_layout(
        template='plotly_dark',
        height=480,
        margin=dict(l=10,r=30,t=20,b=20),
        xaxis=dict(
            range=[0,100],
            tickfont=dict(size=14),
            title=None
        ),
        yaxis=dict(
            tickfont=dict(size=13),
            title=None
        )
    )

    fig.add_vline(
        x=50,
        line_width=1.5,
        line_dash='dash',
        line_color='gray',
        layer='above',
        annotation_text='50%',
        annotation_position='top',
        annotation_font=dict(color='gray', size=12)
    )

    return fig



def plot_risk_return_scatter(data,group):

    data_df = data.copy()
    is_sector = group == 'Sectors'
    name_col = 'sector' if is_sector else 'company'
    txt = 'sector' if is_sector else 'txt_company'

    if not is_sector:
        top_gainers = data_df.nlargest(4,'total_return')['company']
        top_losers = data_df.nsmallest(4,'total_return')['company']
        top_vol = data_df.nlargest(3,'gk_vol')['company']
        outliers = set(top_gainers).union(set(top_losers)).union(set(top_vol))
        data_df['txt_company'] =  data_df['company'].where(data_df['company'].isin(outliers),"")

    fig = px.scatter(data_frame=data_df, x='gk_vol', y='total_return',
                     color='sector',
                     text=txt,
                     hover_name=name_col,
                     custom_data=['sector','weight'],
                     labels={
                            'total_return': 'Rate of Return',
                            'gk_vol': 'Garman-Klass Volatility',
                            'sector': 'Sector'
                            })

    sector_line = "" if is_sector else "Sector: %{customdata[0]}<br>"
    fig.update_traces(
        textposition='top center',
        marker=dict(size=11, opacity=0.8, line=dict(width=1, color="white")),
                    hovertemplate=(
                                "<b>%{hovertext}</b><br>"
                                f"{sector_line}"
                                "Rate of Return: %{y:.2%}<br>"
                                "Garman-Klass Volatility: %{x:.2%}<br>"
                                "Index weight: %{customdata[1]:.2%}"
                                "<extra></extra>"
                            )
    )

    fig.add_hline(y=0, line_dash='dash', line_color='gray', opacity=0.7)
    
    gk_median=data_df['gk_vol'].median()
    fig.add_vline(x=gk_median, line_dash='dash', line_color='gray', opacity=0.7, line_width=0.7,
                 annotation_text='GK median', annotation_position='top', annotation_font=dict(color='gray',size=12))

    fig.update_layout(
        template='plotly_dark',
        height=550,
        showlegend=not is_sector,
        margin=dict(l=10, r=10, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5,
                    font=dict(style='italic', size=14, weight=75),
                    title=dict(font=dict(size=15, weight=100))),
        xaxis=dict(
            tickformat='.1%',
            title_font=dict(size=18),
            tickfont=dict(size=14)
        ),
        yaxis=dict(
            tickformat='.1%',
            title_font=dict(size=18),
            tickfont=dict(size=14)
        )
    )

    return fig



def plot_market_breath_gauge(data,period):

    breadth_df = data['market_breadth']['index_breadth'].copy()
    is_sma50 = period =='SMA50'

    pct_col = 'pct_above50' if is_sma50 else 'pct_above200'
    count_col = 'above50' if is_sma50 else 'above200'

    pct_above = breadth_df[pct_col]
    above_count = breadth_df[count_col]
    total_count = breadth_df['total_stocks']
    below_count = total_count - above_count

    if pct_above < 30:
        bar_color = "#ff4b4b"
    elif pct_above > 70:
        bar_color = "#00e676"
    else:
        bar_color = "#facc15"

    fig = go.Figure(
        go.Indicator(
            mode='gauge+number',
            value=breadth_df[pct_col],
            number=dict(suffix='%',
                        valueformat='.1f',
                        font=dict(size=44)),
            gauge=dict(
                axis=dict(range=[0,100],
                          tickmode='array',
                          tickvals=[0,30,50,70,100],
                          ticktext=['0%', '30%', '50%', '70%', '100%'],
                          tickwidth=2,
                          tickcolor='white',
                          tickfont=dict(size=15, color='white')),
                bar=dict(color=bar_color,thickness=0.75),
                steps=[
                    dict(range=[0,30], color="#1c2128"),
                    dict(range=[31,70], color="#262c36"),
                    dict(range=[71,100], color="#1c2128")
                ],
                threshold=dict(line=dict(color='white',width=3),thickness=0.75,value=50)
            )
        )
    )

    fig.add_annotation(
        x=0.5,
        y=-0.1,
        text=f"{above_count} Above {period} | {below_count} Below {period} (Total: {total_count})",
        showarrow=False,
        font=dict(size=16,color='lightgray')
    )

    fig.update_layout(
        template='plotly_dark',
        height=420,
        margin=dict(l=30, r=30, t=60, b=30)
    )

    return fig


def render_kpi_stats(index_data):

    data_df = index_data.copy()

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric(label='Index return',
                value=f"{data_df['index_performance']['total_return'].iloc[0]*100:+.2f}%")
    kpi2.metric(label='Index breadth (% > SMA50)',
                value=f"{data_df['market_breadth']['index_breadth']['pct_above50']:.2f}%")
    kpi3.metric(label='Garman-Klass Volatility',
                value=f"{data_df['index_performance']['gk_vol'].iloc[0]*100:.2f}%")
    kpi4.metric(label='Standard Deviation',
                value=f"{data_df['index_performance']['std_vol'].iloc[0]*100:.2f}%")


def render_stock_screener(data, active_cols):

    data_df = data.copy()

    row_even = "#11141c"
    row_odd = "#181c26"
    row_bg = [row_even if i % 2 == 0 else row_odd for i in range(len(data_df))]

    COLUMN_CONFIG = {
    "symbol": {
        "label": "<b>Symbol</b>",
        "width": 75,
        "align": "left",
        "format": lambda s: s.astype(str),
        "color": lambda s: "#ffffff",
    },
    "company": {
        "label": "<b>Company</b>",
        "width": 150,
        "align": "left",
        "format": lambda s: s.astype(str),
        "color": lambda s: "#d0d4dc",
    },
    "sector": {
        "label": "<b>Sector</b>",
        "width": 150,
        "align": "left",
        "format": lambda s: s.astype(str),
        "color": lambda s: "#9ea4b0",
    },
    "sub_sector": {
        "label": "<b>Sub-Sector</b>",
        "width": 160,
        "align": "left",
        "format": lambda s: s.astype(str),
        "color": lambda s: "#9ea4b0",
    },
    "weight": {
        "label": "<b>Weight</b>",
        "width": 85,
        "align": "right",
        "format": lambda s: s.map("{:.2f}%".format),
        "color": lambda s: "#e0e0e0",
    },
    "start_price": {
        "label": "<b>Start Price</b>",
        "width": 90,
        "align": "right",
        "format": lambda s: s.map("{:.2f}".format),
        "color": lambda s: "#e0e0e0",
    },
    "end_price": {
        "label": "<b>End Price</b>",
        "width": 90,
        "align": "right",
        "format": lambda s: s.map("{:.2f}".format),
        "color": lambda s: "#e0e0e0",
    },
    "total_return": {
        "label": "<b>Return</b>",
        "width": 90,
        "align": "right",
        "format": lambda s: s.map("{:.2f}%".format),
        "color": lambda s: [
            "#00e676" if v > 0 else "#ff5252" if v < 0 else "#e0e0e0" for v in s
        ],
    },
    "gk_vol": {
        "label": "<b>GK Volatility</b>",
        "width": 90,
        "align": "right",
        "format": lambda s: s.map("{:.2f}%".format),
        "color": lambda s: "#e0e0e0",
    },
    "std_vol" : {
        "label": "<b>Std Dev</b>",
        "width": 90,
        "align": "right",
        "format": lambda s: s.map("{:.2f}%".format),
        "color": lambda s: "#e0e0e0",
    },
    "contribution": {
        "label": "<b>Contribution</b>",
        "width": 90,
        "align": "right",
        "format": lambda s: s.map("{:.2f}%".format),
        "color": lambda s: [
            "#00e676" if v > 0 else "#ff5252" if v < 0 else "#e0e0e0" for v in s
        ],
    }}
    headers = [COLUMN_CONFIG[c]["label"] for c in active_cols]
    aligns = [COLUMN_CONFIG[c]['align'] for c in active_cols]
    widths = [COLUMN_CONFIG[c]['width'] for c in active_cols]

    cell_values = [COLUMN_CONFIG[c]["format"](data_df[c]) for c in active_cols]
    cell_colors = [COLUMN_CONFIG[c]["color"](data_df[c]) for c in active_cols]

    fig_table = go.Figure(
    data=[
        go.Table(
            columnwidth=widths,
            header=dict(
                values=headers,
                fill_color="#1f2430",
                line_color="#2b303c",
                align=aligns,
                font=dict(color="#ffffff", size=13),
                height=36,
            ),
            cells=dict(
                values=cell_values,
                fill_color=[row_bg] * len(active_cols),
                line_color="#2b303c",
                align=aligns,
                font=dict(
                    color=cell_colors,
                    size=12,
                ),
                height=32,
            ),
        )
    ])

    fig_table.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    height=400,
    paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig_table

def render_top_5_table(data, is_gainers=True):
    data_df = data.sort_values(by='total_return',ascending= not is_gainers).head(5).copy()
    data_df['total_return'] = data_df['total_return'] * 100

    ret_color = "#00e676" if is_gainers else "#ff5252"
    font_colors = ["#ffffff", "#d0d4dc", "#9ea4b0", ret_color]

    row_even = "#11141c"
    row_odd = "#181c26"
    row_bg = [row_even if i % 2 == 0 else row_odd for i in range(len(data_df))]

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[75, 150, 140, 85],
                header=dict(
                    values=["<b>Symbol</b>", "<b>Company</b>", "<b>Sector</b>", "<b>Return</b>"],
                    fill_color="#1f2430",
                    line_color="#2b303c",
                    align=["left", "left", "left", "right"],
                    font=dict(color="#ffffff", size=13),
                    height=34,
                ),
                cells=dict(
                    values=[
                        data_df['symbol'],
                        data_df['company'],
                        data_df['sector'],
                        data_df['total_return'].map("{:+.2f}%".format),
                    ],
                    fill_color=[row_bg] * 4,
                    line_color="#2b303c",
                    align=["left", "left", "left", "right"],
                    font=dict(color=font_colors, size=12),
                    height=30,
                )
            )
        ]
    )
    fig.update_layout(
        margin=dict(l=0,r=0,t=4,b=0),
        height=195,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def render_dashboard(data, selected_index):

    st.title(f"{selected_index} – Weekly Market Summary")

    render_kpi_stats(data)
    st.markdown('---')
    
    st.subheader("Market Heatmap")
    fig = plot_index_treemap(index_data=data, selected_index=selected_index)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('---')

    col_left, col_right = st.columns([1,1])
    with col_left:
        st.subheader('Sector Return vs Contribution')
        metric_view = st.radio('Sector metric:',
                            options=['Total return (%)','Index contribution'],
                            horizontal=True,
                            label_visibility='collapsed')
        
        fig2 = plot_return_contribution_barchart(index_data=data,view_option=metric_view)
        st.plotly_chart(fig2, use_container_width=True)

    with col_right:
        st.subheader('Sector Breadth')
        sma_period = st.radio('Choose period:',
                            options=['SMA50','SMA200'],
                            horizontal=True,
                            label_visibility='collapsed')
        fig3=plot_sector_breadth_barchart(index_data=data, period=sma_period)
        st.plotly_chart(fig3,use_container_width=True)

    st.markdown('---')

    col_left, col_right = st.columns([1,1])
    with col_left:
        st.subheader('Risk vs Return')
        col_left2, col_right2 = st.columns([1,2])
        with col_left2:
            mode = st.radio('Choose group:',
                        options=['Sectors','Companies'],
                        horizontal=True,
                        label_visibility='collapsed')
            if mode =='Companies':
                all_sectors = sorted(data['company_performance']['sector'].unique())
                with col_right2:
                    selected_sectors = st.multiselect(
                        'Filter by Sector:',
                        options=all_sectors,
                        default=[],
                        placeholder='Choose sectors...'
                    )
                if not selected_sectors:
                    selected_sectors = all_sectors
                data_df = data['company_performance'][data['company_performance']['sector'].isin(selected_sectors)].copy()
            else:
                data_df = data['sector_performance'].copy()

        fig4 = plot_risk_return_scatter(data=data_df,group=mode)
        st.plotly_chart(fig4,use_container_width=True)

    with col_right:
        st.subheader('Market Breadth')
        sma_period = st.radio('Select period:',
                            options=['SMA50','SMA200'],
                            horizontal=True,
                            label_visibility='collapsed')

        fig5 = plot_market_breath_gauge(data=data, period=sma_period)
        st.plotly_chart(fig5, use_container_width=True) 

    st.markdown('---')

    col_gainers, col_losers = st.columns([2,2])
    with col_gainers:
        st.markdown("<span style='color: #00e676; font-size: 1.5rem; font-weight: 600;'>▲ Top 5 Gainers</span>",
                    unsafe_allow_html=True,)
        fig_gainers = render_top_5_table(data=data['company_performance'],is_gainers=True)
        st.plotly_chart(fig_gainers,use_container_width=True)

    with col_losers:
        st.markdown("<span style='color: #ff5252; font-size: 1.5rem; font-weight: 600;'>▼ Top 5 Losers</span>",
                    unsafe_allow_html=True,)
        fig_losers = render_top_5_table(data=data['company_performance'],is_gainers=False)
        st.plotly_chart(fig_losers,use_container_width=True)

    st.markdown('---')

    st.subheader('Company Screener')

    company_performance=data['company_performance'].copy()

    SORT_OPTIONS = {
    "Weight": "weight",
    "Return (High to Low)": ("total_return", False),
    "Return (Low to High)": ("total_return", True),
    "GK Volatility": "gk_vol",
    "Contribution": "contribution",
    }

    col_search, col_sector, col_subsector, col_sort = st.columns([2, 2, 2, 1.5])
    with col_search:
        search_query = st.text_input("Search Symbol or Company", placeholder='e.g. NVDA, Apple...',)
    
    with col_sector:
        selected_sectors = st.multiselect(
            'Filter by Sector',
            options = sorted(company_performance['sector'].unique()),
            placeholder = 'All Sectors',
        )

    with col_subsector:
        if selected_sectors:
            available_subsectors = sorted(company_performance[company_performance['sector'].isin(selected_sectors)]['sub_sector'].unique())
        else:
            available_subsectors = sorted(company_performance['sub_sector'].unique())

        selected_subsectors = st.multiselect('Filter by Sub-Sector',
            options=available_subsectors,
            placeholder='All Sub-Sectors'
        )

    with col_sort:
        selected_sort_label = st.selectbox("Sort by",
            options=list(SORT_OPTIONS.keys()), index=0,
        )

    df = company_performance.copy()

    if search_query:
        query = search_query.strip()
        df = df[df["company"].str.contains(query, case=False, na=False) | df["symbol"].str.contains(query, case=False, na=False)]    
    
    if selected_sectors:
        df = df[df['sector'].isin(selected_sectors)]

    if selected_subsectors:
        df = df[df['sub_sector'].isin(selected_subsectors)]


    sort_target = SORT_OPTIONS[selected_sort_label]
    if isinstance(sort_target, tuple):
        sort_col, is_asc = sort_target
    else:
        sort_col, is_asc = sort_target, False
    display_df = df.sort_values(by=sort_col, ascending=is_asc).copy()

    pct_cols = ['weight','total_return','contribution','std_vol','gk_vol']
    for col in pct_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col] * 100

    col_toggle, col_info = st.columns([1.5, 1])
    with col_toggle:
        show_all_cols = st.toggle("Show detailed metrics (Prices, Sub-Sector, Volatility)", value=False)

    with col_info:
        st.markdown(
            f"<p style='text-align: right; color: #9ea4b0; margin-top: 10px; font-size: 0.85rem;'>"
            f"Showing <b>{len(display_df)}</b> of <b>{len(company_performance)}</b> companies"
            f"</p>",
            unsafe_allow_html=True
        )
        
    default_cols = ['symbol','company','sector','weight','total_return','gk_vol' ]
    all_cols = [c for c in display_df.columns]
    active_cols = all_cols if show_all_cols else default_cols

    fig5 = render_stock_screener(data=display_df, active_cols=active_cols)
    st.plotly_chart(fig5, use_container_width=True)