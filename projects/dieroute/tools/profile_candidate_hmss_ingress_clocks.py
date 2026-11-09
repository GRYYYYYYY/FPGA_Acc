"""Resolve candidate HMSS ingress and clock nets from archived BD wiring."""
import hashlib,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'work/const_zero_candidate_hmss_path_profile_20261015'
base=json.loads((p/'audit.json').read_text());top=json.loads((p/'top.bd').read_text())['design'];inner=json.loads((p/'hmss.bd').read_text())['design']
def peer(nets,pin,field):
 matches=[(name,v[field]) for name,v in nets.items() if pin in v[field]]
 assert len(matches)==1,(pin,matches)
 name,ports=matches[0];other,=[x for x in ports if x!=pin]
 return name,other
rows=[]
for row in base['rows']:
 path=row['path'];net,vip_pin=peer(inner['interface_nets'],path+'/M_AXI','interface_ports')
 assert vip_pin.endswith('/S_AXI')
 vip=vip_pin.rsplit('/',1)[0];net2,ingress=peer(inner['interface_nets'],vip+'/M_AXI','interface_ports')
 assert re.fullmatch(r'hbm_inst/SAXI_\d+',ingress)
 clock_nets={}
 clocks=[name for name,port in inner['components'][path]['ports'].items() if port.get('type')=='clk']
 assert len(clocks)==2 and 'hbm_aclk' in clocks
 for pin in [path+'/'+clock for clock in clocks]:
  matches=[name for name,n in inner['nets'].items() if pin in n['ports']];assert len(matches)==1
  clock_nets[pin]=matches[0]
 rows.append(dict(master=row['master'],hmss_slave=row['hmss_slave'],path=path,via_vip=vip,hbm_controller_ingress=ingress,clock_nets=clock_nets))
host,=[r for r in rows if r['master']=='axi_vip_data/M_AXI'];assert host['hbm_controller_ingress']=='hbm_inst/SAXI_17'
host_top=[dict(name=k,ports=v['ports']) for k,v in top['nets'].items() if 'axi_vip_data/aclk' in v['ports']];assert len(host_top)==1 and 'ii_level0_wire/ulp_m_aclk_pcie_00' in host_top[0]['ports']
files=[p/'audit.json',p/'top.bd',p/'hmss.bd',Path(__file__).resolve()]
result=dict(status='candidate_hmss_controller_ingress_and_clock_nets_resolved',rows=rows,host_top_clock_net=host_top[0],source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},scope='Exact archived candidate BD wiring. Host path17 bridges PCIe-side clock to hbm_aclk and enters controller SAXI17. Controller ingress numbering does not identify address-selected HBM memory pseudochannel. No actual frequencies inferred; no mapping attribution to older DCP or routed timing/signoff claim.',board_result=False,research_complete=False)
(p/'ingress_clock_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(host))
