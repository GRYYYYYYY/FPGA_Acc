import com.xilinx.rapidwright.design.*;
import com.xilinx.rapidwright.device.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Conversion only: replace audited complete net trees, never invoke a router. */
public final class WriteNativeCohort {
    private static void require(boolean value,String message) {
        if(!value)throw new IllegalArgumentException(message);
    }
    private static String fields(Object... values) {
        StringJoiner j=new StringJoiner("\t");
        for(Object v:values) {
            String s=Objects.toString(v,"");
            j.add(s.replace("\\","\\\\").replace("\t","\\t").replace("\n","\\n").replace("\r","\\r"));
        }
        return j.toString();
    }
    private static final class Hash {
        final MessageDigest md;
        Hash()throws Exception{md=MessageDigest.getInstance("SHA-256");}
        void add(String s){md.update((s+"\n").getBytes(StandardCharsets.UTF_8));}
        String finish(){char[] digits="0123456789abcdef".toCharArray();StringBuilder b=new StringBuilder();
            for(byte x:md.digest()){b.append(digits[(x&255)>>>4]);b.append(digits[x&15]);}return b.toString();}
    }
    private static String hash(List<String> rows)throws Exception {
        Collections.sort(rows);Hash h=new Hash();for(String s:rows)h.add(s);return h.finish();
    }
    private static String node(Node n){return n==null?"":fields(n.getTile().getName(),n.getWireIndex());}
    private static String pip(PIP p){return fields(p.getTile().getName(),p.getStartWireIndex(),p.getEndWireIndex(),
        p.isReversed(),p.isBidirectional(),p.isPIPFixed(),p.isRouteThru(),p.isStub(),p.isStartStub(),p.isLogicalDriver(),p.isEndWireNull());}
    private static String route(List<PIP> pips)throws Exception {
        List<String> rows=new ArrayList<>();for(PIP p:pips)rows.add(pip(p));return hash(rows);
    }
    private static String pin(SitePinInst p){return fields(p.getSiteInstName(),p.getName(),p.isOutPin(),node(p.getConnectedNode()));}
    private static Map<Integer,String> names(Path input)throws Exception {
        Map<Integer,String> names=new TreeMap<>();Set<String> unique=new HashSet<>();
        for(String line:Files.readAllLines(input)) {
            String[] c=line.split("\t",-1);require(c.length==2,"Bad net row");int id=Integer.parseInt(c[0]);
            require(names.putIfAbsent(id,c[1])==null&&unique.add(c[1]),"Duplicate net");
        }
        require(!names.isEmpty(),"No selected nets");return names;
    }
    // Snapshot every net's pins and every unselected route; all physical site/BEL
    // occurrences are included, since Design.getCells() collapses <LOCKED> names.
    private static List<String> snapshot(Design d,Set<String> selected)throws Exception {
        Hash pins=new Hash(),outside=new Hash(),inside=new Hash(),sites=new Hash(),cells=new Hash();
        List<Net> nets=new ArrayList<>(d.getNets());nets.sort(Comparator.comparing(Net::getName));
        for(Net n:nets) {
            List<String> ps=new ArrayList<>();for(SitePinInst p:n.getPins())ps.add(pin(p));
            pins.add(fields(n.getName(),n.getType(),n.getSource()==null?"":pin(n.getSource()),hash(ps)));
            (selected.contains(n.getName())?inside:outside).add(fields(n.getName(),route(n.getPIPs())));
        }
        List<SiteInst> ss=new ArrayList<>(d.getSiteInsts());ss.sort(Comparator.comparing(SiteInst::getName));
        List<Cell> cs=new ArrayList<>();
        for(SiteInst s:ss) {
            List<String> ps=new ArrayList<>(),ws=new ArrayList<>();
            for(SitePIP p:s.getUsedSitePIPs())ps.add(fields(p.getBELName(),p.getInputPinName(),p.getOutputPinName(),s.getSitePIPStatus(p)));
            for(Map.Entry<String,Net> e:s.getSiteWireToNetMap().entrySet())ws.add(fields(e.getKey(),e.getValue().getName()));
            sites.add(fields(s.getName(),s.getSiteName(),s.getSiteTypeEnum(),s.isSiteLocked(),hash(ps),hash(ws)));cs.addAll(s.getCells());
        }
        for(Cell c:d.getCells())if(c.getSiteInst()==null)cs.add(c);
        cs.sort(Comparator.comparing(Cell::getName).thenComparing(Cell::getSiteName,Comparator.nullsFirst(Comparator.naturalOrder()))
            .thenComparing(Cell::getBELName,Comparator.nullsFirst(Comparator.naturalOrder())));
        for(Cell c:cs) {
            List<String> ps=new ArrayList<>();for(Map.Entry<String,String> e:c.getPinMappingsP2L().entrySet())ps.add(fields(e.getKey(),e.getValue(),c.isPinFixed(e.getKey())));
            cells.add(fields(c.getName(),c.getType(),c.getSiteName(),c.getBELName(),c.isSiteFixed(),c.isBELFixed(),c.isLocked(),c.isRoutethru(),hash(ps)));
        }
        List<String> partitions=new ArrayList<>();for(PartitionPin p:d.getPartitionPins())partitions.add(fields(p.getInstanceName(),p.getTerminalName(),p.getTileName(),p.getWireName(),p.isFixed(),p.isWireFixed(),p.isPort()));
        return Arrays.asList("part="+d.getPartName(),"nets="+nets.size(),"sites="+ss.size(),"cell_occurrences="+cs.size(),
            "pins="+pins.finish(),"outside_routes="+outside.finish(),"sites_state="+sites.finish(),"cells_state="+cells.finish(),
            "partition_pins="+hash(partitions),"selected_routes="+inside.finish());
    }
    private static Node resolve(Device d,String tile,String wire) {
        Node n=Node.getNode(Objects.requireNonNull(d.getTile(tile)),Integer.parseInt(wire));
        require(n!=null&&!n.isInvalidNode(),"Missing native node");return n;
    }
    public static void main(String[] args)throws Exception {
        if(args.length==1&&args[0].equals("selftest")) {
            require(!fields("a\tb","c").equals(fields("a","b\tc")),"Field-boundary collision");
            require(!fields("a\tb").equals(fields("a\\tb")),"Escaped-literal collision");
            require(!fields(fields("a","b"),"c").equals(fields("a",fields("b","c"))),"Nested field collision");
            require(hash(new ArrayList<>(Arrays.asList("b","a"))).equals(hash(new ArrayList<>(Arrays.asList("a","b")))),"Order-dependent set digest");
            require(new Hash().finish().equals("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),"SHA-256 encoding");
            System.out.println("snapshot field-boundary, nested-field, ordering and hash checks passed");return;
        }
        require(args.length==5,"write|verify input.dcp readable.edf|- prepared-directory new-output-directory");
        boolean write=args[0].equals("write");require(write||args[0].equals("verify"),"Bad mode");
        Path prepared=Path.of(args[3]),out=Path.of(args[4]);Files.createDirectory(out);
        Map<Integer,String> names=names(prepared.resolve("nets.tsv"));Set<String> selected=new HashSet<>(names.values());
        Design d=args[2].equals("-")?Design.readCheckpoint(Path.of(args[1])):Design.readCheckpoint(args[1],args[2]);
        if(!write) {
            List<String> state=snapshot(d,selected);Files.write(out.resolve("snapshot.txt"),state);
            require(state.equals(Files.readAllLines(prepared.resolve("expected.txt"))),"Serialized physical state mismatch");
            Files.writeString(out.resolve("verified.txt"),"Reloaded all selected routes, outside routes, pins, site routing, cell placement/pin maps and partition pins match.\n");return;
        }
        Map<Integer,Net> nets=new TreeMap<>();Map<Integer,List<PIP>> replacements=new TreeMap<>();
        for(Map.Entry<Integer,String> e:names.entrySet()) {
            Net n=Objects.requireNonNull(d.getNet(e.getValue()));require(!n.isStaticNet()&&!n.isClockNet()&&!n.needsClockNetworkResources(),"Protected net");
            for(PIP p:n.getPIPs())require(!p.isPIPFixed()&&!p.isRouteThru()&&!p.isStub()&&!p.isStartStub(),"Unsupported original net PIP");
            nets.put(e.getKey(),n);replacements.put(e.getKey(),new ArrayList<>());
        }
        Map<Integer,Set<String>> expectedPins=new TreeMap<>();
        for(String line:Files.readAllLines(prepared.resolve("pins.tsv"))) {
            String[] c=line.split("\t",-1);require(c.length==6,"Bad pin row");int id=Integer.parseInt(c[0]);
            require(nets.containsKey(id),"Pin for unselected net");Node n=resolve(d.getDevice(),c[4],c[5]);
            String key=fields(c[1],c[2],c[3],node(n));require(expectedPins.computeIfAbsent(id,k->new TreeSet<>()).add(key),"Duplicate pin");
        }
        for(Map.Entry<Integer,Net> e:nets.entrySet()) {
            Set<String> actual=new TreeSet<>();for(SitePinInst p:e.getValue().getPins())require(actual.add(pin(p)),"Duplicate actual pin");
            require(actual.equals(expectedPins.get(e.getKey())),"Incomplete selected net terminal set");
        }
        Map<Integer,Set<String>> pipKeys=new HashMap<>();
        Map<Integer,Map<Node,Node>> parents=new HashMap<>();Map<Node,Integer> owners=new HashMap<>();
        for(String line:Files.readAllLines(prepared.resolve("pips.tsv"))) {
            String[] c=line.split("\t",-1);require(c.length==9,"Bad PIP row");int id=Integer.parseInt(c[0]);require(nets.containsKey(id),"PIP for unselected net");
            Tile tile=Objects.requireNonNull(d.getDevice().getTile(c[1]));int start=Integer.parseInt(c[2]),end=Integer.parseInt(c[3]);PIP found=null;
            for(PIP p:tile.getPIPs())if(p.getStartWireIndex()==start&&p.getEndWireIndex()==end){require(found==null,"Ambiguous PIP");found=p;}
            require(found!=null&&!found.isRouteThru()&&!found.isEndWireNull(),"Missing/unsupported PIP");
            require(c[4].equals("true")||c[4].equals("false"),"Bad reversal flag");boolean reversed=Boolean.parseBoolean(c[4]);
            require(found.isBidirectional()||found.isReversed()==reversed,"Illegal PIP direction");
            PIP p=new PIP(found);p.setIsReversed(reversed);
            Node src=reversed?p.getEndNode():p.getStartNode(),dst=reversed?p.getStartNode():p.getEndNode();
            require(src.equals(resolve(d.getDevice(),c[5],c[6]))&&dst.equals(resolve(d.getDevice(),c[7],c[8])),"Native PIP endpoint mismatch");
            require(pipKeys.computeIfAbsent(id,k->new HashSet<>()).add(pip(p)),"Duplicate PIP");
            require(parents.computeIfAbsent(id,k->new HashMap<>()).putIfAbsent(dst,src)==null,"Multiple tree parents");
            for(Node n:Arrays.asList(src,dst)){Integer owner=owners.putIfAbsent(n,id);require(owner==null||owner==id,"Cross-net short");}
            replacements.get(id).add(p);
        }
        for(Map.Entry<Integer,Net> e:nets.entrySet()) {
            Map<Node,Node> tree=Objects.requireNonNull(parents.get(e.getKey()));Net n=e.getValue();Node root=Objects.requireNonNull(n.getSource()).getConnectedNode();
            require(!tree.containsKey(root),"Tree reenters source");Set<Node> used=new HashSet<>();
            for(SitePinInst pin:n.getPins())if(!pin.isOutPin()) {
                Node cursor=pin.getConnectedNode();Set<Node> seen=new HashSet<>();
                while(!cursor.equals(root)){require(seen.add(cursor)&&tree.containsKey(cursor),"Disconnected/cyclic tree");used.add(cursor);cursor=tree.get(cursor);}
            }
            require(used.equals(tree.keySet()),"Orphan tree branches");
        }
        // All preflight checks above precede mutation. setPIPs preserves site routing.
        List<String> before=snapshot(d,selected);Files.write(out.resolve("before.txt"),before);
        List<String> changed=new ArrayList<>();
        for(Map.Entry<Integer,Net> e:nets.entrySet()) {
            String old=route(e.getValue().getPIPs()),next=route(replacements.get(e.getKey()));
            changed.add(fields(e.getKey(),e.getValue().getName(),e.getValue().getPIPs().size(),replacements.get(e.getKey()).size(),old,next));
            e.getValue().setPIPs(replacements.get(e.getKey()));
            require(route(e.getValue().getPIPs()).equals(next),"Assigned PIPs differ");
        }
        List<String> after=snapshot(d,selected);require(before.subList(0,9).equals(after.subList(0,9)),"Unexpected mutation outside selected routes");
        Files.write(out.resolve("expected.txt"),after);Files.write(out.resolve("changed_nets.tsv"),changed);
        d.writeCheckpoint(out.resolve("routed.dcp"));
        System.out.println("selected_nets="+nets.size()+" PIPs="+replacements.values().stream().mapToInt(List::size).sum()+" scope=physical_writeback_not_native_legality");
    }
}
