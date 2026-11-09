"""Exact typed min-sum elimination with packed per-message recurrence certificates."""
from pathlib import Path
from array import array
from math import prod
import hashlib,json,sys
from compiled_exact_min_sum_v1 import Factor,Message,eliminate,verify_message,MAX

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def checked(v):
 if type(v) is not int or not 0<=v<=MAX:raise ValueError('unsigned64 objective domain')
 return v
def evaluate(cards,factors,selected,constant=0):
 value=constant
 for f in factors:
  offset=0
  for n in f.scope:offset=offset*cards[n]+selected[n]
  value+=f.values[offset]
 return checked(value)
def conditioned(cards,factor):return Factor(tuple(n for n in factor.scope if cards[n]>1),factor.values)
def write_segment(stream,values,name):
 offset=stream.tell();values.tofile(stream)
 return {'file':name,'offset_bytes':offset,'count':len(values),'sha256':hashlib.sha256(memoryview(values)).hexdigest()}
def solve(cards,factors,order,constant=0,directory=None,max_bytes=8*2**30):
 if sys.byteorder!='little':raise ValueError('certificate format requires little endian host')
 checked(constant)
 if not cards or any(type(n) is not int or type(d) is not int or d<1 for n,d in cards.items()):raise ValueError('model variable domain')
 activevars={n for n,d in cards.items() if d>1}
 if len(order)!=len(set(order)) or set(order)!=activevars:raise ValueError('complete elimination order required')
 for f in factors:
  if type(f) is not Factor or not set(f.scope)<=set(cards) or len(f.values)!=prod(cards[n] for n in f.scope):raise ValueError('initial factor schema')
 root=Path(directory) if directory else None;streams={};inputs=[];records=[]
 if root:
  root.mkdir(parents=True,exist_ok=False)
  for name in ['initial_tables.bin','message_costs.bin','message_argmins.bin']:streams[name]=(root/name).open('xb')
 try:
  remaining=[];base=constant
  for i,f in enumerate(factors):
   name='i'+str(i);entry={'id':name,'scope':list(f.scope)}
   if root:entry['table']=write_segment(streams['initial_tables.bin'],f.values,'initial_tables.bin')
   inputs.append(entry);cf=conditioned(cards,f)
   if cf.scope:remaining.append((name,cf))
   else:base=checked(base+cf.values[0])
  history=[]
  for step,var in enumerate(order):
   bucket=[(n,f) for n,f in remaining if var in f.scope];remaining=[(n,f) for n,f in remaining if var not in f.scope];message=eliminate(cards,var,[f for n,f in bucket],max_bytes=max_bytes,verify=True);name='m'+str(step);record={'id':name,'variable':var,'input_ids':[n for n,f in bucket],'separator':list(message.separator)}
   if root:
    record['table']=write_segment(streams['message_costs.bin'],message.factor.values,'message_costs.bin');record['argmin']=write_segment(streams['message_argmins.bin'],message.argmin,'message_argmins.bin')
   records.append(record);history.append(message)
   if message.separator:remaining.append((name,message.factor))
   else:base=checked(base+message.factor.values[0])
  if remaining:raise ValueError('uneliminated factor dependencies')
  selected={n:0 for n,d in cards.items() if d==1}
  for message in reversed(history):
   index=0
   for n in message.separator:index=index*cards[n]+selected[n]
   selected[message.variable]=int(message.argmin[index])
  assert set(selected)==set(cards) and evaluate(cards,factors,selected,constant)==base
  result={'status':'EXACT_GLOBAL_MIN_SUM_WITH_CANONICAL_ARGMIN','selected':selected,'objective':base,'messages':len(records)}
 finally:
  for stream in streams.values():stream.close()
 if root:
  files={name:{'bytes':(root/name).stat().st_size,'sha256':sha(root/name)} for name in streams};manifest={'schema':'EXACT_FACTOR_ELIMINATION_CERT_V1','byte_order':'little','cardinalities':cards,'initial_constant':constant,'order':list(order),'inputs':inputs,'steps':records,'files':files,**result};(root/'certificate.json').write_text(json.dumps(manifest,separators=(',',':'))+'\n')
 return result

def read_segment(root,record,role,max_bytes):
 if record['file']!=role or type(record['offset_bytes']) is not int or record['offset_bytes']<0 or type(record['count']) is not int or record['count']<1:raise ValueError('packed table role/range')
 if record['count']*8>max_bytes:raise MemoryError('packed table exceeds budget')
 if record['offset_bytes']+record['count']*8>(root/role).stat().st_size:raise ValueError('truncated packed table')
 a=array('Q')
 with (root/role).open('rb') as f:f.seek(record['offset_bytes']);a.fromfile(f,record['count'])
 if hashlib.sha256(memoryview(a)).hexdigest()!=record['sha256']:raise ValueError('table hash')
 return a

def verify_certificate(directory,max_bytes=8*2**30):
 root=Path(directory);m=json.loads((root/'certificate.json').read_text())
 if m['schema']!='EXACT_FACTOR_ELIMINATION_CERT_V1' or m['byte_order']!='little' or sys.byteorder!='little':raise ValueError('certificate schema')
 cards={int(n):d for n,d in m['cardinalities'].items()};order=m['order'];active={n for n,d in cards.items() if d>1}
 if not cards or any(type(d) is not int or d<1 for d in cards.values()) or len(set(order))!=len(order) or set(order)!=active:raise ValueError('certificate domains/order')
 roles=['initial_tables.bin','message_costs.bin','message_argmins.bin']
 if set(m['files'])!=set(roles):raise ValueError('packed roles')
 for role in roles:
  if (root/role).stat().st_size!=m['files'][role]['bytes'] or sha(root/role)!=m['files'][role]['sha256']:raise ValueError('packed bank changed')
 offsets={r:0 for r in roles}
 def take(record,role):
  if record['offset_bytes']!=offsets[role]:raise ValueError('noncanonical segment ordering')
  a=read_segment(root,record,role,max_bytes);offsets[role]+=len(a)*8;return a
 original=[];remaining=[];base=checked(m['initial_constant'])
 for i,entry in enumerate(m['inputs']):
  if entry['id']!='i'+str(i):raise ValueError('initial factor IDs')
  f=Factor(entry['scope'],take(entry['table'],'initial_tables.bin'))
  if not set(f.scope)<=set(cards) or len(f.values)!=prod(cards[n] for n in f.scope):raise ValueError('initial factor dimensions')
  original.append(f);cf=conditioned(cards,f)
  if cf.scope:remaining.append((entry['id'],cf))
  else:base=checked(base+cf.values[0])
 if len(m['steps'])!=len(order):raise ValueError('missing message')
 history=[]
 for step,(entry,var) in enumerate(zip(m['steps'],order)):
  bucket=[(n,f) for n,f in remaining if var in f.scope];remaining=[(n,f) for n,f in remaining if var not in f.scope]
  if entry['id']!='m'+str(step) or entry['variable']!=var or entry['input_ids']!=[n for n,f in bucket]:raise ValueError('message dependency provenance')
  costs=take(entry['table'],'message_costs.bin');args=take(entry['argmin'],'message_argmins.bin');message=Message(var,entry['separator'],costs,args);verify_message(cards,var,[f for n,f in bucket],message,max_bytes);history.append(message)
  if message.separator:remaining.append((entry['id'],message.factor))
  else:base=checked(base+message.factor.values[0])
 if remaining or any(offsets[r]!=m['files'][r]['bytes'] for r in roles):raise ValueError('leftover factors/table bytes')
 selected={n:0 for n,d in cards.items() if d==1}
 for message in reversed(history):
  index=0
  for n in message.separator:index=index*cards[n]+selected[n]
  selected[message.variable]=int(message.argmin[index])
 if selected!={int(n):c for n,c in m['selected'].items()} or base!=m['objective'] or evaluate(cards,original,selected,m['initial_constant'])!=base:raise ValueError('optimal value/backtracking witness')
 return {'status':'ALL_MESSAGE_RECURRENCES_AND_GLOBAL_MINIMUM_WITNESS_VERIFIED','objective':base,'selected':selected,'messages':len(history)}
