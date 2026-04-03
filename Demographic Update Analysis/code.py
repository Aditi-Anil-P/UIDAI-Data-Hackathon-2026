import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# ==========================================
# 1. STATE STANDARDIZATION
# ==========================================

STATE_MAPPING = {
    'westbengal': 'West Bengal', 'west bangal': 'West Bengal','west bengli': 'West Bengal',
    'orissa': 'Odisha','andhrapradesh': 'Andhra Pradesh', 'chhatisgarh': 'Chhattisgarh',
    'uttaranchal': 'Uttarakhand', 'pondicherry': 'Puducherry',
    'dadra and nagar haveli': 'Dadra and Nagar Haveli and Daman and Diu',
    'daman & diu': 'Dadra and Nagar Haveli and Daman and Diu',
    'andaman & nicobar islands': 'Andaman and Nicobar Islands',
    'jammu & kashmir': 'Jammu and Kashmir','a & n islands': 'Andaman and Nicobar Islands'
}

JUNK_STATES = {
    '100000','madanapalle','puttenahalli','balanagar','jaipur','darbhanga','nagpur','raja annamalai puram'
}

def clean_state_name(name):
    if pd.isna(name):
        return np.nan
    name = str(name).replace('\xa0',' ').replace('*','').strip().lower()
    return STATE_MAPPING.get(name, name.title())

# ==========================================
# 2. DATA LOADERS
# ==========================================

def load_and_merge_data(pattern, cols):
    files = glob.glob(pattern)
    if not files:
        print(f"Warning: No files found for pattern {pattern}")
        return pd.DataFrame(columns=['state','total_count','state_clean'])

    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    df['state_clean'] = df['state'].apply(clean_state_name)
    df = df[~df['state_clean'].str.lower().isin(JUNK_STATES)]
    df['total_count'] = df[cols].sum(axis=1)
    return df

# Load datasets
demo_df = load_and_merge_data(
    'api_data_aadhar_demographic_*.csv',
    ['demo_age_5_17','demo_age_17_']
)

enrol_df = load_and_merge_data(
    'api_data_aadhar_enrolment_*.csv',
    ['age_0_5','age_5_17','age_18_greater']
)

# ==========================================
# 3. BASE AADHAAR POPULATION
# ==========================================

base_df = pd.read_csv('Aadhar saturation 2023.csv', header=0)
base_df['state_clean'] = base_df['State Name'].apply(clean_state_name)
base_df = base_df[~base_df['state_clean'].str.lower().isin(JUNK_STATES)]

col_target = [c for c in base_df.columns if 'Numbers of' in c and 'Aadhaar assigned' in c][0]

def clean_number(x):
    if isinstance(x, str):
        return float(x.replace(',', '').strip())
    return float(x) if pd.notnull(x) else 0.0

base_df['base_aadhaar_population'] = base_df[col_target].apply(clean_number)
base_grouped = base_df.groupby('state_clean', as_index=False)['base_aadhaar_population'].sum()

# Age-specific populations
base_5_17 = pd.read_csv('Aadhar saturation 2023 5-18.csv')
base_18p  = pd.read_csv('Aadhar saturation 2023 18+.csv')

base_5_17['state_clean'] = base_5_17['State Name'].apply(clean_state_name)
base_18p['state_clean']  = base_18p['State Name'].apply(clean_state_name)

col_5_17 = [c for c in base_5_17.columns if 'Aadhaar assigned' in c][0]
col_18p  = [c for c in base_18p.columns if 'Aadhaar assigned' in c][0]

base_5_17['base_5_17'] = base_5_17[col_5_17].astype(str).str.replace(',', '').astype(float)
base_18p['base_18_plus'] = base_18p[col_18p].astype(str).str.replace(',', '').astype(float)

base_5_17 = base_5_17.groupby('state_clean', as_index=False)['base_5_17'].sum()
base_18p  = base_18p.groupby('state_clean', as_index=False)['base_18_plus'].sum()

# ==========================================
# 4. AGGREGATION
# ==========================================

analysis_df = (
    demo_df.groupby('state_clean', as_index=False)['total_count']
    .sum().rename(columns={'total_count':'total_updates'})
    .merge(
        enrol_df.groupby('state_clean', as_index=False)['total_count']
        .sum().rename(columns={'total_count':'total_enrolments'}),
        on='state_clean', how='outer'
    )
    .merge(base_grouped, on='state_clean', how='inner')
    .fillna(0)
)

demo_raw = pd.concat(
    (pd.read_csv(f) for f in glob.glob('api_data_aadhar_demographic_*.csv')),
    ignore_index=True
)
demo_raw['state_clean'] = demo_raw['state'].apply(clean_state_name)
demo_raw = demo_raw[~demo_raw['state_clean'].str.lower().isin(JUNK_STATES)]

age_df = demo_raw.groupby('state_clean', as_index=False)[
    ['demo_age_5_17','demo_age_17_']
].sum()

analysis_df = (
    analysis_df
        .merge(age_df, on='state_clean', how='left')
        .merge(base_5_17, on='state_clean', how='left')
        .merge(base_18p, on='state_clean', how='left')
)

num_cols = analysis_df.select_dtypes(include='number').columns
analysis_df[num_cols] = analysis_df[num_cols].fillna(0)

# ==========================================
# 5. NORMALIZATION & Z-SCORES
# ==========================================

analysis_df['monthly_update_rate'] = (
    analysis_df['total_updates'] / analysis_df['base_aadhaar_population'] * 1000
)

analysis_df['monthly_enrollment_rate'] = (
    analysis_df['total_enrolments'] / analysis_df['base_aadhaar_population'] * 1000
)

analysis_df['rate_5_17'] = np.where(
    analysis_df['base_5_17'] > 0,
    analysis_df['demo_age_5_17'] / analysis_df['base_5_17'] * 1000,
    0
)

analysis_df['rate_18_plus'] = np.where(
    analysis_df['base_18_plus'] > 0,
    analysis_df['demo_age_17_'] / analysis_df['base_18_plus'] * 1000,
    0
)

analysis_df['z_score'] = (
    analysis_df['monthly_update_rate'] - analysis_df['monthly_update_rate'].mean()
) / analysis_df['monthly_update_rate'].std()

analysis_df['hotspot'] = pd.cut(
    analysis_df['z_score'],
    [-np.inf, -1, 1, np.inf],
    labels=['Low','Normal','High']
)

# ==========================================
# 6. SIZE STRATIFICATION
# ==========================================

q33, q67 = analysis_df['base_aadhaar_population'].quantile([0.33,0.67])

analysis_df['size_category'] = np.select(
    [analysis_df['base_aadhaar_population'] < q33,
     analysis_df['base_aadhaar_population'] < q67],
    ['Small','Medium'],
    default='Large'
)

# ==========================================
# 7. IMPROVED PATTERN CLASSIFICATION
# ==========================================

def classify_pattern(row):
    """Classify states with clearer, action-oriented labels"""
    hotspot = row['hotspot']
    # This function is applied to 'deviated' which has 'rate_5_17' and 'rate_18_plus'
    rate_5_17 = row.get('rate_5_17', 0)
    rate_18_plus = row.get('rate_18_plus', 0)

    # Calculate ratio to determine primary driver
    if rate_5_17 + rate_18_plus > 0:
        youth_ratio = rate_5_17 / (rate_5_17 + rate_18_plus)
    else:
        youth_ratio = 0.5

    if hotspot == 'High':
        if youth_ratio > 0.6:  # Youth contributing >60%
            return 'High Activity - School-Led Success'
        else:
            return 'High Activity - Adult-Led Success'
    elif hotspot == 'Low':
        # Check for complete stagnation
        if rate_5_17 < 1 and rate_18_plus < 1:
            return 'Stagnation - System-Wide Failure'
        elif youth_ratio < 0.4:  # Youth contributing <40%
            return 'Stagnation - School Programs Failing'
        else:
            return 'Stagnation - Adult Outreach Failing'
    return 'Normal'

def get_driver_analysis(pattern, states_data):
    """Detailed analysis identifying WHO is driving activity"""

    # This function operates on 'pattern_data', which is from 'output_table'.
    # 'output_table' has columns 'Rate_5_17' and 'Rate_18+'.
    avg_youth = states_data['Rate_5_17'].mean()
    avg_adult = states_data['Rate_18+'].mean()
    n_states = len(states_data)

    analyses = {
        'High Activity - School-Led Success': f"""
    🎯 PRIMARY DRIVER: Youth (5–18) | {n_states} State(s)

    • Youth updates far exceed adult updates (Youth: {avg_youth:.1f}/1000 vs Adult: {avg_adult:.1f}/1000)
    • Strong school-led update programmes (admissions, scholarships, PTAs) driving compliance""",

        'High Activity - Adult-Led Success': f"""
    🎯 PRIMARY DRIVER: Adults (18+) | {n_states} State(s)

    • Adult updates dominate (Adult: {avg_adult:.1f}/1000 vs Youth: {avg_youth:.1f}/1000)
    • Updates triggered by welfare schemes, migration, banking, and service mandates""",

        'Stagnation - System-Wide Failure': f"""
    ⚠️ SYSTEM-WIDE STAGNATION | {n_states} State(s)

    • Critically low engagement across youth and adults (Youth: {avg_youth:.1f}, Adult: {avg_adult:.1f}/1000)
    • Indicates infrastructure, awareness, or administrative failure
    • Requires urgent, multi-sector intervention or saturation validation""",

        'Stagnation - School Programs Failing': f"""
    ⚠️ YOUTH SEGMENT FAILURE | {n_states} State(s)

    • Youth updates lag despite active adult participation
    • School-based Aadhaar linkages and enforcement ineffective
    • Infrastructure exists but education-sector execution is weak""",

        'Stagnation - Adult Outreach Failing': f"""
    ⚠️ ADULT SEGMENT FAILURE | {n_states} State(s)

    • Adult updates lag despite active youth programs
    • Welfare, CSC, and workplace outreach underperforming
    • Potential indication of limited migration and job prospects"""
    }


    return analyses.get(pattern, "")