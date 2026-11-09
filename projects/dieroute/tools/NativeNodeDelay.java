import com.xilinx.rapidwright.device.*;
import com.xilinx.rapidwright.rwroute.RouteNode;
import com.xilinx.rapidwright.rwroute.RouterHelper;
import com.xilinx.rapidwright.timing.delayestimator.DelayEstimatorBase;
import com.xilinx.rapidwright.timing.delayestimator.InterconnectInfo;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Read-only export of the installed SDK's nominal node-delay approximation.
 * No route search, tree change, corner calibration or missing-delay substitution.
 */
public final class NativeNodeDelay {
    static void require(boolean value,String message) {if(!value)throw new IllegalArgumentException(message);}
    static String field(Object value) {return Objects.toString(value,"").replace("\\","\\\\").replace("\t","\\t").replace("\n","\\n").replace("\r","\\r");}
    static void row(BufferedWriter out,Object... fields)throws IOException {
        StringJoiner line=new StringJoiner("\t");for(Object f:fields)line.add(field(f));out.write(line+"\n");
    }
    public static void main(String[] args)throws Exception {
        require(args.length==3,"device input-nodes.tsv new-output-directory");
        Path out=Path.of(args[2]);Files.createDirectory(out);
        Device device=Objects.requireNonNull(Device.getDevice(args[0]));
        DelayEstimatorBase<InterconnectInfo> estimator=new DelayEstimatorBase<>(device,new InterconnectInfo(),false,0);
        List<String> lines=Files.readAllLines(Path.of(args[1]));
        require(lines.get(0).equals("node\ttile\twire\tintent\tmembership"),"input schema");
        Set<Integer> seen=new HashSet<>();int unsupported=0;
        try(BufferedWriter w=Files.newBufferedWriter(out.resolve("node_delays.tsv"))) {
            row(w,"node","tile","wire","wire_name","intent","membership","exit_node","long_node","status","helper_delay_ps","extra_if_long_parent_ps","note");
            for(String line:lines.subList(1,lines.size())) {
                String[] f=line.split("\t",-1);require(f.length==5,"input width");
                int id=Integer.parseInt(f[0]),wire=Integer.parseInt(f[2]),intent=Integer.parseInt(f[3]),membership=Integer.parseInt(f[4]);
                require(seen.add(id),"duplicate node");Tile tile=Objects.requireNonNull(device.getTile(f[1]));
                Node node=Objects.requireNonNull(Node.getNode(tile,wire));
                require(node.getTile().equals(tile)&&node.getWireIndex()==wire&&node.getIntentCode().ordinal()==intent,"SDK node identity mismatch");
                boolean exit=RouteNode.isExitNode(node),isLong=DelayEstimatorBase.isLong(node);
                String status="resolved",note="";Integer delay=null,extra=null;
                try {
                    delay=(int)RouterHelper.computeNodeDelay(estimator,node);
                    extra=(int)DelayEstimatorBase.getExtraDelay(node,true);
                    require(delay>=0&&extra>=0,"negative nominal SDK delay");
                    if (!exit) {status="helper_zero_unmodeled";note="RouterHelper returns zero outside exit-node classes; not a physical zero-delay claim";}
                    else if (delay>10000) {status="uturn_penalty";note="SDK useUTurnNodes=false yields an exclusion-scale penalty";}
                } catch(RuntimeException e) {status="unsupported";note=e.getClass().getName()+": "+e.getMessage();unsupported++;delay=null;extra=null;}
                row(w,id,tile.getName(),wire,node.getWireName(),node.getIntentCode(),membership,exit,isLong,status,delay,extra,note);
            }
        }
        Files.writeString(out.resolve("completed.txt"),"nodes="+seen.size()+"\nunsupported="+unsupported+"\nroutes_changed=false\n");
        System.out.println("nodes="+seen.size()+" unsupported="+unsupported);
    }
}
