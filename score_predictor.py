from database import database_query

def predict_score_fpi(away, home):
    
    # Pull FPI, Offensive Efficiency, and Defensive Efficiency for each team as determined by ESPN analytics.
    away_team = database_query.get_cfb_fpi_by_team(away)
    home_team = database_query.get_cfb_fpi_by_team(home)

    # Grabs Home Field Advantage for the team hosting, as determined in an online analysis.
    home_hfa = database_query.get_cfb_hfa_by_team(home)
    
    # Average score a cfb team in 2024 scores.
    base_total_score = 26.65
    
    # Calculate time of possession (TOP) ratio based on offensive and defensive efficiencies
    home_top = float(home_team.get("OffEfficiency")) + (100 - float(away_team.get("DefEfficiency")))
    away_top = float(away_team.get("OffEfficiency")) + (100 - float(home_team.get("DefEfficiency")))
    total_top = home_top + away_top
    
    # TOP factor (1 = 30 min est.)
    home_possession = 2* home_top / total_top
    away_possession = 2* away_top / total_top

    # TOP factor adjustment (to prevent extremely unbalanced TOP)
    home_possession = min(0.67*2,max(home_possession,0.33*2))
    away_possession = min(0.67*2,max(away_possession,0.33*2))

    # Scoring Efficiency off vs def factor, roughly how fast a team plays against a particular defense
    home_score_eff = (float(home_team.get("OffEfficiency")) - float(away_team.get("DefEfficiency")) + 100)/100
    away_score_eff = (float(away_team.get("OffEfficiency")) - float(home_team.get("DefEfficiency")) + 100)/100

    # Estimation of point total for the game (both teams)
    total_score = base_total_score*home_possession*home_score_eff + base_total_score*away_possession*away_score_eff

    # Score estimation by dividing the point total by 2 and adjusting based on expected margin on neutral site (via FPI) and HFA effects.
    home_score = total_score/2 + (float(home_team.get("FPI")) - float(away_team.get("FPI")))/2 + float(home_hfa.get("HFA"))/2
    away_score = total_score/2 + (float(away_team.get("FPI")) - float(home_team.get("FPI")))/2 - float(home_hfa.get("HFA"))/2
    
    return away_team.get("TeamName") + " @ " + home_team.get("TeamName") + " Prediction:\n   " +  away_team.get("TeamName") + ": " + str(round(away_score)) + "; " + home_team.get("TeamName") + ": " + str(round(home_score))

def predict_score_sp_plus(away, home):
    
    # Pull FPI, Offensive Efficiency, and Defensive Efficiency for each team as determined by ESPN analytics.
    away_team = database_query.get_cfb_sp_plus_by_team(away)
    home_team = database_query.get_cfb_sp_plus_by_team(home)

    # Grabs Home Field Advantage for the team hosting, as determined in an online analysis.
    home_hfa = database_query.get_cfb_hfa_by_team(home)
    
    # Estimates how much of the total score each team is responsible for, not used at the score prediction as the margin provided by sp+ accomplishes this.
    home_factor = ((float(home_team.get("OffPoint"))) + (float(away_team.get("DefPoint"))))/2
    away_factor = ((float(away_team.get("OffPoint"))) + (float(home_team.get("DefPoint"))))/2

    # Estimates total score.
    total_score = home_factor + away_factor

    # Estimates margin of victory without accounting for home field advantage, impact of travel, or rest time prior to the game.
    raw_margin = float(home_team.get("SPPlus")) - float(away_team.get("SPPlus"))

    # Estimates the score accounting HFA.
    away_score = score_adjustments(total_score/2 - raw_margin/2 - float(home_hfa.get("HFA"))/2)
    home_score = score_adjustments(total_score/2 + raw_margin/2 + float(home_hfa.get("HFA"))/2)

    # Accounts for ties at end of regulation (doesn't do OT, determines the non-rounded advantage if any, defaults to hfa if exact tie)
    home_score, away_score = tie_breaker(home_score,away_score)
    
    return away_team.get("TeamName") + " @ " + home_team.get("TeamName") + " Prediction:\n   " +  away_team.get("TeamName") + ": " + str(round(away_score)) + "; " + home_team.get("TeamName") + ": " + str(round(home_score))

# Some results have unrealistically low scores
def score_adjustments(score):
    if score < 0:
        score = 0
    elif score < 3:
        score = 3
    elif score < 6:
        score = 6
    return score

# Adds a point if the rounded score is tied, favors home team if non rounded results are tied too.
def tie_breaker(score1, score2):
    r1 = round(score1)
    r2 = round(score2)

    if r1 == r2:
        if score1 >= score2:
            score1 = score1 + 1
        else:
            score2 = score2 + 1
    return score1, score2

# Predict game outcome Away vs Home
#away_name = "Ohio State"
#home_name = "Alabama"

#predicted_scores_sp = predict_score_sp_plus(away_name, home_name)
#print(predicted_scores_sp)
