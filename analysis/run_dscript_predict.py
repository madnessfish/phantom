#!/usr/bin/env python3
"""
D-SCRIPT prediction with version-compat patch.
The 2021 pickled ModelInteraction (human_v1.sav) predates attributes that
dscript 0.2.8's map_predict() references. Patch them to their documented
constructor defaults, then embed + score each candidate pair.
Produces a 3-column y_prob file: prot1  prot2  probability.  seed=42.
"""
import sys, argparse, torch, numpy as np
from tqdm import tqdm
np.random.seed(42); torch.manual_seed(42)

ap = argparse.ArgumentParser()
ap.add_argument("--pairs", required=True)
ap.add_argument("--seqs", required=True)
ap.add_argument("--model", required=True)
ap.add_argument("--lm", required=True, help="language model .sav (lm_v1.sav)")
ap.add_argument("-o","--outfile", required=True)
ap.add_argument("-d","--device", type=int, default=0)
a = ap.parse_args()

dev = torch.device(f"cuda:{a.device}" if torch.cuda.is_available() else "cpu")
print("device", dev)

# ---- load interaction model and PATCH missing attrs to constructor defaults ----
model = torch.load(a.model, map_location=dev)
defaults = dict(do_w=True, do_sigmoid=True, do_pool=False, use_cuda=(dev.type=="cuda"))
for k,v in defaults.items():
    if not hasattr(model, k):
        setattr(model, k, v); print("patched", k, "=", v)
# 'xx' is a fixed index buffer (arange(10000)) absent from the 2021 pickle
if not hasattr(model, "xx"):
    import torch.nn as nn
    model.xx = nn.Parameter(torch.arange(10000).to(dev), requires_grad=False)
    print("patched xx = arange(10000)")
model = model.to(dev).eval()

# ---- language model embeddings: batch to h5 once (loads LM once) ----
import os, h5py
from dscript.language_model import embed_from_fasta

pairs=[]
for line in open(a.pairs):
    p=line.rstrip("\n").split("\t")
    if len(p)>=2: pairs.append((p[0],p[1]))
print("pairs", len(pairs))

h5path = a.outfile + ".embeddings.h5"
if not os.path.exists(h5path):
    embed_from_fasta(a.seqs, h5path, device=a.device, verbose=True)
print("embeddings h5:", h5path)

# load embeddings into memory
emb={}
with h5py.File(h5path, "r") as hf:
    for k in hf.keys():
        emb[k] = torch.from_numpy(hf[k][:]).to(dev)
print("loaded embeddings", len(emb))

# ---- inspect one embedding + do a single diagnostic predict (no swallow) ----
k0 = next(iter(emb))
print("emb sample key", k0, "shape", tuple(emb[k0].shape), "dtype", emb[k0].dtype)
A0,B0 = pairs[0]
print("first pair", A0, B0, "inA", A0 in emb, "inB", B0 in emb)
_diag = model.map_predict(emb[A0], emb[B0])   # let it raise so we see the real error
print("diag map_predict returned", type(_diag), "len", len(_diag) if hasattr(_diag,'__len__') else 'NA')

# ---- predict per pair ----
out=open(a.outfile,"w")
n_ok=0; n_err=0; first_err=None
with torch.no_grad():
    for A,B in tqdm(pairs, desc="predict"):
        if A not in emb or B not in emb:
            out.write(f"{A}\t{B}\tNA\n"); continue
        try:
            _, p = model.map_predict(emb[A], emb[B])
            prob=float(p.item())
            out.write(f"{A}\t{B}\t{prob:.6f}\n"); n_ok+=1
        except Exception as e:
            n_err+=1
            if first_err is None: first_err=repr(e)
            out.write(f"{A}\t{B}\tNA\n")
out.close()
print("wrote", n_ok, "scored,", n_err, "errors ->", a.outfile)
if first_err: print("first error:", first_err)
