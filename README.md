# ByBit PnL Dashboard

A simple and convenient dashboard for tracking your Bybit trading PnL (Profit and Loss). This tool provides an easy way to visualize and monitor your trading performance on Bybit.

## Features

- Real-time PnL tracking
- Clean and intuitive interface
- Multiple account support
- Local data caching for faster load times
- Detailed performance metrics and charts

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

4. Create a `.env` file with your Bybit API credentials. You can configure one main account:
```
BYBIT_API_KEY=your_api_key
BYBIT_API_SECRET=your_api_secret
```

Or multiple accounts using the suffix pattern:
```
# Main account
BYBIT_API_KEY_MAIN=your_main_api_key
BYBIT_API_SECRET_MAIN=your_main_api_secret

# Additional accounts
BYBIT_API_KEY_ACCOUNT2=your_second_api_key
BYBIT_API_SECRET_ACCOUNT2=your_second_api_secret

BYBIT_API_KEY_ACCOUNT3=your_third_api_key
BYBIT_API_SECRET_ACCOUNT3=your_third_api_secret
```

Each account configuration will be automatically detected and made available in the dashboard.

## Usage

1. Start the Streamlit dashboard:
```bash
streamlit run app.py
```

2. Your default browser will automatically open with the dashboard. If it doesn't, the terminal will show you the local URL (typically `http://localhost:8501`)

3. Use the account selector in the sidebar to switch between different Bybit accounts

### Data Management

- Initial data load: When selecting an account for the first time, the dashboard automatically loads the last year of trading data
- Weekly refresh: Use the "Refresh Week" button to update the last 7 days of data
- Full reload: Use the "Load Year" button to reload an entire year of trading data

Each account maintains its own separate cache of trading data.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is for informational purposes only. Always verify your actual PnL on the ByBit platform.