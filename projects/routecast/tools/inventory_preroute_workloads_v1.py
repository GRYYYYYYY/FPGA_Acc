"""Source-only workload inventory; no route outcome or holdout admission."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'placement_consumer_economic_admission_v1_2026-10-20'
V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/benchmarks'
def main():
    roots=[V/'verilog',V/'ultraembedded',V/'vexriscv']
    files=sorted({p for folder in roots for p in folder.glob('*.v')})
    directories=[p.name.lower() for p in E.iterdir() if p.is_dir()]
    rows=[]
    for p in files:
        size=p.stat().st_size;stem=p.stem.lower();tokens=[t for t in re.split(r'[^a-z0-9]+',stem) if t]
        hint=[n for n in directories if stem in re.split(r'[^a-z0-9]+',n) or len(stem)>=5 and stem in n]
        row=dict(source=str(p),sha256=sha(p),bytes=size,name=p.stem,
                 exposure_hint_directories=hint[:20],exposure_hint_count=len(hint),
                 strict_unseen_admitted=False,eligibility='SOURCE_ONLY_FRONTEND_AND_FAMILY_AUDIT_PENDING')
        if size<=32<<20:
            text=p.read_text(errors='replace')
            # Textual structure only: these are not synthesized cells or route-work estimates.
            row['textual_structure']=dict(module_declarations=len(re.findall(r'^\s*module\s+',text,re.M)),
                 posedge_tokens=len(re.findall(r'\bposedge\b',text)),
                 negedge_tokens=len(re.findall(r'\bnegedge\b',text)),
                 include_directives=len(re.findall(r'`include\b',text)))
        rows.append(row)
    out=dict(status='LOCAL_SOURCE_ONLY_WORKLOAD_INVENTORY_FROZEN',rows=rows,
             scope='Top-level Verilog files in frozen local vendor benchmark folders. No native route labels,netlists or QoR read. Name-based exposure hints are incomplete,not proof of independence or absence of prior exposure. Textual size/module/sensitivity counts do not establish synthesized scale,clock legality,source equivalence or expected router time.',
             next='Use this inventory only to propose frontend preflights;require complete family/source provenance,architecture/clock support and frozen pre-route structural-size measurements before workload admission. No best-native-runtime selection.',
             bindings={str(Path(__file__)):sha(__file__)})
    with (D/'source_workload_inventory_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print('SOURCE_ONLY_INPUTS',len(rows))
    for row in sorted(rows,key=lambda r:-r['bytes'])[:10]:print(row['name'],row['bytes'],'exposure_hints',row['exposure_hint_count'])
if __name__=='__main__':main()
