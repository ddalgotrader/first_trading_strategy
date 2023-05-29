import pandas as pd 
import numpy as np
import talib as ta


def sma(data, freq,window, plot_data={1:[('SMA',None, 'red')]}):
    
    df=data.copy()
    
    freq = f"{freq}min"
    df = df.resample(freq).agg({"Open": "first", "High": "max", "Low": "min", "Close": "last",  'spread':'mean','pips':'mean'}).dropna()
        
    df["returns"] = np.log(df['Close'] / df['Close'].shift(1))
    df['position']=np.nan
    df['SMA']=df['Close'].rolling(window=window).mean()
    first_cross_idx=df.index[0]
    df['Close_shifted']=df['Close'].shift(1)
    
    for i in range(len(df)):
        condition1_one_bar=((df['Open'].iloc[i]<df['SMA'].iloc[i]) & (df['Close'].iloc[i]>df['SMA'].iloc[i]))
        condition2_one_bar=((df['Open'].iloc[i]>df['SMA'].iloc[i]) & (df['Close'].iloc[i]<df['SMA'].iloc[i]))
        condition1_two_bars=((df['Close_shifted'].iloc[i]>df['SMA'].iloc[i]) & (df['Close'].iloc[i]<df['SMA'].iloc[i]))
        condition2_two_bars=((df['Close_shifted'].iloc[i]<df['SMA'].iloc[i]) & (df['Close'].iloc[i]>df['SMA'].iloc[i]))
        
           
        if condition1_one_bar or condition1_two_bars or condition2_one_bar or condition2_two_bars:
            
            first_cross_idx=df.index[i]
            break
            
    conditions=[
    (df['Close']>df['SMA']) & (df.index>=first_cross_idx),
    (df['Close']<df['SMA']) & (df.index>=first_cross_idx),
    ]
    values=[1,-1]
    df["position"] = np.select(conditions, values,0)
    
    
    
    df.dropna(inplace = True)
    
    return df


