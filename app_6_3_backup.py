import streamlit as st
import datetime
import pandas as pd
from modules.constants import *
from modules.utils import *
from modules.game import *
from modules.team import *
from modules.player import *

# 1️⃣ **Choose Search Method**
search_method = st.radio(
    "Choose how you want to search:",
    ["Game Date", "Team Roster", "Player Name"]
)

selected_player = None  # Placeholder for player selection
selected_date = None     # Placeholder for date selection

# 2️⃣ **Game Date Search**
if search_method == "Game Date":
    today = datetime.date.today()
    selected_date = st.date_input("Select a date for games:", today)
    month = selected_date.strftime('%B').lower()
    year = selected_date.year

    # Get games for the selected date
    games = get_games_for_date(year, month, selected_date)

    if games:
        game_options = [f"{g['away_team']} vs. {g['home_team']}" for g in games]
        selected_game_index = st.selectbox("Select a game:", range(len(game_options)), format_func=lambda x: game_options[x])
        selected_game = games[selected_game_index]

        st.write(f"**Selected Game:** {selected_game['away_team']} vs. {selected_game['home_team']}")

        # Get players from selected game
        all_players = get_all_players(selected_game)
        selected_player = st.selectbox("Select a player:", all_players, format_func=lambda x: f"{x[1]} ({x[2]})")

# 3️⃣ **Team Roster Search**
elif search_method == "Team Roster":
    teams = get_all_teams()
    selected_team = st.selectbox("Select a team:", teams)

    if selected_team:
        team_roster = get_team_roster(selected_team)
        selected_player = st.selectbox("Select a player:", team_roster, format_func=lambda x: f"{x[1]} ({x[2]})")

    # Select date after choosing player
    selected_date = st.date_input("Select a date:", datetime.date.today())

# 4️⃣ **Player Name Search**
elif search_method == "Player Name":
    all_players = get_all_active_players()
    player_names = [player[1] for player in all_players]

    search_query = st.text_input("Enter player name:")
    matched_player = None

    if search_query:
        matched_player = fuzzy_match_player(search_query, all_players)
    
    if matched_player:
        selected_player = st.selectbox("Select the matching player:", matched_player, format_func=lambda x: f"{x[1]} ({x[2]})")
        selected_date = st.date_input("Select a date:", datetime.date.today())

# 5️⃣ **Proceed to Stats Selection**
if selected_player and selected_date:
    selected_player_name_w_team_code, selected_player_name, selected_player_team = selected_player
    stats = get_player_stats(selected_player_name, selected_player_team, selected_date.year)

        if stats:
            # 4️⃣ **Stat Selection**
            DEFAULT_COLUMNS = ["game_date", "opponent", "result"]

            # Stat dropdown (excluding game_date & opponent)
            selectable_stats = {k: v for k, v in STAT_NAME_MAPPING.items() if k not in DEFAULT_COLUMNS}
            selected_stat_names = st.multiselect("Select Stats", list(selectable_stats.values()))

            # Convert selected names back to original column keys
            inverse_mapping = {v: k for k, v in selectable_stats.items()}
            selected_stats = [inverse_mapping[name] for name in selected_stat_names]

            # 5️⃣ **Stat Type Selection**
            stat_type_options = [
                "Last n Games",
                "Full Season Averages",
                "Stats Against This Opponent",
                "Threshold Stats"
            ]
            selected_stat_types = st.multiselect("Select stat types:", stat_type_options)

            # 6️⃣ **Threshold Input (if selected)**
            stat_thresholds = {}
            if "Threshold Stats" in selected_stat_types:
                st.write("Enter thresholds for selected stats:")
                for stat in selected_stats:
                    threshold = st.number_input(f"Threshold for {STAT_NAME_MAPPING[stat]}:", min_value=0, step=1)
                    stat_thresholds[stat] = threshold

            if "Last n Games" in selected_stat_types:
                n = st.slider("n games", min_value=1, max_value=82, value=5)

            # 7️⃣ **Generate Stats Report**
            if st.button("Generate Report"):
                st.subheader(f"📊 Stats Report for {selected_player_name}")

                # **Last 5 Games**
                if "Last n Games" in selected_stat_types:
                    last_n_games, avg_stats = get_last_n_games_stats(selected_player_name, year, stats,n)
                    if last_n_games:
                        filtered_last_n_games = filter_stats(last_n_games, selected_stats)

                        # Ensure opponent & game_date are always included
                        for i, game in enumerate(filtered_last_n_games):
                            game["opponent"] = last_n_games[i]["opponent"]
                            game["game_date"] = last_n_games[i]["game_date"]
                            game["result"] = last_n_games[i]["result"]

                        df_last_n_games = pd.DataFrame(filtered_last_n_games)

                        # Rename columns using the helper function
                        df_last_n_games = rename_columns(df_last_n_games)

                        # Move default columns to the front
                        df_last_n_games = df_last_n_games[["Game Date", "Opponent","Result"] + [col for col in df_last_n_games.columns if col not in ["Game Date", "Opponent", "Result"]]]

                        # ✅ Adjust index to start from 1
                        df_last_n_games.index = df_last_n_games.index + 1

                        st.write(f"### 📅 Last {n} Games")
                        st.table(df_last_n_games)
                    else:
                        st.write("No matching stats found for Last 5 Games.")

                    # **Averages over last 5 games**
                    filtered_avg_stats = filter_stats(avg_stats, selected_stats, is_average=True)
                    df_avg_stats = pd.DataFrame([filtered_avg_stats])
                    # Format numeric values to 1 decimal place
                    df_avg_stats = df_avg_stats.applymap(lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else x)

                    # Remove 'avg_' prefix from column names
                    df_avg_stats.columns = [col.replace("avg_", "") for col in df_avg_stats.columns]

                    # Rename columns using the rename_columns function
                    df_avg_stats = rename_columns(df_avg_stats)

                    st.write(f"#### 🔄 Averages over last {n} games")
                    st.table(df_avg_stats)

                # **Full Season Averages**
                if "Full Season Averages" in selected_stat_types:
                    season_avg_stats = get_full_season_averages(selected_player_name, year, stats)
                    if season_avg_stats:
                        filtered_season_avg_stats = filter_stats(season_avg_stats, selected_stats, is_average=True)

                        df_season_avg_stats = pd.DataFrame([filtered_season_avg_stats])

                        # Convert to DataFrame, remove "avg_", and rename columns
                        df_season_avg_stats = pd.DataFrame([filtered_season_avg_stats])
                        df_season_avg_stats.columns = [col.replace("avg_", "") for col in df_season_avg_stats.columns]
                        df_season_avg_stats = rename_columns(df_season_avg_stats)

                        # Format numeric values to 1 decimal place
                        df_season_avg_stats = df_season_avg_stats.applymap(lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else x)

                        st.write("### 📊 Full Season Averages")
                        st.table(df_season_avg_stats)
                    else:
                        st.write("No data available for full season.")

                # **Stats Against This Opponent**
                if "Stats Against This Opponent" in selected_stat_types:
                    opponent_stats, avg_opponent_stats = get_stats_against_opponent(selected_player_name, year, stats, selected_game)
                    if opponent_stats:
                        filtered_opponent_stats = filter_stats(opponent_stats, selected_stats)

                        # Ensure opponent & game_date are always included
                        for i, game in enumerate(filtered_opponent_stats):
                            game["opponent"] = opponent_stats[i]["opponent"]
                            game["game_date"] = opponent_stats[i]["game_date"]
                            game["result"] = opponent_stats[i]["result"]

                        df_opponent_stats = pd.DataFrame(filtered_opponent_stats)

                        # Rename columns
                        df_opponent_stats = rename_columns(df_opponent_stats)
                        df_opponent_stats = df_opponent_stats[["Game Date", "Opponent", "Result"] + [col for col in df_opponent_stats.columns if col not in ["Game Date", "Opponent", "Result"]]]

                        # ✅ Adjust index to start from 1
                        df_opponent_stats.index = df_opponent_stats.index + 1

                        st.write("### 🎯 Stats Against Opponent")
                        st.table(df_opponent_stats)
                    else:
                        st.write("No matching stats found for opponent.")

                    if len(opponent_stats) > 1:
                        filtered_avg_opponent_stats = filter_stats(avg_opponent_stats, selected_stats, is_average=True)


                        # Convert to DataFrame, remove "avg_", and rename columns
                        df_avg_opponent_stats = pd.DataFrame([filtered_avg_opponent_stats])
                        df_avg_opponent_stats.columns = [col.replace("avg_", "") for col in df_avg_opponent_stats.columns]
                        df_avg_opponent_stats = rename_columns(df_avg_opponent_stats)

                        # Format numeric values to 1 decimal place
                        df_avg_opponent_stats = df_avg_opponent_stats.applymap(lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else x)

                        st.write("#### 🔄 Averages Against This Opponent")
                        st.table(filtered_avg_opponent_stats)

                # **Threshold Stats**
                if "Threshold Stats" in selected_stat_types:
                    threshold_results = []
                    for stat_type, threshold in stat_thresholds.items():
                        result = count_exceeding_threshold(selected_player_name, stat_type, threshold, stats)
                        count_exceeded, count_not_exceeded, total_games, percentage_exceeded, percentage_not_exceeded = result

                        threshold_results.append([
                            STAT_NAME_MAPPING[stat_type], total_games, count_exceeded, f"{percentage_exceeded:.2f}%", 
                            count_not_exceeded, f"{percentage_not_exceeded:.2f}%"
                        ])
                    
                    if threshold_results:
                        st.write("### 📈 Threshold Stats Analysis")
                        df_thresholds = pd.DataFrame(threshold_results, columns=["Stat", "Total Games", "Exceeded", "% Exceeded", "Not Exceeded", "% Not Exceeded"])

                        # ✅ Adjust index to start from 1
                        df_thresholds.index = df_thresholds.index + 1
                        st.table(df_thresholds)
                    else:
                        st.write("No threshold stats available.")

else:
    st.write(f"⚠️ No games found for {selected_date}. Try selecting another date.")
