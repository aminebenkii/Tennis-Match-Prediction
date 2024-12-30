import pandas as pd
import numpy as np
import os
import json




def read_files_to_dataframe(directory, years):
    data_frames = []

    for year in years:
        file_path = os.path.join(directory, f"{year}.xlsx")
        try:
            
            df = pd.read_excel(file_path)
            df['Year'] = year  
            data_frames.append(df)
        except FileNotFoundError:
            print(f"File {file_path} not found. Skipping.")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    combined_df = pd.concat(data_frames, ignore_index=True)
    return combined_df


def clip_rename_and_flip_dataframe(historical_data_df):
    
    historical_data_df = historical_data_df[['Date', 'Surface', 'Winner', 'Loser', 'WRank', 'LRank', 'WPts', 'LPts', 'W1', 'L1', 'W2', 'L2', 'W3', 'L3', 'W4', 'L4', 'W5', 'L5', 'AvgW', 'AvgL']]

    df = historical_data_df.rename(columns={

        'Winner': 'P1', 'Loser': 'P2',
        'WRank': 'P1_Rank', 'LRank': 'P2_Rank',
        'WPts': 'P1_ATPts', 'LPts': 'P2_ATPts',
        'W1': 'P1S1', 'L1': 'P2S1',
        'W2': 'P1S2', 'L2': 'P2S2',
        'W3': 'P1S3', 'L3': 'P2S3',
        'W4': 'P1S4', 'L4': 'P2S4',
        'W5': 'P1S5', 'L5': 'P2S5',
        'AvgW': 'P1_Avg_Odds', 'AvgL': 'P2_Avg_Odds'
    })

    # Flip rows for alternating matches nad have a 50% Baseline
    df.loc[1::2, ['P1', 'P2']] = historical_data_df.loc[1::2, ['Loser', 'Winner']].values
    df.loc[1::2, ['P1_Rank', 'P2_Rank']] = historical_data_df.loc[1::2, ['LRank', 'WRank']].values
    df.loc[1::2, ['P1_ATPts', 'P2_ATPts']] = historical_data_df.loc[1::2, ['LPts', 'WPts']].values
    df.loc[1::2, ['P1S1', 'P2S1']] = historical_data_df.loc[1::2, ['L1', 'W1']].values
    df.loc[1::2, ['P1S2', 'P2S2']] = historical_data_df.loc[1::2, ['L2', 'W2']].values
    df.loc[1::2, ['P1S3', 'P2S3']] = historical_data_df.loc[1::2, ['L3', 'W3']].values
    df.loc[1::2, ['P1S4', 'P2S4']] = historical_data_df.loc[1::2, ['L4', 'W4']].values
    df.loc[1::2, ['P1S5', 'P2S5']] = historical_data_df.loc[1::2, ['L5', 'W5']].values
    df.loc[1::2, ['P1_Avg_Odds', 'P2_Avg_Odds']] = historical_data_df.loc[1::2, ['AvgL', 'AvgW']].values

    # Create a Winner column
    df['Winner'] = (df['P1'] != historical_data_df['Winner']).astype(int) + 1

    df[['P1S1', 'P2S1', 'P1S2', 'P2S2', 'P1S3', 'P2S3', 'P1S4', 'P2S4', 'P1S5', 'P2S5']] = df[['P1S1', 'P2S1', 'P1S2', 'P2S2', 'P1S3', 'P2S3', 'P1S4', 'P2S4', 'P1S5', 'P2S5']].fillna(0)

    return df


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
    p1_rank, p2_rank = row['P1_Rank'], row['P2_Rank']
    surface = row['Surface']
    winner = row['Winner']


    points_diff = sum(row[f'P1S{i}'] - row[f'P2S{i}'] for i in range(1, 6))
    non_zero_sets_p1 = sum(row[f'P1S{i}'] > 0 for i in range(1, 6))
    non_zero_sets_p2 = sum(row[f'P2S{i}'] > 0 for i in range(1, 6))
    match_sets_played = max(non_zero_sets_p1, non_zero_sets_p2)


    sets_played[p1] += match_sets_played
    sets_played[p2] += match_sets_played
    matches_played[p1] += 1
    matches_played[p2] += 1
    total_points_diff[p1] += points_diff
    total_points_diff[p2] -= points_diff


    if abs(p1_rank - p2_rank) <= 100:
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


    if abs(p1_rank - p2_rank) <= 200:
        surface_stats[p1][surface]['games'] += 1
        surface_stats[p2][surface]['games'] += 1
        if winner == 1:
            surface_stats[p1][surface]['wins'] += 1
        elif winner == 2:
            surface_stats[p2][surface]['wins'] += 1


def calculate_transformed_row(row, total_points_diff, sets_played, matches_played, win_record, h2h_records, surface_stats):

    p1, p2 = row['P1'], row['P2']
    surface = row['Surface']

    p1_avg = total_points_diff[p1] / sets_played[p1] if sets_played[p1] != 0 else np.nan
    p2_avg = total_points_diff[p2] / sets_played[p2] if sets_played[p2] != 0 else np.nan

    p1_wr = sum(win_record[p1][-10:]) / len(win_record[p1][-10:]) if len(win_record[p1][-10:]) > 0 else np.nan
    p2_wr = sum(win_record[p2][-10:]) / len(win_record[p2][-10:]) if len(win_record[p2][-10:]) > 0 else np.nan

    h2h_matches = min(10, h2h_records[(p1, p2)]['matches'])
    h2h_outcomes = h2h_records[(p1, p2)]['outcomes'][-h2h_matches:]
    h2h_p1_p2 = sum(h2h_outcomes) / h2h_matches if h2h_matches > 0 else np.nan

    surface_wr_p1 = surface_stats[p1][surface]['wins'] / surface_stats[p1][surface]['games'] if surface_stats[p1][surface]['games'] > 0 else np.nan
    surface_wr_p2 = surface_stats[p2][surface]['wins'] / surface_stats[p2][surface]['games'] if surface_stats[p2][surface]['games'] > 0 else np.nan

    return {
        'Date' : row['Date'],
        'P1': p1,
        'P2': p2,
        'P1_Rank': row['P1_Rank'],
        'P2_Rank': row['P2_Rank'],
        'DIFF_Rank':row['P2_Rank'] - row['P1_Rank'],
        'P1_ATPts': row['P1_ATPts'],
        'P2_ATPts': row['P2_ATPts'],
        'DIFF_ATPts': row['P1_ATPts'] - row['P2_ATPts'],
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

    #region Save Dictionaries to JSON Files
    # Helper function to convert NumPy types to Python types
    def convert_to_serializable(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()  # Convert NumPy arrays to lists
        else:
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    # Combine all dictionaries into one
    all_dicts = {
        "total_points_diff": total_points_diff,
        "sets_played": sets_played,
        "matches_played": matches_played,
        "win_record": win_record,
        "h2h_records": h2h_records,
        "surface_stats": surface_stats,
    }

    # Save to a single JSON file
    with open('dicts.json', 'w') as f:
        json.dump(all_dicts, f, default=convert_to_serializable)

        #endregion
        
        return pd.DataFrame(new_df)


data_dir = "../Raw_historical_data"
file_years = range(2019, 2025)

historical_data_df = read_files_to_dataframe(data_dir, file_years)

df = clip_rename_and_flip_dataframe(historical_data_df)

new_df = preprocess_data(df, split_index= int(0.75*len(df)))

new_df.to_csv('Preprocessed_data.csv', index=False)



