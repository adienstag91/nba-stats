import streamlit as st
from datetime import datetime, date
import pandas as pd
import altair as alt

from modules.player import Player
from modules.team import Team
from modules.constants import *
from modules.utils import *
from modules.fetch import *

# --- UI Step 1: Search Method Selection ---
search_method = st.radio("Choose how you want to search:", ["Game Date", "Team Roster", "Player Name"])

selected_player = None
selected_date = date.today()
selected_season = get_season_year(selected_date)
selected_game = None

# --- Search Mode: Game Date ---
if search_method == "Game Date":
    selected_date = st.date_input("Select a date for games:", date.today())
    selected_season = get_season_year(selected_date)
    games = get_games_for_date(selected_date)

    if games:
        selected_game = st.selectbox("Select a game:", games, format_func=str)
        col1, col2 = st.columns([1, 1])
        with col1:
            if selected_game.away_team.logo_url:
                st.image(selected_game.away_team.logo_url, width=150, caption=selected_game.away_team.name)
        with col2:
            if selected_game.home_team.logo_url:
                st.image(selected_game.home_team.logo_url, width=150, caption=selected_game.home_team.name)

        all_players = get_all_players_in_game(selected_game)
        selected_player = st.selectbox("Select a player:", all_players, format_func=lambda x: f"{x.name} ({x.team_name})")
    else:
        st.warning(f"No games found on {selected_date}.")

# --- Search Mode: Team Roster ---
elif search_method == "Team Roster":
    selected_team = Team(st.selectbox("Select a team:", get_all_teams()), selected_season)
    if selected_team.logo_url:
        st.image(selected_team.logo_url, caption=selected_team.name, width=150)
    selected_player = st.selectbox("Select a Player", selected_team.roster, format_func=lambda x: f"{x.name}")

# --- Search Mode: Player Name ---
elif search_method == "Player Name":
    all_players = get_all_active_players(selected_season)
    search_query = st.text_input("Enter player name:")
    if search_query:
        fuzzy_player = fuzzy_match_player(search_query, all_players)
        if fuzzy_player:
            selected_player = Player(fuzzy_player.name, fuzzy_player.team_name, selected_season)
            st.write(f"### Selected Player: {selected_player.name} ({selected_player.team_name})")
        else:
            st.warning("No matching player found. Try refining your search.")

# --- Determine Game from Date (Team/Player Search) ---
if selected_player and search_method in ["Team Roster", "Player Name"]:
    selected_date = st.date_input("Select a date for games:", date.today())
    selected_season = get_season_year(selected_date)
    if selected_season != selected_player.season:
        st.info("↩️ Resetting player to correct season context.")
        selected_player = Player(selected_player.name, selected_player.team_name, selected_season)

    games = get_games_for_date(selected_date)
    if games:
        selected_game = next((g for g in games if selected_player.team_name in [g.home_team.name, g.away_team.name]), None)
        if not selected_game:
            st.warning(f"{selected_player.name} ({selected_player.team_name}) does not have a game on {selected_date}.")

# --- Stats Panel ---
if selected_player:
    stats_fetched = selected_player.fetch_stats()

    if not stats_fetched or not selected_player.stats:
        st.error("No stats found.")
        st.stop()

    st.write(f"Fetching stats for {selected_player.name} from {selected_player.stats_url}")

    DEFAULT_COLUMNS = ["game_date", "opponent", "result"]
    selectable_stats = {k: v for k, v in STAT_NAME_MAPPING.items() if k not in DEFAULT_COLUMNS}
    selected_stat_names = st.multiselect("Select Stats", list(selectable_stats.values()))
    # Convert selected names back to original column keys
    inverse_mapping = {v: k for k, v in selectable_stats.items()}
    selected_stats = [inverse_mapping[name] for name in selected_stat_names]

    stat_type_options = [
        "Last n Games",
        "Full Season Averages",
        "Stats Against This Opponent",
        "Threshold Stats"
    ]
    selected_stat_types = st.multiselect("Select stat types:", stat_type_options)

    stat_thresholds = {}
    if "Threshold Stats" in selected_stat_types:
        st.write("Enter thresholds for selected stats:")
        for stat in selected_stats:
            threshold = st.number_input(f"Threshold for {STAT_NAME_MAPPING[stat]}:", min_value=0, step=1)
            stat_thresholds[stat] = threshold

    if "Last n Games" in selected_stat_types:
        n = st.slider("n Games", min_value=1, max_value=82, value=5)

    if st.button("Generate Report"):
        st.subheader(f"📊 Stats Report for {selected_player.name}")
        if selected_player.image_url:
            st.image(selected_player.image_url, caption=selected_player.name, width=150)

        if "Last n Games" in selected_stat_types:
            last_n, avg_n = selected_player.get_last_n_games(n, selected_date)
            if last_n:
                render_table(pd.DataFrame(filter_stats(last_n, selected_stats)), f"### 📅 Last {n} Games")
                avg_df = pd.DataFrame([filter_stats(avg_n, selected_stats, is_average=True)])
                avg_df.columns = [col.replace("avg_", "") for col in avg_df.columns]
                render_table(avg_df, f"#### 🔄 Averages over last {n} games")

                df_chart = pd.DataFrame(filter_stats(last_n, selected_stats))
                df_chart_long = df_chart.melt(id_vars=["game_date", "opponent"],
                                              value_vars=selected_stats,
                                              var_name="Stat", value_name="Value")
                chart = alt.Chart(df_chart_long).mark_line(point=True).encode(
                    x=alt.X("game_date:T", title="Game Date", sort="x"),
                    y=alt.Y("Value:Q", title="Stat Value"),
                    color=alt.Color("Stat:N", legend=alt.Legend(title="Stat Type")),
                    tooltip=["game_date", "opponent", "Stat", "Value"]
                ).properties(width=700, height=400)
                st.altair_chart(chart, use_container_width=True)

        if "Full Season Averages" in selected_stat_types:
            avg_season = selected_player.get_season_averages()
            if avg_season:
                avg_df = pd.DataFrame([filter_stats(avg_season, selected_stats, is_average=True)])
                avg_df.columns = [col.replace("avg_", "") for col in avg_df.columns]
                render_table(avg_df, "### 📊 Full Season Averages")

        if "Stats Against This Opponent" in selected_stat_types and selected_game:
            opponent_team_name = (
                selected_game.away_team.name if selected_player.team_name == selected_game.home_team.name
                else selected_game.home_team.name
            )
            opponent_code = TEAM_CODES[opponent_team_name]
            stats, avg = selected_player.get_stats_against_opponent(opponent_code)
            if stats:
                render_table(pd.DataFrame(filter_stats(stats, selected_stats)), f"### 🎯 Stats Against {opponent_team_name}")
                if len(stats) > 1:
                    avg_df = pd.DataFrame([filter_stats(avg, selected_stats, is_average=True)])
                    avg_df.columns = [col.replace("avg_", "") for col in avg_df.columns]
                    render_table(avg_df, f"#### 🔄 Averages Against {opponent_team_name}")
            else:
                st.warning(f"No matching stats found for {selected_player.name} vs {opponent_team_name}.")

        if "Threshold Stats" in selected_stat_types:
            rows = []
            for stat, threshold in stat_thresholds.items():
                result = selected_player.count_exceeding_threshold(stat, threshold)
                rows.append([
                    STAT_NAME_MAPPING[stat], result[2], result[0], f"{result[3]:.2f}%",
                    result[1], f"{result[4]:.2f}%"
                ])
            if rows:
                df = pd.DataFrame(rows, columns=["Stat", "Total Games", "Exceeded", "% Exceeded", "Not Exceeded", "% Not Exceeded"])
                render_table(df, "### 📈 Threshold Stats Analysis")
            else:
                st.write("No threshold stats available.")
