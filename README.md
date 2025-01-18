# ByBit PnL Dashboard

A simple and convenient dashboard for tracking your Bybit trading PnL (Profit and Loss). This tool provides an easy way to visualize and monitor your trading performance on Bybit.

## Features

- Real-time PnL tracking
- Clean and intuitive interface
- Easy to set up and use
- SQLite for data caching and faster load times

## Requirements

- Python 3.8+
- ByBit API credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PNL-dashboard.git
cd PNL-dashboard
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your Bybit API credentials:
```
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret
```

## Usage

1. Start the Streamlit dashboard:
```bash
streamlit run app.py
```

2. Your default browser will automatically open with the dashboard. If it doesn't, the terminal will show you the local URL (typically `http://localhost:8501`)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is for informational purposes only. Always verify your actual PnL on the ByBit platform.