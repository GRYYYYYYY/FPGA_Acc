import com.xilinx.rapidwright.design.*;
import com.xilinx.rapidwright.device.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Complete used-resource footprint, not a graph of available routing choices.
 * Binary tables are LE u32 records; 0xffffffff denotes an absent node/pin.
 * Retain all owners. Never interpret an SDK representative SLR as membership.
 */
public final class DcpRouteFootprint {
    private static final IntentCode[] INTENTS=IntentCode.values();
    private static final int STATIC=1,CLOCK=2,CLOCK_RESOURCE=4,NO_SOURCE=8,MULTI_SOURCE=16,
        FIXED=32,ROUTETHRU=64,STUB=128,MISSING_NODE=256,NO_SINK=512,DIRECT=1024;
    private static final class LE implements AutoCloseable {
        final DataOutputStream out;
        LE(Path p)throws IOException{out=new DataOutputStream(new BufferedOutputStream(Files.newOutputStream(p,StandardOpenOption.CREATE_NEW),1<<20));}
        void ints(int... data)throws IOException{for(int n:data)out.writeInt(Integer.reverseBytes(n));}
        public void close()throws IOException{out.close();}
    }
    private static void csv(BufferedWriter w,Object... values)throws IOException {
        for(int i=0;i<values.length;i++){if(i>0)w.write(',');w.write("\""+Objects.toString(values[i],"").replace("\"","\"\"")+"\"");}w.newLine();
    }
    private static BufferedWriter csvFile(Path out,String name)throws IOException {
        return Files.newBufferedWriter(out.resolve(name),StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
    }
    private static int die(Tile t){
        SLR slr=t.getSLR();if(slr==null || slr.getId()<0 || slr.getId()>7)throw new IllegalStateException("unsupported SLR: "+t);
        return slr.getId();
    }
    private static long wireKey(Wire w){
        int tile=w.getTile().getUniqueAddress(),wire=w.getWireIndex();
        if(tile<0 || wire<0)throw new IllegalStateException("negative native wire identity");
        return ((long)tile<<32)|(wire & 0xffffffffL);
    }
    private static final class Resource {
        int id,tile,wire,nativeTile,nativeWire,mask,wireCount,firstNet=-1,owners,background,candidate,flags,intent;
    }
    private final Map<Node,Resource> cache=new HashMap<>();
    private final Map<Long,Resource> canonical=new HashMap<>();
    private final List<Resource> resources=new ArrayList<>();
    private final TreeMap<Integer,Tile> tiles=new TreeMap<>();
    private final LE wires;
    private long wireRecords;
    private DcpRouteFootprint(LE wires){this.wires=wires;}
    private int resource(Node n)throws IOException {
        if(n==null || n.isInvalidNode())return -1;
        Resource r=cache.get(n);if(r!=null)return r.id;
        Wire[] members=n.getAllWiresInNode();
        if(members.length==0)throw new IllegalStateException("empty electrical node");
        Arrays.sort(members,Comparator.comparingLong(DcpRouteFootprint::wireKey));
        long key=wireKey(members[0]);int mask=0;
        for(Wire w:members)mask|=1<<die(w.getTile());
        r=canonical.get(key);
        if(r!=null){
            if(r.mask!=mask || r.wireCount!=members.length)throw new IllegalStateException("canonical membership disagreement");
            cache.put(n,r);return r.id;
        }
        r=new Resource();r.id=resources.size();r.tile=members[0].getTile().getUniqueAddress();r.wire=members[0].getWireIndex();
        r.nativeTile=n.getTile().getUniqueAddress();r.nativeWire=n.getWireIndex();r.mask=mask;r.wireCount=members.length;
        r.flags=(n.isTiedToGnd()?1:0)|(n.isTiedToVcc()?2:0);r.intent=n.getIntentCode().ordinal();
        long previous=-1;
        for(Wire w:members){
            long current=wireKey(w);if(current<=previous)throw new IllegalStateException("duplicate native member wire");previous=current;
            Node resolved=Node.getNode(w);
            if(resolved==null || !resolved.equals(n))throw new IllegalStateException("native member does not resolve to the same electrical node");
            tiles.putIfAbsent(w.getTile().getUniqueAddress(),w.getTile());wires.ints(r.id,w.getTile().getUniqueAddress(),w.getWireIndex());wireRecords++;
        }
        resources.add(r);canonical.put(key,r);cache.put(n,r);return r.id;
    }
    private static int flags(PIP p){return (p.isReversed()?1:0)|(p.isBidirectional()?2:0)|(p.isPIPFixed()?4:0)|
        (p.isRouteThru()?8:0)|(p.isStub()?16:0)|(p.isStartStub()?32:0)|(p.isLogicalDriver()?64:0)|(p.isEndWireNull()?128:0);}
    private void export(Design design,Path out)throws Exception {
        List<Net> nets=new ArrayList<>(design.getNets());nets.sort(Comparator.comparing(Net::getName));
        int pinId=0,pipId=0,taskId=0,ownerId=0,candidateNets=0;long unknownNodes=0;
        TreeMap<Integer,Integer> reasons=new TreeMap<>();
        try(LE owners=new LE(out.resolve("owners.bin"));LE pipsOut=new LE(out.resolve("pips.bin"));
            LE pinsOut=new LE(out.resolve("pins.bin"));LE tasks=new LE(out.resolve("tasks.bin"));LE netsOut=new LE(out.resolve("nets.bin"));
            BufferedWriter netNames=csvFile(out,"nets.csv");BufferedWriter pinNames=csvFile(out,"pins.csv")) {
            csv(netNames,"id","name","reason_mask","candidate","source_node","outputs","inputs","pin_count","pip_count","owned_nodes","tasks");
            csv(pinNames,"id","net_id","node_id","site_inst","site","pin","output","access_slr");
            for(int netId=0;netId<nets.size();netId++) {
                Net net=nets.get(netId);int reason=(net.isStaticNet()?STATIC:0)|(net.isClockNet()?CLOCK:0)|(net.needsClockNetworkResources()?CLOCK_RESOURCE:0);
                List<SitePinInst> pins=new ArrayList<>(net.getPins());pins.sort(Comparator.comparing(SitePinInst::getSiteInstName).thenComparing(SitePinInst::getName));
                List<PIP> pips=new ArrayList<>(net.getPIPs());pips.sort(Comparator.comparing((PIP p)->p.getTile().getName())
                    .thenComparingInt(PIP::getStartWireIndex).thenComparingInt(PIP::getEndWireIndex).thenComparingInt(DcpRouteFootprint::flags));
                int pinBegin=pinId,pipBegin=pipId,taskBegin=taskId,ownerBegin=ownerId,outputs=0,inputs=0;
                int source=-1,sourcePin=-1,sourceDie=-1;
                SitePinInst src=net.getSource();TreeSet<Integer> owned=new TreeSet<>();List<int[]> sinks=new ArrayList<>();
                for(SitePinInst pin:pins) {
                    int node=resource(pin.getConnectedNode()),slr=pin.getTile()==null?-1:die(pin.getTile());
                    if(node<0 || slr<0){reason|=MISSING_NODE;unknownNodes++;}else owned.add(node);
                    if(pin.isOutPin())outputs++;else {inputs++;sinks.add(new int[]{node,slr,pinId});}
                    if(pin==src){source=node;sourcePin=pinId;sourceDie=slr;}
                    if(pin.getTile()!=null)tiles.putIfAbsent(pin.getTile().getUniqueAddress(),pin.getTile());
                    pinsOut.ints(netId,node,slr,pin.isOutPin()?1:0);
                    csv(pinNames,pinId,netId,node,pin.getSiteInstName(),pin.getSite()==null?"":pin.getSite().getName(),pin.getName(),pin.isOutPin(),slr);
                    pinId=Math.addExact(pinId,1);
                }
                if(source<0)reason|=NO_SOURCE;if(outputs!=1)reason|=MULTI_SOURCE;if(inputs==0)reason|=NO_SINK;
                for(int[] sink:sinks)if(source>=0 && sink[0]==source)reason|=DIRECT;
                for(PIP pip:pips) {
                    int a=resource(pip.getStartNode()),b=resource(pip.getEndNode());
                    if(a<0 || b<0){reason|=MISSING_NODE;unknownNodes++;}
                    if(a>=0)owned.add(a);if(b>=0)owned.add(b);
                    int f=flags(pip);if((f&4)!=0)reason|=FIXED;if((f&8)!=0)reason|=ROUTETHRU;if((f&48)!=0)reason|=STUB;
                    int tile=pip.getTile().getUniqueAddress();tiles.putIfAbsent(tile,pip.getTile());
                    pipsOut.ints(netId,a,b,tile,pip.getStartWireIndex(),pip.getEndWireIndex(),die(pip.getTile()),f);pipId=Math.addExact(pipId,1);
                }
                boolean candidate=reason==0;if(candidate){candidateNets++;for(int[] sink:sinks){tasks.ints(taskId,netId,source,sink[0],sourceDie,sink[1],sourcePin,sink[2]);taskId=Math.addExact(taskId,1);}}
                for(int id:owned){Resource r=resources.get(id);if(r.firstNet<0)r.firstNet=netId;r.owners=Math.addExact(r.owners,1);
                    if(candidate)r.candidate++;else r.background++;owners.ints(id,netId);ownerId=Math.addExact(ownerId,1);}
                netsOut.ints(reason,source,sourcePin,pinBegin,pins.size(),pipBegin,pips.size(),taskBegin,taskId-taskBegin,ownerBegin,owned.size(),outputs,inputs,0,0,0);
                csv(netNames,netId,net.getName(),reason,candidate,source,outputs,inputs,pins.size(),pips.size(),owned.size(),taskId-taskBegin);
                reasons.merge(reason,1,Integer::sum);
                if(netId%100000==0)System.out.println("nets_processed="+netId+" nodes="+resources.size()+" pips="+pipId);
            }
        }
        List<PartitionPin> partitionPins=new ArrayList<>(design.getPartitionPins());
        partitionPins.sort(Comparator.comparing(PartitionPin::toString));
        try(BufferedWriter w=csvFile(out,"partition_pins.csv")) {
            csv(w,"node_id","instance","terminal","tile","wire","fixed","wire_fixed","is_port");
            for(PartitionPin pin:partitionPins){int id=resource(pin.getNode());if(id>=0)resources.get(id).flags|=4;
                csv(w,id,pin.getInstanceName(),pin.getTerminalName(),pin.getTileName(),pin.getWireName(),pin.isFixed(),pin.isWireFixed(),pin.isPort());}
        }
        int multiOwner=0,sll=0,sharedCandidateBackground=0;
        try(LE nodes=new LE(out.resolve("nodes.bin"))) {
            for(Resource r:resources){nodes.ints(r.id,r.tile,r.wire,r.nativeTile,r.nativeWire,r.mask,r.wireCount,r.firstNet,r.owners,r.background,r.candidate,r.flags,r.intent,0,0,0);
                if(r.owners>1)multiOwner++;if(r.background>0 && r.candidate>0)sharedCandidateBackground++;
                if(r.owners>0 && Integer.bitCount(r.mask)>1 && INTENTS[r.intent]==IntentCode.NODE_LAGUNA_DATA)sll++;}
        }
        try(BufferedWriter w=csvFile(out,"tiles.csv")){csv(w,"address","name","slr","column","row","wire_count");
            for(Tile t:tiles.values())csv(w,t.getUniqueAddress(),t.getName(),die(t),t.getColumn(),t.getRow(),t.getWireCount());}
        try(BufferedWriter w=csvFile(out,"intents.csv")){csv(w,"id","name");for(IntentCode i:IntentCode.values())csv(w,i.ordinal(),i.name());}
        try(BufferedWriter w=csvFile(out,"reason_counts.csv")){csv(w,"reason_mask","nets");for(Map.Entry<Integer,Integer> e:reasons.entrySet())csv(w,e.getKey(),e.getValue());}
        String summary="{\n  \"schema\": \"dieroute.dcp_route_footprint.v1\",\n  \"nets\": "+nets.size()+",\n  \"nodes\": "+resources.size()+
            ",\n  \"pins\": "+pinId+",\n  \"pips\": "+pipId+",\n  \"owners\": "+ownerId+",\n  \"member_wires\": "+wireRecords+
            ",\n  \"candidate_nets\": "+candidateNets+",\n  \"candidate_tasks\": "+taskId+",\n  \"partition_pins\": "+partitionPins.size()+
            ",\n  \"multi_owner_nodes\": "+multiOwner+",\n  \"shared_candidate_background_nodes\": "+sharedCandidateBackground+
            ",\n  \"owned_cross_slr_laguna_nodes\": "+sll+",\n  \"missing_node_encounters\": "+unknownNodes+
            ",\n  \"scope\": \"complete used-resource footprint; candidate task selection is provisional, no unused adjacency, capacities, delays or rerouting\"\n}\n";
        Files.writeString(out.resolve("summary.json"),summary);System.out.print(summary);
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=3)throw new IllegalArgumentException("input.dcp readable.edf new-output-directory");
        Path out=Path.of(args[2]);Files.createDirectory(out);Design design=Design.readCheckpoint(args[0],args[1]);
        try(LE wires=new LE(out.resolve("wires.bin"))){new DcpRouteFootprint(wires).export(design,out);}
    }
}
