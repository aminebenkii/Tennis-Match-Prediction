import numpy as np
import pandas as pd
import os


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


def initialize_dictionaries(unique_players):
    

    total_points_diff = {player: 0 for player in unique_players}
    sets_played = {player: 0 for player in unique_players}
    matches_played = {player: 0 for player in unique_players}
    win_record = {player: [] for player in unique_players}
    h2h_records = {
        (p1, p2): {'outcomes': [], 'matches': 0}
        for p1 in unique_players for p2 in unique_players if p1 != p2
    }
    surface_stats = {
        player: {
            'Hard': {'wins': 0, 'games': 0},
            'Clay': {'wins': 0, 'games': 0},
            'Grass': {'wins': 0, 'games': 0}
        }
        for player in unique_players
    }
    return total_points_diff, sets_played, matches_played, win_record, h2h_records, surface_stats


def update_dictionaries(row, total_points_diff, sets_played, matches_played, win_record, h2h_records, surface_stats):
   
    p1, p2 = row['P1'], row['P2']
    winner = row['Winner']
    p1_ATPts, p2_ATPts = row['P1_ATPts'], row['P2_ATPts']
    surface = row['Surface']

    matches_played[p1] += 1
    matches_played[p2] += 1

    points_diff_p1 = sum(row[f'P1S{i}'] - row[f'P2S{i}'] for i in range(1, 6))
    sets_played_p1 = sum(row[f'P1S{i}'] > 0 for i in range(1, 6))
    sets_played_p2 = sum(row[f'P2S{i}'] > 0 for i in range(1, 6))
    match_sets_played = max(sets_played_p1, sets_played_p2)

    total_points_diff[p1] += points_diff_p1
    total_points_diff[p2] -= points_diff_p1

    sets_played[p1] += match_sets_played
    sets_played[p2] += match_sets_played

    if abs(p1_ATPts - p2_ATPts) <= 500:
        win_record[p1].append(1 if winner == 1 else 0)
        win_record[p2].append(1 if winner == 2 else 0)

    h2h_records[(p1, p2)]['matches'] += 1
    h2h_records[(p2, p1)]['matches'] += 1
    if winner == 1:
        h2h_records[(p1, p2)]['outcomes'].append(1)
        h2h_records[(p2, p1)]['outcomes'].append(0)
    elif winner == 2:
        h2h_records[(p1, p2)]['outcomes'].append(0)
        h2h_records[(p2, p1)]['outcomes'].append(1)

    if abs(p1_ATPts - p2_ATPts) <= 500:
        surface_stats[p1][surface]['games'] += 1
        surface_stats[p2][surface]['games'] += 1
        if winner == 1:
            surface_stats[p1][surface]['wins'] += 1
        elif winner == 2:
            surface_stats[p2][surface]['wins'] += 1


def calculate_transformed_row(row, total_points_diff, sets_played, matches_played, win_record, h2h_records, surface_stats):
    

    p1, p2 = row['P1'], row['P2']
    p1_atpts, p2_atpts = row['P1_ATPts'], row['P2_ATPts']
    surface = row['Surface']

    p1_avg = total_points_diff[p1] / sets_played[p1] if sets_played[p1] != 0 else 0
    p2_avg = total_points_diff[p2] / sets_played[p2] if sets_played[p2] != 0 else 0

    p1_wr = sum(win_record[p1][-10:]) / len(win_record[p1][-10:]) if len(win_record[p1][-10:]) > 0 else 0
    p2_wr = sum(win_record[p2][-10:]) / len(win_record[p2][-10:]) if len(win_record[p2][-10:]) > 0 else 0

    h2h_matches = min(10, h2h_records[(p1, p2)]['matches'])
    h2h_outcomes = h2h_records[(p1, p2)]['outcomes'][-h2h_matches:]
    h2h_p1_p2 = sum(h2h_outcomes) / h2h_matches if h2h_matches > 0 else 0

    surface_wr_p1 = surface_stats[p1][surface]['wins'] / surface_stats[p1][surface]['games'] if surface_stats[p1][surface]['games'] > 0 else 0
    surface_wr_p2 = surface_stats[p2][surface]['wins'] / surface_stats[p2][surface]['games'] if surface_stats[p2][surface]['games'] > 0 else 0

    return {
        'P1': p1,
        'P2': p2,
        'DIFF_ATPts': p1_atpts - p2_atpts,
        'P1_Avg': round(p1_avg, 2),
        'P2_Avg': round(p2_avg, 2),
        'DIFF_Avg': round(p1_avg - p2_avg, 2),
        'Data_Points_Avg': (matches_played[p1], matches_played[p2]),
        'P1_Wr': round(p1_wr, 2),
        'P2_Wr': round(p2_wr, 2),
        'DIFF_Wr': round(p1_wr - p2_wr, 2),
        'P1P2_H2H': round(h2h_p1_p2, 2),
        'Data_Points_H2H': h2h_matches,
        'P1_SWr': round(surface_wr_p1, 2),
        'P2_SWr': round(surface_wr_p2, 2),
        'DIFF_SWr': round(surface_wr_p1 - surface_wr_p2, 2),
        'Surface': surface,
        'Data_Points_SWr': (surface_stats[p1][surface]['games'], surface_stats[p2][surface]['games']),
        'Winner': row['Winner'],
        'P1_Avg_Odds': row['P1_Avg_Odds'],
        'P2_Avg_Odds': row['P2_Avg_Odds']
    }


def preprocess_data(df, split_index):
    
    df = df[['Date', 'Surface', 'Winner', 'Loser', 'WPts', 'LPts', 'W1', 'L1', 'W2', 'L2', 'W3', 'L3','W4','L4','W5','L5', 'AvgW', 'AvgL']]
    unique_players = pd.concat([df['P1'], df['P2']]).unique()
    total_points_diff, sets_played, matches_played, win_record, h2h_records, surface_stats = initialize_dictionaries(unique_players)

    initial_df = df.iloc[:split_index]
    for _, row in initial_df.iterrows():
        update_dictionaries(row, total_points_diff, sets_played, matches_played, win_record, h2h_records, surface_stats)

    new_df = []
    for i in range(split_index, len(df)):
        row = df.iloc[i]
        transformed_row = calculate_transformed_row(row, total_points_diff, sets_played, matches_played, win_record, h2h_records, surface_stats)
        new_df.append(transformed_row)
        update_dictionaries(row, total_points_diff, sets_played, matches_played, win_record, h2h_records, surface_stats)

    return pd.DataFrame(new_df)



data_dir = "../Raw_historical_data"
file_years = range(2023, 2025)  

historical_data_df = read_files_to_dataframe(data_dir, file_years)

new_df = preprocess_data(historical_data_df, split_index=5000)

new_df.to_csv('transformed_data.csv', index=False)
