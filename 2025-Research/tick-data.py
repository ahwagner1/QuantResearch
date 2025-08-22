import argparse
import os
import numpy as np
import polars as pl
import matplotlib.pyplot as plt
from datetime import datetime, timezone


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="Input file path")
    parser.add_argument(
        "-s", "--skip", type=int, default=0, help="Number of records to skip"
    )
    parser.add_argument(
        "-n", "--num", type=int, default=None, help="Max number of records to read"
    )
    parser.add_argument(
        "--plot", action="store_true", help="Generate price plots"
    )
    parser.add_argument(
        "--epoch", default="1899-12-30", 
        help="Custom epoch date (YYYY-MM-DD). Default: 1899-12-30 for financial data"
    )
    parser.add_argument(
        "--show-epochs", action="store_true", 
        help="Show common epoch offsets and exit"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.show_epochs and not args.input:
        parser.error("--input is required unless using --show-epochs")
    
    return args


def calculate_epoch_offset_microseconds(custom_epoch_date):
    """
    Calculate the offset in microseconds between a custom epoch and Unix epoch (1970-01-01)
    
    Common financial data epochs:
    - 1899-12-30: Microsoft Excel/OLE Automation date system (25,567 days before Unix epoch)
    - 1900-01-01: Some financial systems
    - 1980-01-06: GPS epoch
    - 2000-01-01: Y2K epoch
    
    Args:
        custom_epoch_date: Date string in format "YYYY-MM-DD"
    
    Returns:
        Offset in microseconds to convert from custom epoch to Unix epoch
    """
    # Parse the custom epoch date
    custom_epoch = datetime.strptime(custom_epoch_date, "%Y-%m-%d")
    custom_epoch = custom_epoch.replace(tzinfo=timezone.utc)
    
    # Unix epoch
    unix_epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    
    # Calculate difference
    diff = unix_epoch - custom_epoch
    
    # Convert to microseconds
    offset_microseconds = int(diff.total_seconds() * 1_000_000)
    
    return offset_microseconds


def show_common_epochs():
    """Display common epoch offsets for reference"""
    epochs = {
        "1899-12-30": "Excel/OLE Automation (financial data)",
        "1900-01-01": "Some financial systems", 
        "1980-01-06": "GPS epoch",
        "2000-01-01": "Y2K epoch"
    }
    
    print("Common epoch offsets from Unix epoch (1970-01-01):")
    for epoch_date, description in epochs.items():
        offset = calculate_epoch_offset_microseconds(epoch_date)
        days = offset / 1e6 / 86400
        print(f"  {epoch_date}: {offset:,} microseconds ({days:.0f} days) - {description}")
    print()


def get_file_specs(file_path):
    """Get header size, record size, and dtype based on file extension"""
    if file_path.endswith(".scid"):
        header_size = 56
        record_size = 40
        dtypes = np.dtype([
            ("time", "<u8"),
            ("open", "<f4"),
            ("high", "<f4"),
            ("low", "<f4"),
            ("close", "<f4"),
            ("numTrades", "<u4"),
            ("totalVol", "<u4"),
            ("bidVol", "<u4"),
            ("askVol", "<u4"),
        ])
    elif file_path.endswith(".depth"):
        header_size = 64
        record_size = 24
        dtypes = np.dtype([
            ("time", "<u8"),
            ("command", "<u1"),
            ("flags", "<u1"),
            ("numOrders", "<u2"),
            ("price", "<f4"),
            ("quantity", "<u4"),
            ("unused", "<u4"),
        ])
    else:
        raise ValueError(
            f"Unsupported file type for {file_path}. Must be .scid or .depth file"
        )
    
    return header_size, record_size, dtypes


def calc_offset(file_path, records_to_skip):
    """Calculate byte offset from start of file"""
    size = os.path.getsize(file_path)
    header_size, record_size, _ = get_file_specs(file_path)
    
    if size < header_size:
        raise ValueError("File too small to contain header")

    num_records = (size - header_size) // record_size

    if records_to_skip > num_records:
        raise ValueError(
            f"Cannot skip {records_to_skip} records, file only has {num_records} records"
        )

    return header_size + (records_to_skip * record_size)


def read_tick_data(file_path, records_to_skip=0, max_records=None):
    """Read tick data from binary file and return numpy array"""
    _, _, dtypes = get_file_specs(file_path)
    bytes_offset = calc_offset(file_path, records_to_skip)
    
    if max_records:
        data = np.fromfile(file_path, dtype=dtypes, offset=bytes_offset, count=max_records)
    else:
        data = np.fromfile(file_path, dtype=dtypes, offset=bytes_offset)
    
    return data


def process_timestamps(timestamp_col, epoch_offset_us=0):
    """
    Process SC datetime format where last 3 digits are trade counter
    
    Args:
        timestamp_col: Raw timestamp column from data
        epoch_offset_us: Offset in microseconds to convert to Unix epoch
    
    Returns:
        tuple of (unix_timestamp_us, trade_counter)
    """
    # More efficient than string operations: use integer arithmetic
    actual_timestamp_us = timestamp_col // 1000  # Remove last 3 digits (trade counter)
    trade_counter = timestamp_col % 1000         # Get last 3 digits
    
    # Convert to Unix epoch by adding the offset
    unix_timestamp_us = actual_timestamp_us + epoch_offset_us
    
    return unix_timestamp_us, trade_counter


def numpy_to_polars(data, file_type, epoch_offset_us=0):
    """
    Convert numpy structured array to Polars DataFrame with proper timestamp handling
    
    Args:
        data: Numpy structured array
        file_type: 'scid' or 'depth'
        epoch_offset_us: Offset to convert from custom epoch to Unix epoch
    """
    
    # Convert to dictionary for Polars
    data_dict = {name: data[name] for name in data.dtype.names}
    
    # Process timestamps with custom epoch
    unix_timestamp_us, trade_counter = process_timestamps(data_dict['time'], epoch_offset_us)
    
    # Replace raw timestamp with processed components
    data_dict['timestamp_us'] = unix_timestamp_us
    data_dict['trade_counter'] = trade_counter
    data_dict.pop('time')  # Remove original time column
    
    # Create Polars DataFrame
    df = pl.DataFrame(data_dict)
    
    # Convert timestamp to datetime (now properly using Unix epoch)
    df = df.with_columns([
        pl.from_epoch(pl.col('timestamp_us'), time_unit='ms').alias('datetime'),
        pl.col('trade_counter').cast(pl.UInt16)  # Trade counter as small int
    ])
    
    return df


def analyze_scid_data(df):
    """Analyze .scid (bar/candle) data"""
    print("\n=== SCID Data Analysis ===")
    print(f"Time range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
    print(f"Average volume: {df['totalVol'].mean():.0f}")
    print(f"Total trades: {df['numTrades'].sum()}")
    
    # Check for duplicate timestamps (multiple trades per millisecond)
    duplicate_times = df.group_by('timestamp_us').len().filter(pl.col('len') > 1)
    if len(duplicate_times) > 0:
        print(f"Found {len(duplicate_times)} milliseconds with multiple trades")
        print("Sample of trade counters for same millisecond:")
        sample_time = duplicate_times['timestamp_us'][0]
        sample_trades = df.filter(pl.col('timestamp_us') == sample_time).select(['datetime', 'trade_counter'])
        print(sample_trades)


def analyze_depth_data(df):
    """Analyze .depth (order book) data"""
    print("\n=== Depth Data Analysis ===")
    print(f"Time range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
    print(f"Command types: {df['command'].value_counts()}")
    print(f"Average quantity: {df['quantity'].mean():.0f}")


def plot_scid_data(df, max_points=10000):
    """Create price plots for SCID data"""
    # Sample data if too large for plotting
    if len(df) > max_points:
        step = len(df) // max_points
        df_plot = df[::step]
        print(f"Sampling every {step}th point for plotting ({len(df_plot)} points)")
    else:
        df_plot = df
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Convert to pandas for matplotlib (polars datetime plotting can be tricky)
    df_pandas = df_plot.to_pandas()
    
    # Price chart
    ax1.plot(df_pandas['datetime'], df_pandas['close'], linewidth=0.5, alpha=0.8)
    ax1.set_ylabel('Price ($)')
    ax1.set_title('Price Over Time')
    ax1.grid(True, alpha=0.3)
    
    # Volume chart
    ax2.bar(df_pandas['datetime'], df_pandas['totalVol'], width=1, alpha=0.6)
    ax2.set_ylabel('Volume')
    ax2.set_xlabel('Time')
    ax2.set_title('Volume Over Time')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def main(args):
    # Handle show-epochs option
    if args.show_epochs:
        show_common_epochs()
        return
    
    try:
        print(f"Reading {args.input}...")
        
        # Calculate epoch offset for custom epoch
        epoch_offset_us = calculate_epoch_offset_microseconds(args.epoch)
        print(f"Using custom epoch: {args.epoch}")
        print(f"Epoch offset: {epoch_offset_us:,} microseconds ({epoch_offset_us/1e6/86400:.1f} days)")
        
        # Read binary data
        data = read_tick_data(args.input, records_to_skip=args.skip, max_records=args.num)
        print(f"Read {len(data)} records")
        
        if len(data) == 0:
            print("No data to process")
            return
        
        # Convert to Polars DataFrame with custom epoch
        file_type = "scid" if args.input.endswith(".scid") else "depth"
        df = numpy_to_polars(data, file_type, epoch_offset_us)
        
        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {df.columns}")
        print("\nFirst few records:")
        print(df.head())
        
        # Show timestamp conversion example
        if len(df) > 0:
            print(f"\n=== Timestamp Conversion Example ===")
            print(f"Raw timestamp (first record): {data['time'][0]}")
            print(f"After removing trade counter: {data['time'][0] // 1000}")
            print(f"Trade counter: {data['time'][0] % 1000}")
            print(f"Converted datetime: {df['datetime'][0]}")
        
        # Analyze data based on file type
        if file_type == "scid":
            analyze_scid_data(df)
            if args.plot:
                plot_scid_data(df)
        else:
            analyze_depth_data(df)
        
        # Example: Filter data by time range
        print("\n=== Sample Time Filtering ===")
        # Get data from last hour
        last_hour = df.filter(
            pl.col('datetime') >= df['datetime'].max() - pl.duration(hours=1)
        )
        print(f"Records in last hour: {len(last_hour)}")
        
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    args = parse_args()
    main(args)