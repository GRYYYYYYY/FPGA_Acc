"""Audit native adapter artifacts and exact reference trajectory correspondence."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'tools'))
from run_v4_timing_protocol import signature,feedback_signature
from audit_fixed_development import audit_native_trials
from tileplace_provenance import verify_files
from tileplace_vpr import ContractError,sha256

def audit(root,reference_path):
 p=root/'report.json';r=json.loads(p.read_text());reference=json.loads(reference_path.read_text())
 process=json.loads((root/'process.json').read_text())
 if process['returncode']!=0 or r['status']!='pass':raise ContractError('native adapter run did not pass')
 verify_files(r['provenance']['implementation']['sources']);verify_files(r['provenance']['inputs'])
 for actual,expected in [(signature(r),signature(reference)),(feedback_signature(r),feedback_signature(reference)),
                         (r['phases'],reference['phases']),
                         ([t['transactions'] for t in r['trials']],[t['transactions'] for t in reference['trials']])]:
  if actual!=expected:raise ContractError('native trajectory differs from reference')
 if sha256(Path(r['output_place']['path']))!=reference['output_place']['sha256']:raise ContractError('final placement differs')
 count=audit_native_trials(r);checks=json.loads((root/'cpp_checks.json').read_text())
 if checks['status']!='pass' or not checks['checks']:raise ContractError('C++ checks missing or failed')
 return {'status':'pass','native_trials':count,'checked_color_calls':len(checks['checks']),
         'max_forbidden':max(c['forbidden'] for c in checks['checks']),
         'full_search_and_feedback_signatures_match':True,'final_place_matches':True,
         'implementation_sha256':r['provenance']['implementation']['sha256'],
         'scope':checks['scope'],
         'reports':[{'path':str(q.resolve()),'sha256':sha256(q)} for q in [p,reference_path,root/'cpp_checks.json',root/'process.json']]}

def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('reference',type=Path);a=p.parse_args()
 receipt=audit(a.run,a.reference);(a.run/'differential_audit.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
