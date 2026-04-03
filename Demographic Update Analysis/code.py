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
