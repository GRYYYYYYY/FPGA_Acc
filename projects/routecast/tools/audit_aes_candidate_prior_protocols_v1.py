"""Bounded local provenance audit; negative search is not proof of global historical non-use."""
import sys,json,subprocess,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
out=R/'experiments/aes_prior_protocol_audit_v1_2026-10-08';out.mkdir();candidate=R/'experiments/aes_family_candidate_v2_2026-10-08';p=json.loads((candidate/'protocol.json').read_text());hashes={sha(c['source']) for c in p['cases']};needles=['aes_cipher','aes_inv_cipher',*hashes];paths=subprocess.run(['rg','--files','experiments','work','tools','-g','*protocol*.json','-g','*manifest*.json'],cwd=R,check=True,capture_output=True,text=True).stdout.splitlines();excluded_prefixes=['experiments/aes_family_candidate_v1_2026-10-08/','experiments/aes_family_candidate_v2_2026-10-08/','experiments/aes_family_frontend_equivalence_v1_2026-10-08/','experiments/aes_prior_protocol_audit_v1_2026-10-08/'];eligible=sorted(x for x in paths if not any(x.startswith(k) for k in excluded_prefixes));rows=[];matches=[]
for path in eligible:
 f=R/path;text=f.read_text();found=[n for n in needles if n in text];rows.append({'path':path,'sha256':sha(f)})
 if found:matches.append({'path':path,'needles':found})
(out/'receipt.json').write_text(json.dumps({'source_sha256':sha(Path(__file__)),'candidate_protocol_sha256':sha(candidate/'protocol.json'),'scanned_protocol_manifest_files':rows,'matches':matches,'exclusions':excluded_prefixes,'local_prior_protocol_reference_found':bool(matches),'scope':'Bounded current local protocol/manifest provenance search; does not prove all external/deleted historical experiments absent. No routing labels or performance evaluated. Candidate eligibility remains provisional pending broad search and family lineage review.'},indent=2)+'\n');print('AES prior protocol audit',len(rows),'files',len(matches),'matches')
