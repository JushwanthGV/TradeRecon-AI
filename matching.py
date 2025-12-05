import pandas as pd
import numpy as np

def reconcile_trades(broker_df, exchange_df):
    """
    Reconcile trades between broker and exchange data.
    
    Args:
        broker_df: DataFrame with broker trades
        exchange_df: DataFrame with exchange trades
    
    Returns:
        Dictionary containing reconciliation results
    """
    
    # Validate required columns
    required_columns = ['trade_id', 'symbol', 'side', 'quantity', 'price', 'currency', 'trade_time', 'account_id']
    
    for col in required_columns:
        if col not in broker_df.columns:
            raise ValueError(f"Missing column '{col}' in broker trades")
        if col not in exchange_df.columns:
            raise ValueError(f"Missing column '{col}' in exchange trades")
    
    # Create copies to avoid modifying original dataframes
    broker = broker_df.copy()
    exchange = exchange_df.copy()
    
    # Convert trade_time to datetime for comparison
    broker['trade_time'] = pd.to_datetime(broker['trade_time'])
    exchange['trade_time'] = pd.to_datetime(exchange['trade_time'])
    
    # Merge on trade_id
    merged = pd.merge(
        broker,
        exchange,
        on='trade_id',
        how='outer',
        suffixes=('_broker', '_exchange'),
        indicator=True
    )
    
    # Initialize results
    results = {
        'total_trades': len(merged),
        'matched_count': 0,
        'mismatch_count': 0,
        'missing_count': 0,
        'exceptions': []
    }
    
    exceptions_list = []
    
    for idx, row in merged.iterrows():
        trade_id = row['trade_id']
        
        # Case 1: Trade only in broker (missing in exchange)
        if row['_merge'] == 'left_only':
            results['missing_count'] += 1
            exceptions_list.append({
                'trade_id': trade_id,
                'exception_type': 'missing_in_exchange',
                'mismatched_fields': 'N/A',
                'broker_values': f"symbol={row['symbol_broker']}, quantity={row['quantity_broker']}, price={row['price_broker']}",
                'exchange_values': 'NOT FOUND',
                'severity': 'High'
            })
        
        # Case 2: Trade only in exchange (missing in broker)
        elif row['_merge'] == 'right_only':
            results['missing_count'] += 1
            exceptions_list.append({
                'trade_id': trade_id,
                'exception_type': 'missing_in_broker',
                'mismatched_fields': 'N/A',
                'broker_values': 'NOT FOUND',
                'exchange_values': f"symbol={row['symbol_exchange']}, quantity={row['quantity_exchange']}, price={row['price_exchange']}",
                'severity': 'High'
            })
        
        # Case 3: Trade in both - check for mismatches
        else:
            mismatches = []
            broker_vals = []
            exchange_vals = []
            
            # Check each field for mismatches
            fields_to_check = ['symbol', 'side', 'quantity', 'price', 'currency', 'account_id']
            
            for field in fields_to_check:
                broker_val = row[f'{field}_broker']
                exchange_val = row[f'{field}_exchange']
                
                # Handle NaN comparisons
                if pd.isna(broker_val) and pd.isna(exchange_val):
                    continue
                
                # Compare values (with tolerance for float comparisons)
                if field == 'price' or field == 'quantity':
                    if abs(float(broker_val) - float(exchange_val)) > 0.01:
                        mismatches.append(field)
                        broker_vals.append(f"{field}={broker_val}")
                        exchange_vals.append(f"{field}={exchange_val}")
                else:
                    if str(broker_val) != str(exchange_val):
                        mismatches.append(field)
                        broker_vals.append(f"{field}={broker_val}")
                        exchange_vals.append(f"{field}={exchange_val}")
            
            # Check trade_time (allow 1 second tolerance)
            time_diff = abs((row['trade_time_broker'] - row['trade_time_exchange']).total_seconds())
            if time_diff > 1:
                mismatches.append('trade_time')
                broker_vals.append(f"trade_time={row['trade_time_broker']}")
                exchange_vals.append(f"trade_time={row['trade_time_exchange']}")
            
            # Determine severity based on mismatches
            severity = 'Low'
            if 'quantity' in mismatches or 'price' in mismatches:
                severity = 'High'
            elif 'side' in mismatches or 'symbol' in mismatches:
                severity = 'High'
            elif len(mismatches) > 2:
                severity = 'Medium'
            
            if mismatches:
                results['mismatch_count'] += 1
                exceptions_list.append({
                    'trade_id': trade_id,
                    'exception_type': 'mismatch',
                    'mismatched_fields': ', '.join(mismatches),
                    'broker_values': ' | '.join(broker_vals),
                    'exchange_values': ' | '.join(exchange_vals),
                    'severity': severity
                })
            else:
                results['matched_count'] += 1
    
    # Convert exceptions to DataFrame
    if exceptions_list:
        results['exceptions'] = pd.DataFrame(exceptions_list)
    else:
        results['exceptions'] = pd.DataFrame(columns=[
            'trade_id', 'exception_type', 'mismatched_fields', 
            'broker_values', 'exchange_values', 'severity'
        ])
    
    return results


def generate_summary_statistics(results):
    """
    Generate summary statistics from reconciliation results.
    
    Args:
        results: Dictionary from reconcile_trades()
    
    Returns:
        Dictionary with summary stats
    """
    total = results['total_trades']
    matched = results['matched_count']
    mismatched = results['mismatch_count']
    missing = results['missing_count']
    
    match_rate = (matched / total * 100) if total > 0 else 0
    exception_rate = ((mismatched + missing) / total * 100) if total > 0 else 0
    
    summary = {
        'total_trades': total,
        'matched_trades': matched,
        'match_rate_pct': round(match_rate, 2),
        'total_exceptions': mismatched + missing,
        'exception_rate_pct': round(exception_rate, 2),
        'mismatches': mismatched,
        'missing_trades': missing
    }
    
    return summary


def get_high_priority_exceptions(exceptions_df):
    """
    Filter exceptions to show only high-priority items.
    
    Args:
        exceptions_df: DataFrame of exceptions
    
    Returns:
        Filtered DataFrame with high-priority exceptions
    """
    if len(exceptions_df) == 0:
        return exceptions_df
    
    high_priority = exceptions_df[
        (exceptions_df['severity'] == 'High') |
        (exceptions_df['exception_type'].str.contains('missing'))
    ]
    
    return high_priority


def export_exceptions_to_csv(exceptions_df, filename='exceptions_export.csv'):
    """
    Export exceptions to CSV file.
    
    Args:
        exceptions_df: DataFrame of exceptions
        filename: Output filename
    
    Returns:
        Path to exported file
    """
    exceptions_df.to_csv(filename, index=False)
    return filename