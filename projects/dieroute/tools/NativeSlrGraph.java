import com.xilinx.rapidwright.device.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Export a native electrical-node/PIP neighbourhood for functional validation.
 * This is a graph converter, not a router or a representative design workload.
 * Costs, delays and independent capacity are deliberately NOT inferred here.
 */
public final class NativeSlrGraph {
    private static final Comparator<Wire> ORDER = Comparator
        .comparingInt((Wire w) -> w.getTile().getUniqueAddress()).thenComparingInt(Wire::getWireIndex);
    private static Wire[] wires(Node n) {
        if (n == null || n.isInvalidNode()) throw new IllegalArgumentException("Invalid native electrical node");
        Wire[] ws = n.getAllWiresInNode();
        if (ws.length == 0) throw new IllegalArgumentException("Empty native electrical node");
        Arrays.sort(ws, ORDER);
        return ws;
    }
    private static String key(Node n) {
        Wire w = wires(n)[0]; return w.getTile().getName() + "/" + w.getWireName();
    }
    private static int die(Tile t) {
        if (t.getSLR() == null || t.getSLR().getId() < 0 || t.getSLR().getId() >= 8)
            throw new IllegalArgumentException("Unsupported SLR for " + t);
        return t.getSLR().getId();
    }
    private static String pipKey(PIP p) {
        return p.getTile().getName() + "/" + p.getStartWireName() + "/" + p.getEndWireName();
    }
    private static void row(BufferedWriter out, Object... values) throws IOException {
        for (int i=0; i<values.length; ++i) {
            if (i>0) out.write(',');
            out.write("\"" + values[i].toString().replace("\"", "\"\"") + "\"");
        }
        out.newLine();
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 4) throw new IllegalArgumentException("device tile/wire radius output-directory");
        int radius = Integer.parseInt(args[2]);
        if (radius < 1 || radius > 4) throw new IllegalArgumentException("radius must be 1..4");
        Path output = Path.of(args[3]); Files.createDirectory(output);
        Device dev = Objects.requireNonNull(Device.getDevice(args[0]));
        Node centre = Node.getNode(args[1], dev);
        TreeMap<String, Node> nodes = new TreeMap<>(); nodes.put(key(centre), centre);
        TreeMap<String, PIP> pips = new TreeMap<>();
        TreeSet<String> frontier = new TreeSet<>(nodes.keySet());
        HashSet<String> expanded = new HashSet<>();
        int skippedRouteThrus = 0;
        for (int level=0; level<radius; ++level) {
            TreeSet<String> next = new TreeSet<>();
            for (String name : frontier) {
                if (!expanded.add(name)) continue;
                Node node = nodes.get(name);
                List<PIP> adjacent = new ArrayList<>(node.getAllUphillPIPs());
                adjacent.addAll(node.getAllDownhillPIPs());
                for (PIP pip : adjacent) {
                    if (pip.isRouteThru()) { ++skippedRouteThrus; continue; }
                    if (pip.isEndWireNull()) throw new IllegalStateException("Null PIP endpoint");
                    if (pips.putIfAbsent(pipKey(pip), pip) != null) continue;
                    for (Node endpoint : new Node[]{pip.getStartNode(), pip.getEndNode()}) {
                        String k = key(endpoint);
                        nodes.putIfAbsent(k, endpoint); next.add(k);
                    }
                }
            }
            frontier = next;
        }
        HashMap<String,Integer> ids = new HashMap<>();
        try (BufferedWriter out = Files.newBufferedWriter(output.resolve("nodes.csv"), StandardCharsets.UTF_8);
             BufferedWriter members = Files.newBufferedWriter(output.resolve("wires.csv"), StandardCharsets.UTF_8)) {
            row(out,"id","tile","wire","owner_die","membership_mask","intent","xlow","ylow","xhigh","yhigh");
            row(members,"node_id","tile","wire","die");
            for (Map.Entry<String,Node> entry : nodes.entrySet()) {
                int id = ids.size(); ids.put(entry.getKey(), id);
                Wire[] ws = wires(entry.getValue()); int mask=0, xlo=Integer.MAX_VALUE, ylo=xlo, xhi=0, yhi=0;
                for (Wire w : ws) {
                    int d=die(w.getTile()), x=w.getTile().getColumn(), y=w.getTile().getRow();
                    mask |= 1 << d; xlo=Math.min(xlo,x);ylo=Math.min(ylo,y);xhi=Math.max(xhi,x);yhi=Math.max(yhi,y);
                    row(members,id,w.getTile().getName(),w.getWireName(),d);
                }
                Wire canonical=ws[0];
                row(out,id,canonical.getTile().getName(),canonical.getWireName(),die(canonical.getTile()),mask,
                    Node.getNode(canonical).getIntentCode().name(),xlo,ylo,xhi,yhi);
            }
        }
        try (BufferedWriter out = Files.newBufferedWriter(output.resolve("pips.csv"), StandardCharsets.UTF_8)) {
            row(out,"id","src","dst","tile","start_wire","end_wire","bidirectional","die");
            int id=0;
            for (PIP pip : pips.values())
                row(out,id++,ids.get(key(pip.getStartNode())),ids.get(key(pip.getEndNode())),pip.getTile().getName(),
                    pip.getStartWireName(),pip.getEndWireName(),pip.isBidirectional(),die(pip.getTile()));
        }
        System.out.println("scope=native_PIP_neighbourhood_not_a_design_workload radius="+radius);
        System.out.println("device="+dev.getName()+" centre_id="+ids.get(key(centre))+
            " nodes="+nodes.size()+" pips="+pips.size()+" skipped_route_thru_encounters="+skippedRouteThrus);
    }
}
