import streamlit as st
import pandas as pd
import io

@st.cache_data
def load_preloaded_data():
    """Load preloaded Big 5 data from CSV file"""
    try:
        import os
        
        # Try different file paths (like the working version)
        possible_paths = ['big5_data.csv', './big5_data.csv', 'data/big5_data.csv']
        
        df = None
        successful_path = None
        
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    # Read the entire file as text first to analyze structure
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Find the header row (contains Player, Age, Pos, etc.)
                    header_line_idx = None
                    for i, line in enumerate(lines):
                        if 'Player' in line and 'Age' in line and 'Pos' in line:
                            header_line_idx = i
                            break
                    
                    if header_line_idx is not None:
                        # Read CSV starting from the header line
                        df = pd.read_csv(path, skiprows=header_line_idx)
                    else:
                        # Fallback: try to read normally and fix manually
                        df = pd.read_csv(path, header=None)
                        # Look for the row with proper column names
                        for idx in range(min(10, len(df))):
                            row_values = df.iloc[idx].astype(str).tolist()
                            if 'Player' in row_values and 'Age' in row_values:
                                # Set this row as column names
                                df.columns = df.iloc[idx]
                                # Remove rows up to and including the header row
                                df = df.iloc[idx+1:].reset_index(drop=True)
                                break
                        else:
                            continue  # Try next path if this doesn't work
                    
                    successful_path = path
                    break
                    
            except Exception as e:
                continue  # Try next path if this fails
        
        if df is None:
            # If we get here, none of the paths worked
            st.error("❌ Could not find or load big5_data.csv")
            st.info("💡 Please uncheck 'Use preloaded data' and upload your CSV manually")
            return pd.DataFrame()
        
        # Clean the data (same as working version)
        # Remove any rows that are just headers repeated
        if 'Player' in df.columns:
            df = df[df['Player'] != 'Player']
            df = df[df['Player'].notna()]
        
        # Convert numeric columns
        numeric_cols = ['Age', '90s']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Look for progressive distance column (might have different name)
        prgdist_candidates = [col for col in df.columns if 'prg' in col.lower() or 'prog' in col.lower()]
        if prgdist_candidates:
            # Use the first one and rename it
            df['PrgDist'] = pd.to_numeric(df[prgdist_candidates[0]], errors='coerce')
        else:
            st.error("❌ No progressive distance column found")
            return pd.DataFrame()
        
        # Handle league information
        if 'Comp' in df.columns:
            df['League'] = df['Comp']
        elif 'Squad' in df.columns:
            df['League'] = df['Squad'].apply(infer_league_from_squad)
        else:
            df['League'] = 'Unknown'
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading preloaded data: {e}")
        return pd.DataFrame()

def infer_league_from_squad(squad_name):
    """Infer league from squad name"""
    if pd.isna(squad_name):
        return 'Unknown'
    
    squad = str(squad_name).strip()
    
    # Premier League teams
    pl_teams = ['Arsenal', 'Chelsea', 'Liverpool', 'Manchester City', 'Manchester Utd', 
               'Tottenham', 'Newcastle Utd', 'Brighton', 'Aston Villa', 'West Ham',
               'Crystal Palace', 'Fulham', 'Wolves', 'Everton', 'Brentford',
               'Nott\'ham Forest', 'Sheffield Utd', 'Burnley', 'Luton Town', 'Bournemouth']
    
    # La Liga teams
    laliga_teams = ['Real Madrid', 'Barcelona', 'Atlético Madrid', 'Sevilla', 'Real Sociedad',
                   'Betis', 'Villarreal', 'Valencia', 'Athletic Club', 'Espanyol',
                   'Getafe', 'Osasuna', 'Celta Vigo', 'Mallorca', 'Cádiz']
    
    # Bundesliga teams  
    bundesliga_teams = ['Bayern Munich', 'Dortmund', 'RB Leipzig', 'Union Berlin', 'Freiburg',
                       'Bayer Leverkusen', 'Eintracht Frankfurt', 'Wolfsburg', 'Mainz 05',
                       'Borussia Mönchengladbach', 'Köln', 'Augsburg', 'Werder Bremen',
                       'Schalke 04', 'Hoffenheim', 'VfB Stuttgart', 'Hertha BSC']
    
    # Serie A teams
    seria_teams = ['Juventus', 'Inter', 'AC Milan', 'Napoli', 'Lazio', 'Roma', 'Atalanta',
                  'Fiorentina', 'Torino', 'Sassuolo', 'Udinese', 'Bologna', 'Empoli',
                  'Monza', 'Lecce', 'Cagliari', 'Genoa', 'Frosinone', 'Salernitana', 'Verona']
    
    # Ligue 1 teams
    ligue1_teams = ['Paris S-G', 'Marseille', 'Monaco', 'Lille', 'Rennes', 'Nice', 'Lyon',
                   'Montpellier', 'Lens', 'Strasbourg', 'Nantes', 'Reims', 'Toulouse',
                   'Lorient', 'Le Havre', 'Metz', 'Brest', 'Clermont Foot']
    
    if squad in pl_teams:
        return 'Premier League'
    elif squad in laliga_teams:
        return 'La Liga'
    elif squad in bundesliga_teams:
        return 'Bundesliga'
    elif squad in seria_teams:
        return 'Serie A'
    elif squad in ligue1_teams:
        return 'Ligue 1'
    else:
        return 'Unknown'

def process_fbref_progressive_data(uploaded_file):
    """Process FBRef Progressive Passing CSV with specific format"""
    try:
        # Read the file content
        file_content = uploaded_file.read().decode('utf-8')
        
        # Split into lines and find the header row (line with Player, Age, Pos, etc.)
        lines = file_content.split('\n')
        header_line_idx = None
        
        for i, line in enumerate(lines):
            if 'Player' in line and 'Age' in line and 'Pos' in line and '90s' in line and 'PrgDist' in line:
                header_line_idx = i
                break
        
        if header_line_idx is None:
            st.error("❌ Could not find the header row with required columns")
            return pd.DataFrame()
        
        # Join lines from header onwards
        data_content = '\n'.join(lines[header_line_idx:])
        
        # Parse the CSV
        df = pd.read_csv(io.StringIO(data_content))
        
        # Clean up the rank column (it often has extra characters)
        rank_col = df.columns[0]  # First column is usually rank
        
        # Remove any rows that are not actual player data
        df = df[df['Player'].notna()]
        df = df[df['Player'] != 'Player']
        df = df[df['Player'] != 'Matches']
        
        # Convert numeric columns
        numeric_cols = ['Age', '90s', 'PrgDist', 'PrgP']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # For Big 5 combined data, try to extract league info from squad names or add a generic league column
        if 'Comp' in df.columns:
            # If there's a competition column, use that as league
            df['League'] = df['Comp']
        elif 'Squad' in df.columns:
            # Try to infer league from well-known squad names
            df['League'] = df['Squad'].apply(infer_league_from_squad)
        else:
            # Default league column
            df['League'] = 'Unknown'
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
        return pd.DataFrame()

def filter_and_analyze(df, min_90s=13, max_age=25):
    """Filter for U-25 midfielders with minimum 90s and sort by PrgDist"""
    
    if df.empty:
        return pd.DataFrame()
    
    # Check each required column and filter step by step
    if 'Age' not in df.columns:
        st.error("❌ Age column not found in dataset")
        return pd.DataFrame()
    
    if '90s' not in df.columns:
        st.error("❌ 90s column not found in dataset")
        return pd.DataFrame()
        
    if 'Pos' not in df.columns:
        st.error("❌ Position column not found in dataset")
        return pd.DataFrame()
        
    if 'PrgDist' not in df.columns:
        st.error("❌ Progressive Distance column not found in dataset")
        return pd.DataFrame()
    
    # Apply filters
    filtered_df = df[
        (df['Age'] <= max_age) &  # U-25 players (25 and under)
        (df['90s'] >= min_90s) &  # At least specified 90s
        (df['Pos'].str.startswith('MF', na=False)) &  # Primary position is MF
        (df['PrgDist'].notna()) &  # Has progressive distance data
        (df['PrgDist'] > 0)  # Valid progressive distance
    ].copy()
    
    if filtered_df.empty:
        st.warning("⚠️ No players match the criteria")
        return pd.DataFrame()
    
    # Sort by Progressive Distance (highest first)
    filtered_df = filtered_df.sort_values('PrgDist', ascending=False)
    
    # Add ranking
    filtered_df['Rank'] = range(1, len(filtered_df) + 1)
    
    return filtered_df

def main():
    st.title("🎯 U-25 Midfielders: Progressive Distance Leaders")
    st.markdown("*Analyze young midfielders by progressive distance across Europe's Big 5 leagues*")
    
    # Sidebar for settings
    st.sidebar.header("⚙️ Analysis Settings")
    
    # Data source selection
    st.sidebar.subheader("📊 Data Source")
    use_preloaded_data = st.sidebar.checkbox(
        "Use preloaded Big 5 data", 
        value=True,
        help="Toggle off to upload your own data instead"
    )
    
    # Filter settings in sidebar
    min_90s = st.sidebar.slider(
        "Minimum 90s played", 
        min_value=5, 
        max_value=40, 
        value=13, 
        help="13 90s = approximately 1170 minutes"
    )
    
    max_age = st.sidebar.slider(
        "Maximum age", 
        min_value=18, 
        max_value=25, 
        value=25
    )
    
    # League filter for preloaded data
    if use_preloaded_data:
        st.sidebar.subheader("🏆 League Filter")
        available_leagues = ['All Leagues', 'Premier League', 'La Liga', 'Bundesliga', 'Serie A', 'Ligue 1']
        selected_league_filter = st.sidebar.selectbox(
            "Filter by league",
            available_leagues,
            help="Select a specific league to analyze or 'All Leagues' for combined view"
        )
    
    # Display settings
    st.sidebar.subheader("📊 Display Options")
    show_top_3 = st.sidebar.checkbox("Show Top 3 Summary", value=True)
    show_squad_breakdown = st.sidebar.checkbox("Show Squad Breakdown", value=True)
    show_league_comparison = st.sidebar.checkbox("Show League Comparison", value=True)
    
    # Number of players to highlight
    top_n = st.sidebar.number_input(
        "Number of top players to highlight", 
        min_value=10, 
        max_value=100, 
        value=50,
        step=10
    )
    
    # Handle data source
    if use_preloaded_data:
        st.info("🌍 **Using preloaded Big 5 leagues data** - Toggle off in sidebar to upload your own data")
        
        # Load preloaded data
        preloaded_df = load_preloaded_data()
        
        if not preloaded_df.empty:
            # Apply league filter if not "All Leagues"
            if selected_league_filter != 'All Leagues':
                filtered_preloaded = preloaded_df[preloaded_df['League'] == selected_league_filter].copy()
                st.success(f"📊 **Analyzing {selected_league_filter}** - {len(filtered_preloaded)} players in dataset")
            else:
                filtered_preloaded = preloaded_df.copy()
                st.success(f"📊 **Analyzing all Big 5 leagues** - {len(filtered_preloaded)} players in dataset")
            
            # Show league breakdown for "All Leagues"
            if selected_league_filter == 'All Leagues' and 'League' in filtered_preloaded.columns:
                league_counts = filtered_preloaded['League'].value_counts()
                st.write("**League breakdown:**")
                cols = st.columns(len(league_counts))
                for i, (league, count) in enumerate(league_counts.items()):
                    with cols[i]:
                        st.metric(league, count, "players")
            
            # Process the data
            uploaded_files = {'Preloaded Data': filtered_preloaded}
        else:
            uploaded_files = {}
            st.error("❌ Could not load preloaded data. Please upload your own data.")
    
    else:
        # Instructions for manual upload
        with st.expander("📋 How to Upload Your Own Data"):
            st.markdown("""
            **Upload FBRef Progressive Passing CSV files for analysis:**
            
            **Option 1: Big 5 Combined (Easiest)**
            1. **Go to FBRef Big 5 European Leagues page**
            2. **Navigate to Passing stats** 
            3. **Copy the progressive passing table** and paste into Excel/Google Sheets
            4. **Save as CSV** and upload to "Big 5 Combined" uploader
            
            **Option 2: Individual Leagues**
            1. **Go to individual league pages** (Premier League, La Liga, etc.)
            2. **Follow same process** for each league you want to analyze
            3. **Upload to corresponding league uploaders**
            
            **The app will automatically:**
            - Find U-25 players whose **primary position is MF** (excludes "DF,MF", "FW,MF")
            - Filter for players with at least the specified 90s
            - Sort by **Progressive Distance (PrgDist)** - highest first
            - For Big 5 data: Automatically detect league from squad names
            - Combine data from all uploaded sources
            """)
        
        # File uploaders for manual upload
        st.subheader("📁 Upload League Data")
        
        # Big 5 Combined option
        st.markdown("### 🌍 Big 5 Combined (Recommended)")
        big5_file = st.file_uploader(
            "🌍 Big 5 Leagues Combined", 
            type=['csv'],
            key="upload_big5_combined",
            help="Upload the combined Big 5 leagues progressive passing CSV from FBRef"
        )
        
        uploaded_files = {}
        if big5_file:
            uploaded_files['Big 5 Combined'] = big5_file
        
        # Separator
        st.markdown("---")
        st.markdown("### 🏆 Individual Leagues")
        st.markdown("*Use these if you want to analyze specific leagues separately*")
        
        leagues = {
            'Premier League': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
            'La Liga': '🇪🇸', 
            'Bundesliga': '🇩🇪',
            'Serie A': '🇮🇹',
            'Ligue 1': '🇫🇷'
        }
        
        # Create two columns for individual league uploaders
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("##### European Leagues")
            for i, (league, flag) in enumerate(list(leagues.items())[:2]):
                uploaded_file = st.file_uploader(
                    f"{flag} {league}", 
                    type=['csv'],
                    key=f"upload_{league.replace(' ', '_').lower()}",
                    help=f"Upload progressive passing CSV for {league}"
                )
                if uploaded_file:
                    uploaded_files[league] = uploaded_file
        
        with col2:
            st.markdown("##### German & Italian")
            for i, (league, flag) in enumerate(list(leagues.items())[2:4]):
                uploaded_file = st.file_uploader(
                    f"{flag} {league}", 
                    type=['csv'],
                    key=f"upload_{league.replace(' ', '_').lower()}",
                    help=f"Upload progressive passing CSV for {league}"
                )
                if uploaded_file:
                    uploaded_files[league] = uploaded_file
        
        with col3:
            st.markdown("##### French League")
            league, flag = list(leagues.items())[4]
            uploaded_file = st.file_uploader(
                f"{flag} {league}", 
                type=['csv'],
                key=f"upload_{league.replace(' ', '_').lower()}",
                help=f"Upload progressive passing CSV for {league}"
            )
            if uploaded_file:
                uploaded_files[league] = uploaded_file
        
        # Show upload status for manual uploads
        if uploaded_files:
            if 'Big 5 Combined' in uploaded_files:
                st.success(f"✅ **Big 5 Combined dataset uploaded!**")
                if len(uploaded_files) > 1:
                    other_leagues = [k for k in uploaded_files.keys() if k != 'Big 5 Combined']
                    st.info(f"ℹ️ Also uploaded: {', '.join(other_leagues)}")
            else:
                st.success(f"✅ **{len(uploaded_files)} individual league(s) uploaded:** {', '.join(uploaded_files.keys())}")
        else:
            st.info("👆 Upload the Big 5 Combined dataset OR individual league CSVs to begin analysis")
    
    # Process data (either preloaded or uploaded)
    if uploaded_files:
        all_data = []
        
        # Skip the detailed processing section for preloaded data
        if use_preloaded_data:
            # For preloaded data, directly process without showing detailed breakdown
            for dataset_name, df in uploaded_files.items():
                if isinstance(df, pd.DataFrame):  # It's already a DataFrame
                    filtered_df = filter_and_analyze(df, min_90s, max_age)
                    if not filtered_df.empty:
                        all_data.append(filtered_df)
        else:
            # Show detailed processing for uploaded data
            st.subheader("📊 Processing Results")
            
            for league_name, uploaded_file in uploaded_files.items():
                with st.expander(f"🔍 {league_name} Analysis", expanded=False):
                    df = process_fbref_progressive_data(uploaded_file)
                    
                    if not df.empty:
                        st.success(f"✅ Successfully loaded {len(df)} players from {league_name}")
                        
                        # For Big 5 combined, show league breakdown
                        if league_name == 'Big 5 Combined' and 'League' in df.columns:
                            league_counts = df['League'].value_counts()
                            st.write("**League breakdown in dataset:**")
                            for league, count in league_counts.items():
                                st.write(f"- {league}: {count} players")
                        
                        # Filter the data
                        filtered_df = filter_and_analyze(df, min_90s, max_age)
                        
                        if not filtered_df.empty:
                            # For individual leagues, add league column if not present
                            if 'League' not in filtered_df.columns or league_name != 'Big 5 Combined':
                                filtered_df['League'] = league_name
                            
                            all_data.append(filtered_df)
                            
                            st.write(f"**Found {len(filtered_df)} qualifying players in {league_name}**")
                            
                            # Show breakdown by league for Big 5 combined
                            if league_name == 'Big 5 Combined' and 'League' in filtered_df.columns:
                                league_breakdown = filtered_df['League'].value_counts()
                                st.write("**Qualifying players by league:**")
                                for league, count in league_breakdown.items():
                                    st.write(f"- {league}: {count} players")
                            
                            # Show top 3 from this dataset
                            top_3_league = filtered_df.head(3)
                            st.write(f"**Top 3 in {league_name}:**")
                            for i, (_, player) in enumerate(top_3_league.iterrows()):
                                league_info = f" ({player['League']})" if 'League' in player and league_name == 'Big 5 Combined' else ""
                                st.write(f"{i+1}. {player['Player']} ({player['Squad']}){league_info} - {player['PrgDist']:.1f} PrgDist")
                        else:
                            st.warning(f"⚠️ No qualifying players found in {league_name}")
                    else:
                        st.error(f"❌ Could not process {league_name} data")
        
        # Combined analysis
        if all_data:
            # Title based on data source and filter
            if use_preloaded_data and selected_league_filter != 'All Leagues':
                st.subheader(f"🏆 {selected_league_filter} Analysis")
            else:
                st.subheader("🏆 Combined Analysis: All Leagues")
            
            # Combine all dataframes
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_df = combined_df.sort_values('PrgDist', ascending=False)
            combined_df['Overall_Rank'] = range(1, len(combined_df) + 1)
            
            if use_preloaded_data and selected_league_filter != 'All Leagues':
                st.success(f"**Total: {len(combined_df)} qualifying U-{max_age} midfielders in {selected_league_filter}**")
            else:
                st.success(f"**Total: {len(combined_df)} qualifying U-{max_age} midfielders across all leagues**")
            
            # Top performers summary
            if show_top_3 and len(combined_df) >= 3:
                st.markdown("### 🥇 Top 3 Overall")
                top3 = combined_df.head(3)
                
                col1, col2, col3 = st.columns(3)
                
                for i, (_, player) in enumerate(top3.iterrows()):
                    with [col1, col2, col3][i]:
                        st.metric(
                            f"#{i+1} {player['Player']}", 
                            f"{player['PrgDist']:.1f}",
                            f"{player['Squad']} ({player['League']})"
                        )
            
            # Highlight top N players
            st.markdown(f"### ⭐ Top {top_n} Progressive Distance Leaders")
            
            top_n_df = combined_df.head(top_n)
            display_cols = ['Overall_Rank', 'Player', 'League', 'Squad', 'Age', 'Pos', '90s', 'PrgDist', 'PrgP']
            available_cols = [col for col in display_cols if col in top_n_df.columns]
            
            display_df = top_n_df[available_cols].copy()
            
            # Format numeric columns
            if 'PrgDist' in display_df.columns:
                display_df['PrgDist'] = display_df['PrgDist'].round(1)
            if 'PrgP' in display_df.columns:
                display_df['PrgP'] = display_df['PrgP'].round(2)
            if '90s' in display_df.columns:
                display_df['90s'] = display_df['90s'].round(1)
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Overall_Rank": st.column_config.NumberColumn("Rank", width="small"),
                    "League": st.column_config.TextColumn("League", width="medium"),
                    "PrgDist": st.column_config.NumberColumn(
                        "Progressive Distance",
                        help="Total distance of progressive passes per 90 minutes",
                        format="%.1f"
                    ),
                    "PrgP": st.column_config.NumberColumn(
                        "Progressive Passes",
                        help="Number of progressive passes per 90 minutes", 
                        format="%.2f"
                    ),
                    "90s": st.column_config.NumberColumn(
                        "90s Played",
                        help="Number of 90-minute periods played",
                        format="%.1f"
                    )
                }
            )
            
            # League comparison (only show if multiple leagues or "All Leagues" selected)
            if show_league_comparison and (not use_preloaded_data and len(uploaded_files) > 1 or use_preloaded_data and selected_league_filter == 'All Leagues'):
                st.subheader("🌍 League Comparison")
                
                league_stats = combined_df.groupby('League').agg({
                    'Player': 'count',
                    'PrgDist': ['mean', 'max'],
                    'Age': 'mean'
                }).round(1)
                
                league_stats.columns = ['Players', 'Avg PrgDist', 'Max PrgDist', 'Avg Age']
                league_stats = league_stats.sort_values('Avg PrgDist', ascending=False)
                
                st.dataframe(league_stats, use_container_width=True)
                
                # League representation in top performers
                st.markdown("#### 🏅 League Representation in Top Performers")
                top_50_leagues = combined_df.head(50)['League'].value_counts()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Top 50 players by league:**")
                    for league, count in top_50_leagues.items():
                        st.write(f"- {league}: {count} players")
                
                with col2:
                    if len(top_50_leagues) > 0:
                        st.write("**Most represented league:**")
                        top_league = top_50_leagues.index[0]
                        top_count = top_50_leagues.iloc[0]
                        st.metric(top_league, f"{top_count} players", "in top 50")
            
            # Squad breakdown
            if show_squad_breakdown:
                st.subheader("🏟️ Squad Analysis")
                
                squad_stats = combined_df.groupby(['League', 'Squad']).agg({
                    'Player': 'count',
                    'PrgDist': 'mean'
                }).round(1)
                
                squad_stats.columns = ['Players', 'Avg PrgDist']
                squad_stats = squad_stats.sort_values('Avg PrgDist', ascending=False)
                
                # Show squads with multiple qualifying players
                multi_player_squads = squad_stats[squad_stats['Players'] > 1]
                if not multi_player_squads.empty:
                    st.write("**Squads with multiple qualifying players:**")
                    st.dataframe(multi_player_squads, use_container_width=True)
            
            # Summary statistics
            st.subheader("📈 Overall Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Players", len(combined_df))
            
            with col2:
                st.metric(
                    "Average PrgDist", 
                    f"{combined_df['PrgDist'].mean():.1f}"
                )
            
            with col3:
                st.metric(
                    "Highest PrgDist", 
                    f"{combined_df['PrgDist'].max():.1f}"
                )
            
            with col4:
                if use_preloaded_data and selected_league_filter != 'All Leagues':
                    st.metric(
                        "League Analyzed", 
                        selected_league_filter
                    )
                else:
                    st.metric(
                        "Leagues Analyzed", 
                        len(uploaded_files) if not use_preloaded_data else len(combined_df['League'].unique())
                    )
            
            # Download options
            st.subheader("📥 Download Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Download top performers
                top_csv = combined_df.head(top_n).to_csv(index=False)
                st.download_button(
                    label=f"📥 Download Top {top_n} Players",
                    data=top_csv,
                    file_name=f"top_{top_n}_u{max_age}_midfielders_progressive_distance.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Download all results
                all_csv = combined_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download All Results",
                    data=all_csv,
                    file_name=f"all_u{max_age}_midfielders_progressive_distance.csv",
                    mime="text/csv"
                )
        
        else:
            st.warning("⚠️ No valid data found. Please check your data source.")
    else:
        if use_preloaded_data:
            st.info("👆 Preloaded data is ready! Adjust filters in the sidebar to analyze.")
        else:
            st.info("👆 Upload the Big 5 Combined dataset OR individual league CSVs to begin analysis")
    
    # Show current filter settings in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Current Filters")
    st.sidebar.write(f"• **Max Age:** {max_age}")
    st.sidebar.write(f"• **Min 90s:** {min_90s}")
    st.sidebar.write(f"• **Position:** Primary MF only")
    st.sidebar.write(f"• **Sort by:** Progressive Distance")
    
    if use_preloaded_data:
        st.sidebar.write(f"• **Data Source:** Preloaded Big 5")
        if selected_league_filter != 'All Leagues':
            st.sidebar.write(f"• **League Filter:** {selected_league_filter}")
    elif uploaded_files:
        st.sidebar.write(f"• **Leagues:** {len(uploaded_files)}")
        for league in uploaded_files.keys():
            st.sidebar.write(f"  - {league}")

if __name__ == "__main__":
    main()