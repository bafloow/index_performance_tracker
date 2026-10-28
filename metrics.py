from db import get_connection, get_available_indexes
import pandas as pd
import numpy as np


def calc_daily_gk(df_stock):

    log_hl = np.log(df_stock['high']/df_stock['low'])
    log_co = np.log(df_stock['close']/df_stock['open'])

    daily_gk = 0.5 * (log_hl ** 2) - (2 * np.log(2) - 1 ) * (log_co ** 2)
    
    return daily_gk


def get_index_company_data(index_name, con, period=5):
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
            AVG(close) OVER (PARTITION BY company_id ORDER BY date
            ROWS BETWEEN 199 PRECEDING AND CURRENT ROW) as sma_200,
            ROW_NUMBER() OVER(PARTITION BY company_id ORDER BY date DESC) AS rnk
            FROM daily_prices 
            )
            SELECT ci.symbol, s.name AS sector,
            rd.close, rd.sma_50, rd.sma_200
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
            df['sma_200'] = df['sma_200'].astype(float)

        return df

def get_relations(index_name, con):
    with con.cursor() as cur:
        cur.execute(
            """
            SELECT ci.symbol, s.name AS sector, ss.name AS sub_sector 
            FROM company_info ci
            LEFT JOIN sectors s ON ci.sector_id = s.id
            LEFT JOIN sub_sectors ss ON ci.sub_sector_id = ss.id
            JOIN index_components ic ON ci.id = ic.company_id 
            JOIN indexes i ON ic.index_id = i.id
            WHERE i.name = %s    
            """,(index_name,)
        )
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]

        df = pd.DataFrame(data=rows, columns=cols)
        return df    

def get_cash_index_data(index_name,period,con):
    with con.cursor() as cur:
        cur.execute(
            f"""
            WITH newest_dates as (
            SELECT DISTINCT date
            FROM index_prices
            ORDER BY date DESC
            LIMIT {period + 1}
            )
            SELECT i.symbol, ip.date, ip.close, ip.open, ip.high, ip.low 
            FROM index_prices ip
            JOIN indexes i ON i.id = ip.index_id
            JOIN newest_dates nd ON ip.date = nd.date
            WHERE i.name = %s
            ORDER BY i.symbol, ip.date
            """,(index_name,)
        )
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        
        df = pd.DataFrame(data=rows,columns=cols)

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['close'] = df['close'].astype(float)
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)

        return df

def get_daily_returns(df):
    df['daily_return'] = df.sort_values(by=['date'], ascending=True).groupby(['symbol'])['close'].pct_change()
    df['daily_gk'] = calc_daily_gk(df)
    df = df.sort_values(['symbol','date']).reset_index(drop=True) 
    return df

def get_companies_total_return(df_daily):

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

def get_cash_index_total_return(df_daily):

    df_copy = df_daily.sort_values('date')

    start_price = df_copy['close'].iloc[0]
    end_price = df_copy['close'].iloc[-1]

    total_return = (end_price - start_price)/start_price

    std_vol = np.sqrt(df_copy['daily_return'].var() * 252)
    gk_vol = np.sqrt(df_copy['daily_gk'].mean() * 252)

    df = pd.DataFrame([{
        'symbol':df_copy['symbol'].iloc[0],
        'total_return':total_return,
        'start_price':start_price,
        'end_price':end_price,
        'std_vol':std_vol,
        'gk_vol':gk_vol
    }])
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
    df_copy['above_sma200'] = df_copy['close'] > df_copy['sma_200']

    total_stocks = len(df_copy)
    above50_count = df_copy['above_sma50'].sum()
    pct_above50 = round((above50_count / total_stocks)*100,2)

    above200_count = df_copy['above_sma200'].sum()
    pct_above200 = round((above200_count / total_stocks)*100,2)

    index_breadth = {
        'total_stocks' : total_stocks,
        'above50' : above50_count,
        'above200':above200_count,
        'pct_above50' : pct_above50,
        'pct_above200': pct_above200
    }

    sector_breadth = df_copy.groupby('sector').agg(
        total_stocks=('symbol','count'),
        above50=('above_sma50','sum'),
        above200=('above_sma200','sum'),
        pct_above50=('above_sma50', lambda x: round(sum(x)/len(x) * 100,2)),
        pct_above200=('above_sma200', lambda x: round(sum(x)/len(x) * 100,2))
    )
    return {
        'index_breadth' : index_breadth,
        'sector_breadth' : sector_breadth.reset_index()
    }


def get_index_summary(index_name, con, period):
    
    relations = get_relations(index_name=index_name, con=con)
    raw_company_prices = get_index_company_data(index_name=index_name, con=con, period=period)
    raw_index_prices = get_cash_index_data(index_name=index_name,con=con, period=period)
    raw_breadth = get_index_breadth_data(index_name=index_name, con=con)

    company_daily_returns = get_daily_returns(raw_company_prices)
    company_performance = get_companies_total_return(company_daily_returns)

    index_daily_returns = get_daily_returns(raw_index_prices)
    index_performance= get_cash_index_total_return(index_daily_returns)

    sector_performance = get_group_performance(company_performance,group='sector')
    sub_sector_performance = get_group_performance(company_performance,group='sub_sector')
    top_gainers = get_top_gainers(company_performance)
    top_losers = get_top_losers(company_performance)
    breadth = get_market_breadth(raw_breadth)

    clean_company_perf = company_performance.drop(columns=['var','gk_var'])

    index_summary = {
        'index_performance' : index_performance,
        'company_performance' : clean_company_perf,
        'sector_performance' : sector_performance,
        'sub_sector_performance' : sub_sector_performance,
        'top_gainers' : top_gainers,
        'top_losers' : top_losers,
        'market_breadth' : breadth,
        'relations' : relations
    }

    return index_summary

def get_market_summary(index_names=None, period=5):
    con = get_connection()
    try:
        available_indexes = get_available_indexes()
        if not available_indexes:
            raise RuntimeError("No available indexes in database")

        if index_names is None:
            target_indexes = available_indexes
        else:
            if isinstance(index_names,str):
                target_indexes = [index_names.strip()]
            elif isinstance(index_names,(list,tuple)):
                target_indexes = [name.strip() for name in index_names]
                if not target_indexes:
                    raise ValueError("Index list cannot be empty")
            else:
                raise TypeError("Index name must be a string or a list")

            
            diff = set(target_indexes) - set(available_indexes)
            if diff:
                missing = ", ".join(diff)
                raise ValueError(f"Unrecognized indexes: {missing}")

        
        market_summary = {}
        for index in target_indexes:
            market_summary[index] = get_index_summary(index,con,period)
    finally:
        con.close()

    return market_summary
    