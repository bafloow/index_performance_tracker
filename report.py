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


def plot_return_contribution_barchart():
    pass


def plot_sector_breadth_barchart():
    pass


def plot_risk_return_scatter():
    pass


def plot_market_breath_gauge():
    pass


def render_kpi_stats(index_data):
    pass


def render_dashboard():
    pass

    
