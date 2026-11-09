"""Check span reuse against the old independent XML parse on a real RR graph."""
import json,time,sys
import xml.etree.ElementTree as ET
from pathlib import Path
from immutable_xml_prediction_audit import ImmutableXMLAudit
from immutable_channel_span_prices_v1 import channel_span_prices
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
P=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/protocol.json'
g=json.loads(P.read_text())['inputs']['rr_graph'];path=Path(g['path'])
t=time.monotonic();ctx=ImmutableXMLAudit(path,g['sha256']);load=time.monotonic()-t
t=time.monotonic();old={}
for event,node in ET.iterparse(path,events=('end',)):
 if node.tag=='node':
  if node.get('type') in {'CHANX','CHANY'}:
   loc=node.find('loc');old[int(node.get('id'))]=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1
  node.clear()
old_s=time.monotonic()-t
t=time.monotonic();new=channel_span_prices(ctx);new_s=time.monotonic()-t
assert old==new and new and sha(path)==g['sha256']
a=(R/'tools/verify_resident_events_round_schedule_cache_v4.py').read_text();b=(R/'tools/verify_resident_events_round_schedule_cache_v5.py').read_text()
# Everything after price initialization must remain identical, including all gates.
assert a[a.index('prices.update(span_prices)'):]==b[b.index('prices.update(span_prices)'):]
D=R/'experiments/immutable_channel_span_prices_v1_2026-10-09';D.mkdir(exist_ok=True)
out={'graph_sha256':g['sha256'],'nodes':len(ctx.types),'channels':len(new),'all_original_channel_prices_equal':True,'full_event_replay_body_unchanged':True,'seconds':{'authenticated_context_load':load,'old_extra_xml_parse':old_s,'context_span_derivation':new_s},'scope':'One actual adder graph and unchanged replay body. Not a completed v5 event replay, MMC benchmark or complete workflow speedup. Context load and all existing validations still required.','sources':{str(p.relative_to(R)):sha(p) for p in [Path(__file__),R/'tools/immutable_channel_span_prices_v1.py',R/'tools/verify_resident_events_round_schedule_cache_v5.py',P]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
