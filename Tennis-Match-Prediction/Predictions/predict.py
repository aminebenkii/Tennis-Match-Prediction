import json
import joblib
import numpy as np
import pandas as pd

# Load the model
try:
    log_reg_model = joblib.load("log_reg_model.pkl")
except FileNotFoundError:
    print("Error: The logistic regression model file 'log_reg_model.pkl' was not found.")
    exit()

# Load the dictionaries
try:
    with open("dicts.json", "r") as f:
        all_dicts = json.load(f)
except FileNotFoundError:
    print("Error: The dictionaries file 'dicts.json' was not found.")
    exit()

# Extract individual dictionaries from the loaded JSON
total_points_diff = all_dicts["total_points_diff"]
sets_played = all_dicts["sets_played"]
matches_played = all_dicts["matches_played"]
win_record = all_dicts["win_record"]
h2h_records = {eval(k): v for k, v in all_dicts["h2h_records"].items()}  # Convert string keys back to tuples
surface_stats = all_dicts["surface_stats"]

def preprocess_match(p1, p2, surface):
    """
    Preprocesses the match data for the given players and surface to create feature input for the model.

    Args:
        p1 (str): Player 1's name.
        p2 (str): Player 2's name.
        surface (str): Surface type ('Hard', 'Clay', 'Grass').

    Returns:
        pd.DataFrame: A DataFrame containing preprocessed features for the model.
    """
    if p1 not in total_points_diff or p2 not in total_points_diff:
        print("Error: One or both players not found in the dictionaries.")
        return None

    # Calculate average points
    p1_avg = total_points_diff.get(p1, 0) / sets_played.get(p1, 1)
    p2_avg = total_points_diff.get(p2, 0) / sets_played.get(p2, 1)

    # Calculate win ratios
    p1_wr = sum(win_record.get(p1, [])[-10:]) / len(win_record.get(p1, [])[-10:]) if win_record.get(p1, []) else np.nan
    p2_wr = sum(win_record.get(p2, [])[-10:]) / len(win_record.get(p2, [])[-10:]) if win_record.get(p2, []) else np.nan

    # Calculate head-to-head performance
    h2h_matches = min(10, h2h_records.get((p1, p2), {}).get("matches", 0))
    h2h_outcomes = h2h_records.get((p1, p2), {}).get("outcomes", [])[-h2h_matches:]
    h2h_p1_p2 = sum(h2h_outcomes) / h2h_matches if h2h_matches > 0 else np.nan

    # Surface-specific win ratios
    surface_wr_p1 = surface_stats.get(p1, {}).get(surface, {}).get("wins", 0) / surface_stats.get(p1, {}).get(surface, {}).get("games", 1)
    surface_wr_p2 = surface_stats.get(p2, {}).get(surface, {}).get("wins", 0) / surface_stats.get(p2, {}).get(surface, {}).get("games", 1)

    # Create a feature dictionary matching the training features
    features = {
        'DIFF_Rank': 0,  # Placeholder if rank differences were not calculated
        'DIFF_ATPts': 0,  # Placeholder if ATP points difference not available
        'DIFF_Avg': p1_avg - p2_avg,
        'DIFF_Wr': p1_wr - p2_wr,
        'P1P2_H2H': h2h_p1_p2,
        'DIFF_SWr': surface_wr_p1 - surface_wr_p2,
    }

    # Return as DataFrame with correct column order
    return pd.DataFrame([features], columns=[
        'DIFF_Rank', 'DIFF_ATPts', 'DIFF_Avg', 'DIFF_Wr', 'P1P2_H2H', 'DIFF_SWr'
    ])


def main():
    """
    Main function to accept user input, preprocess match data, and predict odds using the trained model.
    """
    print("Enter details for the match you want to predict.")
    p1 = input("Enter Player 1's name: ")
    p2 = input("Enter Player 2's name: ")
    surface = input("Enter surface type (Hard/Clay/Grass): ")

    # Preprocess the match
    features = preprocess_match(p1, p2, surface)
    if features is None:
        return

    # Predict probabilities
    try:
        y_pred_prob = log_reg_model.predict_proba(features)
    except Exception as e:
        print(f"Error during prediction: {e}")
        return

    # Calculate odds
    p1_odds = 1 / y_pred_prob[0, 0]  # Odds for Player 1
    p2_odds = 1 / y_pred_prob[0, 1]  # Odds for Player 2

    # Print the results
    print(f"\nPredicted Odds:")
    print(f"{p1} Odds: {p1_odds:.2f}")
    print(f"{p2} Odds: {p2_odds:.2f}")

if __name__ == "__main__":
    main()
