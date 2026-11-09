#!/usr/bin/env python3
"""Run the strict-SLL development cohort using the dedicated C-model router."""
import argparse,json,shutil,subprocess,time
from pathlib import Path
from run_native_case import sha256

def main():
    if not __debug__:raise RuntimeError('audit requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('search_run','independent_run','quotient_run','router','output'):p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    p.add_argument('--max-labels',type=int,default=2000000);p.add_argument('--per-pair',type=int,default=16);p.add_argument('--iterations',type=int,default=12);p.add_argument('--repeats',type=int,default=1)
    p.add_argument('--shadow-sync-searches',type=int,default=0,help='0: direct serial authority; positive: publish boundary summaries every N searches')
    p.add_argument('--corridor-attempts',type=int,default=0,help='0: flat search; positive: bounded native corridor planning/repair before flat fallback')
    p.add_argument('--corridor-reentry',action='store_true',help='compare a destination-die extension with a new remote entry using complete branch costs')
    p.add_argument('--corridor-cost-bound',action='store_true',help='bound alternative segment costs by an existing complete candidate; equal-cost candidates remain eligible')
    p.add_argument('--corridor-candidates',type=int,default=1,help='maximum completed distinct final-portal proposals, within the global corridor attempt budget; 1 preserves first-feasible behavior')
    p.add_argument('--corridor-joint-portals',action='store_true',help='one joint shortest-path search over all portals in a fixed simple die sequence; diagnostic CPU mode, at most two memberships per boundary')
    p.add_argument('--corridor-defer-budget',action='store_true',help='defer budget-limited joint calls while the tree grows; switch unresolved tasks to full-graph rescue when growth stops')
    p.add_argument('--owner-partition',action='store_true',help='store mutable resource authority only on the lowest member SLR')
    p.add_argument('--die-workers',action='store_true',help='independent die-local label tables/queues and owner-mediated boundary reads, deterministically arbitrated')
    p.add_argument('--net-workers',type=int,default=0,help='whole-net concurrent CPU proposals, 1..8; requires the native parallel router and die workers')
    p.add_argument('--worker-shadow-sync',type=int,default=0,help='refresh persistent per-lane worker summaries every N windows; 0 disables')
    p.add_argument('--summary-hbm',action='store_true',help='use synthesizable summary endpoint for live costs/validation; requires persistent summaries')
    p.add_argument('--net-commit',action='store_true',help='run all native authority mutations through the synthesizable kernel; requires summary-push; execution substrate depends on linked backend')
    p.add_argument('--summary-push',action='store_true',help='use owner-managed subscriptions and changed-only publications; requires persistent summaries')
    a=p.parse_args();assert min(a.max_labels,a.per_pair,a.iterations,a.repeats)>0
    assert a.shadow_sync_searches>=0
    assert 0<=a.corridor_attempts<0xffffffff
    assert not a.corridor_reentry or a.corridor_attempts
    assert 0<a.corridor_candidates<0xffffffff
    assert a.corridor_candidates==1 or a.corridor_attempts
    assert not a.corridor_cost_bound or a.corridor_reentry or a.corridor_candidates>1
    assert not a.corridor_joint_portals or (a.corridor_attempts and a.corridor_candidates==1)
    assert not a.corridor_defer_budget or a.corridor_joint_portals
    assert not (a.summary_hbm or a.summary_push) or a.worker_shadow_sync
    assert not (a.summary_hbm and a.summary_push)
    assert not a.net_commit or (a.summary_push and a.net_workers)
    assert a.worker_shadow_sync>=0 and (not a.worker_shadow_sync or a.net_workers)
    assert 0<=a.net_workers<=8 and (not a.net_workers or (a.die_workers and a.corridor_defer_budget))
    assert not a.die_workers or (a.owner_partition and a.corridor_joint_portals and not a.shadow_sync_searches)
    sr=a.search_run.resolve();sm=json.loads((sr/'manifest.json').read_text());ir=a.independent_run.resolve();im=json.loads((ir/'manifest.json').read_text());qr=a.quotient_run.resolve();qm=json.loads((qr/'manifest.json').read_text())
    assert all(m['status']=='passed' and m['inputs_unchanged'] for m in (sm,im,qm))
    assert im['parent_manifests'][str(sr/'manifest.json')]==qm['inputs'][str(sr/'manifest.json')]==sha256(sr/'manifest.json')
    graph,mapping,footprint=map(Path,sm['command'][1:4]);search=sr/'search'
    inputs={str(p/'manifest.json'):sha256(p/'manifest.json') for p in (sr,ir,qr)}
    inputs[str(graph/'nodes.bin')]=sm['inputs'][str(graph/'nodes.bin')];inputs[str(mapping/'footprint_node_map.bin')]=sm['inputs'][str(mapping/'footprint_node_map.bin')]
    if a.corridor_attempts:
        gm=graph.parent/'manifest.json';inputs[str(gm)]=sha256(gm)
        inputs[str(graph/'pips.bin')]=json.loads(gm.read_text())['artifacts']['graph/pips.bin']
    fm=footprint.parent/'manifest.json';inputs[str(fm)]=sha256(fm);f=json.loads(fm.read_text())
    for name in ('tasks.bin','owners.bin','nets.bin'):inputs[str(footprint/name)]=f['artifacts']['footprint/'+name]
    for name in ('offsets.bin','arcs.bin','node_protection.bin','exclusive_net.bin'):inputs[str(search/name)]=sm['artifacts']['search/'+name]
    for name in ('node_groups.bin','reverse_offsets.bin','reverse_sources.bin','groups.bin'):inputs[str(qr/'quotient'/name)]=qm['artifacts']['quotient/'+name]
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    for name in (Path(__file__).name,'run_native_case.py','route_native_cohort.cpp'):shutil.copy2(Path(__file__).with_name(name),out/name)
    for name in ('native_route_state.hpp','native_die_access.hpp','native_boundary_shadow.hpp','native_corridor.hpp','native_monotone.hpp','native_quotient.hpp','native_csr_io.hpp','sparse_search.hpp','sparse_table.hpp','sparse_label_worker.hpp','label_packet.hpp'):shutil.copy2(Path(__file__).parent.parent/'include'/name,out/name)
    if a.net_workers:
        shutil.copy2(Path(__file__).with_name('route_native_parallel.cpp'),out/'route_native_parallel.cpp')
        for name in ('native_net_transaction.hpp','native_worker_shadows.hpp','native_summary_hbm.hpp','summary_hbm.hpp','owner_publish_hbm.hpp'):shutil.copy2(Path(__file__).parent.parent/'include'/name,out/name)
    if a.net_workers:shutil.copy2(Path(__file__).parent.parent/'src/summary_hbm.cpp',out/'summary_hbm.cpp')
    if a.net_workers:shutil.copy2(Path(__file__).parent.parent/'src/owner_publish_hbm.cpp',out/'owner_publish_hbm.cpp')
    if a.net_workers:
        for name in ('native_net_commit.hpp','net_commit_hbm.hpp'):shutil.copy2(Path(__file__).parent.parent/'include'/name,out/name)
        shutil.copy2(Path(__file__).parent.parent/'src/net_commit_hbm.cpp',out/'net_commit_hbm.cpp')
    shutil.copy2(Path(__file__).with_name('route_native_strict_parallel.cpp'),out/'route_native_strict_parallel.cpp')
    for name in ('native_capacity_grants.hpp','native_sll_grant_commit.hpp','native_net_transaction_strict.hpp'):
        shutil.copy2(Path(__file__).parent.parent/'include'/name,out/name)
    shutil.copy2(a.router,out/'router')
    command=[str(out/'router'),str(graph),str(search),str(footprint),str(mapping),str(qr/'quotient'),sm['architecture_sha256'][:32],str(out/'route'),str(a.max_labels),str(a.per_pair),str(a.iterations),str(a.repeats)]
    options=[a.shadow_sync_searches,a.corridor_attempts,int(a.corridor_reentry),int(a.corridor_cost_bound),a.corridor_candidates,int(a.corridor_joint_portals),int(a.corridor_defer_budget),int(a.owner_partition),int(a.die_workers)]
    defaults=[0,0,0,0,1,0,0,0,0]
    last=max((i+1 for i,(value,default) in enumerate(zip(options,defaults)) if value!=default),default=0)
    if a.net_workers:last=len(options)
    command.extend(map(str,options[:last]))
    if a.net_workers:command.append(str(a.net_workers))
    if a.worker_shadow_sync:command.append(str(a.worker_shadow_sync))
    if a.summary_hbm or a.summary_push:command.append('2' if a.summary_push else '1')
    if a.net_commit:command.append('1')
    record=dict(schema='dieroute.native_cohort_run.v1',status='running',execution_profile='strict_sll_cmodel_development',strict_sll_capacity=True,board_result=False,inputs=inputs,command=command,started_ns=time.time_ns(),source_sha256={f.name:sha256(f) for f in out.iterdir() if f.is_file()})
    manifest=out/'manifest.json'
    def save():
        tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(manifest)
    save()
    try:
        for path,digest in inputs.items():assert sha256(path)==digest,path
        with (out/'run.log').open('w') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);record['pid']=proc.pid;save();record['returncode']=proc.wait()
        for path,digest in inputs.items():assert sha256(path)==digest,path
        record['inputs_unchanged']=True;assert record['returncode']==0,'cohort execution failed'
        result=json.loads((out/'route/audit.json').read_text());record.update(status='passed',electrical_model_converged=result['electrical_model_converged_repeats']==a.repeats)
    except Exception as exc:record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns();record['artifacts']={str(f.relative_to(out)):sha256(f) for f in out.rglob('*') if f.is_file() and f!=manifest};save()
    print(json.dumps({'status':record['status'],'electrical_model_converged':record['electrical_model_converged'],'manifest':str(manifest)}))
if __name__=='__main__':main()
