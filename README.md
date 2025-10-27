# Blinkit Grocery Sales Analytics

## Project Overview
This repository contains data analysis tools and scripts for the Blinkit grocery sales dashboard project. It includes utilities to analyze sales data, compute key metrics, and validate dashboard calculations.

## Data Sources
- `BlinkIT Grocery Data.xlsx`: Primary dataset containing grocery sales transactions
  - Features: Item details, outlet information, sales figures, ratings
  - 8,523 records spanning multiple outlet types and locations

## Dashboard Metrics

### Key Performance Indicators
- Total Sales: $1.20M
- Average Sales: $141
- Total Items: 8,523
- Average Rating: 3.9/5

### Analysis Dimensions
1. **Time Series Analysis**
   - Sales trends from 2012-2022
   - Peak year: 2018 ($205K)
   - Stable performance in recent years (~$131K)

2. **Product Analysis**
   - Top categories: Fruits/Vegetables and Snack Foods ($0.18M each)
   - Fat content distribution (Low Fat vs Regular)
   - 16 distinct product categories

3. **Outlet Performance**
   - Types: Grocery Store, Supermarket Type1/2/3
   - Locations: Tier 1/2/3 analysis
   - Size impact: High/Medium/Small outlet comparisons

## Python Scripts

### 1. compute_detailed_metrics.py
Comprehensive metrics calculator that:
- Reads Excel data and computes all dashboard metrics
- Handles currency formatting and aggregations
- Produces detailed JSON output and comparison reports

```bash
python compute_detailed_metrics.py "BlinkIT Grocery Data.xlsx" --out-dir outputs/
```

Key features:
- Robust column name detection
- Multiple aggregation levels
- Formatted currency outputs
- Dashboard metric validation

### 2. read_excel.py
Quick Excel file inspector that:
- Lists sheet names and structures
- Prints data previews
- Auto-installs required packages

```bash
python read_excel.py "BlinkIT Grocery Data.xlsx"
```

## Output Files
1. `outputs/detailed_metrics.json`: Complete metrics in JSON format
   - KPI calculations
   - Time series data
   - Category breakdowns
   - Outlet performance metrics

2. `outputs/outlet_type_table.csv`: Detailed outlet performance

## Requirements
- Python 3.8+
- Required packages:
  ```
  pandas
  numpy
  openpyxl
  ```

## Setup & Usage

1. Clone/download the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the detailed metrics computation:
   ```bash
   python compute_detailed_metrics.py "BlinkIT Grocery Data.xlsx" --out-dir outputs/
   ```

## Key Insights from Analysis

1. **Sales Distribution**
   - Supermarket Type1 dominates with $787.55K in sales
   - Regular products outperform Low Fat items
   - Tier 3 locations show strongest performance

2. **Product Performance**
   - Fresh produce and snacks lead sales
   - Health and hygiene products show growth potential
   - Seafood category has lowest sales ($0.01M)

3. **Outlet Patterns**
   - High correlation between outlet size and sales
   - Tier system effectively segments market
   - Consistent rating performance across outlet types

## Future Enhancements
1. Add trend analysis capabilities
2. Implement predictive sales modeling
3. Create Power BI direct connection
4. Add automated report generation
5. Include market basket analysis

## Contributing
Feel free to submit issues and enhancement requests.

## License
This project is licensed for internal use only. All data and analysis tools are proprietary to Blinkit.