"""Extend the frozen scoped corpus to all module aliases for chosen peripherals."""
import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/ultraembedded_lineage_inventory_v1_2026-10-08/inventory.json';d=json.loads(P.read_text());chosen=[c for c in d['candidates'] if c['filename'] in ['usb_uart_core.v','mmc_core.v']];aliases={c['filename']:c['modules'] for c in chosen};hits={k:[] for k in aliases};patterns={k:re.compile(r'(?<![A-Za-z_0-9])(?:'+ '|'.join(map(re.escape,names))+r')(?![A-Za-z_0-9])') for k,names in aliases.items()}
for item in d['searched_files']:
 raw=Path(item['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==item['sha256'],'Frozen prior-use corpus changed; do not silently update provenance';text=raw.decode('utf-8',errors='replace')
 for name,pattern in patterns.items():
  found=sorted(set(pattern.findall(text)))
  if found:hits[name].append(dict(path=item['path'],aliases=found))
D=R/'experiments/ultraembedded_module_alias_audit_v1_2026-10-08';D.mkdir();(D/'verification.json').write_text(json.dumps(dict(inventory_path=str(P),inventory_sha256=hashlib.sha256(P.read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),files_checked=len(d['searched_files']),aliases=aliases,hits=hits,all_selected_aliases_absent_in_frozen_scoped_corpus=not any(hits.values()),scope='Exact case-sensitive whole-identifier module aliases in the entire frozen 32092-file local metadata/code corpus. Does not cover external history, all raw routes/logs/netlists, normalized HDL equivalence, other project histories or broad domain overlap. No strict-heldout proof.'),indent=2)+'\n');print({k:len(v) for k,v in hits.items()},flush=True)
