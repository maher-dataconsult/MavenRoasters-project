import pandas as pd
import numpy as np
from sklearn.utils import resample
from datetime import datetime, timedelta

# Load the dataset from the correct sheet
file_path = r'D:\0.coding\0.Projects\MavenRoasters-project\Coffee Shop Sales raw_data.xlsx'
xls = pd.ExcelFile(file_path)
df = pd.read_excel(xls, sheet_name='Transactions')

# Remove data from 2019
df = df[df['transaction_date'].dt.year > 2019]

# Original store locations with IDs
original_locations = {
    'Astoria': 3,
    'Lower Manhattan': 5,
    'Hell\'s Kitchen': 8
}

# Adding new locations
new_locations = {
    'Harlem': 10,
    'Brooklyn': 12
}

# Combining the original and new locations
all_locations = {**original_locations, **new_locations}

# Define weights for weekdays, seasons, and locations
weekday_weights = [5.71, 8.57, 11.43, 14.29, 17.14, 22.86, 20.00]
weekday_weights = [w/sum(weekday_weights) for w in weekday_weights]  # Normalize to sum to 1
season_weights = [25.00, 30.00, 20.00, 25.00]
season_weights = [w/sum(season_weights) for w in season_weights]  # Normalize to sum to 1
location_weights = [15.00, 30.00, 20.00, 20.00, 15.00]
location_weights = [w/sum(location_weights) for w in location_weights]  # Normalize to sum to 1

# Define custom year weights
year_weights = {
    2020: 0.15,
    2021: 0.25,
    2022: 0.28,
    2023: 0.32
}

# Ensure product_id is linked to one unit_price, product_category, and product_type
product_info = df[['product_id', 'unit_price', 'product_category', 'product_type']].drop_duplicates()

# Calculate original weekday distribution
df['transaction_date'] = pd.to_datetime(df['transaction_date'])
weekday_distribution = df['transaction_date'].dt.weekday.value_counts(normalize=True)

# Function to get season from date
def get_season(date):
    month = date.month
    if month in [12, 1, 2]:
        return 0  # Winter
    elif month in [3, 4, 5]:
        return 1  # Spring
    elif month in [6, 7, 8]:
        return 2  # Summer
    else:
        return 3  # Fall

# Function to augment dates while preserving weekdays and applying seasonality
def augment_dates_preserve_weekdays_and_seasons(start_date, end_date, weekday_weights, season_weights):
    while True:
        weekday = int(np.random.choice(range(7), p=weekday_weights))
        season = int(np.random.choice(range(4), p=season_weights))
        days_range = (end_date - start_date).days
        random_days = np.random.randint(0, days_range)
        new_date = start_date + timedelta(days=random_days)
        new_date += timedelta(days=(weekday - new_date.weekday()) % 7)
        if get_season(new_date) == season and start_date <= new_date <= end_date:
            return new_date

# Augment the transaction dates
df_augmented = df.copy()
total_records = 0
for year, weight in year_weights.items():
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    num_records = int(weight * 1_000_000)
    df_augmented_year = df_augmented.copy()
    df_augmented_year['transaction_date'] = df_augmented_year.apply(lambda row: augment_dates_preserve_weekdays_and_seasons(start_date, end_date, weekday_weights, season_weights), axis=1)
    df_augmented_year = resample(df_augmented_year, replace=True, n_samples=num_records, random_state=42)
    df_augmented = pd.concat([df_augmented, df_augmented_year], ignore_index=True)
    total_records += num_records

# Assign store_id and store_location based on location weights
df_augmented['store_location'] = np.random.choice(list(all_locations.keys()), size=len(df_augmented), p=location_weights)
df_augmented['store_id'] = df_augmented['store_location'].map(all_locations)

# Ensure product_id retains its original unit_price, product_category, and product_type
df_augmented = df_augmented.drop(['unit_price', 'product_category', 'product_type'], axis=1)
df_augmented = df_augmented.merge(product_info, on='product_id', how='left')

# Sort the DataFrame by transaction_date and transaction_time
df_augmented.sort_values(by=['transaction_date', 'transaction_time'], inplace=True)

# Assign new transaction_id in ascending order based on the new chronological order
df_augmented['transaction_id'] = range(1, len(df_augmented) + 1)

# Save the augmented dataset to a new CSV file
df_augmented.to_csv('augmented_coffee_shop_sales.csv', index=False)

print(f"Data augmentation completed with {total_records} records and saved as 'augmented_coffee_shop_sales.csv'")
print(f"Date range: {df_augmented['transaction_date'].min()} to {df_augmented['transaction_date'].max()}")

# Verify seasonality distribution
df_augmented['season'] = df_augmented['transaction_date'].apply(get_season)
season_distribution = df_augmented['season'].value_counts(normalize=True).sort_index()
print("\nSeasonality distribution in the augmented dataset:")
print(season_distribution)
print("\nExpected seasonality distribution:")
print(pd.Series(season_weights, index=['Winter', 'Spring', 'Summer', 'Fall']))