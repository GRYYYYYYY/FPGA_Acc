"""Conservative source-family grouping and bounded provenance-reference scan."""
import hashlib,json,re,time
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'preroute_family_reference_crosscheck_v2_2026-10-20';I=E/'placement_consumer_economic_admission_v1_2026-10-20/source_workload_inventory_v1.json'
def family(row):
 p=Path(row['source']);stem=row['name'].lower()
 if p.parent.name=='vexriscv':return 'vexriscv_folder'
 if p.parent.name=='ultraembedded':return 'ultraembedded_folder'
 if stem.startswith('stereovision'):return 'stereovision'
 if re.fullmatch(r'lu\d+peeng',stem):return 'lu_peeng'
 if stem.startswith('diffeq'):return 'diffeq'
 if stem.startswith('multiclock'):return 'multiclock_tests'
 return stem
ALIASES={'vexriscv_folder':['vexriscv','briey','murax'],'ultraembedded_folder':['ultraembedded','enet_core','mmc_core','soc_core','uriscv_core','usb_uart_core','ethernet','mmc','usb_uart','uriscv'],'lu_peeng':['lu8peeng','lu32peeng','lu64peeng'],'diffeq':['diffeq','diffeq1','diffeq2'],'stereovision':['stereovision','stereovision0','stereovision1','stereovision2','stereovision3']}
def main():
 D.mkdir(exist_ok=False);start=time.perf_counter();inventory=json.loads(I.read_text());groups=defaultdict(list)
 for row in inventory['rows']:groups[family(row)].append(row)
 paths=[Path(p) for p in Path('/tmp/routecast_family_provenance_paths_v1.txt').read_text().splitlines()];excluded=[];scan=[]
 for p in paths:
  if p.parts[1] in ['placement_consumer_economic_admission_v1_2026-10-20','preroute_family_admission_v1_2026-10-20']:excluded.append(str(p));continue
  if p.stat().st_size>2<<20:excluded.append(str(p));continue
  scan.append(p)
 protocol=dict(status='FAMILY_AND_SOURCE_PREFLIGHT_FROZEN',grouping='Conservative samefolder group for VexRiscv and Ultraembedded;stereovision/LU/diffeq variants grouped. Sharedfolder is an exclusion caution,not proof all algorithms equivalent.',provenance='Scan existing protocol/manifest/decision/source/family/exposure JSON filenames up to2MiB;exclude new inventory/admission outputs to avoid selfexposure. Matching refs do not prove routelabel use. Absence does not prove heldout because scan incomplete.',frontend_plan='After references inspected,select eligible-family representatives by fixed preroute source-size/support criteria. No exactrouter timing/QoR is consulted.',scanned_files=len(scan),excluded_files=excluded,bindings={str(I):sha(I),str(Path(__file__)):sha(__file__)})
 (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');hits=defaultdict(list);hash_to_family={r['sha256']:f for f,rows in groups.items() for r in rows};patterns={f:re.compile(r'(?<![a-z0-9])(?:'+ '|'.join(map(re.escape,ALIASES.get(f,[f])))+r')(?![a-z0-9])',re.I) for f in groups};scanned_bytes=0;file_digests={}
 for index,p in enumerate(scan):
  raw=p.read_bytes();file_digests[str(p)]=hashlib.sha256(raw).hexdigest();text=raw.decode('utf-8',errors='replace');lower=text.lower();ascii_only=text.isascii();scanned_bytes+=len(text);digest_hits={hash_to_family[h] for h in re.findall(r'(?<![a-f0-9])[a-f0-9]{64}(?![a-f0-9])',text) if h in hash_to_family}
  for f,pattern in patterns.items():
   exact=f in digest_hits
   aliases=ALIASES.get(f,[f])
   name=False if ascii_only and not any(alias in lower for alias in aliases) else bool(pattern.search(text))
   if exact or name:hits[f].append(dict(path=str(p),source_hash_match=exact,alias_match=name))
  if index%3000==0:print('FAMILY_SCAN_FILES',index,flush=True)
 rows=[]
 for f,sources in sorted(groups.items()):
  descriptors=[]
  for r in sources:
   p=Path(r['source']);assert sha(p)==r['sha256'];text=p.read_text(errors='replace');clean=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S);edges=sorted(set(re.findall(r'\b(?:pos|neg)edge\s+([A-Za-z_$][\w$]*)',clean)));includes=re.findall(r'`include\s+"([^"]+)"',clean);descriptors.append(dict(name=r['name'],source=str(p),sha256=r['sha256'],bytes=r['bytes'],module_names=re.findall(r'\bmodule\s+([A-Za-z_$][\w$]*)',clean),lexical_edge_signals=edges,includes=[dict(name=name,resolves_relative=(p.parent/name).is_file()) for name in includes]))
  rows.append(dict(family=f,sources=descriptors,reference_count=len(hits[f]),exact_source_hash_references=sum(h['source_hash_match'] for h in hits[f]),reference_samples=hits[f][:30],strict_unseen_admitted=False,status='PRIOR_REFERENCES_REQUIRE_PURPOSE_REVIEW' if hits[f] else 'NO_REFERENCE_IN_BOUNDED_SCAN_NOT_HELDOUT_PROOF'))
 (D/'scanned_file_digests.json').write_text(json.dumps(file_digests,indent=2)+'\n')
 out=dict(status='CONSERVATIVE_FAMILY_SOURCE_REFERENCE_AUDIT_COMPLETE',rows=rows,scanned_files=len(scan),scanned_bytes=scanned_bytes,excluded_files=len(excluded),seconds=time.perf_counter()-start,strict_unseen_admitted=0,bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(D/'scanned_file_digests.json'):sha(D/'scanned_file_digests.json')})
 with (D/'family_audit_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 for row in rows:print(row['family'],len(row['sources']),row['reference_count'],row['exact_source_hash_references'])
if __name__=='__main__':main()
