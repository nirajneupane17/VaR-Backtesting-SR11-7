import numpy as np, pandas as pd, pickle, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, MonthLocator

B = pickle.load(open('out/base.pkl', 'rb')); A = pickle.load(open('out/allvar.pkl', 'rb'))
roll = pickle.load(open('out/roll.pkl', 'rb'))
dates = pd.to_datetime(B['dates']); r = B['r']; idx = B['idx']; V = A['V']
od = dates[idx]; ro = r[idx] * 100
C = dict(HS='#2a78d6', N='#eb6834', FHS='#1baf7a', T='#eda100')
INK = '#2b2b2b'; MUTED = '#6b6b68'; GRID = '#e4e3df'
plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 9, 'axes.edgecolor': MUTED,
                     'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED,
                     'axes.spines.top': False, 'axes.spines.right': False})

# realised 21-day volatility (information to t-1) scaled to a Normal 99% quantile
rv = pd.Series(r).rolling(21).std().shift(1).values[idx] * 100 * 2.326

fig, axes = plt.subplots(2, 1, figsize=(7.2, 7.0))
for ax, yr in zip(axes, (2020, 2022)):
    m = od.year == yr; d = od[m]
    ax.bar(d, np.where(ro[m] < 0, -ro[m], 0), width=1.0, color='#c9c8c3', label='Daily loss (%)', zorder=1)
    ax.plot(d, rv[m], color=MUTED, lw=1.0, ls=':', label='2.326 × 21-day realised volatility', zorder=2)
    for k, ls, lab in (('HS', '-', 'Historical Simulation 99%'), ('N', '--', 'Parametric Normal 99%'),
                       ('FHS', '-.', 'Filtered HS (EWMA, λ=0.94) 99%')):
        ax.plot(d, V[k + '99'][m] * 100, color=C[k], lw=1.6, ls=ls, label=lab, zorder=3)
    viol = m & (ro < -V['N99'] * 100)
    ax.scatter(od[viol], -ro[viol], s=22, marker='v', color=C['N'], edgecolor='white', lw=0.6, zorder=4,
               label='Parametric Normal violation')
    ax.set_title(f'{yr}', loc='left', color=INK, fontsize=10, fontweight='bold')
    ax.set_ylabel('Loss / VaR (% of value)')
    ax.grid(axis='y', color=GRID, lw=0.6); ax.set_axisbelow(True)
    ax.xaxis.set_major_locator(MonthLocator(bymonth=[1, 3, 5, 7, 9, 11])); ax.xaxis.set_major_formatter(DateFormatter('%b'))
    ax.set_ylim(0, None if yr == 2020 else 6.5)
h,l=axes[0].get_legend_handles_labels()
fig.legend(h,l,loc='lower center',ncol=3,fontsize=7.5,frameon=False)
fig.tight_layout(rect=(0,0.07,1,1)); fig.savefig('out/figure1_var_paths.png', dpi=300); fig.savefig('out/figure1_var_paths.pdf')

fig, ax = plt.subplots(figsize=(7.2, 3.4))
for k, ls, lab in (('HS', '-', 'Historical Simulation'), ('N', '--', 'Parametric Normal'),
                   ('T', (0, (1, 1)), 'Student-t'), ('FHS', '-.', 'Filtered HS')):
    ax.step(roll[k]['end'], roll[k]['counts'], where='post', color=C[k], lw=1.5, ls=ls, label=lab)
ax.axhline(4.5, color=MUTED, lw=0.8); ax.axhline(9.5, color=MUTED, lw=0.8)
x0 = roll['HS']['end'][0] - pd.Timedelta(days=250)
ax.set_xlim(x0, roll['HS']['end'][-1] + pd.Timedelta(days=20))
for yv, t in ((2.0, 'Green\n(0–4)'), (7.0, 'Amber\n(5–9)'), (12.5, 'Red\n(≥10)')):
    ax.text(x0 + pd.Timedelta(days=15), yv, t, color=MUTED, fontsize=7.5, va='center')
ax.set_yticks(range(0, 21, 5))
ax.set_ylabel('99% violations in trailing 250 days'); ax.grid(axis='y', color=GRID, lw=0.6)
ax.legend(loc='upper right', fontsize=7.5, frameon=False, ncol=1)
fig.tight_layout(); fig.savefig('out/figure2_rolling_zones.png', dpi=300); fig.savefig('out/figure2_rolling_zones.pdf')
print('ok')
