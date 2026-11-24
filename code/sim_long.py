import numpy as np, json
from numpy.lib.stride_tricks import sliding_window_view as swv
from core import kupiec, W
P=6748; n=W+P; rng=np.random.default_rng(7); Ns={'normal':[], 't4':[]}
for dgp in Ns:
    for _ in range(1000):
        x=rng.standard_normal(n) if dgp=='normal' else rng.standard_t(4,n)/np.sqrt(2)
        srt=np.sort(swv(x[:-1],W),axis=1); v=-(srt[:,2]+0.49*(srt[:,3]-srt[:,2]))
        Ns[dgp].append(int((x[W:]<-v).sum()))
out={}
for k,N in Ns.items():
    N=np.array(N); out[k]=dict(mean=float(N.mean()), q95=float(np.quantile(N,.95)), p94=float((1+np.sum(N>=94))/1001), p104=float((1+np.sum(N>=104))/1001), p113=float((1+np.sum(N>=113))/1001))
print(json.dumps(out,indent=1)); json.dump(out,open('out/sim_long.json','w'))
