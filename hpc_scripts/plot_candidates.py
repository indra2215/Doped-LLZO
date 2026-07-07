import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

df = pd.read_csv(r'd:\doped_2\FINAL_Results\High_Performance_Pipeline\MASTER_RESULTS.csv')

fig, axes = plt.subplots(1, 2, figsize=(16, 8))
fig.patch.set_facecolor('#0f0f1a')

# --- Plot 1: Ranked conductivity bar chart ---
ax1 = axes[0]
ax1.set_facecolor('#1a1a2e')
colors = ['#00d4ff' if i < 5 else '#7b68ee' if i < 10 else '#4a4a7a' for i in range(len(df))]
bars = ax1.barh(range(len(df)), df['gpr_predicted_sigma_S_cm'] * 1000, color=colors, alpha=0.85, edgecolor='none')
ax1.set_yticks(range(len(df)))
ax1.set_yticklabels([f"{r['rank']}. {r['formula'][:30]}" for _, r in df.iterrows()], fontsize=6.5, color='white')
ax1.invert_yaxis()
ax1.set_xlabel('GPR Predicted σ_RT (mS/cm)', color='white', fontsize=11)
ax1.set_title('Top 35 LLZO Candidates\nRanked by Predicted Ionic Conductivity', color='white', fontsize=12, fontweight='bold')
ax1.tick_params(colors='white')
ax1.spines['bottom'].set_color('#333355')
ax1.spines['top'].set_color('#333355')
ax1.spines['left'].set_color('#333355')
ax1.spines['right'].set_color('#333355')
ax1.axvline(x=0.1, color='#ff6b6b', linestyle='--', alpha=0.6, label='0.1 mS/cm threshold')
gold   = mpatches.Patch(color='#00d4ff', label='Top 5')
silver = mpatches.Patch(color='#7b68ee', label='Top 6-10')
rest   = mpatches.Patch(color='#4a4a7a', label='Remaining')
ax1.legend(handles=[gold, silver, rest], facecolor='#1a1a2e', labelcolor='white', fontsize=9)

# --- Plot 2: Energy vs Conductivity scatter ---
ax2 = axes[1]
ax2.set_facecolor('#1a1a2e')
energy = df['chgnet_energy_eV_per_atom'].clip(-10, 100)
sigma  = df['gpr_predicted_sigma_S_cm'] * 1000
sc = ax2.scatter(energy, sigma, c=df['rank'], cmap='plasma_r', s=90, alpha=0.9, edgecolors='white', linewidths=0.4)
for _, row in df.head(5).iterrows():
    e = min(row['chgnet_energy_eV_per_atom'], 100)
    ax2.annotate(f"#{int(row['rank'])}", xy=(e, row['gpr_predicted_sigma_S_cm']*1000),
                 xytext=(5, 3), textcoords='offset points', color='#00d4ff', fontsize=9, fontweight='bold')
cbar = plt.colorbar(sc, ax=ax2)
cbar.set_label('Rank', color='white')
cbar.ax.yaxis.set_tick_params(color='white')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white')
ax2.set_xlabel('CHGNet Energy/atom (eV/atom, clipped at 100)', color='white', fontsize=10)
ax2.set_ylabel('GPR Predicted σ_RT (mS/cm)', color='white', fontsize=10)
ax2.set_title('Conductivity vs. CHGNet Relaxation Energy\n(lower energy = more stable structure)', color='white', fontsize=12, fontweight='bold')
ax2.tick_params(colors='white')
ax2.spines['bottom'].set_color('#333355')
ax2.spines['top'].set_color('#333355')
ax2.spines['left'].set_color('#333355')
ax2.spines['right'].set_color('#333355')

plt.tight_layout(pad=2.5)
out = r'd:\doped_2\FINAL_Results\High_Performance_Pipeline\candidates_overview.png'
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#0f0f1a')
print('Saved:', out)
