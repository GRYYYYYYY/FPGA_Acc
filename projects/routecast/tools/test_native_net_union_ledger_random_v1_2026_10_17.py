"""Independent seeded transactional differential test, no performance claim."""
import ctypes as C,hashlib,json,random
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'experiments/native_net_union_ledger_replay_v1_2026-10-17'
assert (B/'verification.json').is_file(), 'Full real-corpus replay must pass first'
proof=json.loads((B/'verification.json').read_text());assert proof['all4498_candidates_native_decisions_deltas_and_epochs_equal']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(B/'ledger.so')==proof['library_sha256']
lib=C.CDLL(str(B/'ledger.so'));U=C.c_uint64;P=C.POINTER(U)
lib.rc_ledger_create.argtypes=[P,U];lib.rc_ledger_create.restype=C.c_void_p
lib.rc_ledger_add.argtypes=[C.c_void_p,U,U,P,U]
lib.rc_ledger_replace.argtypes=[C.c_void_p,U,U,P,U,C.POINTER(C.c_int64)]
lib.rc_ledger_export.argtypes=[C.c_void_p,P,U]
lib.rc_ledger_epoch.argtypes=[C.c_void_p,U];lib.rc_ledger_epoch.restype=U
lib.rc_ledger_free.argtypes=[C.c_void_p]
def arr(xs):return (U*len(xs))(*xs)
rng=random.Random(20261017);counts=Counter()
for trial in range(24):
 n=64;caps=[rng.randrange(4) for _ in range(n)];state={i:set(rng.sample(range(n),rng.randrange(1,16))) for i in range(12)};epochs={i:1 for i in state}
 p=lib.rc_ledger_create(arr(caps),n);assert p
 for net,nodes in state.items():assert lib.rc_ledger_add(p,net,1,arr(sorted(nodes)),len(nodes))==0
 for step in range(240):
  mode=rng.choice(['valid','valid','valid','stale','unknown','duplicate','invalid'])
  net=rng.randrange(12);ep=epochs[net];nodes=sorted(rng.sample(range(n),rng.randrange(1,22)))
  if mode=='stale':ep+=1
  if mode=='unknown':net=100
  if mode=='duplicate':nodes=[0,0]
  if mode=='invalid':nodes=[n]
  old=Counter(x for ns in state.values() for x in ns);expected_delta=None
  if mode in ['stale','unknown']:status=2
  elif mode in ['duplicate','invalid']:status=1
  else:
   changed=dict(state);changed[net]=set(nodes);new=Counter(x for ns in changed.values() for x in ns)
   expected_delta=sum(max(0,new[i]-caps[i])-max(0,old[i]-caps[i]) for i in range(n));status=3 if expected_delta>0 else 0
  delta=C.c_int64(-987654321);got=lib.rc_ledger_replace(p,net,ep,arr(nodes),len(nodes),C.byref(delta));assert got==status
  assert delta.value==(expected_delta if expected_delta is not None else -987654321)
  if status==0:state[net]=set(nodes);epochs[net]+=1
  observed=(U*n)();assert lib.rc_ledger_export(p,observed,n)==0
  reference=Counter(x for ns in state.values() for x in ns);assert list(observed)==[reference[i] for i in range(n)]
  assert all(lib.rc_ledger_epoch(p,k)==v for k,v in epochs.items())
  counts[str(status)]+=1
 lib.rc_ledger_free(p)
D=R/'experiments/native_net_union_ledger_random_v1_2026-10-17';D.mkdir(exist_ok=False)
with (D/'verification.json').open('x') as f:
 json.dump(dict(bindings={str(Path(__file__).resolve()):sha(__file__),str(B/'verification.json'):sha(B/'verification.json'),str(B/'ledger.so'):sha(B/'ledger.so')},seed=20261017,states=24,operations=5760,status_counts=dict(counts),all_operations_full_occupancy_and_all_epochs_equal=True,scope='Independent randomized state-transition arithmetic and refusal/rollback testing; not physical path, RC budget, whole-model or speed evidence.'),f,indent=2);f.write('\n')
print(dict(states=24,operations=5760,status_counts=dict(counts)))
