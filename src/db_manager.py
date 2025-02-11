import sqlite3
import pandas as pd
from pathlib import Path
from .logger import logger


class DBManager:
    def __init__(self, account="main"):
        """
        Inizializza il database manager per uno specifico account

        :param account: Nome dell'account (default: "main")
        """
        # Normalizza il nome dell'account per il filesystem
        self.account = account.lower().replace(" ", "_")

        # Crea la directory data se non esiste
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # Il path del database sarà data/account_trades.sqlite
        self.db_path = data_dir / f"{self.account}_trades.sqlite"
        self.conn = None
        self.connect()

    def connect(self):
        """Connette al database e crea la tabella se non esiste"""
        try:
            self.conn = sqlite3.connect(self.db_path)

            # Crea la tabella trades se non esiste
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    symbol TEXT,
                    side TEXT,
                    closedSize REAL,
                    cumEntryValue REAL,
                    avgEntryPrice REAL,
                    avgExitPrice REAL,
                    closedPnl REAL,
                    fillCount INTEGER,
                    createdTime TIMESTAMP,
                    updatedTime TIMESTAMP,
                    invested_capital REAL,
                    pct REAL,
                    trade_duration REAL
                )
            """)
            self.conn.commit()
            logger.info(f"Connected to SQLite database for account {self.account}")
        except Exception as e:
            logger.error(f"Error connecting to database for account {self.account}: {str(e)}")
            raise

    def save_trades(self, df):
        """Salva i trades nel database, sostituendo i dati esistenti"""
        try:
            # Cancella i dati esistenti
            self.conn.execute("DELETE FROM trades")

            # Prepara il DataFrame per il salvataggio
            df = df.copy()

            # Calcola la durata del trade in minuti se non presente
            if 'trade_duration' not in df.columns:
                df['trade_duration'] = (pd.to_datetime(df['updatedTime']) - pd.to_datetime(
                    df['createdTime'])).dt.total_seconds() / 60

            # Inserisce i nuovi dati
            df.to_sql('trades', self.conn, if_exists='replace', index=False)
            self.conn.commit()
            logger.info(f"Saved {len(df)} trades to database for account {self.account}")
        except Exception as e:
            logger.error(f"Error saving trades to database for account {self.account}: {str(e)}")
            raise

    def get_trades(self, start_time=None, end_time=None):
        """Recupera i trades dal database con filtri opzionali"""
        query = "SELECT * FROM trades"
        conditions = []
        params = []

        if start_time:
            conditions.append("updatedTime >= ?")
            params.append(start_time.strftime('%Y-%m-%d %H:%M:%S'))
        if end_time:
            conditions.append("updatedTime <= ?")
            params.append(end_time.strftime('%Y-%m-%d %H:%M:%S'))

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        try:
            df = pd.read_sql_query(query, self.conn, params=params)
            # Converti le colonne datetime usando il formato 'mixed' per maggiore robustezza
            df['createdTime'] = pd.to_datetime(df['createdTime'], format='mixed')
            df['updatedTime'] = pd.to_datetime(df['updatedTime'], format='mixed')
            return df
        except Exception as e:
            logger.error(f"Error retrieving trades for account {self.account}: {str(e)}")
            raise

    def close(self):
        """Chiude la connessione al database"""
        if self.conn:
            self.conn.close()
            logger.info(f"Closed database connection for account {self.account}")

    def __del__(self):
        """Assicura che la connessione venga chiusa quando l'oggetto viene distrutto"""
        self.close()