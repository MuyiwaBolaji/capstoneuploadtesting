# RexUS - Real Estate eXploration and Unified Synthesis

A web application that helps you understand your data through interactive visualizations and forecasting.

## Description

RexUS is a comprehensive data analysis platform designed to make data exploration simple and intuitive. Whether you're analyzing sales trends, property values, or any structured dataset, RexUS provides powerful tools to help you discover insights.

### Key Features

**Data Upload & Management**
- Upload CSV and Excel files up to 5MB
- Automatic delimiter detection for CSV files
- Support for multiple file formats (.csv, .xlsx, .xls)
- Secure file storage with user-specific access

**Data Cleaning**
- Remove entire columns you don't need
- Clean null records from specific columns
- Bulk remove all records containing any null values
- Real-time statistics showing null counts and percentages

**Interactive Visualizations**
- Bar charts for comparing categories
- Line charts for tracking changes
- Time series charts for temporal data
- Pie and doughnut charts for proportions
- Support for multiple data series on single chart
- Automatic date formatting for cleaner displays

**Forecasting**
- Predict future values based on historical trends
- Linear forecasting for steady growth patterns
- Polynomial forecasting for curved trends
- Adjustable forecast periods (1-20 steps ahead)
- 95% confidence intervals to show prediction uncertainty
- Visual forecast overlay on existing data

**Statistical Analysis**
- Automatic data type detection (numeric vs text)
- Min, max, and mean calculations for numeric columns
- Null value counts and percentages
- Column-by-column breakdown
- Dataset overview with total records and file size

Originally built for real estate data analysis, RexUS works with any structured data in CSV or Excel format.

## Requirements

- Docker and Docker Compose
- Web browser (Chrome, Firefox, Safari, or Edge)

That's it! Docker handles all the dependencies including:
- Python 3.12
- PostgreSQL database
- Required Python packages
- Web server configuration

## Setup

**1. Get the code**

Download or clone this repository to your computer:

`https://github.com/MuyiwaBolaji/CIDM-6395-70-CAPSTONE.git`

Or download the ZIP file and extract it.

**2. Run the application**

Start the application with Docker:

```bash
docker compose up --build
```

Wait for the containers to start (first time takes a few minutes).

**3. Access the application**

Open your browser and visit: `http://localhost:8000`

**4. Stop the application**

Press `Ctrl+C` in the terminal, then run:

```bash
docker compose down
```

## Sample Data

Test the application with real estate data: https://catalog.data.gov/dataset/property-sale-history

## Usage

1. Create an account and login
2. Upload your CSV or Excel file
3. Process the file to analyze your data
4. View statistics and create visualizations
5. Use forecasting to predict future trends
6. Clean your data by removing columns or null records
