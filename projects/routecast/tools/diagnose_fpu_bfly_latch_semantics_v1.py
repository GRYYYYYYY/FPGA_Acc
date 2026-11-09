"""Complete latch provenance and serialization census; no semantics repair."""
import json,re,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/fpu_bfly_frontend_readiness_v1_2026-10-10';P=R/'experiments/fpu_bfly_frontend_admission_v1_2026-10-10/verification.json';p=json.loads(P.read_text());assert all(sha(k)==v for k,v in p['bindings'].items())
A=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';lines=(S/'design.v').read_text().splitlines();groups=Counter(x['source'] for x in p['latches']);sources=[]
for src,count in sorted(groups.items()):
 m=re.fullmatch(r'design.v:(\d+)\.\d+-(\d+)\.\d+',src);assert m,src
 a,b=map(int,m.groups());sources.append(dict(source_attribute=src,storage_bits=count,start_line=a,end_line=b,source_lines=lines[a-1:b]))
blif=[]
for line,text in enumerate((S/'design.blif').read_text().splitlines(),1):
 if text.startswith('.latch '):
  t=text.split();assert len(t)==6;blif.append(dict(line=line,data=t[1],output=t[2],type=t[3],control=t[4],initial=t[5]))
counts=Counter(x['type'] for x in blif);assert dict(counts)=={'re':2308,'al':652};assert sum(groups.values())==counts['al']
arch=[dict(attributes=x.attrib,children=[dict(tag=c.tag,attributes=c.attrib) for c in x]) for x in E.parse(A).iter('pb_type') if x.get('blif_model')=='.latch'];assert arch and all(x['attributes'].get('class')=='flipflop' for x in arch)
D=R/'experiments/fpu_bfly_latch_semantics_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={**p['bindings'],**{str(x):sha(x) for x in [P,A,S/'design.v',S/'design.blif',Path(__file__).resolve()]}}
assert all(sha(k)==v for k,v in bindings.items())
(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,source_groups=sources,blif_storage_counts=dict(counts),active_low_storage=[x for x in blif if x['type']=='al'],architecture_latch_nodes=arch,complete_652_source_and_serialized_census_pass=True,transparent_latch_timing_proven=False,native_admitted=False,scope='Four source-attribute ranges retained verbatim; whole BLIF census preserves al storage count. Not per-bit semantic equivalence or a Verilog behavior proof. Architecture .latch class flipflop evidence alone does not prove transparent latch timing; no source alteration or route trial.'),indent=2)+'\n');print('PASS source groups',dict(groups),'BLIF',dict(counts),'architecture nodes',len(arch))
