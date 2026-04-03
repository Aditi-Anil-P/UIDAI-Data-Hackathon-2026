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

def get_targeted_recommendations(pattern, states_data):
    """Recommendations Actions"""

    recommendations = {
        'High Activity - School-Led Success': """

1. Standardize school-led Aadhaar update workflows for replication
2. Audit records to ensure quality and avoid duplication
3. Leverage schools/PTAs for parent and family outreach
4. Expand mobile enrollment camps via educational institutions""",

        'High Activity - Adult-Led Success': """

1. Identify key adult update drivers (migration, welfare schemes, address changes)
2. Strengthen CSC and enrollment infrastructure to manage sustained demand
3. Strengthen anomaly detection controls to flag mass address shifts or fraudulent updates.
4. Replicate high-performing adult outreach models in low-activity regions""",

        'Stagnation - System-Wide Failure': """

1. Conduct rapid audits of enrollment infrastructure and service availability
2. Deploy mobile enrollment units in remote areas
3. Launch local-language awareness campaigns
4. Integrate Aadhaar updates with public policies""",

        'Stagnation - School Programs Failing': """

1. Mandate Aadhaar verification during school admissions and examinations
2. Link scholarships and mid-day meals with Aadhaar verification
5. Monitor school-wise coverage as a performance indicator""",

        'Stagnation - Adult Outreach Failing': """

1. Link Aadhaar updates to welfare scheme renewals and service access
2. Expand and incentivise CSC operations in low-coverage areas
3. Target migrant workers, elderly, and women through focused outreach
4. Run awareness campaigns to increase participation"""
    }

    return recommendations.get(pattern, "")

# ==========================================
# 8. APPLY NEW CLASSIFICATION
# ==========================================

# First ensure all rate columns exist
if 'rate_5_17' not in analysis_df.columns:
    analysis_df['rate_5_17'] = 0
if 'rate_18_plus' not in analysis_df.columns:
    analysis_df['rate_18_plus'] = 0

deviated = analysis_df[analysis_df['hotspot'] != 'Normal'].copy()
deviated['Hotspot_ID'] = range(1, len(deviated) + 1)
deviated['pattern'] = deviated.apply(classify_pattern, axis=1)
deviated = deviated.sort_values(['pattern', 'z_score'], ascending=[True, False]).reset_index(drop=True)

# ==========================================
# 9. CREATE OUTPUT TABLES 
# ==========================================

output_rows = []
for idx, row in deviated.iterrows():
    output_rows.append({
        'Hotspot_ID': idx + 1,
        'State/UT': row['state_clean'],
        'Size': row['size_category'],
        'Category': row['hotspot'],
        'Pattern_Group': row['pattern'],
        'Z_Score': row['z_score'],
        'Update_Rate': row['monthly_update_rate'],
        'Enroll_Rate': row['monthly_enrollment_rate'],
        'Rate_5_17': row['rate_5_17'],
        'Rate_18+': row['rate_18_plus'],
        'Base_Population': row['base_aadhaar_population']
    })

output_table = pd.DataFrame(output_rows)

# ==========================================
# 10. VISUALIZATIONS
# ==========================================

colors = {'Low':'#302BE0', 'Normal':'#51F057', 'High':'#FF0000'}
markers = {'Small':'o', 'Medium':'s', 'Large':'^'}

plt.figure(figsize=(18, 12))

mean_update = analysis_df['monthly_update_rate'].mean()
mean_enroll = analysis_df['monthly_enrollment_rate'].mean()
max_enroll = analysis_df['monthly_enrollment_rate'].max()
max_update = analysis_df['monthly_update_rate'].max()

plt.axhline(y=mean_update, color='#FF8C00', linestyle='--', linewidth=2, alpha=0.9)
plt.text(x=max_enroll*0.95, y=mean_update + (max_update*0.01),
         s=f'Avg Update Rate: {mean_update:.1f}',
         color='#FF8C00', fontweight='bold', ha='right', fontsize=14, backgroundcolor='white')

plt.axvline(x=mean_enroll, color='#800080', linestyle='--', linewidth=2, alpha=0.9)
plt.text(x=mean_enroll + (max_enroll*0.01), y=max_update*0.95,
         s=f'Avg Enrollment Rate: {mean_enroll:.1f}',
         color='#800080', fontweight='bold', va='top', rotation=90, fontsize=14, backgroundcolor='white')

np.random.seed(42)
analysis_df['x_jitter'] = 0.0
analysis_df['y_jitter'] = 0.0
is_normal = analysis_df['hotspot'] == 'Normal'

analysis_df.loc[is_normal, 'x_jitter'] = np.random.uniform(
    -0.1 * analysis_df['monthly_enrollment_rate'].std(),
     0.1 * analysis_df['monthly_enrollment_rate'].std(),
    size=is_normal.sum()
)
analysis_df.loc[is_normal, 'y_jitter'] = np.random.uniform(
    -0.1 * analysis_df['monthly_update_rate'].std(),
     0.1 * analysis_df['monthly_update_rate'].std(),
    size=is_normal.sum()
)

for size in markers:
    for hs in colors:
        subset = analysis_df[(analysis_df['size_category'] == size) & (analysis_df['hotspot'] == hs)]
        if len(subset) > 0:
            plt.scatter(
                subset['monthly_enrollment_rate'] + subset['x_jitter'],
                subset['monthly_update_rate'] + subset['y_jitter'],
                s=700,
                c=colors[hs],
                marker=markers[size],
                edgecolors='black',
                alpha=0.7
            )

for row in deviated.itertuples():
    plt.text(
        row.monthly_enrollment_rate,
        row.monthly_update_rate,
        str(int(row.Hotspot_ID)),
        fontsize=14,
        fontweight='bold',
        ha='center',
        va='center',
        color='white'
    )

plt.xlabel('Monthly Enrollment Rate (per 1,000)', fontweight='bold', fontsize=16)
plt.ylabel('Monthly Demographic Update Rate (per 1,000)', fontweight='bold', fontsize=16)
plt.title('Monthly Aadhaar Demographic Update Activity Analysis \n', fontweight='bold', fontsize=20)
plt.grid(True, which="both", ls="-", alpha=0.15)
plt.ylim(bottom=0)

color_legend = [Patch(facecolor=colors[k], edgecolor='black', label=f'{k} Activity') for k in colors]
shape_legend = [Line2D([0], [0], marker=markers[k], color='w', markerfacecolor='gray',
                       markersize=15, label=f'{k} Population') for k in markers]

plt.legend(
    handles=color_legend + shape_legend,
    title='Legend',
    loc='upper left',
    bbox_to_anchor=(1.02, 1),
    fontsize=14,
    title_fontsize=16,
    borderaxespad=0
)

plt.tight_layout()
plt.show()

# BAR CHART
plt.figure(figsize=(20, 10))

cat_order = ['Small', 'Medium', 'Large']
analysis_df['size_category'] = pd.Categorical(
    analysis_df['size_category'],
    categories=cat_order,
    ordered=True
)
df_sorted = analysis_df.sort_values(['size_category', 'base_aadhaar_population']).reset_index(drop=True)

bar_colors = df_sorted['hotspot'].map(colors).tolist()

bars = plt.bar(
    df_sorted['state_clean'],
    df_sorted['monthly_update_rate'],
    color=bar_colors,
    edgecolor='black',
    alpha=0.85
)

current_idx = 0
max_val = df_sorted['monthly_update_rate'].max()
plt.ylim(0, max_val * 1.25)

for cat in cat_order:
    subset_len = len(df_sorted[df_sorted['size_category'] == cat])
    if subset_len > 0:
        end_idx = current_idx + subset_len
        if end_idx < len(df_sorted):
            plt.axvline(x=end_idx - 0.5, color='gray', linestyle=':', linewidth=2)

        mid_point = current_idx + (subset_len / 2) - 0.5
        plt.text(mid_point, max_val * 1.1,
                 f"{cat} States",
                 ha='center', va='bottom', fontweight='bold', fontsize=15,
                 bbox=dict(facecolor='#f0f0f0', edgecolor='gray', boxstyle='round,pad=0.3'))

        current_idx += subset_len

plt.axhline(y=mean_update, color='#FF8C00', linestyle='--', linewidth=2.5)
plt.text(len(df_sorted)-1, mean_update * 1.05, f'National Avg: {mean_update:.1f}',
         color='#FF8C00', fontweight='bold', ha='right', fontsize=12, backgroundcolor='white')

plt.xlabel('States (Sorted by Population Size)', fontweight='bold', fontsize=18)
plt.ylabel('Monthly Demographic Update Rate (per 1,000)', fontweight='bold', fontsize=16)
plt.title('\n\nState-wise Aadhaar Update Activity\n', fontweight='bold', fontsize=20, pad=20)
plt.xticks(rotation=90, fontsize=10)
plt.legend(handles=color_legend, title='Activity Level', fontsize=12, loc='upper left')
plt.tight_layout()
plt.show()

# AGE-WISE COMPARISON
def plot_agewise(df, title):
    if len(df) == 0:
        return
    x = np.arange(len(df))
    w = 0.32

    plt.figure(figsize=(14,6))
    plt.bar(x - w/2, df['rate_5_17'], w, label='Youth (5–17)', color='#1f77b4', edgecolor='black')
    plt.bar(x + w/2, df['rate_18_plus'], w, label='Adults (18+)', color='#ff7f0e', edgecolor='black')

    plt.xticks(x, df['state_clean'], ha='right')
    plt.ylabel('Updates per 1,000 (Age-Normalized)', fontweight='bold')
    plt.title(title, fontweight='bold', fontsize=14)
    plt.legend()
    plt.tight_layout()
    plt.show()

plot_agewise(
    analysis_df[analysis_df['hotspot']=='High'],
    'High Activity States : Driver Diagnosis'
)

plot_agewise(
    analysis_df[analysis_df['hotspot']=='Low'],
    'Low Activity States : Driver Diagnosis'
)