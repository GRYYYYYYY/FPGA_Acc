import com.xilinx.rapidwright.design.*;
import com.xilinx.rapidwright.device.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Inventory a complete DCP using physical pin access locations, not XY labels.
 * No routes are changed. Missing sources/pins remain explicit inventory rows.
 */
public final class DcpSlrProbe {
    private static void csv(BufferedWriter out,Object... values) throws IOException {
        for(int i=0;i<values.length;++i) {
            if(i!=0)out.write(',');
            out.write("\""+Objects.toString(values[i], "").replace("\"","\"\"")+"\"");
        }
        out.newLine();
    }
    private static String routeHash(Net net) throws Exception {
        List<String> keys=new ArrayList<>();
        for(PIP p:net.getPIPs()) keys.add(p.getTile().getName()+"\t"+p.getStartWireName()+"\t"+
            p.getEndWireName()+"\t"+p.isReversed()+"\t"+p.isPIPFixed()+"\t"+p.isStub()+"\t"+
            p.isStartStub()+"\t"+p.isLogicalDriver());
        return hashStrings(keys);
    }
    private static String hashStrings(List<String> keys) throws Exception {
        Collections.sort(keys);
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        for(String k:keys)digest.update((k+"\n").getBytes(StandardCharsets.UTF_8));
        StringBuilder hex=new StringBuilder();
        for(byte b:digest.digest())hex.append(String.format("%02x",b & 255));
        return hex.toString();
    }
    private static Object[] nodeAccess(Node node) {
        if(node==null || node.isInvalidNode())return new Object[]{"",0};
        Wire[] wires=node.getAllWiresInNode();
        Arrays.sort(wires,Comparator.comparingInt((Wire w)->w.getTile().getUniqueAddress())
            .thenComparingInt(Wire::getWireIndex));
        if(wires.length==0)throw new IllegalStateException("empty electrical node");
        int mask=0;
        for(Wire w:wires) {
            SLR slr=w.getTile().getSLR();
            if(slr==null || slr.getId()<0 || slr.getId()>=8)
                throw new IllegalStateException("unsupported native SLR");
            mask|=1<<slr.getId();
        }
        return new Object[]{wires[0].getTile().getName()+"/"+wires[0].getWireName(),mask};
    }
    public static void main(String[] args) throws Exception {
        if(args.length<2 || args.length>4)throw new IllegalArgumentException(
            "input.dcp new-output-directory [readable.edf [new-output.dcp]]");
        Path output=Path.of(args[1]);Files.createDirectory(output);
        if(args.length==4 && Files.exists(Path.of(args[3])))
            throw new IllegalArgumentException("refusing existing checkpoint: "+args[3]);
        Design design=args.length>=3 ? Design.readCheckpoint(args[0],args[2])
            : Design.readCheckpoint(Path.of(args[0]));
        List<Net> nets=new ArrayList<>(design.getNets());nets.sort(Comparator.comparing(Net::getName));
        long cross=0,signals=0,unknownPins=0,totalPips=0;
        try(BufferedWriter out=Files.newBufferedWriter(output.resolve("nets.csv"),StandardCharsets.UTF_8);
            BufferedWriter pins=Files.newBufferedWriter(output.resolve("pins.csv"),StandardCharsets.UTF_8)) {
            csv(out,"net","static","clock","pins","pips","pin_slrs","missing_pin_locations",
                "source_site","source_pin","source_slr","source_node_present","route_sha256");
            csv(pins,"net","site_inst","site","pin","is_output","tile","access_slr",
                "canonical_node","membership_mask");
            for(Net net:nets) {
                TreeSet<Integer> slrs=new TreeSet<>();int unknown=0;
                List<SitePinInst> orderedPins=new ArrayList<>(net.getPins());
                orderedPins.sort(Comparator.comparing(SitePinInst::getSiteInstName)
                    .thenComparing(SitePinInst::getName));
                for(SitePinInst pin:orderedPins) {
                    Tile tile=pin.getTile();
                    if(tile==null || tile.getSLR()==null)++unknown;
                    else slrs.add(tile.getSLR().getId());
                    Object[] access=nodeAccess(pin.getConnectedNode());
                    csv(pins,net.getName(),pin.getSiteInstName(),pin.getSite()==null?"":pin.getSite().getName(),
                        pin.getName(),pin.isOutPin(),tile==null?"":tile.getName(),
                        tile==null || tile.getSLR()==null?-1:tile.getSLR().getId(),access[0],access[1]);
                }
                SitePinInst source=net.getSource();
                int sourceSlr=source!=null && source.getTile()!=null && source.getTile().getSLR()!=null
                    ? source.getTile().getSLR().getId():-1;
                boolean sourceNode=source!=null && source.getConnectedNode()!=null;
                boolean signal=!net.isStaticNet() && !net.isClockNet();
                if(signal)++signals;
                if(signal && slrs.size()>1)++cross;
                unknownPins+=unknown;totalPips+=net.getPIPs().size();
                csv(out,net.getName(),net.isStaticNet(),net.isClockNet(),net.getPins().size(),net.getPIPs().size(),
                    String.join(";",slrs.stream().map(String::valueOf).toArray(String[]::new)),unknown,
                    source==null?"":source.getSiteInstName(),source==null?"":source.getName(),sourceSlr,sourceNode,
                    routeHash(net));
            }
        }
        // Design.getCells() collapses the repeated <LOCKED> name and may pick a
        // different representative after serialization. Enumerate physical BEL
        // occurrences, including locked placeholders and multi-BEL cells.
        List<SiteInst> sites=new ArrayList<>(design.getSiteInsts());
        sites.sort(Comparator.comparing(SiteInst::getName));
        List<Cell> cells=new ArrayList<>();
        Set<String> occupied=new HashSet<>();
        for(SiteInst site:sites)for(Cell cell:site.getCells()) {
            String identity=Objects.toString(cell.getSiteName(),"")+"\t"+Objects.toString(cell.getBELName(),"");
            if(cell.isPlaced() && !occupied.add(identity))
                throw new IllegalStateException("duplicate physical BEL occurrence: "+identity);
            cells.add(cell);
        }
        for(Cell cell:design.getCells())if(cell.getSiteInst()==null)cells.add(cell);
        cells.sort(Comparator.comparing(Cell::getName)
            .thenComparing(Cell::getSiteName,Comparator.nullsFirst(Comparator.naturalOrder()))
            .thenComparing(Cell::getBELName,Comparator.nullsFirst(Comparator.naturalOrder())));
        try(BufferedWriter out=Files.newBufferedWriter(output.resolve("cells.csv"),StandardCharsets.UTF_8);
            BufferedWriter pins=Files.newBufferedWriter(output.resolve("cell_pin_mapping.csv"),StandardCharsets.UTF_8)) {
            csv(out,"cell","type","site","bel","site_fixed","bel_fixed","locked","routethru");
            csv(pins,"cell","site","bel","physical_pin","logical_pin","pin_fixed");
            for(Cell cell:cells) {
                csv(out,cell.getName(),cell.getType(),cell.getSiteName(),cell.getBELName(),
                    cell.isSiteFixed(),cell.isBELFixed(),cell.isLocked(),cell.isRoutethru());
                for(Map.Entry<String,String> p:new TreeMap<>(cell.getPinMappingsP2L()).entrySet())
                    csv(pins,cell.getName(),cell.getSiteName(),cell.getBELName(),p.getKey(),p.getValue(),
                        cell.isPinFixed(p.getKey()));
            }
        }
        try(BufferedWriter out=Files.newBufferedWriter(output.resolve("sites.csv"),StandardCharsets.UTF_8)) {
            csv(out,"site_inst","site","type","locked","used_site_pips","site_wires","pip_sha256","wire_net_sha256");
            for(SiteInst site:sites) {
                List<String> pips=new ArrayList<>(),wires=new ArrayList<>();
                for(SitePIP p:site.getUsedSitePIPs())pips.add(p.getBELName()+"\t"+p.getInputPinName()+"\t"+p.getOutputPinName());
                for(Map.Entry<String,Net> e:site.getSiteWireToNetMap().entrySet())
                    wires.add(e.getKey()+"\t"+e.getValue().getName());
                csv(out,site.getName(),site.getSiteName(),site.getSiteTypeEnum(),site.isSiteLocked(),
                    pips.size(),wires.size(),hashStrings(pips),hashStrings(wires));
            }
        }
        System.out.println("device="+design.getDevice().getName()+" part="+design.getPartName()+
            " slrs="+design.getDevice().getSLRs().length);
        System.out.println("cells="+design.getCells().size()+" nets="+nets.size()+" signal_nets="+signals+
            " cross_slr_signal_nets="+cross+" total_pips="+totalPips+" missing_pin_locations="+unknownPins);
        System.out.println("scope=complete_DCP_pin_inventory_not_rerouting_or_legality_proof");
        System.out.println("physical_cell_occurrences="+cells.size()+" locked_occurrences="+
            cells.stream().filter(Cell::isLocked).count()+" sites="+sites.size());
        if(args.length==4) {
            design.writeCheckpoint(Path.of(args[3]));
            System.out.println("checkpoint_operation=unmodified_serialization_roundtrip");
        }
    }
}
