import json
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import stft, find_peaks
from scipy.ndimage import gaussian_filter1d
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'analysis/reedit-v2'
OUT.mkdir(exist_ok=True)
y,sr=sf.read(ROOT/'remotion/public/audio/feisheng-master.wav')
y=y.mean(axis=1)
freq,t,z=stft(y,fs=sr,nperseg=2048,noverlap=1792,boundary='zeros')
s=np.abs(z)
bands={'bass':(30,180),'body':(180,2000),'air':(2000,10000)}
features={}
for name,(lo,hi) in bands.items():
    b=s[(freq>=lo)&(freq<hi)]
    level=np.sqrt(np.sum(b*b,axis=0))
    flux=np.mean(np.maximum(np.diff(np.log1p(b*3000),axis=1,prepend=np.zeros((len(b),1))),0),axis=0)
    features[name+'_level']=level
    features[name+'_flux']=gaussian_filter1d(flux,.7)
features['all_flux']=features['body_flux']+features['air_flux']*.6
candidates={}
for name in ['bass_flux','all_flux']:
    f=features[name]
    peaks,props=find_peaks(f,distance=int(.12/(256/sr)),prominence=np.percentile(f,70)*.35)
    candidates[name]=[{'time':round(float(t[i]),4),'strength':round(float(f[i]),6)} for i in peaks if 35<t[i]<90]
old=json.loads((ROOT/'remotion/src/data/timeline.json').read_text(encoding='utf-8'))
np.savez_compressed(OUT/'transient-features.npz',times=t,**features)
(OUT/'transient-candidates.json').write_text(json.dumps(candidates,indent=2))
for start,end in [(35,52),(45,62),(60,78),(76,92)]:
    fig,ax=plt.subplots(3,1,figsize=(18,8),sharex=True)
    mask=(t>=start)&(t<=end)
    ax[0].plot(np.arange(len(y))[::64]/sr,y[::64],lw=.4,color='#526579')
    ax[1].plot(t,features['bass_level'],lw=.6,color='#bb273b',label='Bass level')
    ax[1].plot(t,features['bass_flux']*.08,lw=.6,color='#cda052',label='Bass attack')
    ax[2].plot(t,features['all_flux'],lw=.5,color='#426886')
    for a in ax:
        a.set_xlim(start,end);a.grid(alpha=.2);a.set_xticks(np.arange(start,end,.6))
        for c in old['cuts']:
            if c['kind']=='scene_cut' and start<c['seconds']<end:a.axvline(c['seconds'],color='#ba283a',ls='--',alpha=.75)
    ax[1].legend();ax[2].set_xlabel('Seconds | dashed lines = old scene cuts')
    fig.tight_layout();fig.savefig(OUT/f'late-{start}-{end}.png',dpi=125);plt.close(fig)
for name in candidates:
    print(name,sorted(candidates[name],key=lambda x:x['strength'],reverse=True)[:30])
