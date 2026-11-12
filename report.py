import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from metrics import get_market_summary

def plot_index_treemap(index_data, selected_index):

    df_tree = index_data['company_performance'].copy()
    df_tree['label'] = (df_tree['company'] + "<br>" + (df_tree['total_return']*100).map('{:+.1f}%'.format))

    sec_df = index_data['sector_performance'].copy()
    if 'sector' in sec_df.columns:
        sec_df = sec_df.set_index('sector')

    color_list = [
        [0.0, "#E63946"],
        [0.5, "#1E1E2E"],
        [1.0, "#06D6A0"]
    ]

    tree = px.treemap(data_frame=df_tree,
                      path=[px.Constant(selected_index),'sector','company'],
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


def render_dashboard():
    pass

    
