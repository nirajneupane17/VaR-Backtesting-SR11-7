import numpy as np, pandas as pd, pickle, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
roll=pickle.load(open('out/robust_roll.pkl','rb'))
C=dict(HS='#2a78d6',N='#eb6834',FHS='#1baf7a',T='#eda100'); INK='#2b2b2b'; MUTED='#6b6b68'; GRID='#e4e3df'
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':9,'axes.edgecolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(2,1,figsize=(7.2,5.2),sharex=True)
for ax,keys in zip(axes,(('HS','N','T'),('HS','FHS'))):
    for k,ls,lab in (('HS','-','Historical Simulation'),('N','--','Parametric Normal'),('T',(0,(1,1)),'Student-t'),('FHS','-.','Filtered HS')):
        if k in keys: ax.step(pd.to_datetime(roll[k]['end']),roll[k]['counts'],where='post',color=C[k],lw=1.2,ls=ls,label=lab)
    ax.axhline(4.5,color=MUTED,lw=0.8); ax.axhline(9.5,color=MUTED,lw=0.8)
    ax.set_ylabel('99% violations, trailing 250 days'); ax.grid(axis='y',color=GRID,lw=0.6); ax.set_ylim(0,31); ax.set_xlim(pd.Timestamp('2000-06-01'),pd.Timestamp('2028-06-01'))
    ax.legend(loc='upper left',bbox_to_anchor=(0,0.86),fontsize=7.5,frameon=False,ncol=3)
for x,t in (('2002-07-01','Dot-com'),('2008-10-15','GFC'),('2011-09-01','2011'),('2020-04-01','COVID'),('2022-10-01','2022')):
    axes[0].text(pd.Timestamp(x),29,t,color=MUTED,fontsize=7,ha='center')
axes[1].text(pd.Timestamp('2027-01-01'),2.0,'Green',color=MUTED,fontsize=7); axes[1].text(pd.Timestamp('2027-01-01'),6.6,'Amber',color=MUTED,fontsize=7); axes[1].text(pd.Timestamp('2027-01-01'),11,'Red',color=MUTED,fontsize=7)
fig.tight_layout(); fig.savefig('out/figure3_rolling_zones_long.png',dpi=300); print('ok')
