import com.xilinx.rapidwright.device.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Export explicitly selected native PIPs for identity tests, not design routing. */
public final class NativePipSubset {
    private static Wire[] wires(Node n) {
        if(n==null || n.isInvalidNode())throw new IllegalArgumentException("Invalid native endpoint");
        Wire[] result=n.getAllWiresInNode();
        Arrays.sort(result,Comparator.comparingInt((Wire w)->w.getTile().getUniqueAddress()).thenComparingInt(Wire::getWireIndex));
        if(result.length==0)throw new IllegalArgumentException("Empty native members unsupported in this diagnostic");
        return result;
    }
    private static String key(Node n){Wire w=wires(n)[0];return w.getTile().getName()+"/"+w.getWireName();}
    private static void row(BufferedWriter out,Object... cells)throws IOException {
        for(int i=0;i<cells.length;++i){if(i>0)out.write(',');out.write("\""+cells[i].toString().replace("\"","\"\"")+"\"");}out.newLine();
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=3)throw new IllegalArgumentException("device selected-pips.tsv output-directory (TSV: tile,start_index,end_index)");
        Device dev=Objects.requireNonNull(Device.getDevice(args[0]));
        TreeMap<String,PIP> pips=new TreeMap<>();TreeMap<String,Node> nodes=new TreeMap<>();
        for(String line:Files.readAllLines(Path.of(args[1]))){
            String[] c=line.split("\t",-1);if(c.length!=3)throw new IllegalArgumentException("Expected tile,start_index,end_index");
            Tile tile=Objects.requireNonNull(dev.getTile(c[0]));int start=Integer.parseInt(c[1]),end=Integer.parseInt(c[2]);PIP selected=null;
            for(PIP p:tile.getPIPs())if(p.getStartWireIndex()==start&&p.getEndWireIndex()==end){
                if(selected!=null)throw new IllegalArgumentException("Ambiguous native PIP");selected=p;}
            if(selected==null||selected.isRouteThru()||selected.isEndWireNull())throw new IllegalArgumentException("Missing/unsupported native PIP");
            String id=tile.getName()+"/"+selected.getStartWireName()+"/"+selected.getEndWireName();
            if(pips.putIfAbsent(id,selected)!=null)throw new IllegalArgumentException("Duplicate native PIP");
            for(Node n:new Node[]{selected.getStartNode(),selected.getEndNode()})nodes.putIfAbsent(key(n),n);
        }
        if(pips.isEmpty())throw new IllegalArgumentException("Empty PIP subset");
        Path out=Path.of(args[2]);Files.createDirectory(out);Map<String,Integer> ids=new HashMap<>();
        try(BufferedWriter ns=Files.newBufferedWriter(out.resolve("nodes.csv"));BufferedWriter ws=Files.newBufferedWriter(out.resolve("wires.csv"))){
            row(ns,"id","tile","wire","owner_die","membership_mask","intent","xlow","ylow","xhigh","yhigh");row(ws,"node_id","tile","wire","die");
            for(Map.Entry<String,Node> entry:nodes.entrySet()){
                int id=ids.size(),mask=0,xmin=Integer.MAX_VALUE,ymin=xmin,xmax=0,ymax=0;ids.put(entry.getKey(),id);Wire[] members=wires(entry.getValue());
                for(Wire w:members){Tile t=w.getTile();int die=t.getSLR().getId();if(die<0||die>=8)throw new IllegalArgumentException("Invalid die");
                    mask|=1<<die;xmin=Math.min(xmin,t.getColumn());xmax=Math.max(xmax,t.getColumn());ymin=Math.min(ymin,t.getRow());ymax=Math.max(ymax,t.getRow());row(ws,id,t.getName(),w.getWireName(),die);}
                Wire first=members[0];row(ns,id,first.getTile().getName(),first.getWireName(),first.getTile().getSLR().getId(),mask,entry.getValue().getIntentCode(),xmin,ymin,xmax,ymax);
            }
        }
        try(BufferedWriter ps=Files.newBufferedWriter(out.resolve("pips.csv"))){
            row(ps,"id","src","dst","tile","start_wire","end_wire","bidirectional","die");int id=0;
            for(PIP p:pips.values())row(ps,id++,ids.get(key(p.getStartNode())),ids.get(key(p.getEndNode())),p.getTile().getName(),p.getStartWireName(),p.getEndWireName(),p.isBidirectional(),p.getTile().getSLR().getId());
        }
        System.out.println("nodes="+nodes.size()+" pips="+pips.size()+" scope=selected_native_PIP_identity_only_not_design_legality_or_timing");
    }
}
