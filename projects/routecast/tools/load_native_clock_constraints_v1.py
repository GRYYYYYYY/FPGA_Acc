"""Strict native constraint snapshot parser; preserves float32 and undefined values."""
import math,struct
from fractions import Fraction

def value(text):
 f=struct.unpack('<f',struct.pack('<f',float(text)))[0]
 return dict(defined=math.isfinite(f),bits=struct.pack('>f',f).hex() if math.isfinite(f) else None,seconds=str(Fraction(f)) if math.isfinite(f) else None)
def load(path):
 result=dict(schema='ROUTECAST_NATIVE_CLOCK_CONSTRAINTS_V1',domains={},clock_constraints={},io_constraints={},uncertainties={},latencies={},constants=[],native_queries=[],native_latency_queries=[],native_uncertainty_queries=[])
 seen_header=False
 for line in path.open():
  x=line.rstrip('\n').split('\t');kind=x[0]
  if kind=='H':assert x==['H','1'] and not seen_header;seen_header=True
  elif kind=='D':
   assert len(x)==5;domain=int(x[1]);assert domain not in result['domains'];result['domains'][domain]=dict(source=int(x[2]),virtual=bool(int(x[3])),name=x[4])
  elif kind=='C':
   assert len(x)==6 and x[1] in ['SETUP','HOLD'];key=(x[1],*map(int,x[2:5]));assert key not in result['clock_constraints'];result['clock_constraints'][key]=value(x[5])
  elif kind in ['I','O']:
   assert len(x)==5 and x[1] in ['MAX','MIN'];key=(kind,x[1],int(x[2]),int(x[3]));assert key not in result['io_constraints'];result['io_constraints'][key]=value(x[4])
  elif kind=='U':
   assert len(x)==5 and x[1] in ['SETUP','HOLD'];key=(x[1],int(x[2]),int(x[3]));assert key not in result['uncertainties'];result['uncertainties'][key]=value(x[4])
  elif kind=='L':
   assert len(x)==4 and x[1] in ['EARLY','LATE'];key=(x[1],int(x[2]));assert key not in result['latencies'];result['latencies'][key]=value(x[3])
  elif kind=='G':assert len(x)==2;result['constants'].append(int(x[1]))
  elif kind=='Q':
   assert len(x)==7;result['native_queries'].append(dict(source=int(x[1]),sink=int(x[2]),capture=int(x[3]),analyze=bool(int(x[4])),setup=value(x[5]),hold=value(x[6])))
  elif kind=='QL':assert len(x)==4;result['native_latency_queries'].append(dict(kind=x[1],domain=int(x[2]),value=value(x[3])))
  elif kind=='QU':assert len(x)==5;result['native_uncertainty_queries'].append(dict(source=int(x[1]),sink=int(x[2]),setup=value(x[3]),hold=value(x[4])))
  else:raise ValueError('unknown native constraint record '+kind)
 assert seen_header and result['domains'];return result

def resolve(data,source,sink,capture=-1):
 maps=data['clock_constraints'];out={}
 for kind in ('SETUP','HOLD'):
  explicit=(kind,source,sink,capture);fallback=(kind,source,sink,-1)
  out[kind.lower()]=maps.get(explicit,maps.get(fallback,dict(defined=False,bits=None,seconds=None)))
 out['analyze']=any((k,source,sink,c) in maps for k in ('SETUP','HOLD') for c in (capture,-1));return out

def serializable(data):
 out={k:v for k,v in data.items() if k not in ('clock_constraints','io_constraints','uncertainties','latencies')}
 for name in ['clock_constraints','io_constraints','uncertainties','latencies']:out[name]=[dict(key=list(k),value=v) for k,v in sorted(data[name].items())]
 return out
