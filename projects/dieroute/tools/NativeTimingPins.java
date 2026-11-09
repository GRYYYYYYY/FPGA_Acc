import com.xilinx.rapidwright.design.*;
import com.xilinx.rapidwright.device.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Read-only conversion of native logical load pins and existing site routing. */
public final class NativeTimingPins {
    static void require(boolean value,String message) {if(!value)throw new IllegalArgumentException(message);}
    static String field(Object value) {return Objects.toString(value,"").replace("\\","\\\\").replace("\t","\\t").replace("\n","\\n").replace("\r","\\r");}
    static void row(BufferedWriter w,Object... values)throws Exception {
        StringJoiner s=new StringJoiner("\t");for(Object v:values)s.add(field(v));w.write(s+"\n");
    }
    static String unescape(String s) {
        StringBuilder b=new StringBuilder();
        for(int i=0;i<s.length();i++) {
            char c=s.charAt(i);
            if(c=='\\') {require(++i<s.length(),"Bad escape");c=s.charAt(i);
                if(c=='t')c='\t';else if(c=='n')c='\n';else if(c=='r')c='\r';else require(c=='\\',"Bad escape");}
            b.append(c);
        }
        return b.toString();
    }
    static BufferedWriter writer(Path p,String... header)throws Exception {
        BufferedWriter w=Files.newBufferedWriter(p);row(w,(Object[])header);return w;
    }
    public static void main(String[] args)throws Exception {
        require(args.length==4,"input.dcp readable.edf load-pins.tsv new-output");
        Path out=Path.of(args[3]);Files.createDirectory(out);
        Design d=Design.readCheckpoint(args[0],args[1]);
        Map<Integer,Net> nets=new TreeMap<>();Map<Integer,Set<SiteInst>> sites=new TreeMap<>();
        Set<String> seen=new HashSet<>();int logicalCount=0,physicalCount=0;
        try(BufferedWriter logical=writer(out.resolve("logical_pins.tsv"),"net_id","net_name","to_pin","cell","logical_pin","site_inst","site","bel","physical_pin","wire");
            BufferedWriter mapped=writer(out.resolve("sdk_site_pins.tsv"),"net_id","to_pin","physical_pin","site_inst","site_pin","tile","wire")) {
            List<String> lines=Files.readAllLines(Path.of(args[2]));
            require(lines.get(0).equals("net_id\tnet_name\tto_pin"),"Bad header");
            for(String line:lines.subList(1,lines.size())) {
                String[] c=line.split("\t",-1);require(c.length==3,"Bad input row");
                int id=Integer.parseInt(c[0]);String name=unescape(c[1]),pin=unescape(c[2]);
                require(seen.add(id+"\t"+pin),"Duplicate logical pin");
                Net n=Objects.requireNonNull(d.getNet(name),"Missing net "+name);
                Net old=nets.putIfAbsent(id,n);require(old==null||old==n,"Net ID alias");
                int split=pin.lastIndexOf('/');require(split>0,"No cell path");
                String cellName=pin.substring(0,split),lp=pin.substring(split+1);
                Cell cell=Objects.requireNonNull(d.getCell(cellName),"Missing cell "+cellName);
                require(cell.isPlaced()&&!cell.isRoutethru(),"Not a placed functional cell");
                SiteInst si=cell.getSiteInst();sites.computeIfAbsent(id,k->new TreeSet<>(Comparator.comparing(SiteInst::getName))).add(si);
                Set<String> physical=cell.getAllPhysicalPinMappings(lp);
                require(physical!=null&&!physical.isEmpty(),"Missing physical mapping "+pin);
                for(String pp:new TreeSet<>(physical)) {
                    BELPin bp=Objects.requireNonNull(cell.getBEL().getPin(pp));
                    require(bp.isInput(),"Load is not an input");
                    require(si.getNetFromSiteWire(bp.getSiteWireName())==n,"Logical load site-wire net mismatch "+pin);
                    row(logical,id,name,pin,cellName,lp,si.getName(),si.getSiteName(),cell.getBELName(),pp,bp.getSiteWireName());
                    for(String sp:new TreeSet<>(DesignTools.getAllRoutedSitePinsFromPhysicalPin(cell,n,pp))) {
                        SitePinInst spi=Objects.requireNonNull(si.getSitePinInst(sp),"No SitePinInst");
                        require(spi.getNet()==n&&!spi.isOutPin()&&n.getPins().contains(spi),"Site input net mismatch");
                        Node node=Objects.requireNonNull(spi.getConnectedNode());
                        row(mapped,id,pin,pp,si.getName(),sp,node.getTile().getName(),node.getWireIndex());
                    }
                    physicalCount++;
                }
                logicalCount++;
            }
        }
        // Export complete net-labelled site connectivity for an independent audit.
        try(BufferedWriter wires=writer(out.resolve("site_wires.tsv"),"net_id","site_inst","site","wire","bel","pin","direction","bel_class","site_port","cell","cell_type","routethru","logical_pin");
            BufferedWriter pips=writer(out.resolve("site_pips.tsv"),"net_id","site_inst","bel","input_pin","output_pin","input_wire","output_wire");
            BufferedWriter pins=writer(out.resolve("net_site_pins.tsv"),"net_id","site_inst","site","pin","output","tile","wire")) {
            for(Map.Entry<Integer,Net> entry:nets.entrySet()) {
                int id=entry.getKey();Net net=entry.getValue();
                List<SitePinInst> np=new ArrayList<>(net.getPins());np.sort(Comparator.comparing(SitePinInst::getSiteInstName).thenComparing(SitePinInst::getName));
                for(SitePinInst sp:np) {
                    Node node=Objects.requireNonNull(sp.getConnectedNode());
                    row(pins,id,sp.getSiteInstName(),sp.getSite().getName(),sp.getName(),sp.isOutPin(),node.getTile().getName(),node.getWireIndex());
                }
                for(SiteInst si:sites.get(id)) {
                    Set<String> used=new TreeSet<>(si.getSiteWiresFromNet(net));
                    for(String wire:used) {
                        List<BELPin> bps=new ArrayList<>(Arrays.asList(si.getSiteWirePins(wire)));
                        bps.sort(Comparator.comparing(BELPin::getBELName).thenComparing(BELPin::getName));
                        for(BELPin bp:bps) {
                            Cell cell=si.getCell(bp.getBEL());
                            row(wires,id,si.getName(),si.getSiteName(),wire,bp.getBELName(),bp.getName(),bp.getDir(),bp.getBEL().getBELClass(),bp.isSitePort(),
                                cell==null?"":cell.getName(),cell==null?"":cell.getType(),cell!=null&&cell.isRoutethru(),cell==null?"":cell.getLogicalPinMapping(bp.getName()));
                        }
                    }
                    List<SitePIP> ps=new ArrayList<>(si.getUsedSitePIPs());ps.sort(Comparator.comparing(SitePIP::toString));
                    for(SitePIP p:ps)if(used.contains(p.getInputPin().getSiteWireName())||used.contains(p.getOutputPin().getSiteWireName())) {
                        require(used.contains(p.getInputPin().getSiteWireName())&&used.contains(p.getOutputPin().getSiteWireName()),"Used site PIP changes net");
                        row(pips,id,si.getName(),p.getBELName(),p.getInputPinName(),p.getOutputPinName(),p.getInputPin().getSiteWireName(),p.getOutputPin().getSiteWireName());
                    }
                }
            }
        }
        Files.writeString(out.resolve("completed.txt"),"logical_loads="+logicalCount+"\nphysical_load_pins="+physicalCount+"\nnets="+nets.size()+"\nroutes_changed=false\n");
        System.out.println("logical_loads="+logicalCount+" physical_load_pins="+physicalCount+" nets="+nets.size());
    }
}
