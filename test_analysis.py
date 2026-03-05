import pandas as pd
import pingouin as pg
from factor_analyzer.factor_analyzer import calculate_kmo, calculate_bartlett_sphericity

# Load data
df = pd.read_csv("Questionnaire - Sheet1 (4).csv")

# Extract columns
adv_cols = [c for c in df.columns if c.startswith('adv_')]
chal_cols = [c for c in df.columns if c.startswith('chal_')]
strat_cols = [c for c in df.columns if c.startswith('strat_')]

def analyze_section(name, cols):
    print(f"--- {name} ---")
    data = df[cols].dropna()
    print(f"N = {len(data)}")

    # Reliability: Cronbach's Alpha
    alpha, ci = pg.cronbach_alpha(data=data)
    print(f"Cronbach's Alpha: {alpha:.3f} (CI: {ci})")

    # Validity: KMO and Bartlett
    kmo_all, kmo_model = calculate_kmo(data)
    print(f"KMO Measure: {kmo_model:.3f}")

    chi_square_value, p_value = calculate_bartlett_sphericity(data)
    print(f"Bartlett's Test: Chi-square = {chi_square_value:.3f}, p-value = {p_value:.3e}")

analyze_section("Advantages", adv_cols)
analyze_section("Challenges", chal_cols)
analyze_section("Strategies", strat_cols)
