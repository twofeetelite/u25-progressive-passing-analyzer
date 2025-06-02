# 🎯 U-25 Progressive Passing Analyzer

A Streamlit web application for analyzing young midfielders (under 25) by progressive passing distance across Europe's top 5 leagues.

## Features

- 📊 Analyze U-25 midfielders with primary position "MF"
- 🌍 Support for Big 5 Combined dataset or individual league uploads
- 📈 Sort players by Progressive Distance (PrgDist) 
- 🎛️ Customizable filters (age, minutes played)
- 📁 Multi-league comparison and analysis
- 📥 Export results to CSV

## How to Use

1. **Upload Data**: Use either Big 5 Combined CSV or individual league CSVs from FBRef
2. **Set Filters**: Adjust minimum 90s played and maximum age in sidebar
3. **Analyze**: View top performers, league comparisons, and detailed statistics
4. **Export**: Download results for further analysis

## Data Source

Progressive passing data from [FBRef.com](https://fbref.com) - Europe's top 5 leagues:
- Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿
- La Liga 🇪🇸  
- Bundesliga 🇩🇪
- Serie A 🇮🇹
- Ligue 1 🇫🇷

## Installation

```bash
git clone https://github.com/yourusername/u25-progressive-passing-analyzer.git
cd u25-progressive-passing-analyzer
pip install -r requirements.txt
streamlit run app.py
```

## Live Demo

[View the app live here](https://your-app-url.streamlit.app)

---
*Built with Streamlit • Data from FBRef*