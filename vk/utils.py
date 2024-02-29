import time

def unix_to_days_ago(unix):
    # Get the current unix timestamp
    current_unix_timestamp = time.time()
    
    # Subtract the seconds to get the min date in unix format
    days = (current_unix_timestamp - unix) / (24 * 60 * 60)
    
    return int(days)

def days_ago_to_unix_timestamp(days):
    # Convert days to seconds
    seconds = days * 24 * 60 * 60
    
    # Get the current unix timestamp
    current_unix_timestamp = time.time()
    
    # Subtract the seconds to get the min date in unix format
    min_unix_timestamp = current_unix_timestamp - seconds
    
    return int(min_unix_timestamp)