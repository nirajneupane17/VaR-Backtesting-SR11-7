"""Core walk-forward VaR backtest: data, models, tests (shared by all scripts)."""
import os
import numpy as np, pandas as pd
from scipy import stats

W = 250
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sp500_close_2018_2024.csv')


def load():
    d = pd.read_csv(DATA, parse_dates=['Date'])
    d['r'] = np.log(d.Close).diff()
    d = d.dropna().reset_index(drop=True)
    return d  # 1,759 returns, 3 Jan 2018 .. 30 Dec 2024


# ---------- backtests ----------
def kupiec(I, p):
    T, N = len(I), int(I.sum()); ph = N / T
    ll0 = (T - N) * np.log(1 - p) + N * np.log(p)
    ll1 = ((T - N) * np.log(1 - ph) if N < T else 0) + (N * np.log(ph) if N > 0 else 0)
    lr = -2 * (ll0 - ll1)
    return N, lr, stats.chi2.sf(lr, 1)


def christoffersen(I, p):
    I = np.asarray(I, int)
    a, b = I[:-1], I[1:]
    n00 = np.sum((a == 0) & (b == 0)); n01 = np.sum((a == 0) & (b == 1))
    n10 = np.sum((a == 1) & (b == 0)); n11 = np.sum((a == 1) & (b == 1))
    p01 = n01 / (n00 + n01) if n00 + n01 else 0
    p11 = n11 / (n10 + n11) if n10 + n11 else 0
    pi = (n01 + n11) / (n00 + n01 + n10 + n11)

    def xl(n, q):
        return n * np.log(q) if n > 0 else 0.0
    l0 = xl(n00 + n10, 1 - pi) + xl(n01 + n11, pi)
    l1 = xl(n00, 1 - p01) + xl(n01, p01) + xl(n10, 1 - p11) + xl(n11, p11)
    lr_ind = -2 * (l0 - l1)
    _, lr_uc, _ = kupiec(I, p)
    lr_cc = lr_uc + lr_ind
    return dict(n00=n00, n01=n01, n10=n10, n11=n11, p01=p01, p11=p11,
                lr_ind=lr_ind, p_ind=stats.chi2.sf(lr_ind, 1),
                lr_cc=lr_cc, p_cc=stats.chi2.sf(lr_cc, 2))


# ---------- models ----------
def hs_var(x, a, method='linear'):
    return -np.quantile(x, 1 - a, method=method)


def normal_var(x, a, ddof=1):
    return -(x.mean() + stats.norm.ppf(1 - a) * x.std(ddof=ddof))


def t_fit(x, bounded=False):
    if bounded:
        # location-scale t MLE with nu restricted to [2.1, 100]
        from scipy.optimize import minimize
        mu0, s0 = np.median(x), x.std()

        def nll(th):
            nu = 2.1 + (100 - 2.1) / (1 + np.exp(-th[0])); mu = th[1]; s = np.exp(th[2])
            return -stats.t.logpdf(x, nu, mu, s).sum()
        best = None
        for nu_start in (0.0, -2.0, 2.0):
            r = minimize(nll, [nu_start, mu0, np.log(s0 * 0.8)], method='Nelder-Mead',
                         options=dict(xatol=1e-8, fatol=1e-8, maxiter=4000))
            if best is None or r.fun < best.fun:
                best = r
        th = best.x
        return 2.1 + (100 - 2.1) / (1 + np.exp(-th[0])), th[1], np.exp(th[2])
    nu, mu, s = stats.t.fit(x)
    return nu, mu, s


def t_var(params, a):
    nu, mu, s = params
    return -(mu + stats.t.ppf(1 - a, nu) * s)


def ewma_sigma(r, lam=0.94, seed_n=250):
    """sigma_t^2 = lam*sigma_{t-1}^2 + (1-lam) r_{t-1}^2 ; sigma_t uses info to t-1."""
    s2 = np.empty(len(r)); s2[0] = np.var(r[:seed_n])
    for t in range(1, len(r)):
        s2[t] = lam * s2[t - 1] + (1 - lam) * r[t - 1] ** 2
    return np.sqrt(s2)


def walk_forward(r, bounded_t=False, store_nu=True):
    """Return dict of VaR arrays (positive numbers, as fraction) for t = W..len-1."""
    n = len(r); idx = np.arange(W, n)
    out = {k: np.empty(len(idx)) for k in
           ['HS95', 'HS99', 'N95', 'N99', 'T95', 'T99']}
    nus = np.empty(len(idx))
    for j, t in enumerate(idx):
        x = r[t - W:t]
        out['HS95'][j] = hs_var(x, .95); out['HS99'][j] = hs_var(x, .99)
        out['N95'][j] = normal_var(x, .95); out['N99'][j] = normal_var(x, .99)
        pr = t_fit(x, bounded=bounded_t); nus[j] = pr[0]
        out['T95'][j] = t_var(pr, .95); out['T99'][j] = t_var(pr, .99)
    return idx, out, nus
