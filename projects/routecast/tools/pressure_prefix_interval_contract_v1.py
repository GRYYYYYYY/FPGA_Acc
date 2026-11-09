"""Digest-bound checkpoint1 interval reader; returns state arrays, never targets."""
import pathlib,json,hashlib,sys
from array import array
KEYS={'schema','case','policy','graph_sha256','cutoff_iteration','phase','prefix_end_byte','prefix_sha256','capacities','arrays','external_occupancy_assumed_zero'}
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def load(path,expected_sha256):
 if sys.byteorder!='little':raise ValueError('unsupported host byte order')
 p=pathlib.Path(path)
 if sha(p)!=expected_sha256:raise ValueError('manifest digest')
 m=json.loads(p.read_text())
 if set(m)!=KEYS or m['schema']!='MMC_PREFIX_OCCUPANCY_INTERVALS_V1':raise ValueError('interval schema')
 if type(m['cutoff_iteration']) is not int or m['cutoff_iteration']!=1 or m['phase']!='iteration_end_after_local_opins' or m['external_occupancy_assumed_zero'] is not False:raise ValueError('boundary/unknown policy')
 if set(m['capacities'])!={'path','sha256'} or set(m['arrays'])!={'tracked_NET_occupancy','lower_occupancy','upper_occupancy'}:raise ValueError('payload schema')
 def read(meta):
  if sha(meta['path'])!=meta['sha256']:raise ValueError('array digest')
  x=array('I');x.frombytes(pathlib.Path(meta['path']).read_bytes());return x
 caps=read(m['capacities']);vectors={}
 for name,meta in m['arrays'].items():
  if set(meta)!={'path','sha256','values','dtype'} or meta['dtype']!='little_endian_uint32' or type(meta['values']) is not int:raise ValueError('array descriptor')
  x=read(meta)
  if len(x)!=meta['values'] or len(x)!=len(caps):raise ValueError('array size')
  vectors[name]=x
 for cap,tracked,low,high in zip(caps,vectors['tracked_NET_occupancy'],vectors['lower_occupancy'],vectors['upper_occupancy']):
  if not tracked<=low<=high:raise ValueError('interval order')
  if low>cap:
   if low!=high:raise ValueError('observed overflow exactness')
  elif low!=tracked or high!=cap:raise ValueError('unobserved external state policy')
 return caps,vectors
