"""Review every actual node's lossless potential storage and static capacity arithmetic."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_potential8_lossless_storage_20261015'
def main():
 refs={}
 def sha(f):
  key=str(f)
  if key not in refs:
   h=hashlib.sha256()
   with Path(f).open('rb') as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 x=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='full_native_lossless8_codec_terminal_requires_review' and len(m['steps'])==4 and all(v['returncode']==0 for v in m['steps'])
 for f,h in x['source_sha256'].items():assert sha(f)==h,f
 b=json.loads((P/'build.log').read_text());v=json.loads((P/'verify.log').read_text());assert b['status']=='lossless8_full_native_potential_built' and v['status']=='all_native_potentials_byte_decode_match_original64'
 assert b['nodes']==v['checked']==91975782 and b['maximum']==v['maximum']==42 and b['source_value']==v['source_value']==42 and b['sink_value']==v['sink_value']==0
 prior=R/'work/native_policy_identity_hop_bound_20261015/independent_audit.json';old=json.loads(prior.read_text())
 assert b['BFS_expanded']==v['BFS_expanded']==old['preparation_BFS_expanded'] and b['BFS_edges']==v['BFS_edges']==old['preparation_BFS_edges']
 f=P/'potential8.raw';assert sha(f)==m['packed_sha256'];data=f.read_bytes();assert len(data)==b['packed_bytes']==91975784 and all(z==0 for z in data[b['nodes']:])
 counts=collections.Counter(data[:b['nodes']]);assert [counts.get(i,0) for i in range(256)]==b['histogram'] and sum(counts.values())==b['nodes']
 cap=R/'work/native_higher_g_hw_emu_link_20261015/capacity.json';region=json.loads(cap.read_text())['regions']['graph'];parts=region['parts'];assert parts['potential']==b['unpacked_bytes']==735806256
 align=lambda value:(value+4095)//4096*4096
 assert sum(align(z) for z in parts.values())==region['aligned_bytes']
 proposed=dict(parts);proposed['potential']=len(data);new_bytes=sum(align(z) for z in proposed.values())
 host=R/'work/native_identity_XRT_commit_stage_diagnostic_20261015/source/tb/host.cpp';assert 'std::min<U>((*quotient)(n),nodes)' in host.read_text()
 for f in [P/'protocol.json',P/'manifest.json',P/'build.log',P/'verify.log',P/'build',P/'verify',prior,cap,host,Path(__file__).resolve()]:sha(f)
 report=dict(status='all91975782_native_potentials_losslessly_packed8_and_direct_byte_verified',nodes=b['nodes'],maximum=42,source_value=42,sink_value=0,unpacked_bytes=b['unpacked_bytes'],packed_bytes=len(data),logical_payload_bytes_saved=b['unpacked_bytes']-len(data),unchanged_BFS_expanded=b['BFS_expanded'],unchanged_BFS_edges=b['BFS_edges'],static_graph_capacity=dict(original_page_aligned_bytes=region['aligned_bytes'],proposed_page_aligned_bytes=new_bytes,capacity_bytes=region['capacity_bytes'],original_page_aligned_headroom=region['headroom_bytes'],proposed_page_aligned_headroom=region['capacity_bytes']-new_bytes),value_histogram=dict(sorted(counts.items())),source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Actual fixed full native task, unchanged original source-bounded quotient preparation and all node values. Range<=255 required, no new clipping. Builder word/shift output independently decoded by direct bytes for every node. Page-aligned capacity is a static proposal under existing4KiB convention, not allocator/HBM delivery proof. Preprocessing remains31Mnodes/108Medges, not eliminated. No changed kernel, ABI, XRT run, transaction count, speed or board result.')
 with (P/'independent_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','value_histogram']}))
if __name__=='__main__':main()
