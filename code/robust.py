"""Robustness: walk-forward backtest over Jan 2000 - Oct 2026 (estimation from 1999)."""
import numpy as np, pandas as pd, pickle, json, warnings
from scipy import stats
from arch import arch_model
from core import kupiec, christoffersen, hs_var, normal_var, t_fit, t_var, ewma_sigma, W
warnings.filterwarnings('ignore')

import os
d = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sp500_close_1999_2026.csv'), parse_dates=['Date'])
d['r'] = np.log(d.Close).diff(); d = d.dropna().reset_index(drop=True)
r = d.r.values; dates = d.Date
start = np.searchsorted(dates.values, np.datetime64('2000-01-03'))
assert start >= W
idx = np.arange(start, len(r)); od = dates.iloc[idx].reset_index(drop=True); ro = r[idx]; P = len(idx)
print('returns', len(r), dates.iloc[0].date(), '| OOS', od.iloc[0].date(), od.iloc[-1].date(), 'P', P)

sig = ewma_sigma(r, 0.94, seed_n=W)
V = {k: np.empty(P) for k in ['HS95', 'HS99', 'N95', 'N99', 'T95', 'T99', 'EN95', 'EN99', 'FHS95', 'FHS99', 'G95', 'G99']}
nus = np.empty(P)
for j, t in enumerate(idx):
    x = r[t - W:t]
    for a_, tag in ((.95, '95'), (.99, '99')):
        V['HS' + tag][j] = hs_var(x, a_); V['N' + tag][j] = normal_var(x, a_)
        V['EN' + tag][j] = -stats.norm.ppf(1 - a_) * sig[t]
        V['FHS' + tag][j] = -np.quantile(x / sig[t - W:t], 1 - a_) * sig[t]
    pr = t_fit(x); nus[j] = pr[0]
    V['T95'][j] = t_var(pr, .95); V['T99'][j] = t_var(pr, .99)
    f = arch_model(x * 100, mean='Constant', vol='GARCH', p=1, q=1, dist='t').fit(disp='off', show_warning=False)
    fc = f.forecast(horizon=1, reindex=False); mu = fc.mean.values[-1, 0]; s = np.sqrt(fc.variance.values[-1, 0]); nu = f.params['nu']
    for a_, tag in ((.95, '95'), (.99, '99')):
        V['G' + tag][j] = -(mu + stats.t.ppf(1 - a_, nu) * np.sqrt((nu - 2) / nu) * s) / 100
pickle.dump(dict(dates=od.values, ro=ro, V=V, nus=nus, sig=sig[idx]), open('out/robust_var.pkl', 'wb'))
print('VaR done')


def duration_lr(I):
    from scipy.optimize import minimize_scalar
    h = np.where(I == 1)[0]; T = len(I)
    if len(h) < 2: return np.nan, np.nan
    D = np.diff(h).astype(float); dl = T - h[-1] - 1.0
    durs = np.array([h[0] + 1.0] + list(D) + ([dl] if dl > 0 else []))
    cens = np.array([1] + [0] * len(D) + ([1] if dl > 0 else []))
    nunc = np.sum(cens == 0)

    def nll(bb):
        aa = (nunc / np.sum(durs ** bb)) ** (1 / bb)
        lf = bb * np.log(aa) + np.log(bb) + (bb - 1) * np.log(durs) - (aa * durs) ** bb
        return -np.sum(np.where(cens == 1, -(aa * durs) ** bb, lf))
    rb = minimize_scalar(nll, bounds=(0.05, 5), method='bounded')
    return 2 * (nll(1.0) - rb.fun), rb.x


rng = np.random.default_rng(20261124)
names = ['HS', 'N', 'T', 'EN', 'FHS', 'G']
rows = []; I = {}
y = od.dt.year.values
for m in names:
    for tag, a_ in (('99', .99), ('95', .95)):
        Ii = (ro < -V[m + tag]).astype(int); I[m + tag] = Ii; p = 1 - a_
        N, lr, pu = kupiec(Ii, p); c = christoffersen(Ii, p); dl, bh = duration_lr(Ii)
        ph = Ii.mean(); si = np.empty(4999); sc = np.empty(4999); sd = []
        for s in range(4999):
            z = (rng.random(P) < ph).astype(int); si[s] = christoffersen(z, p)['lr_ind']
            z2 = (rng.random(P) < p).astype(int); sc[s] = christoffersen(z2, p)['lr_cc']
            if s < 999: sd.append(duration_lr(z)[0])
        sd = np.array(sd)
        rows.append(dict(model=m, conf=tag, N=N, exp=P * p, rate=ph * 100, LRuc=lr, p_uc=pu, n11=c['n11'],
                         p01=c['p01'] * 100, p11=c['p11'] * 100, p_ind=c['p_ind'],
                         p_ind_mc=(1 + np.sum(si >= c['lr_ind'])) / 5000, p_cc_mc=(1 + np.sum(sc >= c['lr_cc'])) / 5000,
                         b=bh, LRdur=dl, p_dur_mc=(1 + np.sum(sd >= dl)) / (len(sd) + 1), meanVaR=V[m + tag].mean() * 100))
        print(rows[-1]['model'], tag, N, round(pu, 4), rows[-1]['p_ind_mc'], rows[-1]['p_dur_mc'], flush=True)
RT = pd.DataFrame(rows); RT.to_csv('out/robust_tests.csv', index=False)

# yearly 99% counts
yrs = sorted(set(y))
Y = pd.DataFrame({m: [int(I[m + '99'][y == k].sum()) for k in yrs] for m in names}, index=yrs)
Y['days'] = [int((y == k).sum()) for k in yrs]; Y['exp'] = Y.days * 0.01
Y.to_csv('out/robust_yearly99.csv'); print(Y.to_string())

# episodes
EP = {'Dot-com decline (Mar 2000-Oct 2002)': ('2000-03-24', '2002-10-09', 'gradual'),
      'GFC crash (Sep 2008-Mar 2009)': ('2008-09-01', '2009-03-09', 'abrupt'),
      'Aug-Oct 2011 sell-off': ('2011-07-25', '2011-10-03', 'abrupt'),
      'Q4 2018 sell-off': ('2018-10-01', '2018-12-24', 'abrupt'),
      'COVID crash (Feb-Mar 2020)': ('2020-02-20', '2020-04-30', 'abrupt'),
      '2022 rate-hike decline': ('2022-01-03', '2022-12-30', 'gradual')}
ep = []
for nm, (s0, s1, kind) in EP.items():
    mk = ((od >= s0) & (od <= s1)).values; n = mk.sum()
    row = dict(episode=nm, kind=kind, days=int(n), exp=n * .01, realised_sd=float(ro[mk].std() * 100),
               window_sd=float(np.mean([r[t - W:t].std() for t in idx[mk]]) * 100), ewma_sd=float(np.mean(sig[idx[mk]]) * 100))
    for m in names: row[m] = int(I[m + '99'][mk].sum())
    ep.append(row)
E = pd.DataFrame(ep); E.to_csv('out/robust_episodes.csv', index=False); print(E.round(2).to_string())

# rolling zones
def zone(n): return 'Green' if n <= 4 else ('Amber' if n <= 9 else 'Red')
roll = {}
for m in names:
    cs = np.concatenate([[0], np.cumsum(I[m + '99'])]); cnt = cs[W:] - cs[:-W]
    z = pd.Series([zone(c) for c in cnt])
    roll[m] = dict(counts=cnt, end=od.iloc[W - 1:].values, share={k: float((z == k).mean()) for k in ('Green', 'Amber', 'Red')})
    print(m, roll[m]['share'])
pickle.dump(roll, open('out/robust_roll.pkl', 'wb'))
nuq = dict(share_le2=float(np.mean(nus <= 2)), med=float(np.median(nus)))
json.dump(dict(P=int(P), oos_start=str(od.iloc[0].date()), oos_end=str(od.iloc[-1].date()), nu=nuq,
               roll={k: v['share'] for k, v in roll.items()}, n_windows=int(len(roll['HS']['counts']))),
          open('out/robust_summary.json', 'w'), indent=1)
print('nu', nuq)
