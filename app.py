import streamlit as st
from datetime import datetime, date
import pandas as pd
from modules.player import Player
from modules.constants import *
from modules.utils import *
from modules.fetch import *
from modules.processing import *
import altair as alt

# 1️⃣ **Choose Search Method**
search_method = st.radio(
    "Choose how you want to search:",
    ["Game Date", "Team Roster", "Player Name"]
)

selected_player = None  # Placeholder for player selection
selected_date = None     # Placeholder for date selection
selected_game = None     # Placeholder for game selection

# 2️⃣ **Game Date Search**
if search_method == "Game Date":
    selected_date = st.date_input("Select a date for games:", date.today())

    # Get games for the selected date
    games = get_games_for_date(selected_date)
    print(f"games - {games}")

    if games:
        game_options = [f"{g['away_team']} @ {g['home_team']} at {g['game_time']}" for g in games]
        print(f"game options - {game_options}")
        selected_game_index = st.selectbox("Select a game:", range(len(game_options)), format_func=lambda x: game_options[x])
        print(f"selected_game_index - {selected_game_index}")
        selected_game = games[selected_game_index]
        print(f"selected_game - {selected_game}")

        away_team_logo = get_team_logo(selected_game['away_team'])
        home_team_logo = get_team_logo(selected_game['home_team'])

        # Create two columns for side-by-side layout
        col1, col2 = st.columns([1, 1])
        with col1:
            if away_team_logo:
                st.image(away_team_logo, width=150, caption=selected_game['away_team'])
        with col2:
            if home_team_logo:
                st.image(home_team_logo, width=150, caption=selected_game['home_team'])


        # Get players from selected game
        all_players = get_all_players_in_game(selected_game)
        selected_player = st.selectbox("Select a player:", all_players, format_func=lambda x: f"{x[0]} ({x[1]})")

    else:
        st.write(f"⚠️ No Games found on {selected_date}")

# 3️⃣ **Team Roster Search**
elif search_method == "Team Roster":
    selected_team = st.selectbox("Select a team:", get_all_teams())
    team_logo = get_team_logo(selected_team)
    if team_logo:
        st.image(team_logo, caption=selected_team, width=150)
    else:
        st.write("No image available for this team.")
    team_roster = get_team_roster(selected_team)
    #st.write("DEBUG - team_roster:", team_roster)

    if selected_team:
        selected_player = st.selectbox("Select a Player", team_roster, format_func=lambda x: x[0])

# 4️⃣ **Player Name Search**
elif search_method == "Player Name":
    all_players = get_all_active_players()  # Returns a list of (team_code, player_name, team_name)
    
    search_query = st.text_input("Enter player name:")

    if search_query:
        selected_player = fuzzy_match_player(search_query, all_players)

        if selected_player:
            st.write(f"### Selected Player: {selected_player[0]} ({selected_player[1]})")
        else:
            st.warning("No matching player found. Try refining your search.")
    else:
        selected_player = None  # Ensure selected_player is None if no query entered

# Standardize player details
if selected_player:  # Only unpack if a valid match is found
    selected_player_name, selected_player_team = selected_player
else:
    selected_player_name, selected_player_team = None, None  # Set defaults to avoid errors

if selected_player_name and search_method in ["Team Roster","Player Name"]:
    selected_date = st.date_input("Select a date for games:", date.today())

    # Fetch games for the selected date
    games = get_games_for_date(selected_date)

    # ✅ Only check for games if there's a valid player & date
    if selected_player_team and games:
        selected_game = next((game for game in games if selected_player_team in [game["home_team"], game["away_team"]]), None)

        if not selected_game:
            st.warning(f"{selected_player_name} ({selected_player_team}) does not have a game on {selected_date}.")
# 5️⃣ **Proceed to Stats Selection**
if selected_player:
    player = Player(selected_player_name, selected_player_team, selected_date.year)

    if not player.profile_url:
        st.error("❌ Player not found.")
        st.stop()

    if not player.fetch_stats():
        st.error("❌ Failed to fetch player stats.")
        st.stop()

    # Check if we have stats data
    if player.stats is None:
        st.error("❌ No stats found for this player.")
        st.stop()

    st.write(f"Fetching stats for {selected_player_name} from {player.stats_url}")

    #st.write(f"📊 Player stats: {stats}")  # Debugging

    if player.stats:
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
            n = st.slider("n Games", min_value=1, max_value=82, value=5)

        # 7️⃣ **Generate Stats Report**
        if st.button("Generate Report"):
            st.subheader(f"📊 Stats Report for {selected_player_name}")

            if player.image_url:
                st.image(player.image_url, caption=selected_player_name, width=150)
            else:
                st.write("No image available for this player.")

            # **Last 5 Games**
            if "Last n Games" in selected_stat_types:
                last_n_games, avg_over_last_n_games = player.get_last_n_games(n, selected_date)
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
                    # Convert filtered_last_n_games to DataFrame
                    df_chart = pd.DataFrame(filtered_last_n_games)

                    # Melt the DataFrame to a long format for Altair
                    df_chart_long = df_chart.melt(id_vars=["game_date", "opponent"], 
                                                  value_vars=selected_stats, 
                                                  var_name="Stat", 
                                                  value_name="Value")

                    # Create a line chart for each stat
                    chart = alt.Chart(df_chart_long).mark_line(point=True).encode(
                        x=alt.X("game_date:T", title="Game Date", sort="x"),
                        y=alt.Y("Value:Q", title="Stat Value"),
                        color=alt.Color("Stat:N", legend=alt.Legend(title="Stat Type")),
                        tooltip=["game_date", "opponent", "Stat", "Value"]
                    ).properties(width=700, height=400)

                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.write("No matching stats found for Last 5 Games.")

                # **Averages over last 5 games**
                filtered_avg_stats = filter_stats(avg_over_last_n_games, selected_stats, is_average=True)
                df_avg_stats = pd.DataFrame([filtered_avg_stats])
                # Format numeric values to 1 decimal place
                df_avg_stats = df_avg_stats.astype(str).apply(lambda col: col.str.format("{:.1f}") if col.dtype == "float64" else col)

                # Remove 'avg_' prefix from column names
                df_avg_stats.columns = [col.replace("avg_", "") for col in df_avg_stats.columns]

                # Rename columns using the rename_columns function
                df_avg_stats = rename_columns(df_avg_stats)

                st.write(f"#### 🔄 Averages over last {n} games")
                st.table(df_avg_stats)

            # **Full Season Averages**
            if "Full Season Averages" in selected_stat_types:
                season_avg_stats = player.get_season_averages()
                if season_avg_stats:
                    filtered_season_avg_stats = filter_stats(season_avg_stats, selected_stats, is_average=True)

                    df_season_avg_stats = pd.DataFrame([filtered_season_avg_stats])

                    # Convert to DataFrame, remove "avg_", and rename columns
                    df_season_avg_stats = pd.DataFrame([filtered_season_avg_stats])
                    df_season_avg_stats.columns = [col.replace("avg_", "") for col in df_season_avg_stats.columns]
                    df_season_avg_stats = rename_columns(df_season_avg_stats)

                    # Format numeric values to 1 decimal place
                    df_season_avg_stats = df_season_avg_stats.astype(str).apply(lambda col: col.str.format("{:.1f}") if col.dtype == "float64" else col)

                    st.write("### 📊 Full Season Averages")
                    st.table(df_season_avg_stats)
                else:
                    st.write("No data available for full season.")

            # **Stats Against This Opponent**
            if "Stats Against This Opponent" in selected_stat_types:
                if selected_game:
                    if selected_player_team == selected_game['home_team']:
                        opponent_team_name = selected_game['away_team']
                    elif player_team == selected_game['away_team']:
                        selected_opponent_team_name = selected_game['home_team']
                    else:
                        print(f"Player {player_name} not found in either team's roster.")
                    
                    opponent_team_code = TEAM_CODES[opponent_team_name]
                    opponent_stats, avg_opponent_stats = player.get_stats_against_opponent(opponent_team_code)
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

                        st.write(f"### 🎯 Stats Against {opponent_team_name}")
                        st.table(df_opponent_stats)
                        if len(opponent_stats) > 1:
                            filtered_avg_opponent_stats = filter_stats(avg_opponent_stats, selected_stats, is_average=True)


                            # Convert to DataFrame, remove "avg_", and rename columns
                            df_avg_opponent_stats = pd.DataFrame([filtered_avg_opponent_stats])
                            df_avg_opponent_stats.columns = [col.replace("avg_", "") for col in df_avg_opponent_stats.columns]
                            df_avg_opponent_stats = rename_columns(df_avg_opponent_stats)

                            # Format numeric values to 1 decimal place
                            df_avg_opponent_stats = df_avg_opponent_stats.astype(str).apply(lambda col: col.str.format("{:.1f}") if col.dtype == "float64" else col)

                            st.write(f"#### 🔄 Averages Against {opponent_team_name}")
                            st.table(df_avg_opponent_stats)
                    else:
                        st.warning(f"No matching stats found for {selected_player_name} against {opponent_team_name}.")
                else:
                    st.warning(f"{selected_player_name} ({selected_player_team}) does not have a game on {selected_date}.")

            # **Threshold Stats**
            if "Threshold Stats" in selected_stat_types:
                threshold_results = []
                for stat, threshold in stat_thresholds.items():
                    result = player.count_exceeding_threshold(stat, threshold)
                    count_exceeded, count_not_exceeded, total_games, percentage_exceeded, percentage_not_exceeded = result

                    threshold_results.append([
                        STAT_NAME_MAPPING[stat], total_games, count_exceeded, f"{percentage_exceeded:.2f}%", 
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
