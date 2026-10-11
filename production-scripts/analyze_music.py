import json,hashlib,subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
root=Path(__file__).resolve().parent
y,sr=sf.read(root/'analysis/music-mono.wav');hop=220
print('Decoded',len(y)/sr,'seconds',flush=True)
S=np.abs(librosa.stft(y,n_fft=2048,hop_length=hop))
on=librosa.onset.onset_strength(S=librosa.amplitude_to_db(S+1e-9),sr=sr,hop_length=hop)
tempo,beats=librosa.beat.beat_track(onset_envelope=on,sr=sr,hop_length=hop,trim=False,units='time')
onsets=librosa.onset.onset_detect(onset_envelope=on,sr=sr,hop_length=hop,units='time',backtrack=False)
rms=librosa.feature.rms(S=S,frame_length=2048)[0]
times=librosa.times_like(on,sr=sr,hop_length=hop)
freq=librosa.fft_frequencies(sr=sr,n_fft=2048)
low=np.sqrt(np.mean(S[(freq>=30)&(freq<=180)]**2,axis=0))
high=np.sqrt(np.mean(S[(freq>=2000)&(freq<=8000)]**2,axis=0))
chroma=librosa.feature.chroma_stft(S=S**2,sr=sr,hop_length=hop)
energy=gaussian_filter1d(rms,100)
peaks,_=find_peaks(energy,distance=int(6*sr/hop),prominence=float(energy.max())*.08)
novelty=np.linalg.norm(np.diff(gaussian_filter1d(chroma,35,axis=1),axis=1),axis=0)
boundaries,_=find_peaks(gaussian_filter1d(novelty,50),distance=int(6*sr/hop),prominence=.00015)
windows=[]
for start in range(0,int(len(y)/sr),4):
    mask=(times>=start)&(times<start+4)
    windows.append({'start':start,'rms_db':float(20*np.log10(np.mean(rms[mask])+1e-9)),'low':float(np.mean(low[mask])),'high':float(np.mean(high[mask])),'onsets':int(np.sum((onsets>=start)&(onsets<start+4)))})
local=[]
for start in range(0,88,8):
    mask=(times>=start)&(times<start+12)
    candidates=librosa.feature.tempo(onset_envelope=on[mask],sr=sr,hop_length=hop,start_bpm=float(np.asarray(tempo).item()))
    local.append({'start':start,'bpm':float(candidates[0])})
data={'duration':len(y)/sr,'sample_rate':sr,'hop_seconds':hop/sr,'tempo_bpm':float(np.asarray(tempo).item()),'beats':beats.tolist(),'onsets':onsets.tolist(),'energy_peaks':times[peaks].tolist(),'harmonic_change_candidates':times[boundaries].tolist(),'local_tempo':local,'windows':windows,'analysis_method':'Local librosa 0.11.0 onset/DP beat tracking, RMS and spectral bands; detected beats are estimates, not score-derived downbeats.','user_harmony':'Dm, G/B, Dm, G/D (user supplied, not independently transcribed)'}
(root/'analysis/music-analysis.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
np.savez_compressed(root/'analysis/features.npz',times=times,rms=rms,onset=on,low=low,high=high,chroma=chroma)
fig,ax=plt.subplots(4,1,figsize=(18,11),sharex=True)
ax[0].plot(np.arange(len(y))[::100]/sr,y[::100],lw=.25,color='#6f7680');ax[0].set_ylabel('Waveform')
ax[1].plot(times,20*np.log10(rms+1e-9),lw=.4,color='#b52536');ax[1].set_ylabel('RMS dBFS')
ax[2].plot(times,on,lw=.45,color='#527790');ax[2].vlines(beats,0,on.max(),color='#b52536',alpha=.15,lw=.5);ax[2].set_ylabel('Onsets + beats')
ax[3].plot(times,low/(low.max()+1e-9),label='30-180Hz',color='#b52536');ax[3].plot(times,high/(high.max()+1e-9),label='2-8kHz',color='#c29e52');ax[3].legend();ax[3].set_xlabel('Seconds')
for a in ax:a.grid(alpha=.2);a.set_xlim(0,len(y)/sr)
fig.suptitle(f'FEISHENG | local audio analysis | estimated pulse {float(np.asarray(tempo).item()):.2f} BPM')
fig.tight_layout();fig.savefig(root/'analysis/music-analysis.png',dpi=140)
print(json.dumps({k:data[k] for k in ['duration','tempo_bpm','energy_peaks','harmonic_change_candidates','local_tempo','windows']},indent=2),flush=True)
