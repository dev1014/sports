# Sports Betting Analytics

## Overview
This project is a comprehensive sports betting analytics platform built with Streamlit. It provides detailed insights, performance metrics, and betting propositions for various sports. The platform includes features such as player comparison, expected value analysis, and advanced filtering options.

## Features
- **Dynamic Filtering**: Filter by teams, players, proposition types, odds, and more.
- **Detailed Performance Metrics**: View historical performance trends, including last 5/10 games and head-to-head matchups.
- **Sortable Tables**: Sort by different columns for quick insights.
- **Highlighted Insights**: Automatically highlights key trends and data points.
- **Proposition-Specific Data**: Focus on specific propositions for each player.
- **Save/Add Options**: Save specific propositions or bets for further analysis.
- **Live Prop Count**: Shows a live count of available propositions.
- **Advanced Betting Tools**: Includes EV+ (Expected Value Analysis), Boosts, Arbitrage, and Middle Bets.
- **Responsive Design**: Optimized layout for efficient data display.

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/sports-betting-analytics.git
    cd sports-betting-analytics
    ```

2. **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**
    Create a `.env` file in the root directory and add your API keys:
    ```env
    JWT_SECRET=your_jwt_secret
    PORT=5000
    THE_ODDS_API_KEY=your_odds_api_key
    OPENAI_API_KEY=your_openai_api_key
    ```

## Usage

1. **Run the Streamlit app:**
    ```bash
    streamlit run main.py
    ```

2. **Navigate to the app in your browser:**
    ```
    http://localhost:8501
    ```

## Project Structure

```
.
├── main.py                 # Main application file
├── utils.py                # Utility functions
├── team_data.py            # Functions to fetch team and player data
├── stats_utils.py          # Statistical analysis functions
├── data_utils.py           # Data fetching and processing functions
├── betting_analysis.py     # Betting analysis functions
├── auth_utils.py           # Authentication utility functions
├── requirements.txt        # Required Python packages
├── .env                    # Environment variables (not included in version control)
├── .gitignore              # Git ignore file
└── README.md               # Project documentation
```

## Contributing

1. **Fork the repository**
2. **Create a new branch:**
    ```bash
    git checkout -b feature/your-feature-name
    ```
3. **Make your changes and commit them:**
    ```bash
    git commit -m 'Add some feature'
    ```
4. **Push to the branch:**
    ```bash
    git push origin feature/your-feature-name
    ```
5. **Submit a pull request**

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/)
- [NBA API](https://github.com/swar/nba_api)
- [OpenAI](https://openai.com/)
- [The Odds API](https://the-odds-api.com/)
