package edu.fpgaacc.persistroute;

import com.xilinx.rapidwright.design.Design;
import com.xilinx.rapidwright.design.Net;
import com.xilinx.rapidwright.design.SitePinInst;
import com.xilinx.rapidwright.device.Device;
import com.xilinx.rapidwright.device.Node;
import com.xilinx.rapidwright.device.PIP;
import com.xilinx.rapidwright.device.Tile;
import com.xilinx.rapidwright.device.Wire;
import com.xilinx.rapidwright.edif.EDIFNetlist;
import com.xilinx.rapidwright.interchange.LogNetlistReader;
import com.xilinx.rapidwright.interchange.PhysNetlistReader;
import com.xilinx.rapidwright.interchange.PhysNetlistWriter;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.security.MessageDigest;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Stream;

/** DCP/FPGA-Interchange bridge for PersistRoute.
 *
 * Route CSV schema: net,tile,start_wire,end_wire,reversed.  All listed nets
 * are replaced atomically after validation; nets not listed are preserved.
 */
public final class RapidWrightBridge {
    private static final String SCHEMA = "PERSISTROUTE_RAPIDWRIGHT_V1";

    private static final class RouteRow {
        final String net;
        final String tile;
        final String start;
        final String end;
        final boolean reversed;
        RouteRow(String net, String tile, String start, String end, boolean reversed) {
            this.net = net; this.tile = tile; this.start = start; this.end = end; this.reversed = reversed;
        }
    }

    private static final class TileBounds {
        final int minX;
        final int maxX;
        final int minY;
        final int maxY;

        TileBounds(int minX, int maxX, int minY, int maxY) {
            if (minX > maxX || minY > maxY) throw new IllegalArgumentException("invalid tile bounds");
            this.minX = minX;
            this.maxX = maxX;
            this.minY = minY;
            this.maxY = maxY;
        }

        boolean contains(Tile tile) {
            if (tile == null) return false;
            String name = tile.getName();
            int xMarker = name.lastIndexOf("_X");
            int yMarker = name.lastIndexOf('Y');
            if (xMarker < 0 || yMarker <= xMarker + 2 || yMarker == name.length() - 1) return false;
            try {
                int x = Integer.parseInt(name.substring(xMarker + 2, yMarker));
                int y = Integer.parseInt(name.substring(yMarker + 1));
                return x >= minX && x <= maxX && y >= minY && y <= maxY;
            } catch (NumberFormatException ignored) {
                return false;
            }
        }

        String json() {
            return "{\"min_x\":" + minX + ",\"max_x\":" + maxX +
                    ",\"min_y\":" + minY + ",\"max_y\":" + maxY + "}";
        }
    }

    private RapidWrightBridge() {}

    private static Design readDesign(Path input) {
        String lower = input.toString().toLowerCase();
        if (lower.endsWith(".dcp")) return Design.readCheckpoint(input);
        if (lower.endsWith(".phys") || lower.endsWith(".netlist")) {
            Path logical = lower.endsWith(".netlist") ? input : findLogicalNetlist(input);
            Path physical = lower.endsWith(".phys") ? input : replaceExtension(input, ".phys");
            if (!Files.isRegularFile(logical)) {
                throw new IllegalArgumentException("missing companion logical netlist: " + logical);
            }
            try {
                EDIFNetlist netlist = LogNetlistReader.readLogNetlist(logical.toString());
                return Files.isRegularFile(physical)
                        ? PhysNetlistReader.readPhysNetlist(physical.toString(), netlist)
                        : new Design(netlist);
            } catch (IOException error) {
                throw new IllegalArgumentException("cannot read FPGA Interchange design: " + input, error);
            }
        }
        throw new IllegalArgumentException("input must be .dcp, .phys, or .netlist: " + input);
    }

    private static Path findLogicalNetlist(Path physical) {
        Path exact = replaceExtension(physical, ".netlist");
        if (Files.isRegularFile(exact)) return exact;
        Path parent = physical.toAbsolutePath().getParent();
        String physicalName = physical.getFileName().toString();
        String physicalStem = physicalName.substring(0, physicalName.length() - ".phys".length());
        List<Path> matches = new ArrayList<>();
        try (Stream<Path> entries = Files.list(parent)) {
            entries.filter(Files::isRegularFile)
                    .filter(path -> path.getFileName().toString().endsWith(".netlist"))
                    .filter(path -> {
                        String name = path.getFileName().toString();
                        String stem = name.substring(0, name.length() - ".netlist".length());
                        return physicalStem.startsWith(stem + "_");
                    })
                    .forEach(matches::add);
        } catch (IOException error) {
            throw new IllegalArgumentException("cannot search for companion logical netlist: " + physical, error);
        }
        matches.sort(Comparator.comparingInt((Path path) -> path.getFileName().toString().length()).reversed());
        if (matches.isEmpty()) return exact;
        if (matches.size() > 1 && matches.get(0).getFileName().toString().length() ==
                matches.get(1).getFileName().toString().length()) {
            throw new IllegalArgumentException("ambiguous companion logical netlist for " + physical + ": " + matches);
        }
        return matches.get(0);
    }

    private static Path replaceExtension(Path path, String extension) {
        String name = path.getFileName().toString();
        int dot = name.lastIndexOf('.');
        String replaced = (dot < 0 ? name : name.substring(0, dot)) + extension;
        Path parent = path.getParent();
        return parent == null ? Paths.get(replaced) : parent.resolve(replaced);
    }

    private static String key(Node node) {
        Wire wire = baseWire(node);
        if (wire == null) return "";
        return wire.getTile().getName() + "/" + wire.getWireName();
    }

    private static Wire baseWire(Node node) {
        if (node == null || node.isInvalidNode()) return null;
        Wire[] wires = node.getAllWiresInNode();
        if (wires.length == 0) return null;
        Wire base = wires[0];
        for (int i = 1; i < wires.length; ++i) {
            Wire candidate = wires[i];
            int addressCompare = Integer.compare(candidate.getTile().getUniqueAddress(),
                    base.getTile().getUniqueAddress());
            if (addressCompare < 0 || (addressCompare == 0 &&
                    candidate.getWireIndex() < base.getWireIndex())) base = candidate;
        }
        return base;
    }

    private static Long nodeKey(Node node) {
        Wire base = baseWire(node);
        if (base == null) return null;
        return ((long) base.getTile().getUniqueAddress() << 32) |
                (base.getWireIndex() & 0xffffffffL);
    }

    private static int intern(Node node, Map<Long, Integer> nodeIds, List<Wire> nodes, TileBounds bounds) {
        Wire base = baseWire(node);
        if (base == null || (bounds != null && !bounds.contains(base.getTile()))) return -1;
        long nodeKey = ((long) base.getTile().getUniqueAddress() << 32) |
                (base.getWireIndex() & 0xffffffffL);
        Integer existing = nodeIds.get(nodeKey);
        if (existing != null) return existing;
        int id = nodes.size();
        nodeIds.put(nodeKey, id);
        nodes.add(base);
        return id;
    }

    private static Integer nodeId(Node node, Map<Long, Integer> nodeIds) {
        Long nodeKey = nodeKey(node);
        return nodeKey == null ? null : nodeIds.get(nodeKey);
    }

    private static boolean isSupportedPip(Tile tile, PIP pip) {
        String tileName = tile.getName();
        return !(pip.isRouteThru() && (tileName.startsWith("CLE") || tileName.startsWith("RCLK")));
    }

    private static long edgeKey(int src, int dst) {
        return ((long) src << 32) | (dst & 0xffffffffL);
    }

    private static List<Tile> sortedTiles(Device device) {
        List<Tile> tiles = new ArrayList<>(device.getAllTiles());
        tiles.sort(Comparator.comparing(Tile::getName));
        return tiles;
    }

    private static List<PIP> sortedPips(Tile tile) {
        List<PIP> pips = new ArrayList<>(tile.getPIPs());
        pips.sort(Comparator.comparing(PIP::getStartWireName)
                .thenComparing(PIP::getEndWireName));
        return pips;
    }

    private static void writeCsv(BufferedWriter out, String... values) throws IOException {
        for (int i = 0; i < values.length; ++i) {
            if (i != 0) out.write(',');
            String value = values[i] == null ? "" : values[i];
            boolean quote = value.indexOf(',') >= 0 || value.indexOf('"') >= 0 ||
                    value.indexOf('\n') >= 0 || value.indexOf('\r') >= 0;
            if (quote) out.write('"');
            out.write(quote ? value.replace("\"", "\"\"") : value);
            if (quote) out.write('"');
        }
        out.newLine();
    }

    private static String sha256(Path path) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (java.io.InputStream stream = Files.newInputStream(path)) {
            byte[] block = new byte[1 << 20];
            int count;
            while ((count = stream.read(block)) >= 0) digest.update(block, 0, count);
        }
        StringBuilder result = new StringBuilder();
        for (byte value : digest.digest()) result.append(String.format("%02x", value));
        return result.toString();
    }

    private static void exportDesign(Path input, Path output, TileBounds bounds) throws Exception {
        Files.createDirectories(output);
        Design design = readDesign(input);
        Device device = design.getDevice();
        List<Tile> tiles = sortedTiles(device);
        if (bounds != null) tiles.removeIf(tile -> !bounds.contains(tile));
        Map<Long, Integer> nodeIds = new HashMap<>();
        List<Wire> nodes = new ArrayList<>();

        // Canonicalize every electrical node independently of the queried wire.
        // RapidWright 2022.2 places that queried wire first in the returned array.
        for (Tile tile : tiles) {
            for (PIP pip : sortedPips(tile)) {
                if (!isSupportedPip(tile, pip)) continue;
                intern(pip.getStartNode(), nodeIds, nodes, bounds);
                intern(pip.getEndNode(), nodeIds, nodes, bounds);
            }
        }
        List<Net> nets = new ArrayList<>(design.getNets());
        nets.sort(Comparator.comparing(Net::getName));
        for (Net net : nets) {
            for (SitePinInst pin : net.getPins()) intern(pin.getConnectedNode(), nodeIds, nodes, bounds);
        }

        Path nodesCsv = output.resolve("nodes.csv");
        try (BufferedWriter out = Files.newBufferedWriter(nodesCsv, StandardCharsets.UTF_8)) {
            writeCsv(out, "id", "tile", "wire", "row", "column", "slr");
            for (int id = 0; id < nodes.size(); ++id) {
                Wire node = nodes.get(id);
                Tile tile = node.getTile();
                writeCsv(out, Integer.toString(id), tile.getName(), node.getWireName(),
                        Integer.toString(tile.getRow()), Integer.toString(tile.getColumn()),
                        tile.getSLR() == null ? "" : tile.getSLR().toString());
            }
        }

        long edgeCount = 0;
        long skippedPips = 0;
        long duplicatePips = 0;
        Set<Long> directedEdges = new HashSet<>();
        Path pipsCsv = output.resolve("pips.csv");
        try (BufferedWriter out = Files.newBufferedWriter(pipsCsv, StandardCharsets.UTF_8)) {
            writeCsv(out, "edge_id", "src", "dst", "tile", "start_wire", "end_wire", "bidirectional");
            for (Tile tile : tiles) {
                for (PIP pip : sortedPips(tile)) {
                    if (!isSupportedPip(tile, pip)) {
                        ++skippedPips;
                        continue;
                    }
                    Integer src = nodeId(pip.getStartNode(), nodeIds);
                    Integer dst = nodeId(pip.getEndNode(), nodeIds);
                    if (src == null || dst == null) {
                        ++skippedPips;
                        continue;
                    }
                    if (!directedEdges.add(edgeKey(src, dst))) {
                        ++duplicatePips;
                        continue;
                    }
                    if (pip.isBidirectional()) directedEdges.add(edgeKey(dst, src));
                    writeCsv(out, Long.toString(edgeCount++), Integer.toString(src), Integer.toString(dst),
                            tile.getName(), pip.getStartWireName(), pip.getEndWireName(),
                            Boolean.toString(pip.isBidirectional()));
                }
            }
        }

        long connectionCount = 0;
        long skippedConnections = 0;
        Path connectionsCsv = output.resolve("connections.csv");
        try (BufferedWriter out = Files.newBufferedWriter(connectionsCsv, StandardCharsets.UTF_8)) {
            writeCsv(out, "id", "net_id", "net", "source", "sink", "criticality_q", "max_hops", "priority", "epoch",
                    "source_pin", "sink_pin");
            int stableNetId = 0;
            for (Net net : nets) {
                SitePinInst source = net.getSource();
                if (source == null || source.getConnectedNode() == null) {
                    skippedConnections += net.getSinkPins().size();
                    continue;
                }
                Integer sourceId = nodeId(source.getConnectedNode(), nodeIds);
                List<SitePinInst> sinks = new ArrayList<>(net.getSinkPins());
                sinks.sort(Comparator.comparing(SitePinInst::getSitePinName));
                for (SitePinInst sink : sinks) {
                    Integer sinkId = nodeId(sink.getConnectedNode(), nodeIds);
                    if (sourceId == null || sinkId == null) {
                        ++skippedConnections;
                        continue;
                    }
                    writeCsv(out, Long.toString(connectionCount), Integer.toString(stableNetId), net.getName(),
                            Integer.toString(sourceId), Integer.toString(sinkId),
                            "0", "256", Long.toString(connectionCount), "0",
                            source.getSitePinName(), sink.getSitePinName());
                    ++connectionCount;
                }
                ++stableNetId;
            }
        }

        Path existingCsv = output.resolve("existing_routes.csv");
        long routedPips = 0;
        try (BufferedWriter out = Files.newBufferedWriter(existingCsv, StandardCharsets.UTF_8)) {
            writeCsv(out, "net", "tile", "start_wire", "end_wire", "reversed");
            for (Net net : nets) {
                List<PIP> route = new ArrayList<>(net.getPIPs());
                route.sort(Comparator.comparing(PIP::toString));
                for (PIP pip : route) {
                    writeCsv(out, net.getName(), pip.getTile().getName(), pip.getStartWireName(),
                            pip.getEndWireName(), Boolean.toString(pip.isReversed()));
                    ++routedPips;
                }
            }
        }

        Path manifest = output.resolve("manifest.json");
        String json = "{\n" +
                "  \"schema\": \"" + SCHEMA + "\",\n" +
                "  \"input\": \"" + input.toAbsolutePath().toString().replace("\\", "\\\\") + "\",\n" +
                "  \"input_sha256\": \"" + sha256(input) + "\",\n" +
                "  \"device\": \"" + device.getName() + "\",\n" +
                "  \"tile_bounds\": " + (bounds == null ? "null" : bounds.json()) + ",\n" +
                "  \"tiles\": " + tiles.size() + ",\n" +
                "  \"nodes\": " + nodes.size() + ",\n" +
                "  \"edges\": " + edgeCount + ",\n" +
                "  \"directed_edges\": " + directedEdges.size() + ",\n" +
                "  \"skipped_pips\": " + skippedPips + ",\n" +
                "  \"duplicate_pips\": " + duplicatePips + ",\n" +
                "  \"connections\": " + connectionCount + ",\n" +
                "  \"skipped_connections\": " + skippedConnections + ",\n" +
                "  \"existing_route_pips\": " + routedPips + "\n" +
                "}\n";
        Files.write(manifest, json.getBytes(StandardCharsets.UTF_8));
        System.out.println(json);
    }

    private static void inspectDesign(Path input) throws Exception {
        Design design = readDesign(input);
        String json = "{\n" +
                "  \"schema\": \"" + SCHEMA + "\",\n" +
                "  \"input\": \"" + input.toAbsolutePath().toString().replace("\\", "\\\\") + "\",\n" +
                "  \"input_sha256\": \"" + sha256(input) + "\",\n" +
                "  \"device\": \"" + design.getDevice().getName() + "\",\n" +
                "  \"nets\": " + design.getNets().size() + ",\n" +
                "  \"cells\": " + design.getCells().size() + ",\n" +
                "  \"site_instances\": " + design.getSiteInsts().size() + "\n" +
                "}\n";
        System.out.println(json);
    }

    private static List<String> parseCsvLine(String line) {
        List<String> fields = new ArrayList<>();
        StringBuilder field = new StringBuilder();
        boolean quoted = false;
        for (int i = 0; i < line.length(); ++i) {
            char c = line.charAt(i);
            if (c == '"') {
                if (quoted && i + 1 < line.length() && line.charAt(i + 1) == '"') {
                    field.append('"'); ++i;
                } else quoted = !quoted;
            } else if (c == ',' && !quoted) {
                fields.add(field.toString()); field.setLength(0);
            } else field.append(c);
        }
        if (quoted) throw new IllegalArgumentException("unterminated CSV quote");
        fields.add(field.toString());
        return fields;
    }

    private static List<RouteRow> readRoutes(Path path) throws IOException {
        List<RouteRow> rows = new ArrayList<>();
        try (BufferedReader in = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            String first = in.readLine();
            if (first == null) return rows;
            List<String> header = parseCsvLine(first);
            Map<String, Integer> column = new HashMap<>();
            for (int i = 0; i < header.size(); ++i) column.put(header.get(i), i);
            for (String name : Arrays.asList("net", "tile", "start_wire", "end_wire", "reversed")) {
                if (!column.containsKey(name)) throw new IllegalArgumentException("missing route column " + name);
            }
            String line;
            while ((line = in.readLine()) != null) {
                if (line.trim().isEmpty()) continue;
                List<String> value = parseCsvLine(line);
                rows.add(new RouteRow(value.get(column.get("net")), value.get(column.get("tile")),
                        value.get(column.get("start_wire")), value.get(column.get("end_wire")),
                        Boolean.parseBoolean(value.get(column.get("reversed")))));
            }
        }
        return rows;
    }

    private static PIP makePip(Device device, RouteRow row) {
        Tile tile = device.getTile(row.tile);
        if (tile == null) throw new IllegalArgumentException("unknown tile " + row.tile);
        Integer start = tile.getWireIndex(row.start);
        Integer end = tile.getWireIndex(row.end);
        if (start == null || end == null) throw new IllegalArgumentException("unknown wire in " + row.tile);
        PIP existing = tile.getPIP(start, end);
        if (existing == null && row.reversed) existing = tile.getPIP(end, start);
        if (existing == null) throw new IllegalArgumentException("nonexistent PIP " + row.tile + "/" + row.start + "->" + row.end);
        PIP pip = new PIP(existing);
        pip.setIsReversed(row.reversed);
        return pip;
    }

    private static boolean reachesAllSinks(Net net, List<PIP> pips) {
        SitePinInst sourcePin = net.getSource();
        if (sourcePin == null || sourcePin.getConnectedNode() == null) return net.getSinkPins().isEmpty();
        Map<String, List<String>> adjacency = new HashMap<>();
        for (PIP pip : pips) {
            String start = key(pip.isReversed() ? pip.getEndNode() : pip.getStartNode());
            String end = key(pip.isReversed() ? pip.getStartNode() : pip.getEndNode());
            adjacency.computeIfAbsent(start, ignored -> new ArrayList<>()).add(end);
        }
        Set<String> visited = new HashSet<>();
        ArrayDeque<String> queue = new ArrayDeque<>();
        queue.add(key(sourcePin.getConnectedNode()));
        while (!queue.isEmpty()) {
            String current = queue.removeFirst();
            if (!visited.add(current)) continue;
            for (String next : adjacency.getOrDefault(current, Collections.emptyList())) queue.addLast(next);
        }
        for (SitePinInst sink : net.getSinkPins()) {
            if (sink.getConnectedNode() != null && !visited.contains(key(sink.getConnectedNode()))) return false;
        }
        return true;
    }

    private static void extractRoutes(Path input, Path routes, String requestedNet) throws Exception {
        Design design = readDesign(input);
        List<Net> nets = new ArrayList<>(design.getNets());
        nets.sort(Comparator.comparing(Net::getName));
        Net selected = null;
        List<PIP> selectedPips = null;
        for (Net net : nets) {
            if (requestedNet != null && !requestedNet.equals(net.getName())) continue;
            if (requestedNet == null && (net.isStaticNet() || net.isClockNet())) continue;
            List<PIP> pips = new ArrayList<>(net.getPIPs());
            if (pips.isEmpty() || !reachesAllSinks(net, pips)) continue;
            selected = net;
            selectedPips = pips;
            break;
        }
        if (selected == null) {
            throw new IllegalArgumentException(requestedNet == null
                    ? "no non-static fully connected routed net found"
                    : "requested net is missing, unrouted, or incomplete: " + requestedNet);
        }
        selectedPips.sort(Comparator.comparing(PIP::toString));
        if (routes.getParent() != null) Files.createDirectories(routes.getParent());
        try (BufferedWriter out = Files.newBufferedWriter(routes, StandardCharsets.UTF_8)) {
            writeCsv(out, "net", "tile", "start_wire", "end_wire", "reversed");
            for (PIP pip : selectedPips) {
                writeCsv(out, selected.getName(), pip.getTile().getName(), pip.getStartWireName(),
                        pip.getEndWireName(), Boolean.toString(pip.isReversed()));
            }
        }
        System.out.println("{\"schema\":\"" + SCHEMA + "\",\"net\":\"" +
                selected.getName().replace("\\", "\\\\").replace("\"", "\\\"") +
                "\",\"pips\":" + selectedPips.size() + ",\"routes_sha256\":\"" +
                sha256(routes) + "\"}");
    }

    private static void applyRoutes(Path input, Path routes, Path outputDcp, Path outputPhys) throws Exception {
        Design design = readDesign(input);
        Device device = design.getDevice();
        Map<String, List<PIP>> byNet = new LinkedHashMap<>();
        Map<String, String> owner = new HashMap<>();
        for (RouteRow row : readRoutes(routes)) {
            Net net = design.getNet(row.net);
            if (net == null) throw new IllegalArgumentException("route references unknown net " + row.net);
            PIP pip = makePip(device, row);
            String resource = pip.getTile().getName() + "/" + pip.getStartWireName() + "/" + pip.getEndWireName();
            String prior = owner.putIfAbsent(resource, row.net);
            if (prior != null && !prior.equals(row.net)) {
                throw new IllegalArgumentException("PIP conflict between " + prior + " and " + row.net + ": " + resource);
            }
            List<PIP> netPips = byNet.computeIfAbsent(row.net, ignored -> new ArrayList<>());
            if (!netPips.contains(pip)) netPips.add(pip);
        }
        for (Map.Entry<String, List<PIP>> entry : byNet.entrySet()) {
            Net net = design.getNet(entry.getKey());
            if (!reachesAllSinks(net, entry.getValue())) {
                throw new IllegalArgumentException("route is not source-to-sink connected: " + net.getName());
            }
        }
        for (Map.Entry<String, List<PIP>> entry : byNet.entrySet()) {
            Net net = design.getNet(entry.getKey());
            net.setPIPs(entry.getValue());
            for (SitePinInst sink : net.getSinkPins()) sink.setRouted(true);
        }
        if (outputDcp.getParent() != null) Files.createDirectories(outputDcp.getParent());
        design.writeCheckpoint(outputDcp);
        if (outputPhys != null) {
            if (outputPhys.getParent() != null) Files.createDirectories(outputPhys.getParent());
            PhysNetlistWriter.writePhysNetlist(design, outputPhys.toString());
        }
        System.out.println("{\"schema\":\"" + SCHEMA + "\",\"nets\":" + byNet.size() +
                ",\"output_dcp\":\"" + outputDcp.toAbsolutePath().toString().replace("\\", "\\\\") + "\"}");
    }

    private static void usage() {
        System.err.println("usage:\n" +
                "  RapidWrightBridge inspect <input.dcp|input.phys|input.netlist>\n" +
                "  RapidWrightBridge export <input.dcp|input.phys|input.netlist> <output-dir> " +
                "[--tile-bounds <min-x> <max-x> <min-y> <max-y>]\n" +
                "  RapidWrightBridge extract <routed.dcp|routed.phys> <routes.csv> [net]\n" +
                "  RapidWrightBridge apply <input.dcp|input.phys> <routes.csv> <output.dcp> [output.phys]");
    }

    public static void main(String[] args) throws Exception {
        if (args.length == 2 && args[0].equals("inspect")) {
            inspectDesign(Paths.get(args[1]));
        } else if ((args.length == 3 || args.length == 8) && args[0].equals("export")) {
            TileBounds bounds = null;
            if (args.length == 8) {
                if (!args[3].equals("--tile-bounds")) {
                    throw new IllegalArgumentException("expected --tile-bounds");
                }
                bounds = new TileBounds(Integer.parseInt(args[4]), Integer.parseInt(args[5]),
                        Integer.parseInt(args[6]), Integer.parseInt(args[7]));
            }
            exportDesign(Paths.get(args[1]), Paths.get(args[2]), bounds);
        } else if ((args.length == 3 || args.length == 4) && args[0].equals("extract")) {
            extractRoutes(Paths.get(args[1]), Paths.get(args[2]), args.length == 4 ? args[3] : null);
        } else if ((args.length == 4 || args.length == 5) && args[0].equals("apply")) {
            applyRoutes(Paths.get(args[1]), Paths.get(args[2]), Paths.get(args[3]),
                    args.length == 5 ? Paths.get(args[4]) : null);
        } else {
            usage(); System.exit(2);
        }
    }
}
