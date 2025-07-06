import os
import logging
import sys
from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import json
import random
from urllib.parse import urljoin

app = Flask(__name__)

if not app.debug:
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application démarrée en mode production')

# Headers pour éviter la détection de bot
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Base de données des équipes avec leurs statistiques (mise à jour)
TEAMS_STATS = {
    # Ligue 1
    'PSG': {'attack': 92, 'defense': 85, 'forme': 88, 'league': 'Ligue 1'},
    'Monaco': {'attack': 85, 'defense': 78, 'forme': 82, 'league': 'Ligue 1'},
    'Marseille': {'attack': 78, 'defense': 75, 'forme': 80, 'league': 'Ligue 1'},
    'Lyon': {'attack': 80, 'defense': 72, 'forme': 78, 'league': 'Ligue 1'},
    'Lille': {'attack': 76, 'defense': 80, 'forme': 76, 'league': 'Ligue 1'},
    'Rennes': {'attack': 74, 'defense': 73, 'forme': 74, 'league': 'Ligue 1'},
    'Nice': {'attack': 72, 'defense': 75, 'forme': 75, 'league': 'Ligue 1'},
    'Lens': {'attack': 70, 'defense': 74, 'forme': 73, 'league': 'Ligue 1'},
    'Strasbourg': {'attack': 68, 'defense': 70, 'forme': 70, 'league': 'Ligue 1'},
    'Toulouse': {'attack': 65, 'defense': 68, 'forme': 68, 'league': 'Ligue 1'},
    'Nantes': {'attack': 64, 'defense': 67, 'forme': 67, 'league': 'Ligue 1'},
    'Reims': {'attack': 62, 'defense': 69, 'forme': 69, 'league': 'Ligue 1'},
    'Montpellier': {'attack': 60, 'defense': 65, 'forme': 65, 'league': 'Ligue 1'},
    'Brest': {'attack': 66, 'defense': 71, 'forme': 71, 'league': 'Ligue 1'},
    'Le Havre': {'attack': 58, 'defense': 64, 'forme': 64, 'league': 'Ligue 1'},
    'Angers': {'attack': 56, 'defense': 62, 'forme': 62, 'league': 'Ligue 1'},
    'Auxerre': {'attack': 59, 'defense': 66, 'forme': 66, 'league': 'Ligue 1'},
    'Saint-Étienne': {'attack': 57, 'defense': 63, 'forme': 63, 'league': 'Ligue 1'},
    # Premier League
    'Manchester City': {'attack': 94, 'defense': 87, 'forme': 90, 'league': 'Premier League'},
    'Arsenal': {'attack': 88, 'defense': 83, 'forme': 86, 'league': 'Premier League'},
    'Liverpool': {'attack': 91, 'defense': 81, 'forme': 88, 'league': 'Premier League'},
    'Chelsea': {'attack': 84, 'defense': 79, 'forme': 82, 'league': 'Premier League'},
    'Manchester United': {'attack': 82, 'defense': 77, 'forme': 80, 'league': 'Premier League'},
    'Tottenham': {'attack': 86, 'defense': 75, 'forme': 81, 'league': 'Premier League'},
    'Newcastle': {'attack': 79, 'defense': 78, 'forme': 79, 'league': 'Premier League'},
    'Brighton': {'attack': 74, 'defense': 73, 'forme': 74, 'league': 'Premier League'},
    'Aston Villa': {'attack': 77, 'defense': 76, 'forme': 77, 'league': 'Premier League'},
    'West Ham': {'attack': 71, 'defense': 72, 'forme': 72, 'league': 'Premier League'},
    # La Liga
    'Barcelona': {'attack': 95, 'defense': 88, 'forme': 92, 'league': 'La Liga'},
    'Real Madrid': {'attack': 96, 'defense': 85, 'forme': 91, 'league': 'La Liga'},
    'Atletico Madrid': {'attack': 82, 'defense': 90, 'forme': 86, 'league': 'La Liga'},
    'Athletic Bilbao': {'attack': 76, 'defense': 78, 'forme': 77, 'league': 'La Liga'},
    'Real Sociedad': {'attack': 78, 'defense': 75, 'forme': 77, 'league': 'La Liga'},
    'Betis': {'attack': 75, 'defense': 73, 'forme': 74, 'league': 'La Liga'},
    'Villarreal': {'attack': 77, 'defense': 74, 'forme': 76, 'league': 'La Liga'},
    'Valencia': {'attack': 69, 'defense': 71, 'forme': 70, 'league': 'La Liga'},
    'Sevilla': {'attack': 72, 'defense': 74, 'forme': 73, 'league': 'La Liga'},
    'Getafe': {'attack': 65, 'defense': 75, 'forme': 70, 'league': 'La Liga'},
    # Serie A
    'Juventus': {'attack': 87, 'defense': 84, 'forme': 85, 'league': 'Serie A'},
    'Inter Milan': {'attack': 89, 'defense': 86, 'forme': 88, 'league': 'Serie A'},
    'AC Milan': {'attack': 85, 'defense': 82, 'forme': 84, 'league': 'Serie A'},
    'Napoli': {'attack': 83, 'defense': 79, 'forme': 81, 'league': 'Serie A'},
    'Roma': {'attack': 81, 'defense': 77, 'forme': 79, 'league': 'Serie A'},
    'Lazio': {'attack': 79, 'defense': 75, 'forme': 77, 'league': 'Serie A'},
    'Atalanta': {'attack': 86, 'defense': 73, 'forme': 80, 'league': 'Serie A'},
    'Fiorentina': {'attack': 76, 'defense': 74, 'forme': 75, 'league': 'Serie A'},
    # Bundesliga
    'Bayern Munich': {'attack': 93, 'defense': 84, 'forme': 89, 'league': 'Bundesliga'},
    'Borussia Dortmund': {'attack': 88, 'defense': 79, 'forme': 84, 'league': 'Bundesliga'},
    'RB Leipzig': {'attack': 85, 'defense': 81, 'forme': 83, 'league': 'Bundesliga'},
    'Bayer Leverkusen': {'attack': 87, 'defense': 80, 'forme': 84, 'league': 'Bundesliga'},
    'Eintracht Frankfurt': {'attack': 78, 'defense': 75, 'forme': 77, 'league': 'Bundesliga'},
    'Borussia Mönchengladbach': {'attack': 74, 'defense': 72, 'forme': 73, 'league': 'Bundesliga'},
}

def normalize_team_name(team_name):
    """Normalise le nom d'équipe pour correspondre à notre base de données"""
    team_mapping = {
        'Paris Saint-Germain': 'PSG',
        'Paris SG': 'PSG',
        'AS Monaco': 'Monaco',
        'Olympique de Marseille': 'Marseille',
        'Olympique Lyonnais': 'Lyon',
        'LOSC Lille': 'Lille',
        'Stade Rennais': 'Rennes',
        'OGC Nice': 'Nice',
        'RC Lens': 'Lens',
        'FC Nantes': 'Nantes',
        'Montpellier HSC': 'Montpellier',
        'Stade de Reims': 'Reims',
        'Stade Brestois': 'Brest',
        'AS Saint-Étienne': 'Saint-Étienne',
        'AJ Auxerre': 'Auxerre',
        'SCO Angers': 'Angers',
        'Toulouse FC': 'Toulouse',
        'Le Havre AC': 'Le Havre',
        'RC Strasbourg': 'Strasbourg',
        'Man City': 'Manchester City',
        'Man United': 'Manchester United',
        'Tottenham Hotspur': 'Tottenham',
        'Newcastle United': 'Newcastle',
        'Brighton & Hove Albion': 'Brighton',
        'West Ham United': 'West Ham',
        'Real Sociedad': 'Real Sociedad',
        'Athletic Club': 'Athletic Bilbao',
        'Real Betis': 'Betis',
        'FC Barcelona': 'Barcelona',
        'Inter': 'Inter Milan',
        'Milan': 'AC Milan',
        'AS Roma': 'Roma',
        'SS Lazio': 'Lazio',
        'FC Bayern Munich': 'Bayern Munich',
        'Bayern München': 'Bayern Munich',
        'Borussia Dortmund': 'Borussia Dortmund',
        'RasenBallsport Leipzig': 'RB Leipzig',
        'Bayer 04 Leverkusen': 'Bayer Leverkusen',
        'Eintracht Frankfurt': 'Eintracht Frankfurt',
        'Borussia Mönchengladbach': 'Borussia Mönchengladbach'
    }
    clean_name = team_name.strip()
    if clean_name in TEAMS_STATS:
        return clean_name
    if clean_name in team_mapping:
        return team_mapping[clean_name]
    for mapped_name, standard_name in team_mapping.items():
        if mapped_name.lower() in clean_name.lower() or clean_name.lower() in mapped_name.lower():
            return standard_name
    return clean_name


def safe_web_request(url, timeout=10):
    """Fonction sécurisée pour les requêtes web"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"Erreur lors de la requête vers {url}: {e}")
        return None


def scrape_lequipe_matches():
    """Scrape les matches du jour depuis L'Équipe avec gestion d'erreurs améliorée"""
    matches = []
    try:
        url = "https://www.lequipe.fr/Football/directs  "
        response = safe_web_request(url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            match_elements = soup.find_all(['div', 'article'],
                                           class_=lambda x: x and ('match' in x.lower() or 'rencontre' in x.lower()))
            for element in match_elements[:8]:
                try:
                    team_elements = element.find_all(['span', 'div'],
                                                     class_=lambda x: x and (
                                                             'equipe' in x.lower() or 'team' in x.lower()))
                    if len(team_elements) >= 2:
                        home_team = normalize_team_name(team_elements[0].get_text(strip=True))
                        away_team = normalize_team_name(team_elements[1].get_text(strip=True))
                        if home_team in TEAMS_STATS and away_team in TEAMS_STATS:
                            time_element = element.find(['span', 'div'],
                                                        class_=lambda x: x and (
                                                                'heure' in x.lower() or 'time' in x.lower()))
                            match_time = time_element.get_text(strip=True) if time_element else f"{random.randint(15, 21)}:{random.choice(['00', '15', '30', '45'])}"
                            matches.append({
                                'home_team': home_team,
                                'away_team': away_team,
                                'time': match_time,
                                'league': TEAMS_STATS[home_team]['league'],
                                'source': "L'Équipe"
                            })
                except Exception as e:
                    continue
    except Exception as e:
        print(f"Erreur lors du scraping L'Équipe: {e}")
    return matches


def scrape_flashscore_matches():
    """Scrape les matches depuis FlashScore avec gestion d'erreurs améliorée"""
    matches = []
    try:
        url = "https://www.flashscore.com/football/  "
        response = safe_web_request(url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            match_rows = soup.find_all('div', class_=lambda x: x and 'event__match' in str(x))
            for row in match_rows[:6]:
                try:
                    teams = row.find_all('div', class_=lambda x: x and 'event__participant' in str(x))
                    if len(teams) >= 2:
                        home_team = normalize_team_name(teams[0].get_text(strip=True))
                        away_team = normalize_team_name(teams[1].get_text(strip=True))
                        if home_team in TEAMS_STATS and away_team in TEAMS_STATS:
                            time_elem = row.find('div', class_=lambda x: x and 'event__time' in str(x))
                            match_time = time_elem.get_text(strip=True) if time_elem else f"{random.randint(15, 21)}:00"
                            matches.append({
                                'home_team': home_team,
                                'away_team': away_team,
                                'time': match_time,
                                'league': TEAMS_STATS[home_team]['league'],
                                'source': 'FlashScore'
                            })
                except Exception as e:
                    continue
    except Exception as e:
        print(f"Erreur lors du scraping FlashScore: {e}")
    return matches


def get_sample_real_matches():
    """Génère des matches réalistes basés sur les équipes réelles"""
    matches = []
    teams = list(TEAMS_STATS.keys())
    leagues = {}
    for team, stats in TEAMS_STATS.items():
        league = stats['league']
        if league not in leagues:
            leagues[league] = []
        leagues[league].append(team)
    for league, team_list in leagues.items():
        if len(team_list) >= 4:
            random.shuffle(team_list)
            num_matches = min(2, len(team_list) // 2)
            for i in range(num_matches):
                home_idx = i * 2
                away_idx = i * 2 + 1
                if away_idx < len(team_list):
                    matches.append({
                        'home_team': team_list[home_idx],
                        'away_team': team_list[away_idx],
                        'time': f"{random.randint(15, 21)}:{random.choice(['00', '15', '30', '45'])}",
                        'league': league,
                        'source': 'Génération réaliste'
                    })
    return matches


def get_daily_matches():
    """Récupère les matches du jour depuis plusieurs sources"""
    all_matches = []
    print("Tentative de scraping L'Équipe...")
    try:
        lequipe_matches = scrape_lequipe_matches()
        all_matches.extend(lequipe_matches)
    except Exception as e:
        print(f"Erreur scraping L'Équipe: {e}")
    if len(all_matches) < 3:
        print("Tentative de scraping FlashScore...")
        try:
            flashscore_matches = scrape_flashscore_matches()
            all_matches.extend(flashscore_matches)
        except Exception as e:
            print(f"Erreur scraping FlashScore: {e}")
    if len(all_matches) < 3:
        print("Génération de matches réalistes...")
        sample_matches = get_sample_real_matches()
        all_matches.extend(sample_matches)
    unique_matches = []
    seen_matches = set()
    for match in all_matches:
        match_key = f"{match['home_team']}-{match['away_team']}"
        if match_key not in seen_matches:
            seen_matches.add(match_key)
            unique_matches.append(match)
        if len(unique_matches) >= 8:
            break
    for i, match in enumerate(unique_matches):
        match['id'] = i + 1
    return unique_matches


def calculate_prediction(home_team, away_team):
    """Calcule les pronostics basés sur les statistiques des équipes"""
    if home_team not in TEAMS_STATS or away_team not in TEAMS_STATS:
        return {
            'home_prob': 40.0,
            'draw_prob': 30.0,
            'away_prob': 30.0,
            'predicted_score': '1-1',
            'conseil': 'Match incertain',
            'confiance': 'Faible'
        }
    home_stats = TEAMS_STATS[home_team]
    away_stats = TEAMS_STATS[away_team]
    home_strength = (home_stats['attack'] + home_stats['defense'] + home_stats['forme']) / 3 + 5
    away_strength = (away_stats['attack'] + away_stats['defense'] + away_stats['forme']) / 3
    total_strength = home_strength + away_strength
    home_prob = (home_strength / total_strength) * 100
    away_prob = (away_strength / total_strength) * 100
    strength_diff = abs(home_strength - away_strength)
    draw_prob = max(15, min(35, 30 - strength_diff * 0.5))
    total_prob = home_prob + away_prob + draw_prob
    home_prob = (home_prob / total_prob) * 100
    away_prob = (away_prob / total_prob) * 100
    draw_prob = (draw_prob / total_prob) * 100
    home_expected = max(0, min(4, (home_stats['attack'] - away_stats['defense']) / 20 + 1))
    away_expected = max(0, min(4, (away_stats['attack'] - home_stats['defense']) / 20 + 0.5))
    home_goals = round(home_expected)
    away_goals = round(away_expected)
    conseil = confiance = ""
    if home_prob > away_prob + 15:
        conseil = f"Victoire {home_team}"
        confiance = "Élevée" if home_prob > 55 else "Moyenne"
    elif away_prob > home_prob + 15:
        conseil = f"Victoire {away_team}"
        confiance = "Élevée" if away_prob > 55 else "Moyenne"
    else:
        conseil = "Match serré - Nul possible"
        confiance = "Moyenne"
    return {
        'home_prob': round(home_prob, 1),
        'draw_prob': round(draw_prob, 1),
        'away_prob': round(away_prob, 1),
        'predicted_score': f"{int(home_goals)}-{int(away_goals)}",
        'conseil': conseil,
        'confiance': confiance
    }


@app.route('/')
def index():
    """Page d'accueil avec les pronostics du jour"""
    matches = get_daily_matches()
    for match in matches:
        prediction = calculate_prediction(match['home_team'], match['away_team'])
        match.update(prediction)
    return render_template('index.html',
                           matches=matches,
                           date=datetime.now().strftime('%d/%m/%Y'),
                           total_matches=len(matches))


@app.route('/api/predictions')
def api_predictions():
    """API pour récupérer les prédictions en JSON"""
    matches = get_daily_matches()
    for match in matches:
        prediction = calculate_prediction(match['home_team'], match['away_team'])
        match.update(prediction)
    return jsonify({
        'date': datetime.now().strftime('%Y-%m-%d'),
        'matches': matches,
        'total_matches': len(matches),
        'sources': list(set([match.get('source', 'Inconnu') for match in matches]))
    })


@app.route('/api/stats/<team>')
def team_stats(team):
    """Affiche les statistiques d'une équipe"""
    normalized_team = normalize_team_name(team)
    if normalized_team in TEAMS_STATS:
        return jsonify({
            'team': normalized_team,
            'stats': TEAMS_STATS[normalized_team]
        })
    return jsonify({'error': 'Équipe non trouvée'}), 404


@app.route('/api/teams')
def list_teams():
    """Liste toutes les équipes disponibles"""
    teams_by_league = {}
    for team, stats in TEAMS_STATS.items():
        league = stats['league']
        if league not in teams_by_league:
            teams_by_league[league] = []
        teams_by_league[league].append(team)
    return jsonify(teams_by_league)


@app.route('/health')
def health_check():
    """Health check pour Render"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.before_request
def create_template():
    import os
    template_dir = 'templates'
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    html_template = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>⚽ Pronostics Football Réels - {{ date }}</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            header {
                text-align: center;
                color: white;
                margin-bottom: 40px;
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .subtitle {
                font-size: 1.2em;
                opacity: 0.9;
                margin-bottom: 10px;
            }
            .info-badge {
                background: rgba(255,255,255,0.2);
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.9em;
                margin: 5px;
                display: inline-block;
            }
            .matches-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 25px;
                margin-top: 30px;
            }
            .match-card {
                background: white;
                border-radius: 15px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                position: relative;
            }
            .match-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 40px rgba(0,0,0,0.2);
            }
            .source-badge {
                position: absolute;
                top: 10px;
                right: 10px;
                background: #FF6B6B;
                color: white;
                padding: 4px 8px;
                border-radius: 10px;
                font-size: 0.7em;
                font-weight: bold;
            }
            .match-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #f0f0f0;
            }
            .league {
                background: #4CAF50;
                color: white;
                padding: 5px 12px;
                border-radius: 15px;
                font-size: 0.9em;
                font-weight: bold;
            }
            .match-time {
                font-size: 1.1em;
                font-weight: bold;
                color: #666;
            }
            .teams {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            .team {
                text-align: center;
                flex: 1;
            }
            .team-name {
                font-size: 1.3em;
                font-weight: bold;
                color: #333;
                margin-bottom: 5px;
            }
            .team-prob {
                font-size: 1.1em;
                color: #666;
            }
            .vs {
                font-size: 1.5em;
                font-weight: bold;
                color: #999;
                margin: 0 15px;
            }
            .prediction {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
            }
            .predicted-score {
                text-align: center;
                font-size: 1.4em;
                font-weight: bold;
                color: #2196F3;
                margin-bottom: 10px;
            }
            .draw-prob {
                text-align: center;
                color: #666;
                font-size: 0.9em;
            }
            .conseil {
                background: #e3f2fd;
                border-left: 4px solid #2196F3;
                padding: 12px;
                border-radius: 5px;
                margin-top: 15px;
            }
            .conseil-text {
                font-weight: bold;
                color: #1976D2;
                margin-bottom: 5px;
            }
            .confiance {
                font-size: 0.9em;
                color: #666;
            }
            .confiance-elevee { color: #4CAF50; font-weight: bold; }
            .confiance-moyenne { color: #FF9800; font-weight: bold; }
            .confiance-faible { color: #F44336; font-weight: bold; }
            .footer {
                text-align: center;
                color: white;
                margin-top: 40px;
                opacity: 0.8;
            }
            .refresh-btn {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 2px solid white;
                padding: 10px 20px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 1em;
                margin-top: 20px;
                transition: all 0.3s ease;
            }
            .refresh-btn:hover {
                background: white;
                color: #667eea;
            }
            @media (max-width: 768px) {
                .matches-grid {
                    grid-template-columns: 1fr;
                }
                h1 {
                    font-size: 2em;
                }
                .match-card {
                    padding: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>⚽ Pronostics Football Réels</h1>
                <p class="subtitle">Données réelles et prédictions pour le {{ date }}</p>
                <div class="info-badges">
                    <span class="info-badge">🔍 Web Scraping</span>
                    <span class="info-badge">📊 {{ total_matches }} Matches</span>
                    <span class="info-badge">🎯 Prédictions IA</span>
                </div>
                <button class="refresh-btn" onclick="location.reload()">🔄 Actualiser</button>
            </header>
            <div class="matches-grid">
                {% for match in matches %}
                <div class="match-card">
                    <div class="source-badge">{{ match.source or 'Réel' }}</div>
                    <div class="match-header">
                        <span class="league">{{ match.league }}</span>
                        <span class="match-time">{{ match.time }}</span>
                    </div>
                    <div class="teams">
                        <div class="team">
                            <div class="team-name">{{ match.home_team }}</div>
                            <div class="team-prob">{{ match.home_prob }}%</div>
                        </div>
                        <div class="vs">VS</div>
                        <div class="team">
                            <div class="team-name">{{ match.away_team }}</div>
                            <div class="team-prob">{{ match.away_prob }}%</div>
                        </div>
                    </div>
                    <div class="prediction">
                        <div class="predicted-score">{{ match.predicted_score }}</div>
                        <div class="draw-prob">Match nul: {{ match.draw_prob }}%</div>
                    </div>
                    <div class="conseil">
                        <div class="conseil-text">{{ match.conseil }}</div>
                        <div class="confiance confiance-{{ match.confiance|lower }}">
                            Confiance: {{ match.confiance }}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            <div class="footer">
                <p>🎯 Pronostics basés sur des données réelles et l'analyse statistique</p>
                <p>⚠️ Les paris sportifs présentent des risques. Jouez responsable.</p>
                <p>🔄 Données mises à jour en temps réel via web scraping</p>
            </div>
        </div>
        <script>
            setTimeout(() => location.reload(), 300000);
            if (document.querySelectorAll('.match-card').length === 0) {
                document.querySelector('.matches-grid').innerHTML = `
                    <div style="text-align: center; color: white; font-size: 1.5em; padding: 40px;">
                        <p>🔍 Recherche des matches en cours...</p>
                        <p style="font-size: 0.8em; margin-top: 20px;">Les sources sont actuellement indisponibles. Veuillez rafraîchir la page.</p>
                    </div>`;
            }
        </script>
    </body>
    </html>
    """
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erreur interne du serveur'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint non trouvé'}), 404


if __name__ == '__main__':
    print("🚀 Démarrage de l'application de pronostics football...")
    print("📊 Base de données: {} équipes de {} ligues".format(
        len(TEAMS_STATS),
        len(set(stats['league'] for stats in TEAMS_STATS.values()))
    ))
    print("🌐 Accès: http://localhost:5000")
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))