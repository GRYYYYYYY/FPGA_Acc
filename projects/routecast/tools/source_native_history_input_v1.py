"""Authenticated source epoch prior, encoded once beside immutable span prices."""
import json,hashlib
from pathlib import Path
from collections import Counter

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def normalize(mapping,n,label,positive=False):
 result={}
 for key,value in mapping.items():
  if type(key) is int:node=key
  elif type(key) is str and key.isdecimal() and str(int(key))==key:node=int(key)
  else:raise ValueError(label+' key')
  if not 0<=node<n or node in result or type(value) is not int or value<0 or (positive and not value):raise ValueError(label+' domain')
  result[node]=value
 return result

def load(prior_path,graph_sha256,source_route_sha256,n):
 path=Path(prior_path).resolve();proofpath=path.parent/'verification.json';proof=json.loads(proofpath.read_text())
 if proof['status']!='ALL129090_SOURCE_F32_VALUES_EXACT_INTEGER_EXCESS_PRIOR_PASS' or proof['bindings'].get(str(path))!=sha(path):raise ValueError('prior proof')
 if not all(sha(p)==h for p,h in proof['bindings'].items()):raise ValueError('prior changed binding')
 prior=json.loads(path.read_text())
 if prior['schema']!='SOURCE_FINAL_NATIVE_HISTORY_EXCESS_V1' or prior['graph_sha256']!=graph_sha256 or prior['source_route_sha256']!=source_route_sha256 or prior['nodes']!=n:raise ValueError('source epoch mismatch')
 return normalize(prior['history'],n,'source history',True),{str(path):sha(path),str(proofpath):sha(proofpath)}

def initialize(spans,history,n):
 static=normalize(spans,n,'span');prior=normalize(history,n,'history');encoded=Counter(prior);encoded.update(static);return encoded
