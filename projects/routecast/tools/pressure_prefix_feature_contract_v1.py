"""Strict first-checkpoint feature boundary; exposes no targets or future metadata."""
import pathlib,json,hashlib,re
KEYS={'schema','case','policy','graph_sha256','cutoff_iteration','phase','RR_domain_size','overflow_units_by_rr'}
def validate(row):
 if not isinstance(row,dict) or set(row)!=KEYS:raise ValueError('unexpected feature fields')
 if row['schema']!='MMC_FIRST_CHECKPOINT_OVERFLOW_FEATURES_V1':raise ValueError('feature schema')
 if row['case'] not in ['case_01','case_02','case_03'] or row['policy'] not in ['off','on']:raise ValueError('fixture identity')
 if type(row['cutoff_iteration']) is not int or row['cutoff_iteration']!=1 or row['phase']!='iteration_end_after_local_opins':raise ValueError('temporal boundary')
 if not isinstance(row['graph_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',row['graph_sha256']):raise ValueError('graph identity')
 n=row['RR_domain_size']
 if type(n) is not int or n<1 or not isinstance(row['overflow_units_by_rr'],dict):raise ValueError('RR domain')
 result={}
 for key,value in row['overflow_units_by_rr'].items():
  if not isinstance(key,str) or not key.isascii() or not key.isdecimal() or str(int(key))!=key or not 0<=int(key)<n:raise ValueError('RR identity')
  if type(value) is not int or value<1:raise ValueError('overflow feature value')
  result[int(key)]=value
 return result

def load(path, expected_sha256):
 data=pathlib.Path(path).read_bytes()
 if hashlib.sha256(data).hexdigest()!=expected_sha256:raise ValueError('feature digest mismatch')
 return validate(json.loads(data))
