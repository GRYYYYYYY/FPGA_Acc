import com.xilinx.rapidwright.device.Device;
import com.xilinx.rapidwright.device.Node;
import com.xilinx.rapidwright.device.Tile;
import com.xilinx.rapidwright.device.Wire;
import java.io.BufferedWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.*;

/** Native topology diagnostic only: nodes touching LAG_LAG tiles, not a full RR export.
 * Canonical wire ordering matches PersistRoute RapidWrightBridge.baseWire.
 * A multi-SLR electrical node is one resource; memberships are NOT capacities.
 */
public final class SlrNodeProbe {
    private static final Comparator<Wire> WIRE_ORDER = Comparator
        .comparingInt((Wire w) -> w.getTile().getUniqueAddress())
        .thenComparingInt(Wire::getWireIndex);

    private static int slr(Wire w) {
        if (w.getTile().getSLR() == null)
            throw new IllegalStateException("Missing native SLR: " + w);
        return w.getTile().getSLR().getId();
    }

    private static String csv(String s) {
        return "\"" + s.replace("\"", "\"\"") + "\"";
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException("device output-directory");
        Path out = Path.of(args[1]);
        Files.createDirectory(out); // Never overwrite a prior census.
        Device device = Objects.requireNonNull(Device.getDevice(args[0]));
        List<Tile> tiles = new ArrayList<>();
        for (Tile t : device.getAllTiles())
            if (t.getTileTypeEnum().name().equals("LAG_LAG")) tiles.add(t);
        tiles.sort(Comparator.comparingInt(Tile::getUniqueAddress));
        if (tiles.isEmpty()) throw new IllegalStateException("No LAG_LAG tiles; unsupported scope");
        Set<Long> seen = new HashSet<>();
        Map<String, Long> crossingsByIntent = new TreeMap<>();
        Map<String, Long> crossingsBySlrs = new TreeMap<>();
        long invalid = 0, multiSlr = 0, wireCount = 0;
        try (BufferedWriter nodes = Files.newBufferedWriter(out.resolve("nodes.csv"),
                 StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
             BufferedWriter wires = Files.newBufferedWriter(out.resolve("wires.csv"),
                 StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW)) {
            nodes.write("canonical_tile,canonical_wire,intent,representative_slr,member_slrs,wire_count\n");
            wires.write("canonical_tile,canonical_wire,member_tile,member_wire,member_slr\n");
            for (Tile tile : tiles) for (int i = 0; i < tile.getWireCount(); ++i) {
                Node node = Node.getNode(tile, i);
                if (node == null || node.isInvalidNode()) { ++invalid; continue; }
                Wire[] members = node.getAllWiresInNode();
                if (members.length == 0) throw new IllegalStateException("Empty native node");
                Arrays.sort(members, WIRE_ORDER);
                Wire canonical = members[0];
                long key = ((long) canonical.getTile().getUniqueAddress() << 32)
                    | (canonical.getWireIndex() & 0xffffffffL);
                if (!seen.add(key)) continue;
                TreeSet<Integer> slrs = new TreeSet<>();
                String identity = csv(canonical.getTile().getName()) + "," + csv(canonical.getWireName());
                for (Wire w : members) {
                    int memberSlr = slr(w);
                    slrs.add(memberSlr);
                    wires.write(identity + "," + csv(w.getTile().getName()) + ","
                        + csv(w.getWireName()) + "," + memberSlr + "\n");
                    ++wireCount;
                }
                String memberships = String.join(";", slrs.stream().map(String::valueOf).toArray(String[]::new));
                // Use canonical node intent, independent of which LAG_LAG wire found it first.
                Node canonicalNode = Objects.requireNonNull(Node.getNode(canonical));
                String intent = canonicalNode.getIntentCode().name();
                nodes.write(identity + "," + csv(intent) + "," + slr(canonical) + ","
                    + csv(memberships) + "," + members.length + "\n");
                if (slrs.size() > 1) {
                    ++multiSlr;
                    crossingsByIntent.merge(intent, 1L, Long::sum);
                    crossingsBySlrs.merge(memberships, 1L, Long::sum);
                }
            }
        }
        System.out.println("scope=unique_electrical_nodes_touching_native_LAG_LAG_tiles");
        System.out.println("device=" + device.getName() + " slr_count=" + device.getSLRs().length);
        System.out.println("laguna_tiles=" + tiles.size() + " unique_nodes=" + seen.size()
            + " member_wires=" + wireCount + " invalid_wire_slots=" + invalid);
        System.out.println("multi_slr_nodes=" + multiSlr);
        System.out.println("crossings_by_intent=" + crossingsByIntent);
        System.out.println("crossings_by_membership=" + crossingsBySlrs);
    }
}
