import numpy as np, pandas as pd, pickle
from scipy import stats
from core import *

d = load(); r = d.r.values
print('returns', len(r), d.Date.iloc[0].date(), d.Date.iloc[-1].date())
pct = r * 100
print('Table1 full: mean %.3f sd %.3f min %.3f max %.3f skew %.3f exkurt %.3f' % (
    pct.mean(), pct.std(ddof=1), pct.min(), pct.max(), stats.skew(pct), stats.kurtosis(pct)))
jb = stats.jarque_bera(pct); print('JB', round(jb.statistic, 1))
for nm, (a, b) in {'2018-19': ('2018', '2019'), '2020': ('2020', '2020'), '2021': ('2021', '2021'),
                   '2022': ('2022', '2022'), '2023-24': ('2023', '2024')}.items():
    m = (d.Date.dt.year >= int(a)) & (d.Date.dt.year <= int(b)); x = pct[m]
    print(nm, m.sum(), '%.3f %.3f %.3f %.3f %.3f %.3f' % (x.mean(), x.std(ddof=1), x.min(), x.max(),
                                                          stats.skew(x), stats.kurtosis(x)))

idx, V, nus = walk_forward(r)
print('first forecast date', d.Date.iloc[idx[0]].date(), 'n', len(idx))
ro = r[idx]
res = {}
for k, v in V.items():
    a = .95 if k.endswith('95') else .99
    I = (ro < -v).astype(int)
    N, lr, p = kupiec(I, 1 - a); c = christoffersen(I, 1 - a)
    res[k] = I
    print(k, 'mean %.3f min %.3f max %.3f final %.3f' % (v.mean() * 100, v.min() * 100, v.max() * 100, v[-1] * 100),
          '| N', N, 'LR %.3f p %.4f' % (lr, p), '| p01 %.2f p11 %.2f LRind %.3f (%.3f) LRcc %.3f (%.4f) n11=%d' % (
              c['p01'] * 100, c['p11'] * 100, c['lr_ind'], c['p_ind'], c['lr_cc'], c['p_cc'], c['n11']))
pickle.dump(dict(dates=d.Date.values, r=r, idx=idx, V=V, nus=nus), open('out/base.pkl', 'wb'))
