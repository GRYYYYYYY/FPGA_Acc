"""Supplement the four explicitly bounded-out declarations, no family admission."""
import datetime,gc,json,resource,sys
from pathlib import Path
from archive_design_exposure_v3 import declarations,sha,R
from bounded_model_json_stream_v1 import unique_object,invalid_constant


def main():
    inventory=R/'experiments/design_exposure_inventory_v3_2026-10-15/receipt.json'
    data=json.loads(inventory.read_text());selected=[x for x in data['unresolved_protocols'] if x['reason']=='above2MiB_decode_bound'];assert len(selected)==4
    model=R/'experiments/titan23_neuron_scaled_present_factor1_pipeline_v1_2026-10-15';launch=json.loads((model/'launch_observation_v1.json').read_text());p=Path('/proc')/str(launch['model_pid']);st=(p/'stat').read_text().rsplit(')',1)[1].split();assert int(st[19])==launch['model_startticks'] and st[0]!='Z'
    lines=(p/'status').read_text().splitlines();vm=int(next(x for x in lines if x.startswith('VmSize:')).split()[1])*1024
    reserve=max(0,20*2**30-vm);free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());limit=512*2**20
    admission=dict(shared_headroom_bytes=free,remaining_live_model_reservation_bytes=reserve,child_limit_bytes=limit,margin_bytes=8*2**30,admitted=free>=reserve+limit+8*2**30)
    assert admission['admitted'],'No declaration analysis launched: insufficient memory'
    resource.setrlimit(resource.RLIMIT_AS,(limit,limit));rows=[];records=[];bindings={str(inventory):sha(inventory),str(Path(__file__)):sha(__file__),str(R/'tools/archive_design_exposure_v3.py'):sha(R/'tools/archive_design_exposure_v3.py')}
    for item in selected:
        path=R/item['protocol'];expected=data['stable_protocol_hashes'][item['protocol']];assert sha(path)==expected
        assert path.stat().st_size<=16*2**20
        # The previous 2MiB ceiling was a scan policy, not a measured memory
        # failure. Decode these four fixed files sequentially, bounded at16MiB.
        decoded=json.loads(path.read_text(),object_pairs_hook=unique_object,parse_constant=invalid_constant);found=list(declarations(decoded));del decoded;gc.collect()
        assert sha(path)==expected
        bindings[str(path)]=expected
        rows.append(dict(protocol=item['protocol'],bytes=path.stat().st_size,complete_strict_decode_pass=True,source_declarations=len(found)))
        records.extend(dict(protocol=item['protocol'],protocol_sha256=expected,**r) for r in found)
    out=R/'experiments/design_exposure_large_protocol_supplement_v1_2026-10-15';out.mkdir()
    report=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bindings=bindings,resource_admission=admission,complete_selected_protocols=rows,source_declarations=records,protocols_remaining_unparsed_due_to_original_2MiB_bound=0,strict_unseen_families_certified=0,scope='Exact supplement of four size-excluded protocols from the immutable v3 snapshot. Source declarations remain historical references, not reauthenticated source files or proof of model/label use. Other2228 protocols with no direct source identity and indirect/global exposure still unresolved; no unseen-family claim.')
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(protocols=rows,additional_source_declarations=len(records),strict_unseen_families_certified=0,resource_admission=admission),indent=2))


if __name__=='__main__':main()
