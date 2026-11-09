"""Map generated candidate HMSS slave interfaces to actual BD path hierarchies."""
import hashlib,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'work/native_commit_const_zero_variant_20261015'
paths=[p/'link_temp/link/vivado/vpl/prj/prj.srcs/my_rm/bd/ulp/ulp.bd',p/'link_temp/link/vivado/vpl/prj/prj.gen/my_rm/bd/ulp/ip/ulp_hmss_0_0/bd_0/bd_85ad.bd']
out=root/'work/const_zero_candidate_hmss_path_profile_20261015';out.mkdir(exist_ok=False)
objects=[];sources={}
for label,path in zip(['top','hmss'],paths):
 raw=path.read_bytes();assert hashlib.sha256(path.read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest()
 snapshot=out/(label+'.bd');snapshot.write_bytes(raw);objects.append(json.loads(raw)['design']);sources[str(path)]=hashlib.sha256(raw).hexdigest();sources[str(snapshot)]=hashlib.sha256(raw).hexdigest()
top,hmss=objects;rows=[]
for name,net in top['interface_nets'].items():
 ports=net['interface_ports'];slaves=[s for s in ports if re.fullmatch(r'hmss_0/S\d+_AXI',s)]
 if not slaves:continue
 slave,=slaves;peer,=[s for s in ports if s!=slave];local=slave.split('/')[1]
 internal=[v['interface_ports'] for v in hmss['interface_nets'].values() if local in v['interface_ports']]
 assert len(internal)==1
 path_pin,=[v for v in internal[0] if v!=local];assert re.fullmatch(r'path_\d+/S\d+_AXI',path_pin)
 rows.append(dict(top_net=name,master=peer,hmss_slave=local,path=path_pin.split('/')[0],path_slave_pin=path_pin))
assert len(rows)==15 and len({r['master'] for r in rows})==15
host,=[r for r in rows if r['hmss_slave']=='S00_AXI'];assert host['master']=='axi_vip_data/M_AXI' and host['path']=='path_17'
assert sum(r['master'].split('/')[0] in ['net_commit','search_worker','snapshot_search'] for r in rows)==14
host_input=[dict(net=k,ports=v['interface_ports']) for k,v in top['interface_nets'].items() if 'axi_vip_data/S_AXI' in v['interface_ports']];assert len(host_input)==1
sources[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(out/'audit.json').write_text(json.dumps(dict(status='generated_candidate_fifteen_hmss_slave_paths_resolved',rows=sorted(rows,key=lambda r:r['hmss_slave']),host_input=host_input,source_sha256=sources,scope='Current const-zero candidate generated BD snapshot only,14kernelmasters plushostVIP. Path numbers are generated hierarchy identifiers,not HBM pseudochannels. Previous archived DCP correspondence is unproven; does not attribute its failing paths, prove candidate routed timing or physical traffic.',board_result=False,research_complete=False),indent=2)+'\n')
print(json.dumps(dict(rows=len(rows),host=host,host_input=host_input)))
