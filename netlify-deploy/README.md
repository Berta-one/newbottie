# Trading Reports Dashboard

A comprehensive web application for managing, visualizing, and generating trading reports. This dashboard provides real-time access to trading performance, ML analytics, backtesting results, and sentiment analysis.

## Features

### 🎯 Core Functionality
- **Report Viewing**: Browse and filter existing reports by type, date, and content
- **Report Generation**: Create new reports on-demand with customizable parameters
- **Data Visualization**: Interactive charts and graphs for all report types
- **Real-time Updates**: Auto-refresh functionality with live data integration
- **Responsive Design**: Works seamlessly on desktop and mobile devices

### 📊 Report Types
1. **Trading Performance**: Analyze trade history, win rates, profit/loss, and performance metrics
2. **ML Performance**: Monitor machine learning model accuracy, feature importance, and quantum metrics
3. **Backtesting Results**: Review strategy performance with detailed statistics and equity curves
4. **Sentiment Analysis**: Track market sentiment from multiple sources with correlation analysis
5. **Portfolio Overview**: Comprehensive portfolio analysis with position tracking and allocation

### 🔧 Key Features
- **Advanced Filtering**: Filter reports by time range, type, and search terms
- **Multiple Views**: Switch between grid and list views for optimal browsing
- **Detailed Analytics**: Drill down into report details with comprehensive data visualization
- **Export Capabilities**: Download reports in JSON and CSV formats
- **Mobile Responsive**: Optimized for all screen sizes

## Quick Start

### Netlify Deployment

1. **Fork/Clone the Repository**
   ```bash
   git clone <your-repo-url>
   cd <project-directory>
   ```

2. **Deploy to Netlify**
   - Connect your repository to Netlify
   - Set build directory to `netlify-deploy`
   - Deploy automatically triggers on push to main branch

3. **Access Your Dashboard**
   - Main dashboard: `https://your-site.netlify.app/`
   - Reports dashboard: `https://your-site.netlify.app/reports`

### Local Development

1. **Setup Environment**
   ```bash
   cd netlify-deploy
   python -m http.server 8080
   ```

2. **Open in Browser**
   ```
   http://localhost:8080/reports.html
   ```

## Usage Guide

### Viewing Reports

1. **Dashboard Overview**
   - View key statistics: total reports, recent reports, average win rate, total profit
   - Get quick insights into your trading performance

2. **Filter Reports**
   - **Time Filter**: All Time, Today, This Week, This Month, This Year
   - **Type Filter**: Trading, ML Performance, Backtesting, Sentiment Analysis
   - **Search**: Find reports by name or content

3. **View Modes**
   - **Grid View**: Card-based layout with visual summaries
   - **List View**: Compact table format for quick scanning

### Creating New Reports

1. **Click "New Report" Button**
2. **Select Report Type**:
   - Trading Performance
   - ML Performance Analysis
   - Backtesting Results
   - Sentiment Analysis
   - Portfolio Overview

3. **Choose Time Range**:
   - Last Hour
   - Last 24 Hours
   - Last 7 Days
   - Last 30 Days
   - Last 90 Days
   - Last Year

4. **Optional**: Provide custom report name
5. **Click "Generate Report"** - Processing takes 1-3 seconds

### Report Details

Click any report card to view:
- **Summary Statistics**: Key metrics and performance indicators
- **Data Visualization**: Interactive charts and graphs
- **Raw Data**: Detailed data tables and JSON exports
- **Historical Context**: Timestamps and metadata

## API Integration

The dashboard integrates with your trading API at `https://bottie-1.onrender.com/api/`:

### Endpoints Used
- `GET /trading/history` - Trading data
- `GET /ml/performance` - ML metrics
- `GET /backtest/results` - Backtesting data
- `GET /sentiment/analysis` - Sentiment data
- `GET /portfolio/overview` - Portfolio data

### Fallback Data
If API endpoints are unavailable, the dashboard generates realistic sample data for demonstration purposes.

## Backend Report Generation

### Python Service
The included `report_generator.py` provides a complete backend service:

```bash
# Generate reports via CLI
python report_generator.py --type trading --range 24h --name "Daily Trading Report"
python report_generator.py --type ml --range 7d
python report_generator.py --type backtest --range 30d
```

### Programmatic Usage
```python
from report_generator import ReportGenerator, ReportRequest

generator = ReportGenerator()
request = ReportRequest(
    report_type="trading",
    time_range="24h",
    name="Custom Report"
)

result = await generator.generate_report(request)
print(f"Generated: {result.title}")
```

## File Structure

```
netlify-deploy/
├── reports.html          # Main reports dashboard
├── reports.js            # Dashboard functionality
├── report_generator.py   # Backend report service
├── README.md            # This documentation
└── reports/             # Generated report files (auto-created)
```

## Configuration

### API Configuration
Edit `reports.js` to change the API endpoint:
```javascript
constructor() {
    this.apiUrl = 'https://your-api-endpoint.com/api';
    // ... rest of configuration
}
```

### Customization
- **Styling**: Modify the embedded CSS in `reports.html`
- **Report Types**: Add new types in both `reports.js` and `report_generator.py`
- **Time Ranges**: Customize available ranges in the filter dropdown
- **Chart Types**: Modify visualization logic in the `initializeDetailCharts` method

## Dependencies

### Frontend
- **Tailwind CSS**: Utility-first CSS framework
- **Font Awesome**: Icon library
- **Chart.js**: Data visualization library
- **Date-fns**: Date manipulation utilities

### Backend (Python)
- **pandas**: Data manipulation
- **numpy**: Numerical computing
- **requests**: HTTP client
- **pathlib**: File system paths

Install Python dependencies:
```bash
pip install pandas numpy requests
```

## Features in Detail

### Advanced Analytics
- **Performance Metrics**: Win rate, profit factor, Sharpe ratio, maximum drawdown
- **Risk Analysis**: Volatility, consecutive wins/losses, expectancy
- **Portfolio Metrics**: Diversification score, allocation analysis, P&L tracking
- **ML Metrics**: Accuracy, precision, recall, F1-score, Brier score, feature importance

### Data Export
- **JSON Format**: Complete data structure with metadata
- **CSV Format**: Tabular data for spreadsheet analysis
- **Chart Export**: Visual data representations

### Real-time Features
- **Auto-refresh**: Updates every 5 minutes
- **Live Statistics**: Real-time dashboard metrics
- **Status Tracking**: Report generation progress
- **Error Handling**: Graceful fallback for API failures

## Troubleshooting

### Common Issues

1. **Reports Not Loading**
   - Check API endpoint connectivity
   - Verify CORS headers are properly configured
   - Check browser console for JavaScript errors

2. **Charts Not Displaying**
   - Ensure Chart.js library is loaded
   - Check for data format issues in browser console
   - Verify canvas elements are properly created

3. **Report Generation Fails**
   - Check API endpoint availability
   - Verify request parameters are valid
   - Review backend logs for error details

### Debug Mode
Enable debug logging in `reports.js`:
```javascript
console.log('Debug info:', data);
```

## Security Considerations

- **CORS**: Properly configured for cross-origin requests
- **Input Validation**: All user inputs are sanitized
- **API Security**: Uses HTTPS endpoints with proper headers
- **XSS Protection**: Content Security Policy headers included

## Performance Optimization

- **Lazy Loading**: Charts initialized only when needed
- **Data Pagination**: Large datasets limited for frontend display
- **Caching**: Browser caching enabled for static assets
- **Compression**: Minified CSS and optimized images

## Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Review browser console for error messages
3. Verify API endpoint connectivity
4. Check Netlify deployment logs

## License

This project is part of the Bottie trading system. See main project license for details.