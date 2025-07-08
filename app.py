import os
import logging
import sys
from flask import Flask, render_template, jsonify
from datetime import datetime
import requests
import random

# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Headers HTTP
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Statistiques des équipes (pour vos prédictions)
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

# Mapping des noms d'équipes pour normalisation
team_mapping = {
    'Paris Saint-Germain': 'PSG', 'Paris SG': 'PSG', 'AS Monaco': 'Monaco',
    'Olympique de Marseille': 'Marseille', 'Olympique Lyonnais': 'Lyon',
    'LOSC Lille': 'Lille', 'Stade Rennais': 'Rennes', 'OGC Nice': 'Nice',
    'RC Lens': 'Lens', 'FC Nantes': 'Nantes', 'Montpellier HSC': 'Montpellier',
    'Stade de Reims': 'Reims', 'Stade Brestois': 'Brest',
    'AS Saint-Étienne': 'Saint-Étienne', 'AJ Auxerre': 'Auxerre',
    'SCO Angers': 'Angers', 'Toulouse FC': 'Toulouse', 'Le Havre AC': 'Le Havre',
    'RC Strasbourg': 'Strasbourg', 'Man City': 'Manchester City',
    'Man United': 'Manchester United', 'Tottenham Hotspur': 'Tottenham',
    'Newcastle United': 'Newcastle', 'Brighton & Hove Albion': 'Brighton',
    'West Ham United': 'West Ham', 'Real Sociedad': 'Real Sociedad',
    'Athletic Club': 'Athletic Bilbao', 'Real Betis': 'Betis',
    'FC Barcelona': 'Barcelona', 'Inter': 'Inter Milan', 'Milan': 'AC Milan',
    'AS Roma': 'Roma', 'SS Lazio': 'Lazio', 'FC Bayern Munich': 'Bayern Munich',
    'Bayern München': 'Bayern Munich', 'Borussia Dortmund': 'Borussia Dortmund',
    'RasenBallsport Leipzig': 'RB Leipzig', 'Bayer 04 Leverkusen': 'Bayer Leverkusen',
    'Eintracht Frankfurt': 'Eintracht Frankfurt', 'Borussia Mönchengladbach': 'Borussia Mönchengladbach'
}

def normalize_team_name(team_name):
    return team_mapping.get(team_name.strip(), team_name.strip())

def safe_web_request(url, timeout=10):
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la requête vers {url}: {e}")
        return None

def get_api_sports_matches():
    matches = []
    try:
        api_key = os.getenv("API_SPORTS_KEY")
        if not api_key:
            raise ValueError("La clé API 'API_SPORTS_KEY' est manquante !")

        today = datetime.now().strftime("%Y-%m-%d")
        url = f"https://v3.football.api-sports.io/fixtures?date={today}"
        headers = {"x-apisports-key": api_key}
        response = safe_web_request(url)

        if not response:
            logger.warning("Aucune réponse reçue de l'API Sports")
            return []

        data = response.json()
        fixtures = data.get("response", [])

        for fixture in fixtures[:8]:
            teams = fixture.get("teams", {})
            home_team = normalize_team_name(teams["home"]["name"])
            away_team = normalize_team_name(teams["away"]["name"])

            if home_team in TEAMS_STATS and away_team in TEAMS_STATS:
                matches.append({
                    "home_team": home_team,
                    "away_team": away_team,
                    "time": fixture["fixture"]["date"][11:16],
                    "league": fixture.get("league", {}).get("name", "Inconnu"),
                    "source": "API-Sports.io"
                })

    except Exception as e:
        logger.error(f"Erreur lors de l'appel à API-Sports.io: {e}")

    return matches

def get_sample_real_matches():
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
    all_matches = []

    logger.info("Tentative d'appel à API-Sports.io...")
    try:
        sports_matches = get_api_sports_matches()
        all_matches.extend(sports_matches)
        logger.info(f"Récupéré {len(sports_matches)} matchs depuis API-Sports.io")
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à API-Sports.io: {e}")

    if len(all_matches) < 2:
        logger.info("Fallback sur des matchs fictifs (à éviter en prod)")
        sample_matches = get_sample_real_matches()
        all_matches.extend(sample_matches)
        logger.info(f"Généré {len(sample_matches)} matchs fictifs")

    seen = set()
    unique_matches = []
    for m in all_matches:
        key = (m['home_team'], m['away_team'])
        if key not in seen:
            seen.add(key)
            unique_matches.append(m)

    return unique_matches[:8]

def calculate_prediction(home_team, away_team):
    if home_team not in TEAMS_STATS or away_team not in TEAMS_STATS:
        return {
            'home_prob': 40.0, 'draw_prob': 30.0, 'away_prob': 30.0,
            'predicted_score': '1-1', 'conseil': 'Match incertain', 'confiance': 'Faible'
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

    home_goals = round(max(0, min(4, (home_stats['attack'] - away_stats['defense']) / 20 + 1)))
    away_goals = round(max(0, min(4, (away_stats['attack'] - home_stats['defense']) / 20 + 0.5)))

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
    try:
        matches = get_daily_matches()
        for match in matches:
            prediction = calculate_prediction(match['home_team'], match['away_team'])
            match.update(prediction)
        return render_template('index.html',
                               matches=matches,
                               date=datetime.now().strftime('%d/%m/%Y'),
                               total_matches=len(matches))
    except Exception as e:
        logger.error(f"Erreur dans la route index: {e}")
        return jsonify({'error': 'Erreur lors du chargement des données'}), 500

@app.route('/api/predictions')
def api_predictions():
    try:
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
    except Exception as e:
        logger.error(f"Erreur dans l'API predictions: {e}")
        return jsonify({'error': 'Erreur interne serveur'}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Démarrage de l'application sur le port {port}")
    logger.info(f"{len(TEAMS_STATS)} équipes de {len(set(stats['league'] for stats in TEAMS_STATS.values()))} ligues")
    app.run(debug=False, host='0.0.0.0', port=port)