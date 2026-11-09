import com.xilinx.rapidwright.device.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** All native tile wires, electrical nodes and PIPs, including unused resources.
 * This is a topology converter. No routing eligibility, capacity or delay is
 * inferred, and route-through/clock/null-endpoint resources remain explicit.
 */
public final class NativeDeviceGraph {
    private static final int UNSEEN=-1, INVALID=-2;
    private static final class LE implements AutoCloseable {
        final OutputStream out; final byte[] buffer=new byte[1<<20]; int used;
        LE(Path p)throws IOException{out=Files.newOutputStream(p,StandardOpenOption.CREATE_NEW);}
        void word(int x)throws IOException {
            if(used+4>buffer.length)flush();
            buffer[used++]=(byte)x;buffer[used++]=(byte)(x>>>8);buffer[used++]=(byte)(x>>>16);buffer[used++]=(byte)(x>>>24);
        }
        void ints(int... a)throws IOException{for(int x:a)word(x);}
        void flush()throws IOException{out.write(buffer,0,used);used=0;}
        public void close()throws IOException{flush();out.close();}
    }
    private static void csv(BufferedWriter w,Object... values)throws IOException {
        for(int i=0;i<values.length;i++){if(i>0)w.write(',');w.write("\""+Objects.toString(values[i],"").replace("\"","\"\"")+"\"");}w.newLine();
    }
    private static BufferedWriter csvFile(Path out,String name)throws IOException {
        return Files.newBufferedWriter(out.resolve(name),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
    private static int die(Tile tile) {
        SLR s=tile.getSLR();if(s==null)return -1;
        int id=s.getId();if(id<0 || id>=8)throw new IllegalStateException("unsupported SLR");return id;
    }
    private static long key(Wire w){return ((long)w.getTile().getUniqueAddress()<<32)|(w.getWireIndex()&0xffffffffL);}
    private static int flags(PIP p){return (p.isReversed()?1:0)|(p.isBidirectional()?2:0)|(p.isPIPFixed()?4:0)|
        (p.isRouteThru()?8:0)|(p.isStub()?16:0)|(p.isStartStub()?32:0)|(p.isLogicalDriver()?64:0)|(p.isEndWireNull()?128:0);}
    private static int mapped(int[][] ids,Tile t,int wire) {
        if(wire<0)return -1;
        int id=ids[t.getUniqueAddress()][wire];
        if(id==UNSEEN)throw new IllegalStateException("PIP wire was not enumerated");return id==INVALID?-1:id;
    }
    private static final class Record {
        int tile,wire,nativeTile,nativeWire,mask,count,intent,flags,xlo=Integer.MAX_VALUE,ylo=Integer.MAX_VALUE,xhi,yhi;
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("device new-output-directory");
        Path out=Path.of(args[1]);Files.createDirectory(out);
        Device device=Objects.requireNonNull(Device.getDevice(args[0]));
        List<Tile> tiles=new ArrayList<>(device.getAllTiles());tiles.sort(Comparator.comparingInt(Tile::getUniqueAddress));
        int maximum=tiles.get(tiles.size()-1).getUniqueAddress();int[][] ids=new int[maximum+1][],baseIds=new int[maximum+1][];
        Tile[] byAddress=new Tile[maximum+1];List<Record> records=new ArrayList<>();
        long tileWires=0;int last=-1;
        for(Tile t:tiles){int a=t.getUniqueAddress();if(a<=last)throw new IllegalStateException("duplicate or negative tile address");last=a;
            byAddress[a]=t;ids[a]=new int[t.getWireCount()];baseIds[a]=new int[t.getWireCount()];
            Arrays.fill(ids[a],UNSEEN);Arrays.fill(baseIds[a],UNSEEN);tileWires+=t.getWireCount();}
        int nodeId=0;long memberWires=0,nullWires=0,emptyMemberNodes=0;TreeMap<Integer,Long> slrNodes=new TreeMap<>(),sllNodes=new TreeMap<>();
        try(LE wires=new LE(out.resolve("wires.bin"));LE invalid=new LE(out.resolve("null_wires.bin"))) {
            int tileIndex=0;
            for(Tile t:tiles) {
                int addr=t.getUniqueAddress();
                for(int wire=0;wire<t.getWireCount();wire++) {
                    Node n=Node.getNode(t,wire);
                    if(n==null || n.isInvalidNode()){ids[addr][wire]=INVALID;invalid.ints(addr,wire);nullWires++;continue;}
                    int ba=n.getTile().getUniqueAddress(),bw=n.getWireIndex(),slr=die(t),id=baseIds[ba][bw];
                    if(slr<0)throw new IllegalStateException("node member lacks native SLR: "+t+"/"+t.getWireName(wire));
                    if(id==UNSEEN) {
                        Node base=Node.getNode(n.getTile(),bw);
                        if(base==null || !base.equals(n))throw new IllegalStateException("native representative is not idempotent");
                        Record r=new Record();r.tile=addr;r.wire=wire;r.nativeTile=ba;r.nativeWire=bw;
                        r.intent=n.getIntentCode().ordinal();r.flags=(n.isTiedToGnd()?1:0)|(n.isTiedToVcc()?2:0);
                        id=nodeId;nodeId=Math.addExact(nodeId,1);baseIds[ba][bw]=id;records.add(r);
                    }
                    Record r=records.get(id);ids[addr][wire]=id;r.mask|=1<<slr;r.count=Math.addExact(r.count,1);
                    r.xlo=Math.min(r.xlo,t.getColumn());r.xhi=Math.max(r.xhi,t.getColumn());r.ylo=Math.min(r.ylo,t.getRow());r.yhi=Math.max(r.yhi,t.getRow());
                    wires.ints(id,addr,wire);memberWires++;
                }
                if(tileIndex++%10000==0)System.out.println("node_phase_tiles="+tileIndex+" nodes="+nodeId+" member_wires="+memberWires);
            }
        }
        if(memberWires+nullWires!=tileWires)throw new IllegalStateException("incomplete wire enumeration");
        try(LE nodes=new LE(out.resolve("nodes.bin"));BufferedWriter empty=csvFile(out,"empty_native_members.csv")) {
            csv(empty,"node_id","native_tile","native_wire","intent","enumerated_member_count");
            for(int id=0;id<records.size();id++) {
                Record r=records.get(id);Node n=Node.getNode(byAddress[r.nativeTile],r.nativeWire);Wire[] reported=n.getAllWiresInNode();
                if(mapped(ids,n.getTile(),n.getWireIndex())!=id)throw new IllegalStateException("native representative absent");
                if(reported.length==0) {
                    r.flags|=4;emptyMemberNodes++;
                    csv(empty,id,n.getTile().getName(),n.getWireName(),n.getIntentCode(),r.count);
                } else {
                    if(reported.length!=r.count)throw new IllegalStateException("native member count disagrees with exhaustive wire-to-node enumeration: "+n+" api="+reported.length+" enumerated="+r.count);
                    Arrays.sort(reported,Comparator.comparingLong(NativeDeviceGraph::key));long previous=-1;
                    for(Wire w:reported){long k=key(w);if(k<=previous || mapped(ids,w.getTile(),w.getWireIndex())!=id)
                        throw new IllegalStateException("native member list disagrees with exhaustive identities: "+n);previous=k;}
                }
                nodes.ints(id,r.tile,r.wire,r.nativeTile,r.nativeWire,r.mask,r.count,r.intent,r.flags,r.xlo,r.ylo,r.xhi,r.yhi,0,0,0);
                slrNodes.merge(r.mask,1L,Long::sum);
                if(Integer.bitCount(r.mask)>1 && n.getIntentCode()==IntentCode.NODE_LAGUNA_DATA)sllNodes.merge(r.mask,1L,Long::sum);
                if(id%5000000==0)System.out.println("member_crosscheck_nodes="+id+" empty_native_lists="+emptyMemberNodes);
            }
        }
        int pipId=0;long nullPips=0,bidirectional=0,routethrus=0;TreeMap<Integer,Long> pipFlags=new TreeMap<>();
        try(LE pipsOut=new LE(out.resolve("pips.bin"));BufferedWriter metadata=csvFile(out,"tiles.csv")) {
            csv(metadata,"address","name","type","slr","column","row","wire_count","pip_begin","pip_count");int tileIndex=0;
            for(Tile t:tiles) {
                List<PIP> pips=t.getPIPs();pips.sort(Comparator.comparingInt(PIP::getStartWireIndex).thenComparingInt(PIP::getEndWireIndex).thenComparingInt(NativeDeviceGraph::flags));
                int begin=pipId;
                for(PIP p:pips) {
                    int a=mapped(ids,t,p.getStartWireIndex()),b=mapped(ids,t,p.getEndWireIndex()),f=flags(p),slr=die(t);
                    if(slr<0)throw new IllegalStateException("PIP lacks SLR");
                    Node na=p.getStartNode(),nb=p.getEndNode();
                    if(a>=0 && (na==null || mapped(ids,na.getTile(),na.getWireIndex())!=a))throw new IllegalStateException("PIP start resolution mismatch");
                    if(b>=0 && (nb==null || mapped(ids,nb.getTile(),nb.getWireIndex())!=b))throw new IllegalStateException("PIP end resolution mismatch");
                    if(a<0 || b<0)nullPips++;if((f&2)!=0)bidirectional++;if((f&8)!=0)routethrus++;
                    pipsOut.ints(pipId,a,b,t.getUniqueAddress(),p.getStartWireIndex(),p.getEndWireIndex(),slr,f);pipId=Math.addExact(pipId,1);
                    pipFlags.merge(f,1L,Long::sum);
                }
                csv(metadata,t.getUniqueAddress(),t.getName(),t.getTileTypeEnum().name(),die(t),t.getColumn(),t.getRow(),t.getWireCount(),begin,pips.size());
                if(tileIndex++%10000==0)System.out.println("pip_phase_tiles="+tileIndex+" pips="+pipId);
            }
        }
        try(BufferedWriter w=csvFile(out,"intents.csv")){csv(w,"id","name");for(IntentCode i:IntentCode.values())csv(w,i.ordinal(),i.name());}
        try(BufferedWriter w=csvFile(out,"node_memberships.csv")){csv(w,"mask","nodes","cross_slr_laguna_nodes");for(Map.Entry<Integer,Long> e:slrNodes.entrySet())csv(w,e.getKey(),e.getValue(),sllNodes.getOrDefault(e.getKey(),0L));}
        try(BufferedWriter w=csvFile(out,"pip_flags.csv")){csv(w,"flags","pips");for(Map.Entry<Integer,Long> e:pipFlags.entrySet())csv(w,e.getKey(),e.getValue());}
        String json="{\n  \"schema\": \"dieroute.native_device_graph.v2\",\n  \"device\": \""+device.getName()+"\",\n  \"tiles\": "+tiles.size()+
            ",\n  \"tile_wires\": "+tileWires+",\n  \"nodes\": "+nodeId+",\n  \"member_wires\": "+memberWires+",\n  \"null_wires\": "+nullWires+
            ",\n  \"empty_native_member_nodes\": "+emptyMemberNodes+",\n  \"pips\": "+pipId+",\n  \"pips_with_missing_node\": "+nullPips+",\n  \"bidirectional_pips\": "+bidirectional+
            ",\n  \"routethru_pips\": "+routethrus+",\n  \"scope\": \"all native tile wires, electrical nodes and PIPs; no design availability, capacity, delay or router eligibility inference\"\n}\n";
        Files.writeString(out.resolve("summary.json"),json);System.out.print(json);
    }
}
