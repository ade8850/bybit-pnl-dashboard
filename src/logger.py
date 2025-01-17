import logging
import sys
from pathlib import Path

def setup_logger():
    # Crea la directory logs se non esiste
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configura il logger
    logger = logging.getLogger("pnl_dashboard")
    logger.setLevel(logging.DEBUG)
    
    # Handler per il file
    fh = logging.FileHandler("logs/app.log")
    fh.setLevel(logging.DEBUG)
    
    # Handler per la console
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    
    # Formattazione
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # Aggiungi gli handler al logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_logger()