"""Estimation-risk / size simulation (Reviewer 5, comment 4): HS and Normal VaR under correctly specified iid nulls."""
import numpy as np, json
from numpy.lib.stride_tricks import sliding_window_view as swv
from scipy import stats
from core import kupiec, christoffersen, W

P = 1509; n = W + P; reps = 3000
rng = np.random.default_rng(42)
crit = stats.chi2.ppf(.95, 1)
res = {}
for dgp in ('normal', 't4'):
    out = {k: dict(rate=[], N=[], LR=[], LRind=[]) for k in ('HS_lin', 'HS_os', 'N')}
    for _ in range(reps):
        x = rng.standard_normal(n) if dgp == 'normal' else rng.standard_t(4, n) / np.sqrt(2)
        win = swv(x[:-1], W)                       # windows ending t-1, t=W..n-1  (P windows)
        test = x[W:]
        srt = np.sort(win, axis=1)
        v_lin = -(srt[:, 2] + 0.49 * (srt[:, 3] - srt[:, 2]))   # numpy linear: h=(W-1)*0.01=2.49 (0-based)
        v_os = -srt[:, 2]                                          # 3rd order statistic (ceil(2.5))
        v_n = -(win.mean(1) + stats.norm.ppf(.01) * win.std(1, ddof=1))
        for k, v in (('HS_lin', v_lin), ('HS_os', v_os), ('N', v_n)):
            I = (test < -v).astype(int); N, lr, _ = kupiec(I, .01)
            out[k]['N'].append(N); out[k]['LR'].append(lr); out[k]['rate'].append(N / P)
            out[k]['LRind'].append(christoffersen(I, .01)['lr_ind'])
    res[dgp] = {}
    for k, o in out.items():
        N = np.array(o['N']); LR = np.array(o['LR']); LRi = np.array(o['LRind'])
        res[dgp][k] = dict(mean_rate=float(np.mean(o['rate']) * 100), reject5=float(np.mean(LR > crit)),
                           P_N_ge26=float(np.mean(N >= 26)), P_N_ge28=float(np.mean(N >= 28)),
                           P_N_ge44=float(np.mean(N >= 44)),
                           crit95_LR=float(np.quantile(LR, .95)),
                           N_q95=float(np.quantile(N, .95)),
                           p_sim_HS26=float((1 + np.sum(N >= 26)) / (reps + 1)),
                           reject5_ind=float(np.mean(LRi > crit)))
print(json.dumps(res, indent=1))
json.dump(res, open('out/size_sim.json', 'w'), indent=1)
