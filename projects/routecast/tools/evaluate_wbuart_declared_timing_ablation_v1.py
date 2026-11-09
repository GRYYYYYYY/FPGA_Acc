"""Score the already frozen timing-frozen ablation; primary result never replaced."""
import hashlib,json
from pathlib import Path
from evaluate_external_forecast_case_v1 import evaluate
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_native_evaluation_v1_2026-10-20';O=D/'declared_frozen_timing_ablation_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);fp=E/'wbuart_forecasts_v1_2026-10-20/manifest.json';fm=json.loads(fp.read_text());assert fm['primary_timing_policy']=='warm_timing_round_updated' and 'warm_timing_frozen' in fm['timing_policies'];fv=json.loads((fp.parent/'verification.json').read_text());workflow=json.loads((D/'workflow.json').read_text());comparisons=[]
 for row in workflow['comparisons']:
  source=Path(row['specification']);spec=json.loads(source.read_text());arms=next(r['arms'] for r in fv['rows'] if r['case']==row['case']);frozen=[a for a in arms if a['timing_policy']=='warm_timing_frozen'];assert len(frozen)==2
  spec['predictions']={('native_retained_on' if a['initializer']=='native_retained' else 'raw_min_on'):{'frame':str(Path(a['output'])/'sketch.json'),'proof':str(Path(a['output'])/'complete_event_audit.json')} for a in frozen};folder=O/row['case'];folder.mkdir(parents=True);sp=folder/'specification.json';sp.write_text(json.dumps(spec,indent=2)+'\n');comparisons.append({'case':row['case'],'specification':str(sp),'comparison':str(folder/'comparison.json')})
 (O/'workflow.json').write_text(json.dumps({'comparisons':comparisons,'predeclared_timing_ablation_manifest':str(fp),'primary_policy_unchanged':True,'scope':'Post-label materialization of previously declared and generated frozen-timing ablation; same original domain/gate, no method/parameter/case choice or primary replacement.','bindings':{str(p):sha(p) for p in [Path(__file__),fp,fp.parent/'verification.json',D/'workflow.json']}},indent=2)+'\n')
 for row in comparisons:print('DECLARED_ABLATION_GATE',row['case'],evaluate(row['specification'],row['comparison']),flush=True)
if __name__=='__main__':main()
