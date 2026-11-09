"""Actual-query wrong-epoch/ownership witnesses; identity price alone is insufficient."""
import json,bisect
from pathlib import Path
from pre_route_endpoints import sha
from verify_prince_query_ledger_join_v1 import history,L,Q,D
from conditional_present_capacity_one_v1 import present_bits,bits

def main():
 case='w128/episode_01';event=L/case/'capture/queries.tsv.ledger.bin';rawp=Q/case/'capture/queries.tsv';entries,times,values=history(event);witness=None
 for line in rawp.open():
  x=list(map(int,line.split()));i,encoded,node,kind,occ,cap,pres,acc,base,cost,nc,active,ident,pin,sink,owns,count=x
  if kind not in [4,5]:continue
  epoch,iteration,net,expected_pin,expected_sink,retained=entries[ident];idx=bisect.bisect_right(times[node],epoch)-1
  alternatives=[j for j in [idx-1,idx+1] if 0<=j<len(times[node]) and values[node][j]!=occ]
  if not alternatives:continue
  bad=alternatives[0];assert values[node][idx]==occ and int(node in retained)==owns
  wrong_epoch=times[node][bad];assert values[node][bisect.bisect_right(times[node],wrong_epoch)-1]!=occ;assert (1-owns)!=int(node in retained)
  witness=dict(case=case,iteration=i,connection=ident,node=node,correct_epoch=epoch,correct_occupancy=occ,wrong_epoch=wrong_epoch,wrong_epoch_occupancy=values[node][bad],correct_retained_membership=owns,wrong_retained_membership=1-owns);break
 assert witness is not None
 # Two distinct ownership states can have identical identity-control cost.
 a=present_bits(1,0,1.,bits(.5));b=present_bits(1,1,0.,bits(.5));assert a==b==bits(1.5)
 out=D/'negative_join_witness_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ACTUAL_WRONG_EPOCH_AND_OWNER_WITNESSES_DETECTED',witness=witness,identity_price_does_not_prove_ownership={'O':1,'p':.5,'I0_other1_bits':a,'I1_other0_bits':b,'reason':'F=O-I cancels I in identity control; independent owner-ledger reconciliation remains necessary.'},bindings={str(p):sha(p) for p in [Path(__file__),event,rawp,D/'verification.json']}),indent=2)+'\n');print('QUERY_LEDGER_NEGATIVE_WITNESS_PASS',witness['node'])
if __name__=='__main__':main()
