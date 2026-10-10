from db import get_connection, get_available_indexes
import pandas as pd
import numpy as np


def calc_daily_gk(df_stock):

    log_hl = np.log(df_stock['high']/df_stock['low'])
    log_co = np.log(df_stock['close']/df_stock['open'])

    daily_gk = 0.5 * (log_hl ** 2) - (2 * np.log(2) - 1 ) * (log_co ** 2)
    
    return daily_gk


def get_index_recent_prices(index_name, con, period=5):
    with con.cursor() as cur:
        cur.execute(
            f"""
            WITH newest_dates AS (
            SELECT DISTINCT date
            FROM daily_prices
            ORDER BY date DESC
            LIMIT {period + 1}
            )
            SELECT 
            ci.symbol, s.name AS sector,
            ss.name AS sub_sector,
            dp.date, dp.close, dp.open, dp.volume,
            dp.high, dp.low,
            ic.weight_percentage AS weight
            FROM indexes ind
            JOIN index_components ic ON ic.index_id = ind.id
            JOIN company_info ci ON ci.id = ic.company_id
            LEFT JOIN sectors s ON s.id = ci.sector_id
            LEFT JOIN sub_sectors ss ON ss.id = ci.sub_sector_id
            JOIN daily_prices dp ON dp.company_id = ci.id
            JOIN newest_dates nd ON nd.date = dp.date
            WHERE ind.name = %s
            ORDER BY ci.symbol, dp.date
            """, (index_name,)
        )
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]

        df = pd.DataFrame(data=rows,columns=cols)

        
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['close'] = df['close'].astype(float)
            df['open'] = df['open'].astype(float)
            df['weight'] = df['weight'].astype(float) / 100
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)

        return df

def get_index_breadth_data(index_name, con):
    with con.cursor() as cur:
        cur.execute(
            f"""
            WITH ranked_data AS (
            SELECT company_id, close,
            AVG(close) OVER(PARTITION BY company_id ORDER BY date
            ROWS BETWEEN 49 PRECEDING AND CURRENT ROW) AS sma_50,
            ROW_NUMBER() OVER(PARTITION BY company_id ORDER BY date DESC) AS rnk
            FROM daily_prices 
            )
            SELECT ci.symbol, s.name AS sector,
            rd.close, rd.sma_50
            FROM indexes ind
            JOIN index_components ic ON ic.index_id = ind.id
            JOIN company_info ci ON ci.id = ic.company_id
            JOIN ranked_data rd ON rd.company_id = ic.company_id
            LEFT JOIN sectors s ON ci.sector_id = s.id
            WHERE ind.name = %s 
            AND rnk = 1
            """, (index_name,)
        )
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]

        df = pd.DataFrame(data=rows, columns=cols)

        if not df.empty:
            df['close'] = df['close'].astype(float)
            df['sma_50'] = df['sma_50'].astype(float)

        return df

    

def get_daily_returns(df):
    df['daily_return'] = df.sort_values(by=['date'], ascending=True).groupby(['symbol'])['close'].pct_change()
    df['daily_gk'] = calc_daily_gk(df)
    df = df.sort_values(['symbol','date']).reset_index(drop=True) 
    return df

def get_total_return(df_daily):

    df = df_daily.groupby('symbol').agg(
        sector=('sector','first'),
        sub_sector=('sub_sector', 'first'),
        weight=('weight', 'first'),
        start_price=('close', 'first'),
        end_price=('close', 'last'),
        var=('daily_return', 'var'),
        gk_var=('daily_gk','mean')
    )

    df['total_return'] = (df['end_price'] - df['start_price'])/df['start_price']
    df['contribution'] = df['total_return'] * df['weight']
    df['std_vol'] = np.sqrt(df['var'] * 252)
    df['gk_vol'] = np.sqrt(df['gk_var'] * 252)

    return df

    

def get_group_performance(df_week, group='sector'):

   df_copy = df_week.copy()
   group_weight_sum = df_copy.groupby(group)['weight'].transform('sum')
   df_copy['intra_group_weight'] = df_copy['weight'] / group_weight_sum

   df_copy['weighted_var'] = df_copy['var'] * df_copy['intra_group_weight']
   df_copy['weighted_gk_var'] = df_copy['gk_var'] * df_copy['intra_group_weight']

   df = df_copy.groupby(group).agg(
        weight=('weight','sum'),
        contribution=('contribution','sum'),
        var=('weighted_var','sum'),
        gk_var=('weighted_gk_var','sum')
   )

   df['total_return'] = df['contribution'] / df['weight']
   df['std_vol'] = np.sqrt(df['var'] * 252)
   df['gk_vol'] = np.sqrt(df['gk_var'] * 252)
   
   return df


def get_top_gainers(df_week):
    columns = ['sector','sub_sector','total_return','contribution','gk_vol']
    winners = df_week.nlargest(5,'total_return')[columns]
    return winners

def get_top_losers(df_week):
    columns = ['sector','sub_sector','total_return','contribution','gk_vol']
    losers = df_week.nsmallest(5,'total_return')[columns]
    return losers

def get_market_breadth(df_breadth):
    df_copy = df_breadth.copy()
    df_copy['above_sma50'] = df_copy['close'] > df_copy['sma_50']

    total_stocks = len(df_copy)
    above_count = df_copy['above_sma50'].sum()
    below_count = total_stocks - above_count
    pct_above = round((above_count / total_stocks)*100,2)

    index_breadth = {
        'total_stocks' : total_stocks,
        'above_count' : above_count,
        'below_count' : below_count,
        'pct_above' : pct_above
    }

    sector_breadth = df_copy.groupby('sector').agg(
        total_stocks=('symbol','count'),
        above_count=('above_sma50','sum'),
        pct_above=('above_sma50', lambda x: round(sum(x)/len(x) * 100,2)),
    )
    sector_breadth['below_count'] = sector_breadth['total_stocks'] - sector_breadth['above_count']
    return {
        'index_breadth' : index_breadth,
        'sector_breadth' : sector_breadth.to_dict(orient='index')
    }


def get_index_summary(index_name, con):
    
    
    raw_prices = get_index_recent_prices(index_name=index_name, con=con, period=5)
    raw_breadth = get_index_breadth_data(index_name=index_name, con=con)

    daily_returns = get_daily_returns(raw_prices)
    total_returns = get_total_return(daily_returns)

    sector_performance = get_group_performance(total_returns,group='sector')
    sub_sector_performance = get_group_performance(total_returns,group='sub_sector')

    best_returns = get_top_gainers(total_returns)
    worst_returns = get_top_losers(total_returns)

    market_breadth = get_market_breadth(raw_breadth)

    index_summary = {
        'total_returns' : total_returns,
        'sector_performance' : sector_performance,
        'sub_sector_performance' : sub_sector_performance,
        'top_5_gainers' : best_returns,
        'top_5_losers' : worst_returns,
        'market_breadth' : market_breadth
    }

    return index_summary

def get_market_summary(index_names=None):
    con = get_connection()
    try:
        available_indexes = get_available_indexes()
        if not available_indexes:
            raise RuntimeError("No available indexes in database")

        if index_names is None:
            target_indexes = available_indexes
        else:
            if isinstance(index_names,str):
                index_names = [index_names]
            elif not isinstance(index_names,(list,tuple)):
                raise TypeError("Index name must be a string or a list")

            diff = set(index_names) - set(available_indexes)
            if diff:
                missing = ", ".join(diff)
                raise ValueError(f"Unrecognized indexes: {missing}")

        
        market_summary = {}
        for index in target_indexes:
            market_summary[index] = get_index_summary(index,con)
    finally:
        con.close()

    return market_summary

    
    