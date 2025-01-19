from pybit.unified_trading import HTTP
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from . import config
from .logger import logger

class BybitClient:
    def __init__(self, account_name='Main'):
        """
        Inizializza il client Bybit con le credenziali dell'account specificato
        
        :param account_name: Nome dell'account da utilizzare (default: 'Main')
        """
        if account_name not in config.BYBIT_SUBACCOUNTS:
            raise ValueError(f"Account '{account_name}' non trovato nella configurazione")
            
        account = config.BYBIT_SUBACCOUNTS[account_name]
        self.account_name = account_name
        self.client = HTTP(
            api_key=account['api_key'],
            api_secret=account['api_secret'],
            testnet=False
        )

    @classmethod
    def get_available_accounts(cls):
        """Restituisce la lista degli account configurati"""
        return list(config.BYBIT_SUBACCOUNTS.keys())

    def _get_date_intervals(self, start_time, end_time, days=6):
        """
        Genera intervalli di N giorni tra start_time e end_time.
        Gli intervalli sono ridotti di un giorno rispetto alla richiesta per assicurare
        che non superino mai il limite quando convertiti in timestamp.
        
        :param start_time: Data di inizio
        :param end_time: Data di fine
        :param days: Numero di giorni per intervallo (default: 6 per avere intervalli sicuri di 7 giorni)
        """
        # Normalizza le date all'inizio della giornata
        start_date = datetime(start_time.year, start_time.month, start_time.day)
        end_date = datetime(end_time.year, end_time.month, end_time.day)
        
        # Assicurati che la data finale sia inclusa aggiungendo un giorno
        end_date = end_date + timedelta(days=1)
        
        intervals = []
        current = start_date
        
        while current < end_date:
            # Calcola la fine dell'intervallo, ma non superare la data finale
            next_date = min(current + timedelta(days=days), end_date)
            intervals.append((current, next_date))
            # Il prossimo intervallo inizia dalla fine dell'intervallo precedente
            current = next_date
            
        return intervals

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
        Recupera tutti i PNL chiusi dal periodo specificato. 
        Se non viene specificato un periodo, cerca di recuperare l'ultimo anno di dati.
        """
        all_pnl = []
        
        # Se non sono specificate le date, prova a recuperare l'ultimo anno
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(days=365)
            
        logger.info(f"Starting data retrieval for account {self.account_name}, from {start_time} to {end_time}")
        
        # Ottieni gli intervalli di 6 giorni (che diventano 7 quando convertiti in timestamp)
        date_intervals = self._get_date_intervals(start_time, end_time, days=6)
        error_count = 0
        max_errors = 3
        
        # Tieni traccia degli intervalli tentati
        tried_intervals = set()
        
        for interval_start, interval_end in date_intervals:
            interval_key = f"{interval_start}-{interval_end}"
            
            # Salta gli intervalli già tentati
            if interval_key in tried_intervals:
                continue
                
            tried_intervals.add(interval_key)
            
            if error_count >= max_errors:
                logger.error(f"Too many consecutive errors ({max_errors}), stopping data retrieval")
                break
                
            try:
                logger.info(f"Fetching data for account {self.account_name} from {interval_start} to {interval_end}")
                
                # Recupera i dati per questo intervallo con paginazione
                cursor = None
                while True:
                    result = self.get_closed_pnl(
                        cursor=cursor,
                        start_time=interval_start,
                        end_time=interval_end,
                        symbol=symbol
                    )
                    
                    if not result["list"]:
                        break
                        
                    trades_count = len(result["list"])
                    all_pnl.extend(result["list"])
                    logger.info(f"Retrieved {trades_count} trades for account {self.account_name}")
                    
                    cursor = result.get("nextPageCursor")
                    if not cursor:
                        break
                        
                # Reset error counter on successful request
                error_count = 0
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error retrieving data for account {self.account_name}, period {interval_start} - {interval_end}: {str(e)}")
                
        logger.info(f"Total trades retrieved for account {self.account_name}: {len(all_pnl)}")
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
            
            # Correggiamo il side: Sell -> Buy, Buy -> Sell
            df['side'] = np.where(df['side'] == 'Sell', 'Buy', 'Sell')
            
            # Calcola il capitale investito
            df['invested_capital'] = df['closedSize'] * df['avgEntryPrice']
            
            # Calcola la percentuale di guadagno/perdita sul capitale investito
            df['pct'] = (df['closedPnl'] / df['invested_capital'] * 100).round(2)
            
            logger.info(f"Created DataFrame with {len(df)} trades for account {self.account_name}")
                    
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
        
        # Funzione per calcolare la media ponderata del PNL
        def weighted_pnl_pct(group):
            total_invested = (group['closedSize'] * group['avgEntryPrice']).sum()
            if total_invested == 0:
                return 0
            weighted_pct = (group['closedPnl'].sum() / total_invested * 100)
            return weighted_pct
            
        # Calcola durate
        df['duration'] = (df.index - df['createdTime']).dt.total_seconds() / 60

        # Funzioni di aggregazione per le durate
        def total_duration(durations):
            return durations.sum()
            
        def avg_duration(durations):
            return durations.mean()
        
        # Aggrega i dati
        aggregated = df.resample(period).agg({
            'closedPnl': 'sum',
            'fillCount': 'sum',
            'symbol': 'count',  # numero di trades
            'duration': [total_duration, avg_duration]  # durate totali e medie
        })
        
        # Appiattisci i livelli delle colonne
        aggregated.columns = ['closedPnl', 'fillCount', 'trades', 'duration_total', 'duration_avg']
        
        # Calcola statistiche aggiuntive
        aggregated['winRate'] = (df.resample(period)['closedPnl']
                                .apply(lambda x: (x > 0).mean() * 100))
                                
        # Calcola la percentuale sul capitale totale investito nel periodo
        aggregated['pct'] = (df.resample(period)
                             .apply(weighted_pnl_pct))
        aggregated['pct'] = aggregated['pct'].round(2)
        
        return aggregated.reset_index()