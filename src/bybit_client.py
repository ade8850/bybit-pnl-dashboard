from pybit.unified_trading import HTTP
import pandas as pd
from datetime import datetime, timedelta
from . import config

class BybitClient:
    def __init__(self):
        self.client = HTTP(
            api_key=config.BYBIT_API_KEY,
            api_secret=config.BYBIT_API_SECRET,
            testnet=config.BYBIT_TESTNET
        )

    def get_closed_pnl(self, category="linear", limit=100, cursor=None, start_time=None, end_time=None, symbol=None):
        """
        Recupera i PNL chiusi con i parametri specificati
        """
        params = {
            "category": category,
            "limit": limit
        }
        
        if cursor:
            params["cursor"] = cursor
        if start_time:
            params["startTime"] = int(start_time.timestamp() * 1000)
        if end_time:
            params["endTime"] = int(end_time.timestamp() * 1000)
        if symbol:
            params["symbol"] = symbol

        response = self.client.get_closed_pnl(**params)
        return response["result"]

    def get_all_closed_pnl(self, start_time=None, end_time=None, symbol=None):
        """
        Recupera tutti i PNL chiusi suddividendo il periodo in intervalli di 7 giorni
        """
        all_pnl = []
        
        # Se non sono specificate le date, usa gli ultimi 7 giorni
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=7)
        
        # Divide il periodo in intervalli di 7 giorni
        current_start = start_time
        while current_start < end_time:
            # Calcola la fine dell'intervallo corrente (max 7 giorni)
            current_end = min(current_start + timedelta(days=7), end_time)
            
            # Recupera i dati per questo intervallo con paginazione
            cursor = None
            while True:
                try:
                    result = self.get_closed_pnl(
                        cursor=cursor,
                        start_time=current_start,
                        end_time=current_end,
                        symbol=symbol
                    )
                    
                    if not result["list"]:
                        break
                        
                    all_pnl.extend(result["list"])
                    cursor = result.get("nextPageCursor")
                    
                    if not cursor:
                        break
                except Exception as e:
                    print(f"Errore nel recupero dei dati per il periodo {current_start} - {current_end}: {str(e)}")
                    break
            
            # Passa all'intervallo successivo
            current_start = current_end
                
        return all_pnl

    def get_pnl_dataframe(self, start_time=None, end_time=None, symbol=None):
        """
        Recupera i PNL come DataFrame pandas
        """
        pnl_data = self.get_all_closed_pnl(start_time, end_time, symbol)
        
        df = pd.DataFrame(pnl_data)
        if not df.empty:
            # Converti prima in numerico per evitare il warning
            df['createdTime'] = pd.to_numeric(df['createdTime'])
            df['updatedTime'] = pd.to_numeric(df['updatedTime'])
            
            # Poi converti in datetime
            df['createdTime'] = pd.to_datetime(df['createdTime'], unit='ms')
            df['updatedTime'] = pd.to_datetime(df['updatedTime'], unit='ms')
            
            # Converti le colonne numeriche
            numeric_columns = ['closedSize', 'cumEntryValue', 'avgEntryPrice', 
                             'avgExitPrice', 'closedPnl', 'fillCount']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
        return df

    def aggregate_pnl(self, df, timeframe='1d', symbol=None):
        """
        Aggrega i PNL per il timeframe specificato
        """
        if df.empty:
            return pd.DataFrame()
            
        # Imposta l'indice temporale
        df = df.set_index('updatedTime')
        
        # Filtra per symbol se specificato
        if symbol:
            df = df[df['symbol'] == symbol]
            
        # Definisci il periodo di resampling
        resample_map = {
            '1d': 'D',
            '1w': 'W',
            '1M': 'M'
        }
        
        period = resample_map.get(timeframe, 'D')
        
        # Aggrega i dati
        aggregated = df.resample(period).agg({
            'closedPnl': 'sum',
            'fillCount': 'sum',
            'symbol': 'count'
        }).rename(columns={'symbol': 'trades'})
        
        # Calcola statistiche aggiuntive
        aggregated['winRate'] = (df.resample(period)['closedPnl']
                                .apply(lambda x: (x > 0).mean() * 100))
        
        return aggregated.reset_index()