#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visualization script for loan prediction results
Creates charts showing success and rejection rates
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'

# Load predictions
df = pd.read_csv('predictions_output.csv')

# Calculate statistics
total_loans = len(df)
success_count = (df['Final_Decision'] == 'success').sum()
rejected_count = (df['Final_Decision'] == 'rejected').sum()
success_rate = (success_count / total_loans) * 100
rejected_rate = (rejected_count / total_loans) * 100

print("\n" + "="*80)
print("LOAN PREDICTION RESULTS - VISUAL ANALYSIS")
print("="*80)
print(f"\nTotal Applications: {total_loans}")
print(f"✅ Success (Approved): {success_count} loans ({success_rate:.1f}%)")
print(f"❌ Rejected: {rejected_count} loans ({rejected_rate:.1f}%)")
print(f"Average Default Probability: {df['Ensemble_Default_Prob'].mean():.2%}")
print("\n" + "="*80)

# Create figure with multiple subplots
fig = plt.figure(figsize=(16, 12))

# =============== 1. PIE CHART - Success vs Rejected ===============
ax1 = plt.subplot(2, 3, 1)
colors = ['#2ecc71', '#e74c3c']  # Green for success, Red for rejected
sizes = [success_count, rejected_count]
labels = [f'Success\n{success_count}\n({success_rate:.1f}%)', 
          f'Rejected\n{rejected_count}\n({rejected_rate:.1f}%)']
explode = (0.05, 0.05)

wedges, texts, autotexts = ax1.pie(sizes, labels=labels, colors=colors, autopct='', 
                                     startangle=90, explode=explode, textprops={'fontsize': 12, 'weight': 'bold'})
ax1.set_title('Success vs Rejection Rate', fontsize=14, weight='bold', pad=20)

# =============== 2. BAR CHART - Comparison ===============
ax2 = plt.subplot(2, 3, 2)
categories = ['Success', 'Rejected']
counts = [success_count, rejected_count]
bars = ax2.bar(categories, counts, color=colors, width=0.6, edgecolor='black', linewidth=2)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=12, weight='bold')

ax2.set_ylabel('Number of Loans', fontsize=11, weight='bold')
ax2.set_title('Loan Decisions - Count Comparison', fontsize=14, weight='bold', pad=20)
ax2.set_ylim(0, max(counts) * 1.15)
ax2.grid(axis='y', alpha=0.3)

# =============== 3. PERCENTAGE BAR ===============
ax3 = plt.subplot(2, 3, 3)
rates = [success_rate, rejected_rate]
bars = ax3.barh(['Success', 'Rejected'], rates, color=colors, height=0.5, edgecolor='black', linewidth=2)

# Add percentage labels
for i, bar in enumerate(bars):
    width = bar.get_width()
    ax3.text(width/2, bar.get_y() + bar.get_height()/2,
            f'{rates[i]:.1f}%',
            ha='center', va='center', fontsize=14, weight='bold', color='white')

ax3.set_xlabel('Percentage (%)', fontsize=11, weight='bold')
ax3.set_title('Success & Rejection Percentage', fontsize=14, weight='bold', pad=20)
ax3.set_xlim(0, 100)
ax3.grid(axis='x', alpha=0.3)

# =============== 4. DEFAULT PROBABILITY DISTRIBUTION ===============
ax4 = plt.subplot(2, 3, 4)
df_success = df[df['Final_Decision'] == 'success']['Ensemble_Default_Prob']
df_rejected = df[df['Final_Decision'] == 'rejected']['Ensemble_Default_Prob']

ax4.hist(df_success, bins=30, alpha=0.7, label='Success', color='#2ecc71', edgecolor='black')
ax4.hist(df_rejected, bins=30, alpha=0.7, label='Rejected', color='#e74c3c', edgecolor='black')
ax4.axvline(0.5, color='black', linestyle='--', linewidth=2, label='Decision Threshold (50%)')
ax4.set_xlabel('Default Probability', fontsize=11, weight='bold')
ax4.set_ylabel('Frequency', fontsize=11, weight='bold')
ax4.set_title('Default Probability Distribution', fontsize=14, weight='bold', pad=20)
ax4.legend(fontsize=10)
ax4.grid(axis='y', alpha=0.3)

# =============== 5. BOX PLOT ===============
ax5 = plt.subplot(2, 3, 5)
data_to_plot = [df_success, df_rejected]
bp = ax5.boxplot(data_to_plot, labels=['Success', 'Rejected'], patch_artist=True,
                  notch=True, showmeans=True)

for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax5.set_ylabel('Default Probability', fontsize=11, weight='bold')
ax5.set_title('Default Probability - Distribution Stats', fontsize=14, weight='bold', pad=20)
ax5.grid(axis='y', alpha=0.3)
ax5.axhline(0.5, color='black', linestyle='--', linewidth=1, alpha=0.5)

# =============== 6. STATISTICS TABLE ===============
ax6 = plt.subplot(2, 3, 6)
ax6.axis('off')

stats_data = [
    ['Metric', 'Success', 'Rejected'],
    ['Count', f'{success_count}', f'{rejected_count}'],
    ['Percentage', f'{success_rate:.1f}%', f'{rejected_rate:.1f}%'],
    ['Avg Default Prob', f'{df_success.mean():.2%}', f'{df_rejected.mean():.2%}'],
    ['Min Default Prob', f'{df_success.min():.2%}', f'{df_rejected.min():.2%}'],
    ['Max Default Prob', f'{df_success.max():.2%}', f'{df_rejected.max():.2%}'],
    ['Median Default Prob', f'{df_success.median():.2%}', f'{df_rejected.median():.2%}'],
]

table = ax6.table(cellText=stats_data, cellLoc='center', loc='center',
                  colWidths=[0.35, 0.32, 0.32])
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 2.5)

# Style header row
for i in range(3):
    table[(0, i)].set_facecolor('#34495e')
    table[(0, i)].set_text_props(weight='bold', color='white')

# Style data rows with alternating colors
for i in range(1, len(stats_data)):
    for j in range(3):
        if j == 0:
            table[(i, j)].set_facecolor('#ecf0f1')
            table[(i, j)].set_text_props(weight='bold')
        elif j == 1:
            table[(i, j)].set_facecolor('#d5f4e6')
        else:
            table[(i, j)].set_facecolor('#fadbd8')

ax6.set_title('Detailed Statistics', fontsize=14, weight='bold', pad=20)

# Overall title
fig.suptitle('Loan Default Prediction - Results Visualization', 
             fontsize=16, weight='bold', y=0.995)

plt.tight_layout()
plt.savefig('reports/loan_prediction_visualization.png', dpi=300, bbox_inches='tight')
print("\n[OK] Visualization saved to: reports/loan_prediction_visualization.png")

# Show plot
plt.show()

# =============== ADDITIONAL: Create a simple dashboard ===============
print("\n" + "="*80)
print("QUICK SUMMARY")
print("="*80)
print(f"\n📊 Total Loans Analyzed: {total_loans}")
print(f"\n✅ APPROVED LOANS: {success_count}")
print(f"   • Success Rate: {success_rate:.1f}%")
print(f"   • Avg Risk: {df_success.mean():.2%}")
print(f"\n❌ REJECTED LOANS: {rejected_count}")
print(f"   • Rejection Rate: {rejected_rate:.1f}%")
print(f"   • Avg Risk: {df_rejected.mean():.2%}")
print(f"\n🎯 Decision Threshold: 50% Default Probability")
print("\n" + "="*80)
