import html
import unidecode
import re
import streamlit as st
import pandas as pd
from datetime import datetime, date
from fuzzywuzzy import process


from modules.constants import *

def get_season_year(dt):
    """
    Given a date, return the 'season year' used by Basketball Reference.
    Example: March 2024 → 2024 season, October 2024 → 2025 season.
    """
    return dt.year + 1 if dt.month >= 10 else dt.year

def format_display_name(player_name):
    """Format the player's name for display (human-readable with special characters)."""
    try:
        decoded = html.unescape(player_name)
        # Only attempt this if decoding succeeds
        return decoded
    except Exception:
        # Fallback to safe ASCII approximation
        return unidecode.unidecode(player_name)

def normalize_player_name(formatted_name):
    """
    Normalize the player name for URL usage:
    - Removes suffixes (Jr., Sr., II, III, etc.).
    - Converts to ASCII (removes accents).
    - Strips extra spaces and converts to lowercase.
    """
    formatted_name = formatted_name.strip()
    
    # Remove common suffixes (e.g., "LeBron James Jr." → "LeBron James")
    name_parts = formatted_name.split()
    if name_parts[-1].lower().rstrip('.') in SUFFIXES:
        name_parts.pop()
    
    cleaned_name = " ".join(name_parts)
    
    return unidecode.unidecode(cleaned_name).lower()

# Helper function to standardize player selection
def extract_player_details(selected_player, selected_team=None):
    """Ensure selected_player is always in the form (player_name, player_team)."""
    if isinstance(selected_player, tuple):
        return selected_player  # Already in correct format
    elif isinstance(selected_player, str) and selected_team: 
        return (selected_player, selected_team)  # From team roster
    return None, None  # No valid selection
  
def fuzzy_match_player(player_name, all_players):
    """
    Perform fuzzy matching to find the best player match.

    Args:
        player_name (str): The name entered by the user.
        all_players (list): A list of (player_name, team_name) tuples.

    Returns:
        tuple: (Best matched player name, team name), or (None, None) if no match.
    """
    #print(type(all_players))  # Check if it's a list
    #print(type(all_players[0]))  # Check if first element is a tuple or list
    #print(all_players[:5])  # Print first 5 elements to inspect structure

    #player_dict = {p[0]: p for p in all_players}  # Map player_name -> (player_name, team_name)

    best_match = process.extractOne(player_name, all_players)
    print(f"best match is {best_match}")

    if best_match:
        return best_match[0]  # Correctly returns (player_name, team_name)

    return None, None
def rename_stats_for_display(df):
    """
    Renames the columns of the DataFrame using the STAT_NAME_MAPPING dictionary.
    """
    return df.rename(columns=STAT_NAME_MAPPING)
    
def filter_stat_columns(stats_list, selected_stats, is_average=False):
    """
    Filter a list of stat dictionaries to include only selected stats.
    Always includes 'game_date', 'opponent', and 'result' for display/charting; returns dictionaries with those fields plus the selected stats.
    """
    always_include = ["game_date", "opponent", "result"]
    if is_average:
        # Prefix averages with "avg_" in case of average rows
        return {
            k:v for k, v in stats_list.items()
            if k in [f"avg_{s}" for s in selected_stats]
        }

    return [
        {
            **{k: game[k] for k in always_include if k in game},
            **{k: game.get(k, 0) for k in selected_stats}
        }
        for game in stats_list
    ]

def highlight_thresholds(row, thresholds):
    return [
        'color: green; font-weight: bold' if stat in thresholds and row[stat] >= thresholds[stat]
        else 'color: red' if stat in thresholds else ''
        for stat in row.index
    ]

def render_table(df, title="", thresholds=None):
    st.write(title)
    df = rename_stats_for_display(df)
    df = df[[col for col in ["Game Date", "Opponent", "Result"] if col in df.columns] + [col for col in df.columns if col not in ["Game Date", "Opponent", "Result"]]]
    df.index += 1
    if thresholds:
        styled_df = df.style.apply(highlight_thresholds, thresholds=thresholds, axis=1)
        st.dataframe(styled_df)
    else:
        st.dataframe(df)
