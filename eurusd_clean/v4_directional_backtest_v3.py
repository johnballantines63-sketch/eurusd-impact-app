#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V4 Directional Backtest V3 (adds --sweep-temps). See file header for details."""
from __future__ import annotations
import argparse, glob
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple
import duckdb
import numpy as np
import pandas as pd

EPS = 1e-12
def sigmoid(x): return 1.0/(1.0+np.exp(-x))
def logit(p):
    p=np.clip(p,EPS,1.0-EPS); return np.log(p/(1.0-p))
def apply_temp_and_clip(prob_up: np.ndarray, temp: float=1.0, clip_logit: Optional[float]=None)->np.ndarray:
    z=logit(prob_up.astype(float))
    if clip_logit is not None:
        z=np.clip(z,-float(clip_logit),float(clip_logit))
    z=z/float(temp)
    return sigmoid(z)

def auc_rank(y_true01: np.ndarray, y_score: np.ndarray)->float:
    y_true01=np.asarray(y_true01,dtype=int); y_score=np.asarray(y_score,dtype=float)
    n_pos=int((y_true01==1).sum()); n_neg=int((y_true01==0).sum())
    if n_pos==0 or n_neg==0: return float('nan')
    ranks=pd.Series(y_score).rank(method='average').to_numpy()
    r_pos=ranks[y_true01==1].sum()
    return float((r_pos - n_pos*(n_pos+1)/2.0)/(n_pos*n_neg))

def brier_score(y_true01,p): return float(np.mean((np.asarray(p)-np.asarray(y_true01))**2))
def log_loss(y_true01,p):
    y=np.asarray(y_true01,dtype=float); p=np.clip(np.asarray(p,dtype=float),EPS,1.0-EPS)
    return float(-np.mean(y*np.log(p)+(1.0-y)*np.log(1.0-p)))

@dataclass
class Metrics:
    acc: float; bacc: float; tpr: float; tnr: float; brier: float; logloss: float; auc: float
    tn: int; fp: int; fn: int; tp: int

def compute_metrics(y_true01: np.ndarray, p: np.ndarray, threshold: float)->Metrics:
    y=np.asarray(y_true01,dtype=int); p=np.asarray(p,dtype=float)
    y_pred=(p>=threshold).astype(int)
    tp=int(((y==1)&(y_pred==1)).sum()); tn=int(((y==0)&(y_pred==0)).sum())
    fp=int(((y==0)&(y_pred==1)).sum()); fn=int(((y==1)&(y_pred==0)).sum())
    n=len(y); acc=float((tp+tn)/n) if n else float('nan')
    pos=int((y==1).sum()); neg=int((y==0).sum())
    tpr=float(tp/pos) if pos else float('nan'); tnr=float(tn/neg) if neg else float('nan')
    bacc=float((tpr+tnr)/2.0) if (pos and neg) else float('nan')
    return Metrics(acc,bacc,tpr,tnr,brier_score(y,p),log_loss(y,p),auc_rank(y,p),tn,fp,fn,tp)

def youden_j(tpr,tnr):
    if np.isnan(tpr) or np.isnan(tnr): return float('nan')
    return float(tpr+tnr-1.0)

def expand_csv_inputs(inputs: List[str])->List[str]:
    out=[]
    for s in inputs:
        m=glob.glob(s); out.extend(m if m else [s])
    seen=set(); uniq=[]
    for p in out:
        if p not in seen: seen.add(p); uniq.append(p)
    return uniq

def read_scores_csvs(csv_paths: List[str])->pd.DataFrame:
    frames=[]
    for p in csv_paths:
        df=pd.read_csv(p); df['_src']=p
        try: df['_mtime']=Path(p).stat().st_mtime
        except Exception: df['_mtime']=0.0
        frames.append(df)
    if not frames: return pd.DataFrame()
    df_all=pd.concat(frames,ignore_index=True)
    if 'date_local' not in df_all.columns: raise ValueError("CSV must contain 'date_local'")
    df_all['date_local']=pd.to_datetime(df_all['date_local']).dt.date.astype(str)
    df_all=df_all.sort_values(['date_local','_mtime']).drop_duplicates('date_local',keep='last')
    return df_all.reset_index(drop=True)

def load_truth(conn)->pd.DataFrame:
    df=conn.execute("SELECT date_local, direction AS truth_dir FROM daily_pattern_truth_v4").df()
    df['date_local']=pd.to_datetime(df['date_local']).dt.date.astype(str)
    return df

def filter_last_years(df: pd.DataFrame, years: float)->pd.DataFrame:
    if years<=0: return df.copy()
    cutoff=(datetime.now(timezone.utc).date()-timedelta(days=int(round(years*365)))).isoformat()
    d=df.copy(); d=d[pd.to_datetime(d['date_local'])>=pd.to_datetime(cutoff)]
    return d.reset_index(drop=True)

def sweep_thresholds_on_train(df_train: pd.DataFrame, p_col: str, y_col: str, criterion: str)->Tuple[float,pd.DataFrame]:
    y=df_train[y_col].to_numpy(dtype=int); p=df_train[p_col].to_numpy(dtype=float)
    thr_grid=np.linspace(0.05,0.95,181)
    rows=[]
    for thr in thr_grid:
        m=compute_metrics(y,p,float(thr))
        rows.append({'threshold':float(thr),'balanced_accuracy':m.bacc,'tpr':m.tpr,'tnr':m.tnr,'accuracy':m.acc,'youden_j':youden_j(m.tpr,m.tnr)})
    res=pd.DataFrame(rows)
    if criterion=='balanced_accuracy': best=res['balanced_accuracy'].astype(float).idxmax()
    elif criterion=='youden': best=res['youden_j'].astype(float).idxmax()
    elif criterion=='accuracy': best=res['accuracy'].astype(float).idxmax()
    else: raise ValueError("Unknown criterion")
    best_thr=float(res.loc[best,'threshold'])
    sort_col = {'balanced_accuracy':'balanced_accuracy','youden':'youden_j','accuracy':'accuracy'}.get(criterion, criterion)
    res=res.sort_values(sort_col,ascending=False).reset_index(drop=True)
    return best_thr,res

def parse_temps_list(s: str)->List[float]:
    return sorted(set(float(x.strip()) for x in s.split(',') if x.strip()))

def sweep_temps_on_train(df_train: pd.DataFrame, prob_up_col: str, y_col: str, temps: List[float], clip_logit: Optional[float], temp_criterion: str)->Tuple[float,pd.DataFrame]:
    y=df_train[y_col].to_numpy(dtype=int); p0=df_train[prob_up_col].to_numpy(dtype=float)
    rows=[]
    for t in temps:
        p=apply_temp_and_clip(p0,temp=t,clip_logit=clip_logit)
        rows.append({'temp':float(t),'train_logloss':log_loss(y,p),'train_brier':brier_score(y,p),'train_auc':auc_rank(y,p)})
    res=pd.DataFrame(rows)
    if temp_criterion=='logloss': best=res['train_logloss'].astype(float).idxmin()
    elif temp_criterion=='brier': best=res['train_brier'].astype(float).idxmin()
    else: raise ValueError("Unknown temp_criterion")
    best_temp=float(res.loc[best,'temp'])
    res=res.sort_values(f'train_{temp_criterion}',ascending=True).reset_index(drop=True)
    return best_temp,res

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db',required=True)
    ap.add_argument('--csv',required=True,nargs='+')
    ap.add_argument('--years',type=float,default=3.0)
    ap.add_argument('--threshold',type=float,default=0.5)
    ap.add_argument('--sweep-thresholds',action='store_true')
    ap.add_argument('--criterion',choices=['balanced_accuracy','youden','accuracy'],default='balanced_accuracy')
    ap.add_argument('--split-date',type=str,default=None)
    ap.add_argument('--temp',type=float,default=1.0)
    ap.add_argument('--clip-logit',type=float,default=None)
    ap.add_argument('--bins',type=int,default=6)
    ap.add_argument('--print-top',type=int,default=10)
    ap.add_argument('--sweep-temps',action='store_true')
    ap.add_argument('--temp-criterion',choices=['logloss','brier'],default='logloss')
    ap.add_argument('--temps',type=str,default='0.6,0.8,1.0,1.2,1.5,1.8,2.2,2.6,3.0')
    args=ap.parse_args()

    csv_paths=expand_csv_inputs(args.csv)
    conn=duckdb.connect(str(args.db),read_only=True)
    try:
        scores=read_scores_csvs(csv_paths)
        truth=load_truth(conn)
    finally:
        conn.close()

    if scores.empty: raise SystemExit("No rows loaded from CSV inputs.")
    if 'prob_up' not in scores.columns: raise SystemExit("CSV must contain 'prob_up'.")

    df=scores.merge(truth,on='date_local',how='inner')
    df=filter_last_years(df,args.years)
    df=df[df['truth_dir'].isin([-1,1])].copy()
    df['y01']=(df['truth_dir']==1).astype(int)

    split_hdr=''
    if args.split_date:
        split_dt=pd.to_datetime(args.split_date).date()
        df['date_dt']=pd.to_datetime(df['date_local']).dt.date
        train=df[df['date_dt']<split_dt].copy()
        test=df[df['date_dt']>=split_dt].copy()
        split_hdr=f" | split @ {args.split_date} (train <, test >=)"
    else:
        train=df.copy(); test=df.copy()

    if args.sweep_thresholds and not args.split_date: raise SystemExit("--sweep-thresholds requires --split-date.")
    if args.sweep_temps and not args.split_date: raise SystemExit("--sweep-temps requires --split-date.")
    if args.sweep_thresholds and train.empty: raise SystemExit("Split produced empty TRAIN set; cannot sweep thresholds.")
    if args.sweep_temps and train.empty: raise SystemExit("Split produced empty TRAIN set; cannot sweep temps.")
    if test.empty: raise SystemExit("Split produced empty TEST set; nothing to report.")

    chosen_temp=float(args.temp); temp_sweep=None
    if args.sweep_temps:
        chosen_temp,temp_sweep=sweep_temps_on_train(train,'prob_up','y01',parse_temps_list(args.temps),args.clip_logit,args.temp_criterion)

    df['prob_up_tx']=apply_temp_and_clip(df['prob_up'].to_numpy(dtype=float),temp=chosen_temp,clip_logit=args.clip_logit)

    chosen_thr=float(args.threshold); thr_sweep=None
    if args.sweep_thresholds:
        train2=train.merge(df[['date_local','prob_up_tx']],on='date_local',how='left')
        chosen_thr,thr_sweep=sweep_thresholds_on_train(train2,'prob_up_tx','y01',args.criterion)

    test2=test.merge(df[['date_local','prob_up_tx']],on='date_local',how='left')
    m=compute_metrics(test2['y01'].to_numpy(dtype=int),test2['prob_up_tx'].to_numpy(dtype=float),chosen_thr)

    clip_str=f", clip_logit={args.clip_logit:g}" if args.clip_logit is not None else ""
    temp_str=f" | temp={chosen_temp:g}{clip_str}" if (args.sweep_temps or args.temp!=1.0 or args.clip_logit is not None) else ""

    print("="*80)
    print(f"V4 Directional Backtest V3 (prob_up vs truth_dir) | last {args.years:.1f}y{split_hdr}{temp_str}")
    print("="*80)
    print(f"Rows matched: {len(df)}")
    if args.split_date: print(f"Train rows:   {len(train)} | Test rows: {len(test)}")
    print(f"Pos (up): {int((df['y01']==1).sum())} | Neg (down): {int((df['y01']==0).sum())}")
    print()

    if args.sweep_temps and temp_sweep is not None and not temp_sweep.empty:
        best=temp_sweep.iloc[0]
        print(f"Temp (selected on TRAIN via {args.temp_criterion}): {chosen_temp:g}")
        print(f"  TRAIN best: logloss={best['train_logloss']:.6f}, brier={best['train_brier']:.6f}, auc={best['train_auc']:.4f}")
        print()

    if args.sweep_thresholds and thr_sweep is not None and not thr_sweep.empty:
        best=thr_sweep.iloc[0]
        print(f"Threshold (selected on TRAIN via {args.criterion}): {chosen_thr:.3f}")
        print(f"  TRAIN best: bacc={best['balanced_accuracy']:.4f} (TPR={best['tpr']:.4f}, TNR={best['tnr']:.4f}), acc={best['accuracy']:.4f}")
        print()
    else:
        print(f"Threshold: {chosen_thr:.3f}")

    print(f"Accuracy (TEST):          {m.acc:.4f}")
    print(f"Balanced accuracy (TEST): {m.bacc:.4f} (TPR={m.tpr:.4f}, TNR={m.tnr:.4f})")
    print(f"Brier score (TEST):       {m.brier:.6f}")
    print(f"Log loss (TEST):          {m.logloss:.6f}")
    print(f"AUC (rank, TEST):         {m.auc:.4f}")
    print()
    print("Confusion matrix (TEST) [tn fp; fn tp]:")
    print(np.array([[m.tn,m.fp],[m.fn,m.tp]]))
    print()

    print("Calibration (quantile bins, TEST):")
    cal=test2[['prob_up_tx','y01']].copy().sort_values('prob_up_tx')
    if len(cal)>=args.bins:
        cal['bin']=pd.qcut(cal['prob_up_tx'],q=args.bins,duplicates='drop')
        out=cal.groupby('bin').agg(n=('y01','size'),mean_p=('prob_up_tx','mean'),frac_up=('y01','mean')).reset_index()
        print(out.to_string(index=False))
    else:
        print("Not enough rows to bin.")
    print()

    if args.print_top>0:
        out=test2.copy()
        out=out.merge(scores[['date_local']+[c for c in ['kernel_size','kernel_releases','score_0_100','prob_up'] if c in scores.columns]],on='date_local',how='left',suffixes=('','_orig'))
        if 'prob_up_orig' in out.columns: out['prob_up']=out['prob_up_orig']
        out['conf']=np.abs(out['prob_up_tx']-0.5)
        out=out.sort_values('conf',ascending=False).head(int(args.print_top))
        cols=[c for c in ['date_local','truth_dir','prob_up','prob_up_tx','kernel_size','kernel_releases','score_0_100'] if c in out.columns]
        print(f"Top {int(args.print_top)} most confident (TEST):")
        print(out[cols].to_string(index=False))
        print()

    if args.sweep_temps and temp_sweep is not None:
        print("Top 10 temps on TRAIN:")
        print(temp_sweep.head(10).to_string(index=False))
        print()
    if args.sweep_thresholds and thr_sweep is not None:
        print("Top 10 thresholds on TRAIN:")
        print(thr_sweep.head(10).to_string(index=False))
        print()

if __name__=='__main__':
    main()