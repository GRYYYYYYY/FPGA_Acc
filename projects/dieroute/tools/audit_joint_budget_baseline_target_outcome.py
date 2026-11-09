"""Independent unchanged-net/crossing and endpoint review of one private probe."""
import csv,hashlib,json,struct
from decimal import Decimal
from pathlib import Path
from profile_sb_ex5p_native_STA_paths import parse


def main():
    root=Path('work/native_joint_budget_net_repair_v2_20261016')
    D=Path('work/native_joint_budget_ex5p_baseline_target_probe_20261016')
    manifest=root/'ex5p/manifest.json';protocol=root/'protocol.json'
    state=json.loads(manifest.read_text());case=json.loads(protocol.read_text())['cases'][0]
    beforetree=Path(state['current_tree']);aftertree=D/'route.route_trees.csv'
    diefile=Path(case['topology_prefix']+'.node_die');dies=[r[0] for r in struct.iter_unpack('<H',diefile.read_bytes())]
    def trees(path):
        result={}
        for r in csv.DictReader(path.open()):
            net=int(r['net_id']);child=int(r['child']);edge=(int(r['source']),int(r['parent']))
            assert child not in result.setdefault(net,{})
            result[net][child]=edge
        return result
    before=trees(beforetree);after=trees(aftertree);assert set(before)==set(after)
    changed=[n for n in before if before[n]!=after[n]];assert changed==[222]
    crossings=lambda t:sum(dies[v]!=dies[u] for p in t.values() for v,(_,u) in p.items())
    baseline=trees(Path(case['native_tree']));assert crossings(after)<=crossings(baseline)
    oldreport=beforetree.parent/'native_validation/report_timing.setup.rpt';newreport=D/'native_validation/report_timing.setup.rpt'
    old=parse(oldreport.read_text());new=parse(newreport.read_text());oldmap={p['endpoint']:p for p in old}
    assert set(oldmap)=={p['endpoint'] for p in new}
    deltas=[dict(endpoint=p['endpoint'],before_ns=oldmap[p['endpoint']]['arrival_ns'],after_ns=p['arrival_ns'],delta_ns=str(Decimal(p['arrival_ns'])-Decimal(oldmap[p['endpoint']]['arrival_ns']))) for p in new]
    qualityfile=D/'native_validation/validation.json';q=json.loads(qualityfile.read_text());assert q['legal']
    oldcritical=next(p for p in new if p['endpoint']==old[0]['endpoint'])
    inputs=[manifest,protocol,beforetree,aftertree,diefile,Path(case['native_tree']),oldreport,newreport,qualityfile,D/'result.json',Path(__file__),Path('tools/profile_sb_ex5p_native_STA_paths.py')]
    output=dict(status='one_net_change_crossing_budget_and63endpoint_reports_independently_checked',changed_nets=changed,unchanged_nets=len(before)-1,
                before_crossings=crossings(before),after_crossings=crossings(after),baseline_crossings=crossings(baseline),
                before_worst_path=old[0],after_worst_path=new[0],previous_critical_endpoint_after=oldcritical,
                endpoints_above_baseline_printed=[r for r in deltas if Decimal(r['after_ns'])>Decimal(str(case['baseline_cpd_ns']))],
                endpoint_deltas=deltas,native_quality=q,adopted=False,research_complete=False,
                source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                scope='Archived native reports, exact one-net change, cross counts. Not an independent exhaustive search or repeat experiment. Rounded path arrivals are descriptive.')
    with (D/'independent_outcome_audit.json').open('x') as stream:json.dump(output,stream,indent=2);stream.write('\n')
    print(json.dumps(dict(changed_nets=changed,unchanged_nets=len(before)-1,before_crossings=crossings(before),after_crossings=crossings(after),
                         old_critical_endpoint=old[0]['endpoint'],old_critical_endpoint_after_ns=oldcritical['arrival_ns'],new_critical_endpoint=new[0]['endpoint'],
                         endpoints_above_baseline=output['endpoints_above_baseline_printed']),indent=2))


if __name__=='__main__':main()
