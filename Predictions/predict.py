import json
import joblib
import numpy as np
import pandas as pd

# Load the model and dictionaries
log_reg_model = joblib.load("log_reg_model.pkl")

with open("dicts.json", "r") as f:
    all_dicts = json.load(f)

total_points_diff = all_dicts["total_points_diff"]
sets_played = all_dicts["sets_played"]
matches_played = all_dicts["matches_played"]
win_record = all_dicts["win_record"]
h2h_records = all_dicts["h2h_records"]
surface_stats = all_dicts["surface_stats"]

# Helper function to preprocess a single match
def preprocess_match(p1, p2, surface):
    # Check if players exist in dictionaries
    if p1 not in total_points_diff or p2 not in total_points_diff:
        print("One or both players not found in the dictionaries.")
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

    # Create a feature dictionary
    features = {
        'P1_Rank': 0,  # Placeholder, replace with actual rank if available
        'P2_Rank': 0,  # Placeholder, replace with actual rank if available
        'DIFF_Rank': 0,  # Placeholder
        'P1_ATPts': 0,  # Placeholder
        'P2_ATPts': 0,  # Placeholder
        'DIFF_ATPts': 0,  # Placeholder
        'P1_Avg': p1_avg,
        'P2_Avg': p2_avg,
        'DIFF_Avg': p1_avg - p2_avg,
        'P1_Wr': p1_wr,
        'P2_Wr': p2_wr,
        'DIFF_Wr': p1_wr - p2_wr,
        'P1P2_H2H': h2h_p1_p2,
        'P1_SWr': surface_wr_p1,
        'P2_SWr': surface_wr_p2,
        'DIFF_SWr': surface_wr_p1 - surface_wr_p2,
    }

    return pd.DataFrame([features])

# Main function to ask for input and calculate odds
def main():
    print("Enter details for the match you want to predict.")
    p1 = input("Enter Player 1's name: ")
    p2 = input("Enter Player 2's name: ")
    surface = input("Enter surface type (Hard/Clay/Grass): ")

    # Preprocess the match
    features = preprocess_match(p1, p2, surface)
    if features is None:
        return

    # Predict probabilities
    y_pred_prob = log_reg_model.predict_proba(features)

    # Calculate odds
    p1_odds = 1 / y_pred_prob[0, 0]  # Odds for Player 1
    p2_odds = 1 / y_pred_prob[0, 1]  # Odds for Player 2

    # Print the results
    print(f"\nPredicted Odds:")
    print(f"{p1} Odds: {p1_odds:.2f}")
    print(f"{p2} Odds: {p2_odds:.2f}")

# Run the program
if __name__ == "__main__":
    main()
