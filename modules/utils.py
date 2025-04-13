import html
import unidecode
import re
import pandas as pd
from fuzzywuzzy import process
from modules.constants import *

def format_display_name(player_name):
    """Format the player's name for display (human-readable with special characters)."""
    formatted_name = html.unescape(player_name)  # Decode HTML entities
    formatted_name = formatted_name.encode('latin1').decode('utf-8', 'ignore')  # Fix encoding issues
    return formatted_name

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

def rename_columns(df):
    """
    Renames the columns of the DataFrame using the STAT_NAME_MAPPING dictionary.
    """
    return df.rename(columns=STAT_NAME_MAPPING)

  
def fuzzy_match_player(player_name, all_players):
    """
    Perform fuzzy matching to find the best player match.

    Args:
        player_name (str): The name entered by the user.
        all_players (list): A list of (player_name, team_name) tuples.

    Returns:
        tuple: (Best matched player name, team name), or (None, None) if no match.
    """
    print(type(all_players))  # Check if it's a list
    print(type(all_players[0]))  # Check if first element is a tuple or list
    print(all_players[:5])  # Print first 5 elements to inspect structure

    player_dict = {p[0]: p for p in all_players}  # Map player_name -> (player_name, team_name)

    best_match = process.extractOne(player_name, player_dict.keys())

    if best_match:
        return player_dict[best_match[0]]  # Correctly returns (player_name, team_name)

    return None, None



