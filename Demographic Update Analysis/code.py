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