"""Independent byte-format inspection and intentionally damaged table rejection."""
import json,hashlib,struct,tempfile,math,xml.etree.ElementTree as ET
from pathlib import Path
from bound_allnet_map_query_v2 import Query
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'allnet_map_binary_contract_v1_2026-10-20';P=E/'wbuart_allnet_map_preflight_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);manifest=json.loads((P/'manifest.json').read_text());case=manifest['cases'][1];ep=case['endpoint'];timing=E/'wbuart_frame_timings_v1_2026-10-20/w096/episode_01/initial_connection_criticalities.json';original=(P/'on/allmap.bin').read_bytes();marker=original.index(b'DATA\n')+5;header=original[:marker].decode().splitlines();payload=original[marker:];digest=hashlib.sha256(payload).hexdigest();h=header[0].split();n,nt,np=map(int,h[4:]);pinlines=[x.split() for x in header if x.startswith('P ')];targets=[int(x.split()[1]) for x in header if x.startswith('T ')];assert len(pinlines)==np==2493 and len(targets)==nt==339 and len(payload)==nt*n*8;assert targets==sorted(set(targets));assert len({(int(w[1]),int(w[2])) for w in pinlines})==np;nonfinite=0
 for a,b in struct.iter_unpack('<ff',payload):
  assert math.isfinite(a) and math.isfinite(b) and min(a,b)>=0
 q=Query(P/'on/allmap.bin',ep,timing,digest);kw=dict(graph_sha256=q.graph_sha256,endpoint_sha256=q.endpoint_sha256);source,target=q.connections[0];channel=next(i for i,k in enumerate(q.kinds) if k=='CHANX');other_source=next(i for i,k in enumerate(q.kinds) if k=='SOURCE' and i!=source);other_opin=next(i for i,k in enumerate(q.kinds) if k=='OPIN' and i not in q.exits[source]);rejections=[]
 def reject(name,fn):
  try:fn()
  except (ValueError,KeyError,UnicodeError):rejections.append(name)
  else:raise AssertionError('invalid admitted '+name)
 for name,node,cid,c,up in [('other_source',other_source,0,'00000000','00000000'),('other_opin',other_opin,0,'00000000','00000000'),('negative_node',-1,0,'00000000','00000000'),('bool_node',True,0,'00000000','00000000'),('unknown_CID',source,999999,'00000000','00000000'),('NaN_c',source,0,'7fc00000','00000000'),('negative_c',source,0,'bf800000','00000000'),('c_above1',source,0,'40000000','00000000'),('nonzero_Rup',source,0,'00000000','3f800000')]:reject(name,lambda node=node,cid=cid,c=c,up=up:q.query(node,cid,c,upstream_bits=up,**kw))
 for field in kw:reject('stale_'+field,lambda field=field:q.query(source,0,'00000000',**dict(kw,**{field:'0'*64})))
 with tempfile.TemporaryDirectory(prefix='routecast_allmap_contract_') as tmp:
  p=Path(tmp)/'damaged.bin'
  variants={'truncated':original[:-1],'trailing':original+b'X','wrong_version':original.replace(b'ALLMAP 1 ',b'ALLMAP 2 ',1),'stale_header':original.replace(q.endpoint_sha256.encode(),b'0'*64,1),'duplicate_target':('\n'.join([('T '+str(targets[0])) if x=='T '+str(targets[1]) else x for x in header])+'\n').encode()+payload,'duplicate_pin':('\n'.join([header[1] if x==header[2] else x for x in header])+'\n').encode()+payload}
  for name,data in variants.items():p.write_bytes(data);reject(name,lambda:Query(p,ep,timing,digest))
  reject('payload_SHA',lambda:Query(P/'on/allmap.bin',ep,timing,'0'*64))
  pos=(q.targets[target]*n+channel)*8
  for name,bits in [('NaN_entry',0x7fc00000),('negative_entry',0xbf800000)]:
   data=bytearray(payload);struct.pack_into('<I',data,pos,bits);newdigest=hashlib.sha256(data).hexdigest();p.write_bytes(original[:marker]+data);bad=Query(p,ep,timing,newdigest);reject(name,lambda:bad.query(channel,0,'00000000',**kw));bad.close()
 q.close();reject('closed_query',lambda:q.query(source,0,'00000000',**kw));files=[Path(__file__),R/'tools/bound_allnet_map_query_v2.py',P/'on/allmap.bin',Path(ep),timing];(D/'verification.json').write_text(json.dumps({'status':'INDEPENDENT_FORMAT_ALL7884462_FINITE_PAIRS_AND21_REJECTIONS_PASS','pairs':nt*n,'rejections':rejections,'bindings':{str(p):sha(p) for p in files},'scope':'First actual native matrix format and parser rejection contract; source/all9 captures and allNET search still pending.'},indent=2)+'\n');print('BINARY_CONTRACT_PASS',nt*n,len(rejections))
if __name__=='__main__':main()
