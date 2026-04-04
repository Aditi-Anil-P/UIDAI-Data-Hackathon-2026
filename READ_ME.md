Unlocking Societal Trends in Aadhaar Enrolment and Updates
UIDAI Data Hackathon 2026

Team ID: UIDAI_5018

Team Members
Aditi Anil Pulikottil (Team Lead)
Anushka Kar
Debasmita Pal
Surabi Mondal
Sneha Gupta
Project Overview

This project performs a multi-dimensional analysis of Aadhaar enrolment and update patterns across India using demographic, biometric, and population-level datasets.

The objective is to move beyond raw counts and extract policy-relevant insights that can help improve Aadhaar coverage, identify administrative gaps, and support targeted government intervention.

By integrating statistical modelling, population normalization, geospatial analysis, and rule-based classification, the project creates a data-driven governance framework for improving digital identity coverage.

Key Objectives

The project aims to:

Identify state-level anomalies in Aadhaar enrolment and updates
Detect age-group drivers behind update patterns
Highlight regional disparities in biometric updates
Compute population-weighted Aadhaar coverage gaps
Build predictive intervention zones for policy planning
Analyse Aadhaar linkage in welfare schemes such as Mid-Day Meals
Provide actionable recommendations for policymakers
Analytical Modules

The project consists of five major analytical frameworks.

1. Demographic Updates Data Analysis
Goal

Identify patterns in Aadhaar demographic updates and enrolment activity across states.

Key Techniques
Population normalization
Z-score based anomaly detection
Age-segmented update analysis
Metrics Used

Update Rate:

Total Updates / Aadhaar Population × 1000

Youth Update Rate (5–17):

Updates (5–17) / Youth Aadhaar Population × 1000

Adult Update Rate (18+):

Updates (18+) / Adult Aadhaar Population × 1000

Output

States are classified into activity groups:

High Activity – Adult Driven
High Activity – School Driven
System-Wide Stagnation
Youth Program Failures
Adult Outreach Failures
Policy Insight

Helps identify whether schools, welfare schemes, or migration patterns drive Aadhaar updates.

2. Biometric Update Data Analysis
Goal

Understand biometric update behaviour across states, districts, and age groups.

Key Metrics

Biometric Update Ratio:

Biometric Updates / Population

Age Skew Index:

Child Update Ratio / Adult Update Ratio

District Analysis

Districts were classified using IQR-based statistical outlier detection:

Lower Bound = Q1 − 1.5 × IQR
Upper Bound = Q3 + 1.5 × IQR

District Categories:

High performing districts
Normal districts
Low activity districts
Insights
Child updates dominate due to physiological growth
Adult updates reflect migration, correction drives, and service requirements
High activity clusters exist in small states and UTs
3. Population-Weighted Aadhaar Coverage Strategy
Goal

Identify Aadhaar enrolment gaps relative to population size.

Key Metric

Coverage Gap %

(Population − Aadhaar Count) / Population × 100

State Classification
Category	Gap %	Meaning
Critical	>10%	Major enrolment deficit
Moderate	3–10%	Targeted campaigns needed
Low	<3%	Near universal coverage
Saturated	<0%	Aadhaar exceeds population estimate
Insight

A small number of high-population states contribute to the majority of the national Aadhaar deficit.

4. Predictive Aadhaar Awareness Zones
Goal

Create a policy decision-support system that identifies which regions need what type of intervention.

Key Signals
Aadhaar Saturation (Population readiness)
Scheme Dependency Index (Policy reliance)
Classification Method
Quantile-based binning (pd.qcut)
Rule-based decision matrix
Policy Zones
Aadhaar Saturation	Scheme Dependency	Zone
Low	Low	Exclusion Risk Zone
Low	High	Access Bottleneck
High	Low	Awareness Gap
High	High	Digitally Mature
Medium	Any	Transition Zone
Output

A geospatial policy intelligence map showing intervention zones across India.

5. Aadhaar Awareness in Mid-Day Meal Scheme
Goal

Evaluate Aadhaar saturation among school children receiving Mid-Day Meals.

Three Statistical Benchmarks
Simple Mean
Weighted Mean
Median
Key Finding

Median State Performance: ~90.4%

National Weighted Mean: ~76.5%

This indicates the national deficit is caused by a few high-population states, not widespread failure.

Zones Identified

Green Zone (>90%)
Orange Zone (80–90%)
Red Zone (<National Average)

Tools & Technologies

The project was implemented entirely using open-source tools.

Programming
Python
Libraries
pandas
numpy
matplotlib
seaborn
geopandas
scikit-learn
Development Environment
Google Colab
Jupyter Notebook
Algorithms & Methods Used
Z-score anomaly detection
IQR outlier detection
Population normalization
Quantile-based classification
KNN imputation for missing values
Rule-based policy grid classification
Geospatial merging using GeoPandas

All algorithms are open-source and fully reproducible.

Impact & Policy Relevance

This framework enables:

Central Government

Identify digital exclusion zones

State Governments

Prioritize Aadhaar enrolment campaigns

District Administration

Deploy mobile enrolment drives

Policy Teams

Allocate budgets based on real data gaps
Key Contributions
Introduces population-weighted governance analytics
Combines demographic, biometric, and policy datasets
Creates a predictive intervention system
Provides region-specific policy recommendations
Repository Structure
project/
│
├── demographic_analysis.ipynb
├── biometric_update_analysis.ipynb
├── population_weighted_coverage.ipynb
├── predictive_awareness_zones.ipynb
├── mid_day_meal_analysis.ipynb
│
├── datasets/
│
└── README.md
Code Links

Demographic Analysis
https://colab.research.google.com/drive/1hA2sPqoGLACD2DYzOkaI-odpk32adSfh

Biometric Update Analysis
https://colab.research.google.com/drive/1GkMYr_RZgNgTeGYTze5kGCdcEiuMfAfT

Population Coverage Strategy
https://colab.research.google.com/drive/1iNfafYCLWh1c8n1WgzPEqwNkRBIEUB-c

Predictive Awareness Zones
https://colab.research.google.com/drive/13k9HkluZBPV_T7fwhD8L6uZmuz86V8n6

Mid-Day Meal Analysis
https://colab.research.google.com/drive/1oHTc6McaTIEALC2MfHFnyw4LWzvnwlVH

Data Sources
UIDAI Data Hackathon 2026 Dataset
data.gov.in Open Government Data
UIDAI Aadhaar Saturation Reports
Mid-Day Meal Scheme datasets
Final Conclusion

This project demonstrates that effective Aadhaar governance requires moving from blanket national strategies to targeted, data-driven interventions.

By combining statistical normalization, geospatial analytics, and policy modeling, the framework identifies coverage gaps, demographic drivers, and operational inefficiencies.

The approach provides a scalable governance intelligence system capable of guiding future Aadhaar policy decisions and ensuring inclusive digital identity coverage across India.