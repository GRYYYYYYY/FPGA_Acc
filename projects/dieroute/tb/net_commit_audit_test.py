import argparse,os,struct,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_net_commit import audit,frames,MAX

def main():
 p=argparse.ArgumentParser();p.add_argument('--directed',required=True);p.add_argument('--adversarial',required=True);a=p.parse_args()
 with tempfile.TemporaryDirectory(prefix='net_commit_audit_') as tmp:
  tmp=Path(tmp)
  for name,exe in [('directed',a.directed),('adversarial',a.adversarial)]:
   path=tmp/(name+'.bin');subprocess.run([exe],check=True,env=dict(os.environ,DIEROUTE_NET_COMMIT_TRACE=str(path)));result=audit(path);assert result['status']=='verified'
  path=tmp/'directed.bin';data=path.read_bytes();entries=list(frames(path));locations=[];base=0
  for v in entries:
   h=v['header'];n,arcs,dies,shard,nets,trees,reads,shadows,branches,paths,_,deltas=h[3:15]
   policy=base+128;command=policy+(n*2+1+arcs)*8;read=command+128;shadow=read+reads*16;branch=shadow+shadows*64;pathbase=branch+branches*64;before=pathbase+paths*16;statebytes=(dies*shard+trees+nets+1)*64;after=before+statebytes;completion=after+statebytes
   locations.append(dict(policy=policy,command=command,reads=read,shadows=shadow,branches=branch,paths=pathbase,before=before,after=after,trees=after+dies*shard*64,nets=after+(dies*shard+trees)*64,control=after+statebytes-64,completion=completion,deltas=completion+64))
   base+=h[1]
  mutations=[]
  def add(label,i,section,word,value=None):
   pos=locations[i][section]+word*8;old=struct.unpack_from('<Q',data,pos)[0];mutations.append((label,pos,old^1 if value is None else value))
  commit=next(i for i,v in enumerate(entries) if v['command'][1]==3 and v['completion'][0]==0)
  v=entries[commit];rs=next(i for i in range(len(v['after']['resources'])//8) if v['after']['resources'][i*8]==1 and v['after']['resources'][i*8+4]&0xffffffff==1)
  tree=next(i for i in range(len(v['after']['trees'])//8) if v['after']['trees'][i*8]==1 and v['after']['trees'][i*8+1]==1)
  for name,col in [('occupancy',1),('history',2),('version',3),('topology',4),('member_head',5)]:add(name,commit,'after',rs*8+col)
  for name,col in [('tree_parent',3),('tree_pip',4),('tree_depth',5),('tree_next',6),('resource_next',7)]:add(name,commit,'trees',tree*8+col)
  add('generation',commit,'nets',5);add('revision',commit,'control',1);add('free_chain',commit,'control',4,0)
  add('accepted_as_rejected',commit,'completion',0,4);add('missing_deltas',commit,'completion',7,0)
  for col in range(8):add('delta_word_'+str(col),commit,'deltas',col)
  add('read_version',commit,'reads',1);add('branch_cost',commit,'branches',5);add('branch_depth',commit,'branches',4);add('branch_sink',commit,'branches',1)
  add('path_pip',commit,'paths',0,struct.unpack_from('<Q',data,locations[commit]['paths'])[0]^(1<<32))
  add('forbidden_node',commit,'policy',1,entries[commit]['policy'][1]|(1<<40))
  add('wrong_net_id',commit,'command',4,11)
  rejected=next(i for i,v in enumerate(entries) if v['completion'][0]==5)
  add('rejection_write',rejected,'after',0)
  conflict=next(i for i,v in enumerate(entries) if v['completion'][3])
  add('conflict_diagnostic',conflict,'completion',3,0);add('truncated_read_check',conflict,'completion',2,0)
  stale=next(i for i,v in enumerate(entries) if v['completion'][4]);add('stale_shadow_diagnostic',stale,'completion',4,0)
  changed=next(i for i,v in enumerate(entries) if v['completion'][5]);add('tree_change_diagnostic',changed,'completion',5,0)
  for label,pos,value in mutations:
   bad=bytearray(data);struct.pack_into('<Q',bad,pos,value);target=tmp/'corrupt.bin';target.write_bytes(bad)
   try:audit(target)
   except (AssertionError,IndexError,KeyError):pass
   else:raise AssertionError('auditor accepted semantic corruption: '+label)
  print('net commit independent replay passed; semantic corruptions rejected='+str(len(mutations)))
if __name__=='__main__':main()
