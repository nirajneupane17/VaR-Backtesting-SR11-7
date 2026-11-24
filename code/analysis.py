"""New analyses for the revision (Reviewer 5 comments 1-5, minor 10-11)."""
import numpy as np, pandas as pd, pickle, json, warnings
from scipy import stats
from core import *
warnings.filterwarnings('ignore')

B = pickle.load(open('out/base.pkl', 'rb'))
dates = pd.to_datetime(B['dates']); r = B['r']; idx = B['idx']; V = dict(B['V']); nus = B['nus']
ro = r[idx]; od = dates[idx]; P = len(idx)
R = {}

# ---------------- conditional benchmarks ----------------
sig = ewma_sigma(r, 0.94, seed_n=W)           # sigma_t from info to t-1
for a, tag in ((.95, '95'), (.99, '99')):
    V['EN' + tag] = np.array([-(stats.norm.ppf(1 - a) * sig[t]) for t in idx])      # EWMA-Normal, zero mean
    fh = np.empty(P)
    for j, t in enumerate(idx):
        z = r[t - W:t] / sig[t - W:t]
        fh[j] = -np.quantile(z, 1 - a) * sig[t]
    V['FHS' + tag] = fh

# GARCH(1,1)-t, re-estimated daily on trailing 250 obs (rolling) -- conditional benchmark
from arch import arch_model
g95 = np.empty(P); g99 = np.empty(P)
for j, t in enumerate(idx):
    x = r[t - W:t] * 100
    am = arch_model(x, mean='Constant', vol='GARCH', p=1, q=1, dist='t')
    f = am.fit(disp='off', show_warning=False)
    fc = f.forecast(horizon=1, reindex=False)
    mu = fc.mean.values[-1, 0]; s = np.sqrt(fc.variance.values[-1, 0]); nu = f.params['nu']
    qs = lambda a: stats.t.ppf(1 - a, nu) * np.sqrt((nu - 2) / nu)   # standardised t
    g95[j] = -(mu + qs(.95) * s) / 100; g99[j] = -(mu + qs(.99) * s) / 100
V['G95'] = g95; V['G99'] = g99

# Student-t with nu bounded in [2.1,100]
tb95 = np.empty(P); tb99 = np.empty(P); nub = np.empty(P)
for j, t in enumerate(idx):
    pr = t_fit(r[t - W:t], bounded=True); nub[j] = pr[0]
    tb95[j] = t_var(pr, .95); tb99[j] = t_var(pr, .99)
V['TB95'] = tb95; V['TB99'] = tb99
pickle.dump(dict(V=V, nus=nus, nub=nub, sig=sig), open('out/allvar.pkl', 'wb'))

names = dict(HS='Historical Simulation', N='Parametric Normal', T='Student-t (MLE)',
             TB='Student-t (nu in [2.1,100])', EN='EWMA-Normal', FHS='Filtered HS', G='GARCH(1,1)-t')
rows = []
I = {}
for m in names:
    for tag, a in (('95', .95), ('99', .99)):
        v = V[m + tag]; Ii = (ro < -v).astype(int); I[m + tag] = Ii
        N, lr, p = kupiec(Ii, 1 - a); c = christoffersen(Ii, 1 - a)
        y = od.year
        rows.append(dict(model=m, conf=tag, N=N, rate=N / P * 100, LRuc=lr, p_uc=p, n11=c['n11'],
                         p01=c['p01'] * 100, p11=c['p11'] * 100, LRind=c['lr_ind'], p_ind=c['p_ind'],
                         LRcc=c['lr_cc'], p_cc=c['p_cc'],
                         y2019=Ii[y == 2019].sum(), y2020=Ii[y == 2020].sum(), y2021=Ii[y == 2021].sum(),
                         y2022=Ii[y == 2022].sum(), y2324=Ii[(y >= 2023)].sum(),
                         meanVaR=v.mean() * 100))
T8 = pd.DataFrame(rows); T8.to_csv('out/benchmarks.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(T8.round(3).to_string())

# ---------------- Fisher exact 2020 vs 2022 ----------------
y = od.year; n20 = (y == 2020).sum(); n22 = (y == 2022).sum()
fish = {}
for m in names:
    for tag in ('95', '99'):
        a = I[m + tag][y == 2020].sum(); b = I[m + tag][y == 2022].sum()
        fish[m + tag] = (int(a), int(n20), int(b), int(n22), stats.fisher_exact([[a, n20 - a], [b, n22 - b]])[1])
print('\nFisher 2020 vs 2022:'); [print(k, v[0], '/', v[1], 'vs', v[2], '/', v[3], 'p=%.3f' % v[4]) for k, v in fish.items()]

# ---------------- subperiod clustering (95%) ----------------
sub = {'2019': y == 2019, '2020': y == 2020, '2021': y == 2021, '2022': y == 2022, '2023-24': y >= 2023}
subc = []
for m in ('HS', 'N', 'T', 'FHS', 'EN'):
    for tag in ('95', '99'):
        for s, mask in sub.items():
            Ii = I[m + tag][mask]; c = christoffersen(Ii, .05 if tag == '95' else .01)
            subc.append(dict(model=m, conf=tag, period=s, N=int(Ii.sum()), n11=int(c['n11']),
                             p11=c['p11'] * 100, p_ind=c['p_ind']))
SC = pd.DataFrame(subc); SC.to_csv('out/subperiod_cluster.csv', index=False)
print('\nSubperiod clustering:'); print(SC[SC.conf == '95'].round(3).to_string())

# ---------------- Monte Carlo p-values: independence & duration ----------------
def duration_lr(Ii):
    """Christoffersen-Pelletier (2004) Weibull duration test with censored first/last spells."""
    hits = np.where(Ii == 1)[0]; T = len(Ii)
    if len(hits) < 2: return np.nan
    D = np.diff(hits).astype(float)
    d0 = hits[0] + 1.0; dl = T - hits[-1] - 1.0
    durs = [d0] + list(D) + ([dl] if dl > 0 else [])
    cens = [1] + [0] * len(D) + ([1] if dl > 0 else [])
    durs = np.array(durs); cens = np.array(cens)

    def ll(b, a):
        # Weibull: f = a^b b d^(b-1) exp(-(a d)^b), S = exp(-(a d)^b)
        lf = b * np.log(a) + np.log(b) + (b - 1) * np.log(durs) - (a * durs) ** b
        lS = -(a * durs) ** b
        return np.sum(np.where(cens == 1, lS, lf))
    from scipy.optimize import minimize_scalar
    nunc = np.sum(cens == 0)

    def prof(b):  # profile out a
        a = (nunc / np.sum(durs ** b)) ** (1 / b)
        return -ll(b, a)
    rb = minimize_scalar(prof, bounds=(0.05, 5), method='bounded')
    l1 = -rb.fun; l0 = -prof(1.0)
    return 2 * (l1 - l0), rb.x


rng = np.random.default_rng(20261123)
MC = {}
nsim = 9999
for m in ('HS', 'N', 'T', 'FHS', 'EN', 'G', 'TB'):
    for tag, a in (('95', .95), ('99', .99)):
        Ii = I[m + tag]; ph = Ii.mean(); c = christoffersen(Ii, 1 - a)
        dl = duration_lr(Ii)
        sim_ind = np.empty(nsim); sim_cc = np.empty(nsim); sim_dur = np.empty(nsim)
        for s in range(nsim):
            z = (rng.random(P) < ph).astype(int)        # H0 independence at observed rate
            sim_ind[s] = christoffersen(z, 1 - a)['lr_ind'] if z.sum() > 0 else 0
            z2 = (rng.random(P) < 1 - a).astype(int)     # H0 correct coverage
            sim_cc[s] = christoffersen(z2, 1 - a)['lr_cc'] if z2.sum() > 0 else 0
            if s < 1999:
                dd = duration_lr(z)
                sim_dur[s] = dd[0] if isinstance(dd, tuple) else np.nan
        sd = sim_dur[:1999]; sd = sd[~np.isnan(sd)]
        MC[m + tag] = dict(LRind=c['lr_ind'], p_ind_asy=c['p_ind'],
                           p_ind_mc=(1 + np.sum(sim_ind >= c['lr_ind'])) / (nsim + 1),
                           LRcc=c['lr_cc'], p_cc_mc=(1 + np.sum(sim_cc >= c['lr_cc'])) / (nsim + 1),
                           LRdur=dl[0], weib_b=dl[1],
                           p_dur_mc=(1 + np.sum(sd >= dl[0])) / (len(sd) + 1),
                           p_dur_asy=stats.chi2.sf(dl[0], 1))
MCd = pd.DataFrame(MC).T; MCd.to_csv('out/mc_pvalues.csv')
print('\nMC p-values:'); print(MCd.round(4).to_string())

# ---------------- Student-t nu distribution ----------------
nuq = dict(share_le2=float(np.mean(nus <= 2)), share_lt3=float(np.mean(nus < 3)),
           share_lt2_5=float(np.mean(nus < 2.5)),
           q05=float(np.quantile(nus, .05)), q25=float(np.quantile(nus, .25)), med=float(np.median(nus)),
           q75=float(np.quantile(nus, .75)), q95=float(np.quantile(nus, .95)), min=float(nus.min()),
           max=float(nus.max()),
           share_le2_2020=float(np.mean(nus[y == 2020] <= 2)),
           by_year_median={int(k): float(np.median(nus[y == k])) for k in range(2019, 2025)},
           by_year_share_le2={int(k): float(np.mean(nus[y == k] <= 2)) for k in range(2019, 2025)},
           bounded_max99=float(V['TB99'].max() * 100), mle_max99=float(V['T99'].max() * 100),
           bounded_mean99=float(V['TB99'].mean() * 100))
print('\nnu:', json.dumps(nuq, indent=1))

# ---------------- rolling Basel zones (99%) ----------------
def zone(n): return 'Green' if n <= 4 else ('Amber' if n <= 9 else 'Red')
roll = {}
for m in ('HS', 'N', 'T', 'FHS', 'EN', 'G'):
    Ii = I[m + '99']; cs = np.concatenate([[0], np.cumsum(Ii)])
    cnt = cs[W:] - cs[:-W]          # windows ending at OOS day W-1 .. P-1
    end = od[W - 1:]
    z = pd.Series([zone(c) for c in cnt])
    roll[m] = dict(counts=cnt, end=end,
                   share={k: float((z == k).mean()) for k in ('Green', 'Amber', 'Red')},
                   by_year={int(yr): {k: float((z[end.year == yr] == k).mean()) for k in ('Green', 'Amber', 'Red')}
                            for yr in range(2019, 2025)},
                   final=int(cnt[-1]))
    print(m, 'final', cnt[-1], roll[m]['share'])
pickle.dump(roll, open('out/roll.pkl', 'wb'))
print('P(N>=5 | p=.01,n=250)=%.4f  P(N>=10)=%.5f' % (stats.binom.sf(4, 250, .01), stats.binom.sf(9, 250, .01)))
print('final-window dates', od[-250].date(), od[-1].date())

# ---------------- multiple testing (Holm) on 18 original p-values ----------------
base = T8[T8.model.isin(['HS', 'N', 'T'])]
pv = []
for _, rw in base.iterrows():
    for k in ('p_uc', 'p_ind', 'p_cc'): pv.append((rw.model + rw.conf, k, rw[k]))
ps = np.array([p for *_, p in pv]); order = np.argsort(ps); m_ = len(ps)
holm = np.empty(m_); run = 0
for rank, i in enumerate(order):
    run = max(run, min(1, (m_ - rank) * ps[i])); holm[i] = run
MT = pd.DataFrame(pv, columns=['combo', 'test', 'p']); MT['holm'] = holm; MT['bonf'] = np.minimum(1, ps * m_)
MT.to_csv('out/multiple_testing.csv', index=False); print('\nHolm:'); print(MT.round(4).to_string())

# ---------------- static calibration comparison ----------------
st = []
x18 = r[:W]; xall = r
for lab, x in (('2018 only (single calibration)', x18), ('Full sample 2018-24 (look-ahead)', xall)):
    pr = t_fit(x)
    for tag, a in (('95', .95), ('99', .99)):
        for m, v in (('HS', hs_var(x, a)), ('N', normal_var(x, a)), ('T', t_var(pr, a))):
            Ii = (ro < -v).astype(int); N, lr, p = kupiec(Ii, 1 - a); c = christoffersen(Ii, 1 - a)
            last = Ii[-250:].sum()
            st.append(dict(design=lab, model=m, conf=tag, VaR=v * 100, N=N, p_uc=p, p_ind=c['p_ind'],
                           n2024=int(last), zone2024=zone(last) if tag == '99' else ''))
ST = pd.DataFrame(st); ST.to_csv('out/static.csv', index=False); print('\nStatic:'); print(ST.round(4).to_string())

# 2022 lag diagnostics
rv = pd.Series(r).rolling(21).std().values * np.sqrt(1)  # realised 21-day sd (info to t)
lag = {}
for yr in (2020, 2022):
    mk = y == yr
    lag[yr] = dict(mean_ratio_N99_to_EWMA99=float(np.mean(V['N99'][mk] / V['EN99'][mk])),
                   mean_window_sd=float(np.mean([r[t - W:t].std() for t in idx[mk]]) * 100),
                   mean_ewma_sd=float(np.mean(sig[idx[mk]]) * 100),
                   realised_sd=float(r[idx[mk]].std() * 100))
print('\nlag', lag)
json.dump(dict(fisher=fish, nu=nuq, lag=lag,
               roll={k: dict(share=v['share'], by_year=v['by_year'], final=v['final']) for k, v in roll.items()}),
          open('out/summary.json', 'w'), indent=1, default=float)
