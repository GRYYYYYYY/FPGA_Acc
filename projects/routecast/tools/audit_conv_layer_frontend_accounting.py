"""Pre-route all-pin accounting, without native labels or prediction data."""
import pathlib,json,collections,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/conv_layer_frozen_frontend_2026-10-06'
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((BASE/'protocol.json').read_text());r=json.loads((BASE/'receipt.json').read_text());assert r['protocol_sha256']==sha(BASE/'protocol.json')
 for n,h in r['outputs'].items():assert sha(BASE/n)==h
 for n,h in p['sources'].items():assert sha(BASE/'source'/n)==h
 for v in p['inputs'].values():assert sha(v['path'])==v['sha256']
 e=json.loads((BASE/'endpoints.json').read_text());m=json.loads((BASE/'mapping.json').read_text());pins=m['pin_details'];excluded={v['net_id']:v for v in e['excluded_nets']};assert len(excluded)==len(e['excluded_nets'])
 source=collections.defaultdict(list);sinks=collections.defaultdict(list);unique=set()
 for row in pins:
  key=(row['block_id'],row['port'],row['bit'],row['role']);assert key not in unique;unique.add(key)
  assert e['net_names'][str(row['net_id'])]==row['net']
  (source if row['role']=='SOURCE' else sinks)[row['net_id']].append(row)
 assert set(source)==set(sinks) and all(len(v)==1 for v in source.values())
 expected=collections.Counter((net,source[net][0]['rr_node'],row['rr_node']) for net,rows in sinks.items() if net not in excluded for row in rows)
 actual=collections.Counter((row['net_id'],row['source'],row['sink']) for row in e['connections']);assert actual==expected
 assert len({v['connection_id'] for v in e['connections']})==len(e['connections'])
 for n,v in excluded.items():assert len(sinks[n])==v['sink_pins']
 total=sum(map(len,sinks.values()));excluded_sinks=sum(v['sink_pins'] for v in excluded.values());assert total==len(e['connections'])+excluded_sinks
 assert r['connections']==len(e['connections']) and r['pin_details']==len(pins) and m['connections']==len(e['connections'])
 out=ROOT/'experiments/conv_layer_frontend_accounting_2026-10-06';out.mkdir();(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 result={'frontend_receipt_sha256':sha(BASE/'receipt.json'),'source_sha256':sha(pathlib.Path(__file__)),'logical_sink_pins':total,'retained_connections':len(e['connections']),'excluded_sink_pins':excluded_sinks,'external_nets':len(source),'retained_nets':len(expected and {v[0] for v in expected}),'excluded_nets':len(excluded),'all_pin_accounting_and_endpoint_multisets_match':True,'scope':'pre-route logical mapping accounting only; independent physical pin-class membership, native endpoint alignment and prediction quality still unverified'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
