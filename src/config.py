import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Configurazioni Bybit
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')
BYBIT_TESTNET = os.getenv('BYBIT_TESTNET', 'false').lower() == 'true'

# Configurazioni aggiuntive
DEFAULT_TIMEFRAME = '1d'  # Timeframe predefinito per le aggregazioni
SUPPORTED_TIMEFRAMES = ['1d', '1w', '1M']  # Timeframe supportati
DEFAULT_CATEGORY = 'linear'  # Categoria predefinita per i contratti