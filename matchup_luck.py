#!/usr/bin/env python3
"""
ESPN Fantaasy Bastketball League Matchup Luck Calculator

Calculates how teams would have fared against all matchups each week instead of just the one they were in.

Author: Daniel Grzelak (@dagrz)
"""

import argparse
import requests
from typing import Optional, Tuple, Dict, Union
from urllib.parse import urlparse, parse_qs
from colorama import init, Fore, Style
import os
import json
from datetime import datetime
from tabulate import tabulate

# Initialize colorama
init()

DEFAULT_LEAGUE_ID = "2803"
DEFAULT_SEASON = "2025"

def print_info(msg: str):
    """Print an information message in blue"""
    print(f"{Fore.BLUE}[i] {msg}{Style.RESET_ALL}")

def print_error(msg: str):
    """Print an error message in red"""
    print(f"{Fore.RED}[!] {msg}{Style.RESET_ALL}")

def print_success(msg: str):
    """Print a success message in green"""
    print(f"{Fore.GREEN}[✓] {msg}{Style.RESET_ALL}")

def print_failure(msg: str):
    """Print a failure message in yellow"""
    print(f"{Fore.YELLOW}[x] {msg}{Style.RESET_ALL}")

def parse_espn_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse ESPN fantasy basketball URL to extract league ID."""
    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        league_id = query.get('leagueId', [None])[0]
        return league_id, None
    except Exception:
        return None, None

def get_user_input(league_id: Optional[str] = None, season: Optional[str] = None) -> Tuple[str, str]:
    """Prompt user for league ID and season if not found in URL."""
    if not league_id:
        print_info(f"Enter league ID (default: {DEFAULT_LEAGUE_ID})")
        league_id = input(f"{Fore.CYAN}> {Style.RESET_ALL}").strip()
        if not league_id:
            league_id = DEFAULT_LEAGUE_ID
        while not league_id.isdigit():
            print_error("League ID must be a number.")
            league_id = input(f"{Fore.CYAN}> {Style.RESET_ALL}").strip()
            if not league_id:
                league_id = DEFAULT_LEAGUE_ID
    
    if not season:
        print_info(f"Enter season year (default: {DEFAULT_SEASON})")
        season = input(f"{Fore.CYAN}> {Style.RESET_ALL}").strip()
        if not season:
            season = DEFAULT_SEASON
        while not season.isdigit() or len(season) != 4:
            print_error("Season must be a 4-digit year.")
            season = input(f"{Fore.CYAN}> {Style.RESET_ALL}").strip()
            if not season:
                season = DEFAULT_SEASON
    
    return league_id, season

def build_api_url(league_id: str, season: str) -> str:
    """Build the ESPN Fantasy Basketball API URL."""
    return (
        f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba/seasons/{season}"
        f"/segments/0/leagues/{league_id}?view=modular&view=mNav&view=mMatchupScore"
        f"&view=mScoreboard&view=mSettings&view=mTeam"
    )

def fetch_league_data(api_url: str) -> dict:
    """Fetch data from ESPN Fantasy API."""
    try:
        print_info("Making API request...")
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print_error(f"Error fetching data: {e}")
        raise

def process_league_data(raw_data: dict) -> Tuple[str, Dict[int, str], Dict[int, str]]:
    """Process raw API data into organized structures."""
    # Extract league name
    league_name = raw_data.get('settings', {}).get('name', 'Unknown League')
    
    # Process team mappings
    team_mappings = {}
    for team in raw_data.get('teams', []):
        team_mappings[team['id']] = team.get('abbrev', f"Team {team['id']}")

    # Define comprehensive stat mappings based on ESPN's internal mappings
    stat_mappings = {
        0: "PTS",    # Points
        1: "BLK",    # Blocks
        2: "STL",    # Steals
        3: "AST",    # Assists
        4: "OREB",   # Offensive Rebounds
        5: "DREB",   # Defensive Rebounds
        6: "REB",    # Rebounds
        7: "EJ",     # Ejections
        8: "FF",     # Flagrant Fouls
        9: "PF",     # Personal Fouls
        10: "TF",    # Technical Fouls
        11: "TO",    # Turnovers
        12: "DQ",    # Disqualifications
        13: "FGM",   # Field Goals Made
        14: "FGA",   # Field Goals Attempted
        15: "FTM",   # Free Throws Made
        16: "FTA",   # Free Throws Attempted
        17: "3PM",   # Three Pointers Made
        18: "3PA",   # Three Pointers Attempted
        19: "FG%",   # Field Goal Percentage
        20: "FT%",   # Free Throw Percentage
        21: "3P%",   # Three Point Percentage
        22: "AFG%",  # Adjusted Field Goal Percentage
        23: "FGMI",  # Field Goals Missed
        24: "FTMI",  # Free Throws Missed
        25: "3PMI",  # Three Pointers Missed
        26: "AST",   # Assists Per Game
        27: "BLK",   # Blocks Per Game
        28: "MIN",   # Minutes Per Game
        29: "PTS",   # Points Per Game
        30: "REB",   # Rebounds Per Game
        31: "STL",   # Steals Per Game
        32: "TO",    # Turnovers Per Game
        33: "3PM",   # Three Pointers Per Game
        34: "PPM",   # Points Per Minute
        35: "A/TO",  # Assists To Turnover Ratio
        36: "STR",   # Steals To Turnover Ratio
        37: "DD",    # Double Doubles
        38: "TD",    # Triple Doubles
        39: "QD",    # Quadruple Doubles
        40: "MIN",   # Minutes
        41: "GS",    # Games Started
        42: "GP",    # Games Played
        43: "TW",    # Team Wins
    }

    # Get active stat categories from league settings
    scoring_items = raw_data.get('settings', {}).get('scoringSettings', {}).get('scoringItems', [])
    active_stat_ids = {item.get('statId') for item in scoring_items if item.get('statId') is not None}
    
    active_stat_mappings = {
        stat_id: stat_mappings[stat_id] 
        for stat_id in active_stat_ids 
        if stat_id in stat_mappings
    }

    return league_name, team_mappings, active_stat_mappings

def print_mappings(team_mappings: Dict[int, str], stat_mappings: Dict[int, str]):
    """Print team and stat mappings on single lines."""
    # Print team mappings
    team_str = ", ".join([f"{team_id}:{name}" for team_id, name in sorted(team_mappings.items())])
    print_info(team_str)

    # Print stat mappings
    stat_str = ", ".join([f"{stat_id}:{name}" for stat_id, name in sorted(stat_mappings.items())])
    print_info(stat_str)

def process_matchup_data(raw_data: dict, team_mappings: Dict[int, str], stat_mappings: Dict[int, str]) -> Dict[int, Dict[str, Dict[str, Dict[str, float]]]]:
    """
    Process matchup data to get scores and results by week and team.
    """
    matchup_data = {}
    schedule = raw_data.get('schedule', [])
    
    for matchup in schedule:
        week = matchup.get('matchupPeriodId')
        
        # Skip if no matchup period or if it's a future matchup
        if not week or not matchup.get('winner', '').strip():
            continue
            
        if week not in matchup_data:
            matchup_data[week] = {}
            
        home = matchup.get('home', {})
        away = matchup.get('away', {})
        
        if not home or not away:  # Skip bye weeks
            continue
            
        home_id = home.get('teamId')
        away_id = away.get('teamId')
        
        if home_id not in team_mappings or away_id not in team_mappings:
            continue
            
        home_name = team_mappings[home_id]
        away_name = team_mappings[away_id]
        
        # Get stats for both teams from scoreByStat with defensive programming
        home_score_by_stat = home.get('cumulativeScore', {}).get('scoreByStat') or {}
        away_score_by_stat = away.get('cumulativeScore', {}).get('scoreByStat') or {}
        
        # Convert stat IDs to stat names and create score dictionaries
        home_scores = {stat_mappings[int(k)]: float(v.get('score', 0)) 
                      for k, v in home_score_by_stat.items() 
                      if int(k) in stat_mappings}
        away_scores = {stat_mappings[int(k)]: float(v.get('score', 0)) 
                      for k, v in away_score_by_stat.items() 
                      if int(k) in stat_mappings}
        
        # Get results directly from the API response
        home_results = {stat_mappings[int(k)]: 1.0 if v.get('result') == 'WIN' else 0.5 if v.get('result') == 'TIE' else 0.0
                       for k, v in home_score_by_stat.items() 
                       if int(k) in stat_mappings}
        away_results = {stat_mappings[int(k)]: 1.0 if v.get('result') == 'WIN' else 0.5 if v.get('result') == 'TIE' else 0.0
                       for k, v in away_score_by_stat.items() 
                       if int(k) in stat_mappings}
        
        # Store home team data
        if home_id:
            matchup_data[week][home_name] = {
                'scores': home_scores,
                'results': home_results
            }
            
        # Store away team data
        if away_id:
            matchup_data[week][away_name] = {
                'scores': away_scores,
                'results': away_results
            }
    
    print(matchup_data)
    return matchup_data

def get_cached_data(league_id: str, season: str) -> Optional[dict]:
    """Try to load cached data from local file."""
    data_dir = "data"
    # List all files in data directory
    if not os.path.exists(data_dir):
        return None
        
    files = os.listdir(data_dir)
    # Find most recent matching file
    matching_files = [f for f in files if f.endswith(f"_{league_id}_{season}_scoreboard.json")]
    if not matching_files:
        return None
        
    latest_file = max(matching_files)  # Get most recent file
    file_path = os.path.join(data_dir, latest_file)
    
    try:
        with open(file_path, 'r') as f:
            print_success(f"Loading cached data from {file_path}")
            return json.load(f)
    except Exception as e:
        print_error(f"Error loading cached data: {e}")
        return None

def save_data(data: dict, league_id: str, season: str):
    """Save data to local JSON file with pretty printing."""
    data_dir = "data"
    # Create data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    # Create filename with ISO date
    iso_date = datetime.now().strftime("%Y-%m-%d")
    filename = f"{iso_date}_{league_id}_{season}_scoreboard.json"
    file_path = os.path.join(data_dir, filename)
    
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)
        print_success(f"Saved data to {file_path}")
    except Exception as e:
        print_error(f"Error saving data: {e}")

def calculate_weekly_expected_results(matchup_data: dict) -> dict:
    """
    Calculate how each team would have fared against all other teams that week.
    Adds an 'expected_results' field showing the average result if they had played everyone.
    """
    enhanced_data = matchup_data.copy()
    
    for week, week_data in matchup_data.items():
        teams = list(week_data.keys())
        
        # For each team
        for team in teams:
            team_scores = week_data[team]['scores']
            expected_results = {}
            
            # For each stat
            for stat in team_scores.keys():
                team_score = team_scores[stat]
                stat_results = []
                
                # Compare against all other teams
                for opponent in teams:
                    if opponent != team:
                        opp_score = week_data[opponent]['scores'][stat]
                        # Calculate result (1.0 for win, 0.5 for tie, 0.0 for loss)
                        if team_score > opp_score:
                            stat_results.append(1.0)
                        elif team_score < opp_score:
                            stat_results.append(0.0)
                        else:
                            stat_results.append(0.5)
                
                # Calculate average result for this stat
                expected_results[stat] = sum(stat_results) / len(stat_results)
            
            # Add expected_results to the structure
            enhanced_data[week][team]['expected_results'] = expected_results
    
    return enhanced_data

def find_extreme_matchups(enhanced_data: dict) -> tuple:
    """
    Find both the luckiest and unluckiest performances.
    Returns (lucky_details, unlucky_details) where each is (week, team, luck_score)
    Used to highlight these cells in the table.
    """
    most_lucky = float('-inf')
    most_unlucky = float('inf')
    luckiest_matchup = None
    unluckiest_matchup = None
    
    for week in enhanced_data:
        for team, team_data in enhanced_data[week].items():
            if not (team_data.get('results') and team_data.get('expected_results')):
                continue
                
            actual = sum(team_data['results'].values()) / len(team_data['results'])
            expected = sum(team_data['expected_results'].values()) / len(team_data['expected_results'])
            luck = actual - expected
            
            if luck > most_lucky:
                most_lucky = luck
                luckiest_matchup = (week, team, luck)
                
            if luck < most_unlucky:
                most_unlucky = luck
                unluckiest_matchup = (week, team, luck)
    
    return luckiest_matchup, unluckiest_matchup

def create_luck_table(enhanced_data: dict) -> None:
    """
    Create a table showing luck factors (actual - expected) for all teams across all weeks.
    Highlights the most lucky (green) and unlucky (red) performances.
    """
    # Get extreme values for highlighting
    luckiest, unluckiest = find_extreme_matchups(enhanced_data)
    
    # Get all weeks and filter out weeks with no data
    active_weeks = []
    for week in sorted(enhanced_data.keys()):
        if any(team_data.get('results') and team_data.get('expected_results')
               for team_data in enhanced_data[week].values()):
            active_weeks.append(week)
    
    # Initialize table data
    table_data = []
    
    # Get all unique teams and their season luck for sorting
    team_luck = {}
    for team in sorted(set(team for week_data in enhanced_data.values() for team in week_data.keys())):
        season_total = 0
        season_count = 0
        
        for week in active_weeks:
            if team in enhanced_data[week]:
                week_data = enhanced_data[week][team]
                
                if (week_data.get('results') and week_data.get('expected_results') and 
                    len(week_data['results']) > 0 and len(week_data['expected_results']) > 0):
                    
                    actual_avg = sum(week_data['results'].values()) / len(week_data['results'])
                    expected_avg = sum(week_data['expected_results'].values()) / len(week_data['expected_results'])
                    luck = actual_avg - expected_avg
                    
                    season_total += luck
                    season_count += 1
        
        if season_count > 0:
            team_luck[team] = season_total / season_count
    
    # Sort teams by season luck
    sorted_teams = sorted(team_luck.keys(), key=lambda x: team_luck[x], reverse=True)
    
    # Create headers
    headers = ['Team', 'Season']
    headers.extend([f'Week {w}' for w in active_weeks])
    
    # Create table data in sorted order
    for team in sorted_teams:
        # Initialize row with team name
        row = [team]
        
        # Add season average luck
        row.append(f"{team_luck[team]:.3f}")
        
        # Calculate weekly luck values
        for week in active_weeks:
            if team in enhanced_data[week]:
                week_data = enhanced_data[week][team]
                
                if (week_data.get('results') and week_data.get('expected_results') and 
                    len(week_data['results']) > 0 and len(week_data['expected_results']) > 0):
                    
                    actual_avg = sum(week_data['results'].values()) / len(week_data['results'])
                    expected_avg = sum(week_data['expected_results'].values()) / len(week_data['expected_results'])
                    luck = actual_avg - expected_avg
                    
                    # Highlight extreme values
                    if luckiest and week == luckiest[0] and team == luckiest[1]:
                        row.append(f"{Fore.GREEN}{luck:.3f}{Style.RESET_ALL}")
                    elif unluckiest and week == unluckiest[0] and team == unluckiest[1]:
                        row.append(f"{Fore.RED}{luck:.3f}{Style.RESET_ALL}")
                    else:
                        row.append(f"{luck:.3f}")
                else:
                    row.append("-")
            else:
                row.append("-")
        
        table_data.append(row)
    
    # Print the table
    print("\nTeam Luck (Actual - Expected) by Week:")
    print("Positive values = Lucky (performed better than expected)")
    print("Negative values = Unlucky (performed worse than expected)")
    print(tabulate(table_data, headers=headers, tablefmt='pipe', floatfmt='.3f'))

def save_output_txt(enhanced_data: dict, league_id: str, season: str, luckiest: tuple, unluckiest: tuple, active_weeks: list, table_data: list, headers: list) -> str:
    """Save output in text format"""
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    iso_date = datetime.now().strftime("%Y-%m-%d")
    txt_filename = os.path.join(output_dir, f"{iso_date}_{league_id}_{season}_luck.txt")
    
    with open(txt_filename, 'w') as f:
        f.write("Team Luck (Actual - Expected) by Week:\n")
        f.write("Positive values = Lucky (performed better than expected)\n")
        f.write("Negative values = Unlucky (performed worse than expected)\n\n")
        f.write(tabulate(table_data, headers=headers, tablefmt='pipe', floatfmt='.3f'))
        
        if luckiest:
            week, team, luck = luckiest
            f.write(f"\n\nMost Lucky Result:\n")
            f.write(f"Week {week}: {team}\n")
            f.write(f"Luck Score: {luck:.3f}\n")
            
        if unluckiest:
            week, team, luck = unluckiest
            f.write(f"\nMost Unlucky Result:\n")
            f.write(f"Week {week}: {team}\n")
            f.write(f"Luck Score: {luck:.3f}\n")
    
    return txt_filename

def save_output_html(enhanced_data: dict, league_id: str, season: str, luckiest: tuple, unluckiest: tuple, active_weeks: list, table_data: list, headers: list) -> str:
    """Save output in HTML format with styling"""
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    iso_date = datetime.now().strftime("%Y-%m-%d")
    html_filename = os.path.join(output_dir, f"{iso_date}_{league_id}_{season}_luck.html")
    
    with open(html_filename, 'w') as f:
        # Write HTML header with styling
        f.write("""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: right; }
                th { background-color: #f5f5f5; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .lucky { color: green; font-weight: bold; }
                .unlucky { color: red; font-weight: bold; }
                .summary { margin: 20px 0; }
            </style>
        </head>
        <body>
        """)
        
        f.write("<h1>Team Luck Analysis</h1>")
        f.write("<p>Positive values = Lucky (performed better than expected)<br>")
        f.write("Negative values = Unlucky (performed worse than expected)</p>")
        
        # Convert table to HTML with highlighting
        html_table = "<table>\n<tr>"
        for header in headers:
            html_table += f"<th>{header}</th>"
        html_table += "</tr>\n"
        
        for row in table_data:
            html_table += "<tr>"
            for i, cell in enumerate(row):
                cell_class = ""
                if luckiest and i > 1 and cell != "-":  # Skip team name and season columns
                    week = active_weeks[i-2]  # Adjust index for week number
                    if week == luckiest[0] and row[0] == luckiest[1]:
                        cell_class = " class='lucky'"
                if unluckiest and i > 1 and cell != "-":
                    week = active_weeks[i-2]
                    if week == unluckiest[0] and row[0] == unluckiest[1]:
                        cell_class = " class='unlucky'"
                html_table += f"<td{cell_class}>{cell}</td>"
            html_table += "</tr>\n"
        
        html_table += "</table>"
        f.write(html_table)
        
        # Add summary section
        if luckiest or unluckiest:
            f.write("<div class='summary'>")
            if luckiest:
                week, team, luck = luckiest
                f.write(f"<p><strong>Most Lucky Result:</strong><br>")
                f.write(f"Week {week}: {team}<br>")
                f.write(f"Luck Score: {luck:.3f}</p>")
            
            if unluckiest:
                week, team, luck = unluckiest
                f.write(f"<p><strong>Most Unlucky Result:</strong><br>")
                f.write(f"Week {week}: {team}<br>")
                f.write(f"Luck Score: {luck:.3f}</p>")
            f.write("</div>")
        
        f.write("</body></html>")
    
    return html_filename

def save_output(enhanced_data: dict, league_id: str, season: str, luckiest: tuple, unluckiest: tuple) -> None:
    """Prepare data and save in both formats"""
    # Get active weeks
    active_weeks = []
    for week in sorted(enhanced_data.keys()):
        if any(team_data.get('results') and team_data.get('expected_results')
               for team_data in enhanced_data[week].values()):
            active_weeks.append(week)
    
    # Create headers
    headers = ['Team', 'Season']
    headers.extend([f'Week {w}' for w in active_weeks])
    
    # Prepare table data
    table_data = []
    team_luck = {}
    
    for team in sorted(set(team for week_data in enhanced_data.values() for team in week_data.keys())):
        season_total = 0
        season_count = 0
        row_data = [team]
        
        for week in active_weeks:
            if team in enhanced_data[week]:
                week_data = enhanced_data[week][team]
                
                if (week_data.get('results') and week_data.get('expected_results') and 
                    len(week_data['results']) > 0 and len(week_data['expected_results']) > 0):
                    
                    actual_avg = sum(week_data['results'].values()) / len(week_data['results'])
                    expected_avg = sum(week_data['expected_results'].values()) / len(week_data['expected_results'])
                    luck = actual_avg - expected_avg
                    
                    season_total += luck
                    season_count += 1
        
        if season_count > 0:
            season_avg = season_total / season_count
            team_luck[team] = season_avg
            row_data.append(f"{season_avg:.3f}")
            
            # Add weekly values
            for week in active_weeks:
                if team in enhanced_data[week]:
                    week_data = enhanced_data[week][team]
                    
                    if (week_data.get('results') and week_data.get('expected_results') and 
                        len(week_data['results']) > 0 and len(week_data['expected_results']) > 0):
                        
                        actual_avg = sum(week_data['results'].values()) / len(week_data['results'])
                        expected_avg = sum(week_data['expected_results'].values()) / len(week_data['expected_results'])
                        luck = actual_avg - expected_avg
                        row_data.append(f"{luck:.3f}")
                    else:
                        row_data.append("-")
                else:
                    row_data.append("-")
            
            table_data.append(row_data)
    
    # Sort table data by season luck
    table_data.sort(key=lambda x: float(x[1]) if x[1] != "-" else float('-inf'), reverse=True)
    
    # Save both formats
    txt_file = save_output_txt(enhanced_data, league_id, season, luckiest, unluckiest, active_weeks, table_data, headers)
    html_file = save_output_html(enhanced_data, league_id, season, luckiest, unluckiest, active_weeks, table_data, headers)
    
    print_success(f"\nOutput saved to:")
    print_success(f"Text: {txt_file}")
    print_success(f"HTML: {html_file}")

def main():
    parser = argparse.ArgumentParser(description='Calculate matchup luck in fantasy basketball')
    parser.add_argument('--url', type=str, help='ESPN Fantasy Basketball league URL')
    args = parser.parse_args()
    
    try:
        # Get league ID and season
        league_id = None
        season = None
        
        if args.url:
            print_info(f"Parsing URL: {args.url}")
            league_id, season = parse_espn_url(args.url)
            if league_id:
                print_success(f"Found league ID: {league_id}")
            else:
                print_failure("Could not extract league ID from URL")
        
        league_id, season = get_user_input(league_id, season)
        
        # Try to load cached data first
        raw_data = get_cached_data(league_id, season)
        
        # If no cached data, fetch from API and save
        if raw_data is None:
            print_info("No cached data found, fetching from API...")
            api_url = build_api_url(league_id, season)
            raw_data = fetch_league_data(api_url)
            save_data(raw_data, league_id, season)
        
        # Process data
        league_name, team_mappings, stat_mappings = process_league_data(raw_data)
        matchup_data = process_matchup_data(raw_data, team_mappings, stat_mappings)
        
        # Calculate luck factors
        enhanced_data = calculate_weekly_expected_results(matchup_data)
        
        # Print mappings
        print_mappings(team_mappings, stat_mappings)
        
        # Create and display the luck table
        create_luck_table(enhanced_data)
        
        # Save output
        luckiest, unluckiest = find_extreme_matchups(enhanced_data)
        save_output(enhanced_data, league_id, season, luckiest, unluckiest)
        
    except Exception as e:
        print_error(f"An error occurred: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 