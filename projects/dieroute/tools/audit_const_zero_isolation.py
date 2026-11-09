"""Verify exact source and link-config isolation for the constant-zero candidate."""
import hashlib
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
p=root/'work/native_commit_const_zero_variant_20261015'
parent=root/'work/native_snapshot_sharded_hw_v1_20261014'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
old='bool zero(const SummaryWord& w,unsigned start){bool yes=true;for(unsigned i=start;i<8;++i)yes&=w.w[i]==0;return yes;}'
new='''template<unsigned Start> bool zero(const SummaryWord& w){
#ifdef __SYNTHESIS__
#pragma HLS INLINE
#endif
 static_assert(Start<8,"zero start outside SummaryWord");
 std::uint64_t any=0;
 for(unsigned i=Start;i<8;++i){
#ifdef __SYNTHESIS__
#pragma HLS UNROLL
#endif
  any|=w.w[i];
 }
 return any==0;
}'''
a=(parent/'source/net_commit_sharded_hbm.cpp').read_text()
assert a.count(old)==1
expected=a.replace(old,new)
expected,count=re.subn(r'zero\((\w+),([056])\)',r'zero<\2>(\1)',expected)
assert count==8
assert expected==(p/'source/net_commit_sharded_hbm.cpp').read_text()
assert sha(parent/'source/net_commit_sharded_hbm.cpp')==sha(p/'original_net_commit_sharded_hbm.cpp')
files={f.name for f in (parent/'source').iterdir() if f.is_file()}
assert files=={f.name for f in (p/'source').iterdir() if f.is_file()}
for name in files-{'net_commit_sharded_hbm.cpp'}:
 assert sha(parent/'source'/name)==sha(p/'source'/name),name
protocol=json.loads((p/'link_protocol.json').read_text())
original=json.loads((parent/'protocol.json').read_text())
normalize=lambda c:[s.replace(str(p),'<BUILD>').replace(str(parent),'<BUILD>') for s in c]
assert normalize(protocol['command'][:-1])==normalize(original['commands'][-1]['command'])
assert protocol['command'][-1]=='--save-temps'
assert sha(p/'connectivity.cfg')==sha(parent/'connectivity.cfg')
for n in ['worker.xo','snapshot.xo']:assert sha(p/n)==sha(parent/n)
protected={root.parent/'persistroute/src/accelerated_pathfinder.cpp':'bc02685f60db5ee761454a086bd80074d0d55cfed1acc451dd642352b71c80e7',root/'src/net_commit_hbm.cpp':'84d5550636cd7bfd12b34176294ca29bd57c0cc15e2a17e11a3c6de32252260c'}
for f,h in protected.items():assert sha(f)==h,f
sources=[Path(__file__).resolve(),p/'link_protocol.json',parent/'protocol.json',p/'source/net_commit_sharded_hbm.cpp',p/'original_net_commit_sharded_hbm.cpp']+list(protected)
result=dict(status='constant_zero_candidate_source_and_link_isolation_verified',source_files=len(files),unchanged_source_files=len(files)-1,rewritten_calls=count,protected_sources_unchanged=True,companion_xos_unchanged=True,connectivity_unchanged=True,only_extra_link_flag='--save-temps',source_sha256={str(f):sha(f) for f in sources},scope='Exact textual transformation and configuration/source isolation. Functional evidence separate; not semantic proof for all inputs, routed timing closure or bitstream correspondence.',board_result=False,research_complete=False)
with (p/'isolation_audit.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps({k:result[k] for k in ['status','source_files','unchanged_source_files','rewritten_calls']}))
