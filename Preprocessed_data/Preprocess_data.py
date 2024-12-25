import os
import pandas as pd




def read_files_to_dataframe(directory, years):
    data_frames = []

    for year in years:
        file_path = os.path.join(directory, f"{year}.xlsx")
        try:
            # Read the Excel file into a DataFrame
            df = pd.read_excel(file_path)
            df['Year'] = year  # Add a column for the year
            data_frames.append(df)
        except FileNotFoundError:
            print(f"File {file_path} not found. Skipping.")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Concatenate all DataFrames into a single DataFrame
    combined_df = pd.concat(data_frames, ignore_index=True)
    return combined_df




data_dir = "../Raw_historical_data"
file_years = range(2014, 2025)  

historical_data_df = read_files_to_dataframe(data_dir, file_years)
historical_data_df = historical_data_df[['Date', 'Surface', 'Winner', 'Loser', 'WPts', 'LPts', 'W1', 'L1', 'W2', 'L2', 'W3', 'L3', 'AvgW', 'AvgL']]

print(historical_data_df.head())


# Create a copy to flip every second row
flipped_df = historical_data_df.copy()

# Flip Winner/Loser columns in every second row
flipped_df.loc[1::2, ['Winner', 'Loser']] = historical_data_df.loc[1::2, ['Loser', 'Winner']].values

# Flip points, ranks, and set scores
flipped_df.loc[1::2, ['WPts', 'LPts']] = historical_data_df.loc[1::2, ['LPts', 'WPts']].values
flipped_df.loc[1::2, ['W1', 'L1']] = historical_data_df.loc[1::2, ['L1', 'W1']].values
flipped_df.loc[1::2, ['W2', 'L2']] = historical_data_df.loc[1::2, ['L2', 'W2']].values
flipped_df.loc[1::2, ['W3', 'L3']] = historical_data_df.loc[1::2, ['L3', 'W3']].values
flipped_df.loc[1::2, ['AvgW', 'AvgL']] = historical_data_df.loc[1::2, ['AvgL', 'AvgW']].values

# Create a new Winner column (1 if P1 wins, 0 otherwise)
flipped_df['WinnerLabel'] = (flipped_df['Winner'] == historical_data_df['Winner']).astype(int)

# Rename columns to P1S1, P2S1, etc.
flipped_df = flipped_df.rename(columns={
    'W1': 'P1S1', 'L1': 'P2S1',
    'W2': 'P1S2', 'L2': 'P2S2',
    'W3': 'P1S3', 'L3': 'P2S3'
})

# Rename Winner and Loser to P1 and P2
flipped_df = flipped_df.rename(columns={'Winner': 'P1', 'Loser': 'P2'})


# Display the first few rows
print(flipped_df.head())