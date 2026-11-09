"""Exact original criticality parity, all native atom aggregation and CID identity."""
import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure


def decode(text,word):
    bits=int(word,16);assert 0<=bits<2**32
    value=struct.unpack('<f',bits.to_bytes(4,'little'))[0]
    parsed=float(text)
    if math.isnan(value):assert math.isnan(parsed)
    else:assert struct.pack('<f',parsed)==bits.to_bytes(4,'little')
    return value,bits


def word(value):return int.from_bytes(struct.pack('<f',value),'little')
def category(x):return 'nan' if math.isnan(x) else 'positive_infinity' if x==math.inf else 'negative_infinity' if x==-math.inf else 'finite'


def main(root):
    root=Path(root).resolve();protocol=json.loads((root/'protocol.json').read_text());work=root/'work'
    assert json.loads((root/'native_terminal.json').read_text())['exit_status']==0
    old=R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality'
    assert sha(work/'criticality.tsv')==sha(old/'criticality.tsv')
    binding=closure([Path(__file__)])
    for p in (root/'protocol.json',root/'native_terminal.json',work/'native.log',work/'criticality.tsv',work/'timing.tsv',old/'criticality.tsv',old/'initial_connection_criticalities.json'):
        binding[str(p)]=sha(p)
    criticalities=[]
    for number,line in enumerate((work/'criticality.tsv').read_text().splitlines(),1):
        p=line.split('\t');assert len(p)==10 and p[0]=='C' and int(p[1])==number
        criticalities.append(p)
    assert len(criticalities)==92608
    atoms=[];rows={};stats=Counter();header=None;total_atoms=0
    with (work/'timing.tsv').open() as stream:
        for line in stream:
            p=line.rstrip('\n').split('\t')
            if p[0]=='H':
                assert header is None and not rows and not atoms and len(p)==7 and p[1]=='1' and p[4]=='0';header=p;continue
            assert header is not None
            if p[0]=='A':
                assert len(p)==10
                seq,net,glob,local,atom=map(int,p[1:6]);assert seq==len(rows)+1
                slack,sbits=decode(p[6],p[7]);crit,cbits=decode(p[8],p[9]);atoms.append((seq,net,glob,local,atom,slack,crit,sbits,cbits))
                stats['atom_slack_'+category(slack)]+=1;stats['atom_criticality_'+category(crit)]+=1;total_atoms+=1
                continue
            assert p[0]=='S' and len(p)==15
            seq,net,glob,local,count=map(int,p[1:6]);assert seq==len(rows)+1 and count==len(atoms)
            oldrow=criticalities[seq-1];assert [seq,net,glob,local]==list(map(int,oldrow[1:5]))
            slack,sbits=decode(p[6],p[7]);raw,rbits=decode(p[8],p[9]);trans,tbits=decode(p[10],p[11]);assert word(float(oldrow[5]))==tbits
            assert p[12:14]==oldrow[8:10] and all(x in ('0','1') for x in p[12:15])
            minimum=math.inf;maximum=0.0
            for a in atoms:
                assert a[:4]==(seq,net,glob,local)
                # C++ std::min/max keep first argument on equal or unordered comparison.
                if a[5]<minimum:minimum=a[5]
                if maximum<a[6]:maximum=a[6]
            assert word(minimum)==sbits and word(maximum)==rbits
            key=(net,local);assert key not in rows
            rows[key]=dict(sequence=seq,net=net,global_pin=glob,local_sink_pin=local,atom_count=count,
                slack_bits=p[7],raw_criticality_bits=p[9],transformed_criticality_bits=p[11],ignored=p[12]=='1',global_net=p[13]=='1',clock_net=p[14]=='1',
                atoms=[dict(atom_pin=a[4],slack_bits=f'{a[7]:08x}',criticality_bits=f'{a[8]:08x}') for a in atoms])
            stats['cluster_slack_'+category(slack)]+=1;stats['cluster_pins_with_multiple_atoms']+=count>1;stats['cluster_pins_without_atoms']+=count==0;atoms=[]
    assert header is not None and not atoms and len(rows)==len(criticalities)==92608
    manifest=json.loads((old/'initial_connection_criticalities.json').read_text());expected={(r['net'],r['local_sink_pin']):r for r in manifest}
    assert len(expected)==77106 and {k for k,v in rows.items() if not v['ignored']}==set(expected)
    for key,reference in expected.items():
        row=rows[key];assert row['global_pin']==reference['global_pin']
        assert row['transformed_criticality_bits']==f"{word(float(reference['criticality_float32_text'])):08x}"
    assert not (work/'output.route').exists()
    log=(work/'native.log').read_text();assert 'exit_before_first_getter_returns=1' in log and f'atom_rows={total_atoms}' in log
    assert 'VPR succeeded' not in log and 'Successfully routed after' not in log
    for p,h in protocol['bindings'].items():assert sha(p)==h
    output=root/'per_cluster_atom_identity_bits.json';output.write_text(json.dumps({f'{n}:{pin}':v for (n,pin),v in rows.items()},separators=(',',':'))+'\n');binding[str(output)]=sha(output)
    result=dict(all_pass=True,bindings=binding,original_criticality_bytes_identical=True,all_cluster_sink_pins=92608,all_nonignored_CIDs=77106,ignored_sink_pins=15502,
        all_atom_rows=total_atoms,all_native_min_slack_max_criticality_aggregates_reconstructed=True,explicit_float32_bits_and_nonfinite_values_preserved=True,
        stats=dict(stats),header=header,scope='Initialized timing metadata at first native criticality getter, exits before getter returns. Atom worst-path slack is not connection additive budget or native routed QoR. No model, labels, timing constraints or routing parameters changed.',promoted=False)
    (root/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','header')},indent=2))


if __name__=='__main__':main(sys.argv[1])
