"""Compare two frozen endpoint-eligibility policies without conflating repetitions."""
import csv,hashlib,json
from pathlib import Path


def main():
    old=Path('work/native_refreshed_critical_policy_v1_20261016');new=Path('work/native_full_endpoint_policy_v1_20261016');results=[];files=[]
    for root in [old,new]:
        audit=root/'independent_audit.json';a=json.loads(audit.read_text());assert len(a['outcomes'])==3 and all(r['joint_baseline_pass'] for r in a['outcomes']);files.append(audit)
    def tree(path):
        rows={}
        for r in csv.DictReader(path.open()):
            key=(int(r['net_id']),int(r['child']));assert key not in rows;rows[key]=(int(r['source']),int(r['parent']))
        return rows
    for label in ['ex5p','diffeq','alu4']:
        manifests=[r/label/'manifest.json' for r in [old,new]];a,b=[json.loads(p.read_text()) for p in manifests]
        ta,tb=Path(a['current_tree']),Path(b['current_tree']);assert tree(ta)==tree(tb)
        quality_same=all(a['current_quality'][k]==b['current_quality'][k] for k in ['total_wirelength','critical_path_delay_ns']) and a['final_crossings']==b['final_crossings'];assert quality_same
        selection=lambda s:[(v['net'],v['critical_task'],v['status'],v['accepted']) for v in s['steps']]
        assert selection(a)==selection(b)
        results.append(dict(case=label,selection_and_acceptance_identical=True,final_directed_trees_identical=True,quality_identical=True,wirelength=b['current_quality']['total_wirelength'],cpd_ns=b['current_quality']['critical_path_delay_ns'],crossings=b['final_crossings']))
        files.extend([*manifests,ta,tb])
    files.append(Path(__file__))
    output=dict(status='complete_input_arc_eligibility_preserves_observed_three_case_routes_and_decisions',outcomes=results,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='One new policy execution from same audited v2 parents. Not an independent seed, end-to-end repeat, heldout, proof for arbitrary designs, hardware or research completion.',research_complete=False,adopted=False)
    with (new/'policy_comparison.json').open('x') as stream:json.dump(output,stream,indent=2);stream.write('\n')
    print(json.dumps(results))


if __name__=='__main__':main()
