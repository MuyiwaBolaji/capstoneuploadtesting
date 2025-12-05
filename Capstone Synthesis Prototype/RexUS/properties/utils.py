import pandas as pd
import json
import csv
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from datetime import datetime, timedelta


def detect_delimiter(file, num_lines=5):
    """
    Detect the delimiter of a CSV file by analyzing the first few lines.
    Returns the most likely delimiter.
    """
    file.seek(0)
    sample = []
    for _ in range(num_lines):
        line = file.readline()
        if isinstance(line, bytes):
            line = line.decode('utf-8', errors='ignore')
        if not line:
            break
        sample.append(line)

    file.seek(0)

    if not sample:
        return ','

    # Use Python's csv.Sniffer to detect delimiter
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(''.join(sample), delimiters=',;\t|')
        return dialect.delimiter
    except:
        # If Sniffer fails, count common delimiters and pick the most frequent
        delimiters = [',', ';', '\t', '|']
        delimiter_counts = {d: sum(line.count(d) for line in sample) for d in delimiters}
        return max(delimiter_counts, key=delimiter_counts.get)


def process_csv_file(file, user, data_file=None):
    try:
        # Detect the delimiter
        delimiter = detect_delimiter(file)

        # Read CSV with detected delimiter
        df = pd.read_csv(file, sep=delimiter, encoding='utf-8', on_bad_lines='skip')

        # Check if dataframe is valid
        if df.empty or len(df.columns) <= 1:
            # Try common delimiters if auto-detection failed
            file.seek(0)
            for sep in [',', ';', '\t', '|']:
                try:
                    df = pd.read_csv(file, sep=sep, encoding='utf-8', on_bad_lines='skip')
                    if not df.empty and len(df.columns) > 1:
                        break
                    file.seek(0)
                except:
                    file.seek(0)
                    continue

        return process_dataframe(df, data_file)
    except Exception as e:
        return None, str(e)


def process_excel_file(file, user, data_file=None):
    try:
        df = pd.read_excel(file)
        return process_dataframe(df, data_file)
    except Exception as e:
        return None, str(e)


def process_dataframe(df, data_file=None):
    try:
        if df.empty:
            return None, 'File is empty'

        df = df.fillna('')

        columns = df.columns.tolist()

        data = df.to_dict('records')
        for record in data:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = ''
                elif isinstance(value, (pd.Timestamp, pd.DatetimeTZDtype)):
                    record[key] = value.isoformat()
                elif not isinstance(value, (str, int, float, bool, type(None))):
                    record[key] = str(value)

        if data_file:
            data_file.columns = columns
            data_file.data = data
            data_file.record_count = len(data)
            data_file.save()

        return len(data), None
    except Exception as e:
        return None, str(e)


def forecast_timeseries(data, x_column, y_column, periods=5, method='linear'):
    """
    Forecast future values for a time series dataset.

    Args:
        data: List of dictionaries containing the dataset
        x_column: Column name for x-axis (time/date)
        y_column: Column name for y-axis (numeric values to forecast)
        periods: Number of periods to forecast ahead
        method: Forecasting method ('linear' or 'polynomial')

    Returns:
        Dictionary with original data and forecast
    """
    try:
        # Extract and clean data
        x_values = []
        y_values = []

        for row in data:
            x_val = row.get(x_column)
            y_val = row.get(y_column)

            # Skip empty values
            if x_val == '' or x_val is None or y_val == '' or y_val is None:
                continue

            try:
                y_values.append(float(y_val))
                x_values.append(x_val)
            except (ValueError, TypeError):
                continue

        if len(x_values) < 3:
            return {'error': 'Not enough data points for forecasting (minimum 3 required)'}

        # Convert x values to numeric indices
        X = np.arange(len(x_values)).reshape(-1, 1)
        y = np.array(y_values)

        # Prepare forecast X values
        future_X = np.arange(len(x_values), len(x_values) + periods).reshape(-1, 1)

        # Perform forecasting based on method
        if method == 'polynomial':
            # Polynomial regression (degree 2)
            poly = PolynomialFeatures(degree=2)
            X_poly = poly.fit_transform(X)
            future_X_poly = poly.transform(future_X)

            model = LinearRegression()
            model.fit(X_poly, y)

            predictions = model.predict(future_X_poly)
        else:
            # Linear regression (default)
            model = LinearRegression()
            model.fit(X, y)

            predictions = model.predict(future_X)

        # Generate future labels
        future_labels = []
        last_x_value = x_values[-1]

        # Try to detect if x_column is a date
        is_date = False
        try:
            if isinstance(last_x_value, str):
                # Try parsing as date
                if 'T' in last_x_value or '-' in last_x_value:
                    parsed_date = pd.to_datetime(last_x_value)
                    is_date = True

                    for i in range(1, periods + 1):
                        future_date = parsed_date + timedelta(days=i)
                        future_labels.append(future_date.strftime('%Y-%m-%d'))
        except:
            pass

        # If not a date, generate sequential labels
        if not is_date:
            try:
                last_numeric = float(last_x_value)
                for i in range(1, periods + 1):
                    future_labels.append(str(last_numeric + i))
            except:
                # Just use "Forecast 1", "Forecast 2", etc.
                for i in range(1, periods + 1):
                    future_labels.append(f'Forecast {i}')

        # Calculate confidence intervals (simple approach using residuals)
        if method == 'polynomial':
            poly = PolynomialFeatures(degree=2)
            X_poly = poly.fit_transform(X)
            fitted_values = model.predict(X_poly)
        else:
            fitted_values = model.predict(X)

        residuals = y - fitted_values
        std_error = np.std(residuals)

        # 95% confidence interval (approximately ±2 standard errors)
        lower_bound = predictions - (2 * std_error)
        upper_bound = predictions + (2 * std_error)

        return {
            'success': True,
            'original_labels': x_values,
            'original_values': y.tolist(),
            'forecast_labels': future_labels,
            'forecast_values': predictions.tolist(),
            'lower_bound': lower_bound.tolist(),
            'upper_bound': upper_bound.tolist(),
            'method': method
        }

    except Exception as e:
        return {'error': str(e)}
