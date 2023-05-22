import pandas as pd
import numpy as np
import inspect
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from DataCollectorXtb import DataCollectorXtb as dcxtb
from Strategies import *

class StrategyTesterXTB():
    
    def __init__(self,symbol, data, strategy_func=None):
        
        #Define function arguments
        self.symbol=symbol
        self.strategy_func=strategy_func
        self.results=None
        self.df_to_plot=None
        self.data=data
        
        #Extract arguments from strategy
        self.strategy_name=strategy_func.__name__
        self.func_args=[x for x in inspect.getfullargspec(self.strategy_func)[0] if x not in ['data','plot_data']]
        self.plot_data=inspect.getfullargspec(self.strategy_func)[3][-1]
        
        
    def __repr__(self):
        return f"{self.strategy_name.upper} backtester(symbol = {self.symbol}, start = {self.start}, end = {self.end})"
    
    
 
    def test_strategy(self, **kwargs):
        
        
        #Check if arguments of strategy are defined correctly
        check_attr_error=False
        for i in range(len(self.func_args)):
            if self.func_args[i] not in kwargs.keys():
                print(f'Define  correct parameters {self.func_args} for {self.strategy_func.__name__} strategy range before test strategy')
                check_attr_error=True
            
        if check_attr_error==False:
            attrs_to_test=[]
            
            for attr in self.func_args:
                if attr=='freq':
                    setattr(self,attr,f'{kwargs[attr]}min')
                else:
                    setattr(self,attr,kwargs[attr])
            
            self.results=self.strategy_func(self.data, **kwargs) 
            self.df_to_plot=self.results.copy()
            self.run_strategy()
            data = self.results.copy()
            data["creturns"] = data["returns"].cumsum().apply(np.exp)
            data["cstrategy"] = data["strategy"].cumsum().apply(np.exp)
            self.results = data
            print(f'Buy and hold strategy - {data.creturns.iloc[-1]}')
            print(f'{self.strategy_func.__name__.upper()} strategy - {data.cstrategy.iloc[-1]}')
            
    def run_strategy(self):
        ''' Runs the strategy backtest.
        '''
        data = self.results.copy()
        data["strategy"] = data["position"].shift(1) * data["returns"]
        data["trades"] = data.position.diff().fillna(0).abs()
        data.strategy = data.strategy - data.trades * (data.spread/2)
        self.results = data
       
            
        
    
    def plot_results(self):
        ''' Plots the performance of the trading strategy and compares to "buy and hold".
        '''
        if self.results is None:
            print("Test strategy before plot results")
       
        else:
            df_plot=self.results.copy()
            title=f'{self.symbol}'
            for attr in self.func_args:
                title=title+f'| {attr} = {getattr(self, attr)}'
            title=title
            
            figure=make_subplots(rows=1, cols=1)
            figure.add_trace(go.Scatter(x=df_plot.index, y=df_plot['creturns'], mode='lines', name='buy and hold'), col=1, row=1)
            figure.add_trace(go.Scatter(x=df_plot.index, y=df_plot['cstrategy'], mode='lines', name=f'{self.strategy_name} strategy'), col=1, row=1)
            
            figure.update_layout(title=title, xaxis_rangeslider_visible=False)  
            figure.update_xaxes(rangebreaks=[dict(bounds=['sat', 'mon'])])
            figure.show()
    def plot_trades(self):
        
        
        title=f'{self.symbol}'
        for attr in self.func_args:
            title=title+f'| {attr} = {getattr(self, attr)}'
        title=title
        
        df_plot=self.df_to_plot.dropna().copy()
        self.buy_signal_index=[]
        self.sell_signal_index=[]
        self.neutral_signal_index=[]
        
        for i in range(len(df_plot)):
            if i==0:
                if df_plot['position'].iloc[1]==1:
                    if (df_plot['position'].iloc[i]==-1 or df_plot['position'].iloc[i]==0):
                        self.buy_signal_index.append(df_plot.index[1])
                if df_plot['position'].iloc[1]==-1:
                    if (df_plot['position'].iloc[i]==1 or df_plot['position'].iloc[i]==0):
                        self.buy_signal_index.append(df_plot.index[1])
            else:
                if df_plot['position'].iloc[i-1]==1:
                    if df_plot['position'].iloc[i]==-1:
                        self.sell_signal_index.append(df_plot.index[i])
                    if df_plot['position'].iloc[i]==0:
                        self.neutral_signal_index.append(df_plot.index[i])
                if df_plot['position'].iloc[i-1]==-1:
                    if df_plot['position'].iloc[i]==1:
                        self.buy_signal_index.append(df_plot.index[i])
                    if df_plot['position'].iloc[i]==0:
                        self.neutral_signal_index.append(df_plot.index[i])
                if df_plot['position'].iloc[i-1]==0:
                    if df_plot['position'].iloc[i]==1:
                        self.buy_signal_index.append(df_plot.index[i])
                    if df_plot['position'].iloc[i]==-1:
                        self.sell_signal_index.append(df_plot.index[i])
                
        self.buy_y=[df_plot['Low'].loc[idx]*0.9998 for idx in self.buy_signal_index]
        self.sell_y= [df_plot['High'].loc[idx]*1.0002 for idx in self.sell_signal_index] 
        
        row_heights=[1.0]
        figure_height=600
        rows=max(self.plot_data.keys())
        
        if rows==2:
            figure_height=800
            row_heights=[0.7,0.3]
        if rows==3:
            figure_height=1000
            row_heights=[0.6,0.2,0.2]
            
        figure=make_subplots(rows=rows, cols=1, row_heights=row_heights)
        figure.update_layout(height=figure_height)
        figure.add_trace(go.Candlestick(x=df_plot.index,
                open=df_plot['Open'],
                high=df_plot['High'],
                low=df_plot['Low'],
                close=df_plot['Close'],
                name='price'), row=1, col=1)
        figure.append_trace(go.Scatter(x=self.buy_signal_index, y=self.buy_y, mode='markers', marker_symbol='arrow-up', marker_color='green', name='buy', marker_size=10), col=1, row=1)
        figure.append_trace(go.Scatter(x=self.sell_signal_index, y=self.sell_y, mode='markers', marker_symbol='arrow-down', marker_color='red', name='sell', marker_size=10), col=1, row=1)
        
        for k in self.plot_data.keys():
            for v in self.plot_data[k]:
                figure.add_trace(go.Scatter(x=df_plot.index, 
                                               y=df_plot[v[0]],
                                               mode='lines',
                                               name=v[0]), row=k, col=1)
                if v[1]!=None:
                    figure.add_hline(y=getattr(self,v[1]), row=k, col=1)
               
        figure.update_layout(title=title, xaxis_rangeslider_visible=False)
        figure.update_xaxes(rangebreaks=[dict(bounds=['sat', 'mon'])])
        figure.show()
        
        

   