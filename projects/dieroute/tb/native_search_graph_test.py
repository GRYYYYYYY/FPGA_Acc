"""Byte-level oracle for full-graph fixed pin access and Laguna PINFEED rules."""
import argparse,csv,json,shutil,struct,subprocess,tempfile
from pathlib import Path
from native_csr_test import FINGERPRINT,crc,table

def container(path,kind,width,payload):
    path.write_bytes(struct.pack('<8sHHIQQ16sQQ',b'FPGAACCP',0,1,kind,len(payload)//width,len(payload),bytes.fromhex(FINGERPRINT),crc(payload),1)+payload)

def main():
    p=argparse.ArgumentParser();p.add_argument('--builder',type=Path,required=True);p.add_argument('--verifier',type=Path);p.add_argument('--output',type=Path);args=p.parse_args()
    if args.output is None:scratch=tempfile.TemporaryDirectory();args.output=Path(scratch.name)/'cases'
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False);base=out/'input';base.mkdir()
    for n in ('graph','mapping','footprint','csr','policy','access'):(base/n).mkdir()
    tile_kinds=[0,0,1,1,0,1,1,2,2,1,0,1,0,1,0]
    with (base/'graph/tiles.csv').open('w',newline='') as f:
        w=csv.writer(f,quoting=csv.QUOTE_ALL);w.writerow(['address','name','type','slr','column','row','wire_count','pip_begin','pip_count'])
        for i,t in enumerate(('BRAM','INT','LAG_LAG')):w.writerow([i,'T'+str(i),t,0,i,0,20,0,0])
    (base/'graph/intents.csv').write_text('"id","name"\n"0","NODE_LOCAL"\n"6","NODE_PINFEED"\n"19","NODE_LAGUNA_DATA"\n')
    table(base/'graph/nodes.bin',[[i,t,i,t,i,3 if i==8 else 1,1,6 if i in (3,5,6,13) else 19 if i==8 else 0,0,0,0,0,0,0,0,0] for i,t in enumerate(tile_kinds)])
    pairs=[(0,1),(1,2),(2,3),(3,4),(12,13),(13,14),(2,10),(2,5),(2,6),(6,7),(7,8),(8,9),(2,11),(3,13),(0,2),(1,2),(9,13),(0,4)]
    table(base/'mapping/footprint_node_map.bin',[[i] for i in range(15)])
    table(base/'mapping/footprint_pip_map.bin',[[i] for i in range(6)])
    table(base/'footprint/nets.bin',[[0]*16,[0]*16])
    table(base/'footprint/pins.bin',[[0,0,0,1],[0,4,0,0],[1,12,0,1],[1,14,0,0]])
    (base/'sdk').mkdir();table(base/'sdk/inputs.bin',[[1,6]]);table(base/'sdk/ubump_nodes.bin',[[2,8]])
    table(base/'footprint/pips.bin',[[int(i>=4),a,b,0,a,b,0,2 if i==1 else 0] for i,(a,b) in enumerate(pairs[:6])])
    raw=[(a,b,2*i) for i,(a,b) in enumerate(pairs)]+[(2,1,3)]
    raw.sort();offsets=[0];arcs=[]
    for node in range(15):arcs.extend((b,k) for a,b,k in raw if a==node);offsets.append(len(arcs))
    container(base/'csr/offsets.bin',0x44520001,8,struct.pack('<16Q',*offsets))
    container(base/'csr/arcs.bin',0x44520002,8,b''.join(struct.pack('<2I',*r) for r in arcs))
    owner=[0xffffffff]*15
    for i,n in ((0,0),(4,0),(12,1),(14,1)):owner[i]=n
    container(base/'policy/node_protection.bin',0x44520004,1,bytes([int(i==11) for i in range(15)]))
    container(base/'policy/terminal_net.bin',0x44520005,4,struct.pack('<15I',*owner))
    container(base/'policy/pip_protection.bin',0x44520006,1,bytes(len(pairs)))
    container(base/'access/core_nodes.bin',0x44520007,1,bytes(int(t!=0) for t in tile_kinds))
    private=[0xffffffff]*15
    for i,n in ((0,0),(1,0),(4,0),(12,1),(14,1)):private[i]=n
    container(base/'access/private_owner.bin',0x44520008,4,struct.pack('<15I',*private))
    access=[(int(i>=4),2*i,*pairs[i]) for i in (0,1,3,4,5)]
    def access_file(d,rows):container(d/'access/access_arcs.bin',0x44520009,16,b''.join(struct.pack('<4I',*r) for r in rows))
    access_file(base,access);(base/'access/nonterminal_components.csv').write_text('net_id,component,nodes,input_pins,output_pins,core_entry_edges,core_exit_edges\n')
    def owner_collision(d):
        x=owner.copy();x[3]=1;container(d/'policy/terminal_net.bin',0x44520005,4,struct.pack('<15I',*x))
    def wrong_core(d):
        x=bytearray(int(t!=0) for t in tile_kinds);x[10]=1;container(d/'access/core_nodes.bin',0x44520007,1,x)
    def single_slr(d):
        path=d/'graph/nodes.bin';b=bytearray(path.read_bytes());struct.pack_into('<I',b,8*64+5*4,1);path.write_bytes(b)
    cases=[('base',lambda d:None,None),('single_slr_ubump',single_slr,None),('extra_reverse_access',lambda d:access_file(d,access+[(0,3,2,1)]),'access inventory differs'),
        ('missing_access',lambda d:access_file(d,access[:-1]),'access inventory differs'),
        ('wrong_core_class',wrong_core,'core class disagrees'),('projected_owner_collision',owner_collision,'projected sink is owned'),
        ('nonterminal_transit',lambda d:(d/'access/nonterminal_components.csv').write_text('header\n0,0,1,0,0,1,1\n'),'nonterminal noncore component')]
    records=[]
    for name,mutate,error in cases:
        d=out/name;shutil.copytree(base,d);mutate(d);target=d/'search'
        cmd=[str(args.builder.resolve()),*[str(d/n) for n in ('graph','mapping','footprint','csr','policy','access')],FINGERPRINT,str(target)]
        r=subprocess.run(cmd,capture_output=True,text=True);(d/'run.log').write_text(r.stdout+r.stderr)
        assert r.returncode==(1 if error else 0),(name,r.stderr)
        if error:assert error in r.stderr,(name,r.stderr)
        else:
            allowed={0,2,4,6,8,10,16,18,20,22,32};chosen=[(a,b,k) for a,b,k in raw if k in allowed];expected_offsets=[0];expected_arcs=[]
            for node in range(15):expected_arcs.extend((b,k) for a,b,k in chosen if a==node);expected_offsets.append(len(expected_arcs))
            masks=bytes(64 if i==5 else 32 if i==10 else 1 if i==11 else 0 for i in range(15))
            exclusive=private.copy();exclusive[3]=0;exclusive[13]=1
            expected={'offsets.bin':struct.pack('<16Q',*expected_offsets),'arcs.bin':b''.join(struct.pack('<2I',*r) for r in expected_arcs),
                      'node_protection.bin':masks,'exclusive_net.bin':struct.pack('<15I',*exclusive),'laguna_input.bin':bytes(int(i==6) for i in range(15))}
            for filename,payload in expected.items():
                b=(target/filename).read_bytes();assert b[64:]==payload,filename;assert struct.unpack_from('<Q',b,48)[0]==crc(payload)
            a=json.loads((target/'audit.json').read_text());assert a['original_candidate_pips_preserved'] and a['search_arcs']==11 and a['fixed_access_arcs']==5
            assert a['foreign_terminal_owner_arcs_removed']==1 and a['new_projected_sink_nodes']==2 and a['laguna_pinfeed_nodes']==1
            if args.verifier:
                verify=[str(args.verifier.resolve()),*[str(d/n) for n in ('graph','mapping','footprint','csr','policy','access','search')],str(d/'sdk/inputs.bin'),FINGERPRINT,str(d/'audit')]
                v=subprocess.run(verify,capture_output=True,text=True);(d/'verify.log').write_text(v.stdout+v.stderr);assert v.returncode==0,(name,v.stderr)
        records.append({'case':name,'returncode':r.returncode,'passed':True})
    if args.verifier:
        mutations=[('missing_laguna','laguna_input.bin',6,b'\0','Laguna input differs'),('relaxed_pinfeed','node_protection.bin',5,b'\0','qualified node mask'),
                   ('stolen_private','exclusive_net.bin',0,struct.pack('<I',1),'exclusive owner differs'),('wrong_pip','arcs.bin',4,struct.pack('<I',28),'missing/extra/reordered'),
                   ('unprotected_background','node_protection.bin',11,b'\0','qualified node mask')]
        d=out/'base'
        for name,file,offset,value,error in mutations:
            target=out/name;shutil.copytree(d/'search',target)
            b=bytearray((target/file).read_bytes());b[64+offset:64+offset+len(value)]=value;struct.pack_into('<Q',b,48,crc(b[64:]));(target/file).write_bytes(b)
            cmd=[str(args.verifier.resolve()),*[str(d/n) for n in ('graph','mapping','footprint','csr','policy','access')],str(target),str(d/'sdk/inputs.bin'),FINGERPRINT,str(out/(name+'_audit'))]
            r=subprocess.run(cmd,capture_output=True,text=True);(out/(name+'.log')).write_text(r.stdout+r.stderr)
            assert r.returncode==1 and error in r.stderr,(name,r.stderr);records.append({'case':name,'returncode':r.returncode,'passed':True})
    (out/'tests.json').write_text(json.dumps({'passed':True,'cases':records},indent=2)+'\n');print(json.dumps({'passed':True,'cases':len(records)}))

if __name__=='__main__':main()
