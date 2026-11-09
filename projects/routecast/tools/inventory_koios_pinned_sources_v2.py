"""Read-only complete Koios source/config provenance; no native labels opened."""
import datetime,hashlib,json,resource,subprocess,urllib.request
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
COMMIT='8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
VTR=R.parent/'tileplace/third_party'/('vtr-verilog-to-routing-'+COMMIT)
DIRS=['vtr_flow/benchmarks/verilog/koios','vtr_flow/benchmarks/verilog/koios_proxy','vtr_flow/benchmarks/system_verilog/koios_sv']


def config(path):
    values=defaultdict(list)
    for line in path.read_text().splitlines():
        line=line.split('#',1)[0].strip()
        if '=' in line:
            key,value=line.split('=',1);values[key.strip()].append(value.strip())
    return dict(values)


def group(path):
    name=Path(path).name;stem=Path(path).stem
    if '/koios_proxy/' in path:return 'koios_proxy_generator'
    if '/koios_sv/' in path:return 'deepfreeze'
    for prefix in ('bwave_like','clstm_like','dla_like','tdarknet_like','tpu_like'):
        if name.startswith(prefix+'.'):return prefix
    if name in ('conv_layer.v','conv_layer_hls.v'):return 'conv_layer'
    return stem


def git_blob(path):
    size=path.stat().st_size;h=hashlib.sha1(('blob '+str(size)+'\0').encode())
    with path.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()


def main():
    # Reserve remaining address space for the currently verified pipeline stage.
    # Refuse gaps or unknown identities; no launch/recovery of experiment stages.
    from observe_neuron_scaled_present_pipeline_v1 import snapshot
    observation=snapshot()
    assert observation['supervisor']['verified_live'], 'Pipeline owner not verified live'
    active=[v for v in observation['stages'].values() if v.get('process',{}).get('verified_live')]
    assert len(active)==1, 'Expected exactly one verified active stage'
    stage=active[0];process=stage['process'];limit_record=stage['recorded_address_space_limit_bytes']
    limits=Path(f"/proc/{process['pid']}/limits").read_text()
    actual=next(line.split() for line in limits.splitlines() if line.startswith('Max address space'))
    assert int(actual[3])==int(actual[4])==limit_record
    vm=process['memory_KiB']['VmSize']*1024
    reserve=max(0,limit_record-vm)
    free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    limit=256*2**20
    admission=dict(shared_headroom_bytes=free,remaining_live_stage_reservation_bytes=reserve,
        observed_stage_pid=process['pid'],observed_stage_startticks=process['startticks'],
        stage_address_space_limit_bytes=limit_record,child_limit_bytes=limit,margin_bytes=8*2**30,
        admitted=free>=reserve+limit+8*2**30)
    assert admission['admitted'], 'Source inventory not launched: memory admission unavailable'
    resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
    out=R/'experiments/koios_pinned_source_inventory_v2_2026-10-15';out.mkdir()
    url=f'https://api.github.com/repos/verilog-to-routing/vtr-verilog-to-routing/git/trees/{COMMIT}?recursive=1'
    request=urllib.request.Request(url,headers={'User-Agent':'RouteCast-source-provenance'})
    with urllib.request.urlopen(request,timeout=30) as f:raw=f.read(16*2**20+1)
    assert len(raw)<=16*2**20
    (out/'upstream_tree.json').write_bytes(raw);upstream=json.loads(raw);assert upstream.get('truncated') is False
    blobs={x['path']:x for x in upstream['tree'] if x['type']=='blob'}
    listing=subprocess.run(['rg','--files',str(VTR/'vtr_flow/tasks')],text=True,capture_output=True,check=True)
    configs=sorted(Path(x) for x in listing.stdout.splitlines() if '/koios' in x and x.endswith('/config/config.txt'))
    members=defaultdict(list);sources=set();archs=set();task_rows=[]
    for path in configs:
        values=config(path);sources.add(path)
        cdir=values.get('circuits_dir',[]);assert len(cdir)==1
        for name in values.get('circuit_list_add',[]):
            src=VTR/'vtr_flow'/cdir[0]/name;assert src.is_file();members[str(src.relative_to(VTR))].append(str(path.relative_to(VTR)))
        adir=values.get('archs_dir',[]);assert len(adir)==1
        for name in values.get('arch_list_add',[]):archs.add(VTR/'vtr_flow'/adir[0]/name)
        task_rows.append(dict(path=str(path.relative_to(VTR)),values=values))
    assets=[]
    for d in DIRS:
        for path in sorted((VTR/d).iterdir()):
            if path.is_file() and path.suffix in ('.v','.sv','.md'):sources.add(path);assets.append(path)
    sources.update(archs);rows=[];bindings={str(Path(__file__)):sha(__file__),str(R/'tools/observe_neuron_scaled_present_pipeline_v1.py'):sha(R/'tools/observe_neuron_scaled_present_pipeline_v1.py')}
    for path in sorted(sources):
        rel=str(path.relative_to(VTR));expected=blobs[rel]['sha'];before=path.stat();local_blob=git_blob(path);digest=sha(path);after=path.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
        assert local_blob==expected,('local differs from official fixed commit',rel)
        bindings[str(path)]=digest
        rows.append(dict(path=str(path),relative_to_official_VTR=rel,bytes=after.st_size,sha256=digest,upstream_git_blob_sha1=expected,official_commit_blob_equal=True))
    cohorts=[];aux=[];groups=defaultdict(list)
    for path in assets:
        rel=str(path.relative_to(VTR))
        if path.suffix not in ('.v','.sv'):continue
        role='benchmark' if rel in members and path.name!='test.v' else 'architecture_test' if path.name=='test.v' else 'shared_include'
        if role!='benchmark':aux.append(dict(source=rel,role=role));continue
        key=group(rel);groups[key].append(rel)
        cohorts.append(dict(source=rel,provisional_group=key,task_references=members[rel],prior_RC_declared_family_reference=key in ('spmv','conv_layer'),strict_family_admitted=False))
    assert len(cohorts)==40 and len(aux)==4
    assert sum('/koios_proxy/' in r['source'] for r in cohorts)==8 and sum('/koios_sv/' in r['source'] for r in cohorts)==3
    assert set(members)-{x['source'] for x in cohorts}=={x['source'] for x in aux if x['role']=='architecture_test'}
    exposure=R/'experiments/design_exposure_inventory_v3_2026-10-15/receipt.json';bindings[str(exposure)]=sha(exposure);v=json.loads(exposure.read_text());references=[x for x in v['declared_source_records'] if 'koios' in x['path'].lower()]
    for p,h in bindings.items():assert sha(p)==h
    result=dict(bindings=bindings,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),official_repository='https://github.com/verilog-to-routing/vtr-verilog-to-routing',official_commit=COMMIT,upstream_tree_API=url,upstream_tree_response_sha256=sha(out/'upstream_tree.json'),complete_upstream_tree=True,all_selected_assets_equal_official_commit=True,local_git_metadata_present=(VTR/'.git').exists(),resource_admission=admission,authenticated_files=rows,task_configs=task_rows,all_benchmark_members=cohorts,auxiliary_RTL=aux,provisional_groups=dict(groups),prior_Koios_source_declarations=references,benchmark_count=40,shared_include_count=3,architecture_test_count=1,task_config_count=len(configs),architecture_file_count=len(archs),strict_unseen_families_certified=0,new_route_labels_read=False,new_synthesis_placement_or_route_launched=False,scope='Complete pinned official Koios40 source membership across29 Verilog,8 proxy,3 SystemVerilog designs; shared includes and architecture-only test separated using actual official task lists. Names/docs yield conservative provisional groups, not independent-family certificates. spmv/conv_layer have prior local declarations; absence for others does not establish unseen status. Remaining indirect exposure and cross-project family history require audit before prospective split. All TilePlace/PersistRoute assets read-only; no new labels or heavy jobs.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(official_commit=COMMIT,benchmarks=len(cohorts),provisional_groups=len(groups),task_configs=len(configs),architecture_files=len(archs),authenticated_files=len(rows),strict_unseen_families_certified=0,new_labels_read=False),indent=2),flush=True)


if __name__=='__main__':main()
