import com.xilinx.rapidwright.device.*;
import java.nio.file.*;
import java.util.*;

/** Read TSV paths and resolve every selected PIP again in the native device DB. */
public final class VerifyNativePipPaths {
    private static String canonical(Node node) {
        if (node == null || node.isInvalidNode()) throw new IllegalArgumentException("Invalid native node");
        Wire[] ws=node.getAllWiresInNode();
        Arrays.sort(ws, Comparator.comparingInt((Wire w)->w.getTile().getUniqueAddress())
            .thenComparingInt(Wire::getWireIndex));
        if(ws.length==0)throw new IllegalArgumentException("Empty native node");
        return ws[0].getTile().getName()+"/"+ws[0].getWireName();
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("device paths.tsv");
        Device dev=Objects.requireNonNull(Device.getDevice(args[0]));
        HashMap<String,String> previous=new HashMap<>();
        HashMap<String,Integer> lengths=new HashMap<>(), dies=new HashMap<>();
        int edges=0, transitions=0;
        for(String line:Files.readAllLines(Path.of(args[1]))) {
            if(line.isEmpty())throw new IllegalArgumentException("Empty TSV row");
            String[] c=line.split("\t",-1);
            if(c.length!=8)throw new IllegalArgumentException("Expected path,index,src,dst,tile,start,end,reversed");
            int index=Integer.parseInt(c[1]);
            if(index!=lengths.getOrDefault(c[0],0))throw new IllegalArgumentException("Non-contiguous path");
            if(index>0 && !previous.get(c[0]).equals(c[2]))throw new IllegalArgumentException("Disconnected path");
            Tile tile=Objects.requireNonNull(dev.getTile(c[4]));
            PIP pip=null;
            for(PIP p:tile.getPIPs())if(p.getStartWireName().equals(c[5]) && p.getEndWireName().equals(c[6])) {
                if(pip!=null)throw new IllegalArgumentException("Ambiguous PIP identity");
                pip=p;
            }
            if(pip==null || pip.isRouteThru())throw new IllegalArgumentException("Unsupported/missing native PIP");
            if(!c[7].equals("false") && !c[7].equals("true"))throw new IllegalArgumentException("Bad PIP direction");
            boolean reverse=c[7].equals("true");
            if(reverse && !pip.isBidirectional())throw new IllegalArgumentException("Illegal PIP reversal");
            String src=canonical(reverse?pip.getEndNode():pip.getStartNode());
            String dst=canonical(reverse?pip.getStartNode():pip.getEndNode());
            if(!src.equals(c[2]) || !dst.equals(c[3]))throw new IllegalArgumentException("Native PIP endpoint mismatch");
            int die=tile.getSLR().getId();
            if(index>0 && dies.get(c[0])!=die)++transitions;
            dies.put(c[0],die);previous.put(c[0],dst);lengths.put(c[0],index+1);++edges;
        }
        if(edges==0)throw new IllegalArgumentException("No paths verified");
        System.out.println("native_paths="+lengths.size()+" native_pips="+edges+" pip_access_slr_transitions="+transitions);
        System.out.println("scope=electrical_connectivity_only_not_DCP_design_legality_or_timing");
    }
}
