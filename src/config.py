import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# Dizionario per mappare gli account
BYBIT_SUBACCOUNTS = {}

# Controlla prima se esistono variabili per subaccount
env_vars = dict(os.environ)
api_keys = [k for k in env_vars if k.startswith('BYBIT_API_KEY_')]
accounts = [k.replace('BYBIT_API_KEY_', '') for k in api_keys]

# Se non ci sono subaccount configurati, usa il main account
if not accounts and os.getenv('BYBIT_API_KEY'):
    BYBIT_SUBACCOUNTS['Main'] = {
        'api_key': os.getenv('BYBIT_API_KEY'),
        'api_secret': os.getenv('BYBIT_API_SECRET')
    }
else:
    # Carica le configurazioni per ogni account rilevato
    for account in accounts:
        api_key = os.getenv(f'BYBIT_API_KEY_{account}')
        api_secret = os.getenv(f'BYBIT_API_SECRET_{account}')
        
        if api_key and api_secret:
            account_name = account.replace('_', ' ')  # Per una visualizzazione più pulita
            BYBIT_SUBACCOUNTS[account_name] = {
                'api_key': api_key,
                'api_secret': api_secret
            }

# Configurazioni aggiuntive
DEFAULT_TIMEFRAME = '1d'  # Timeframe predefinito per le aggregazioni
SUPPORTED_TIMEFRAMES = ['1d', '1w', '1M']  # Timeframe supportati
DEFAULT_CATEGORY = 'linear'  # Categoria predefinita per i contratti