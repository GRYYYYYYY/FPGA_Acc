import com.xilinx.rapidwright.edif.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Flatten EDIF net aliases for connectivity verification, not routing.
 * Includes every declared leaf/top-level port bit, even unconnected bits.
 * Primitive and opaque cell bodies are boundaries, not reimplemented logic.
 * No static-net coalescing or removal of constant drivers is performed.
 */
public final class EdifConnectivityProbe {
    private static String frame(String s) { return s.length()+":"+s; }
    private static String hex(byte[] data) {
        char[] chars=new char[data.length*2], digits="0123456789abcdef".toCharArray();
        for(int i=0;i<data.length;i++){chars[2*i]=digits[(data[i]&255)>>>4];chars[2*i+1]=digits[data[i]&15];}
        return new String(chars);
    }
    private static void row(BufferedWriter out,Object... values)throws IOException {
        for(int i=0;i<values.length;i++) {
            if(i>0)out.write(',');
            out.write("\""+Objects.toString(values[i],"").replace("\"","\"\"")+"\"");
        }
        out.newLine();
    }
    private static String hashStrings(List<String> strings)throws Exception {
        Collections.sort(strings);MessageDigest d=MessageDigest.getInstance("SHA-256");
        for(String s:strings)d.update(frame(s).getBytes(StandardCharsets.UTF_8));
        return hex(d.digest());
    }
    private static String properties(EDIFPropertyObject object)throws Exception {
        List<String> list=new ArrayList<>();
        for(Map.Entry<String,EDIFPropertyValue> e:object.getPropertiesMap().entrySet()) {
            EDIFPropertyValue v=e.getValue();
            list.add(frame(e.getKey())+frame(v.getType().toString())+frame(v.getValue())+
                frame(Objects.toString(v.getOwner(),"")));
        }
        return hashStrings(list);
    }
    private static final class DSU {
        int[] parent=new int[1024],size=new int[1024];int count;
        int add(){
            if(count==parent.length){parent=Arrays.copyOf(parent,count*2);size=Arrays.copyOf(size,count*2);}
            parent[count]=count;size[count]=1;return count++;
        }
        int find(int x){while(x!=parent[x]){parent[x]=parent[parent[x]];x=parent[x];}return x;}
        void union(int x,int y){x=find(x);y=find(y);if(x==y)return;
            if(size[x]<size[y]){int t=x;x=y;y=t;}parent[y]=x;size[x]+=size[y];}
    }
    private static final class Endpoint {
        String key,instance,port,direction;int node;
        Endpoint(String k,String i,String p,String d,int n){key=k;instance=i;port=p;direction=d;node=n;}
    }
    private static final class Leaf {
        String key,path,library,type,properties,typeProperties,ports;boolean primitive;int portBits;
    }
    private final DSU dsu=new DSU();
    private final List<Endpoint> endpoints=new ArrayList<>();
    private final List<Leaf> leaves=new ArrayList<>();
    private final Set<EDIFCell> active=Collections.newSetFromMap(new IdentityHashMap<>());
    private final Map<EDIFCell,Map<EDIFPort,EDIFNet[]>> insideCache=new IdentityHashMap<>();
    private long nets,aliases,unconnectedBits,leafInstances;
    private static List<EDIFPort> ports(EDIFCell type){
        List<EDIFPort> ports=new ArrayList<>(type.getPorts());ports.sort(Comparator.comparing(EDIFPort::getName));return ports;
    }
    private static int bitIndex(EDIFPortInst pi) {
        int i=pi.getIndex();if(i==-1 && !pi.getPort().isBus())i=0;
        if(i<0 || i>=pi.getPort().getWidth())throw new IllegalStateException("invalid EDIF member index");return i;
    }
    private static String bitName(EDIFPort port,int i) {
        if(!port.isBus())return port.getBusName();
        // This SDK's getPortInstNameFromPort() calls the inverse mapping for
        // ascending nonzero-based buses. Use the EDIF member index directly.
        int named=port.getLeft()+(port.isLittleEndian()?-i:i);
        return port.getBusName(true)+named+"]";
    }
    private Map<EDIFPort,EDIFNet[]> internal(EDIFCell cell) {
        Map<EDIFPort,EDIFNet[]> map=insideCache.get(cell);if(map!=null)return map;
        map=new IdentityHashMap<>();
        for(EDIFNet net:cell.getNets())for(EDIFPortInst pi:net.getPortInsts())if(pi.getCellInst()==null) {
            EDIFNet[] bits=map.computeIfAbsent(pi.getPort(),p->new EDIFNet[p.getWidth()]);int i=bitIndex(pi);
            if(bits[i]!=null && bits[i]!=net)throw new IllegalStateException("internal port bit joins multiple local nets");bits[i]=net;
        }
        insideCache.put(cell,map);return map;
    }
    private EDIFNet internal(EDIFCell cell,EDIFPort port,int i) {
        EDIFNet[] bits=internal(cell).get(port);return bits==null?null:bits[i];
    }
    private int node(Map<EDIFNet,Integer> nodes,EDIFNet net){
        if(net==null){unconnectedBits++;return dsu.add();}
        Integer id=nodes.get(net);if(id==null)throw new IllegalStateException("net is not in declared parent cell");return id;
    }
    private void leaf(EDIFCellInst inst,String path,String key,Map<EDIFNet,Integer> nodes)throws Exception {
        Leaf leaf=new Leaf();leaf.key=key;leaf.path=path;leaf.type=inst.getCellType().getName();
        leaf.library=inst.getCellType().getLibrary().getName();leaf.primitive=inst.getCellType().isPrimitive();
        leaf.properties=properties(inst);leaf.typeProperties=properties(inst.getCellType());
        Set<String> names=new HashSet<>();List<String> schema=new ArrayList<>();
        Map<EDIFPort,EDIFNet[]> links=new IdentityHashMap<>();
        Set<String> connected=new HashSet<>();
        for(EDIFPortInst pi:inst.getPortInsts()) {
            int i=bitIndex(pi);String identity=frame(pi.getPort().getName())+i;
            if(!connected.add(identity))throw new IllegalStateException("duplicate leaf port connection");
            links.computeIfAbsent(pi.getPort(),p->new EDIFNet[p.getWidth()])[i]=pi.getNet();
        }
        for(EDIFPort port:ports(inst.getCellType()))for(int i=0;i<port.getWidth();i++) {
            String name=bitName(port,i);
            if(!names.add(name))throw new IllegalStateException("duplicate leaf port bit");
            EDIFNet[] bits=links.get(port);
            String direction=port.getDirection().toString();
            endpoints.add(new Endpoint("L"+key+frame(name)+frame(direction),key,name,direction,
                node(nodes,bits==null?null:bits[i])));
            schema.add(frame(name)+frame(direction)+frame(properties(port)));leaf.portBits++;
        }
        for(EDIFPortInst pi:inst.getPortInsts())if(!names.contains(bitName(pi.getPort(),bitIndex(pi))))
            throw new IllegalStateException("connected leaf pin absent from declared interface: "+path+"/"+pi.getName());
        leaf.ports=hashStrings(schema);leaves.add(leaf);leafInstances++;
    }
    private Map<EDIFNet,Integer> visit(EDIFCell type,String path,String key)throws Exception {
        if(!active.add(type))throw new IllegalStateException("recursive cell hierarchy");
        Map<EDIFNet,Integer> nodes=new IdentityHashMap<>();
        for(EDIFNet net:type.getNets()){nodes.put(net,dsu.add());nets++;}
        List<EDIFCellInst> children=new ArrayList<>(type.getCellInsts());children.sort(Comparator.comparing(EDIFCellInst::getName));
        for(EDIFCellInst child:children) {
            EDIFCell ct=child.getCellType();String ck=key+frame(child.getName()),cp=path.isEmpty()?child.getName():path+"/"+child.getName();
            if(ct.isPrimitive() || (ct.getCellInsts().isEmpty() && ct.getNets().isEmpty())) {
                leaf(child,cp,ck,nodes);continue;
            }
            Map<EDIFNet,Integer> inner=visit(ct,cp,ck);
            for(EDIFPortInst pi:child.getPortInsts()) {
                EDIFNet inside=internal(ct,pi.getPort(),bitIndex(pi)),outside=pi.getNet();
                if(inside!=null && outside!=null){dsu.union(node(nodes,outside),node(inner,inside));aliases++;}
            }
        }
        active.remove(type);return nodes;
    }
    private void export(EDIFNetlist netlist,Path out)throws Exception {
        Map<EDIFNet,Integer> top=visit(netlist.getTopCell(),"","");
        for(EDIFPort port:ports(netlist.getTopCell()))for(int i=0;i<port.getWidth();i++) {
            String name=bitName(port,i),direction=port.getDirection().toString();
            endpoints.add(new Endpoint("T"+frame(name)+frame(direction),"",name,direction,node(top,internal(netlist.getTopCell(),port,i))));
        }
        endpoints.sort(Comparator.comparing(e->e.key));
        Map<Integer,MessageDigest> hashes=new HashMap<>();Map<Integer,Integer> counts=new HashMap<>();
        String previous=null;
        for(Endpoint e:endpoints) {
            if(e.key.equals(previous))throw new IllegalStateException("duplicate flattened endpoint identity");previous=e.key;
            e.node=dsu.find(e.node);MessageDigest d=hashes.get(e.node);
            if(d==null){d=MessageDigest.getInstance("SHA-256");hashes.put(e.node,d);}
            d.update(frame(e.key).getBytes(StandardCharsets.UTF_8));counts.merge(e.node,1,Integer::sum);
        }
        Map<Integer,String> signatures=new HashMap<>();
        for(Map.Entry<Integer,MessageDigest> e:hashes.entrySet())signatures.put(e.getKey(),hex(e.getValue().digest()));
        hashes.clear();
        try(BufferedWriter w=Files.newBufferedWriter(out.resolve("endpoints.csv"),StandardCharsets.UTF_8)) {
            row(w,"endpoint","instance_key","port","direction","component_sha256","component_terminals");
            for(Endpoint e:endpoints)row(w,e.key,e.instance,e.port,e.direction,signatures.get(e.node),counts.get(e.node));
        }
        leaves.sort(Comparator.comparing(l->l.key));
        try(BufferedWriter w=Files.newBufferedWriter(out.resolve("leaves.csv"),StandardCharsets.UTF_8)) {
            row(w,"instance_key","instance","library","type","primitive","port_bits","properties_sha256","type_properties_sha256","port_schema_sha256");
            for(Leaf l:leaves)row(w,l.key,l.path,l.library,l.type,l.primitive,l.portBits,l.properties,l.typeProperties,l.ports);
        }
        long components=0;for(int i=0;i<dsu.count;i++)if(dsu.find(i)==i)components++;
        String json="{\n  \"schema\": \"dieroute.edif_connectivity.v1\",\n  \"leaf_instances\": "+leafInstances+
            ",\n  \"endpoints\": "+endpoints.size()+",\n  \"net_instances\": "+nets+",\n  \"alias_unions\": "+aliases+
            ",\n  \"unconnected_declared_bits\": "+unconnectedBits+",\n  \"components\": "+components+
            ",\n  \"components_with_terminals\": "+signatures.size()+",\n  \"components_without_terminals\": "+(components-signatures.size())+
            ",\n  \"scope\": \"EDIF leaf and top-level connectivity, primitive and opaque cell boundaries; no constant normalization\"\n}\n";
        Files.writeString(out.resolve("summary.json"),json);System.out.print(json);
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("input.edf new-output-directory");
        Path out=Path.of(args[1]);Files.createDirectory(out);
        EDIFNetlist netlist=EDIFTools.readEdifFile(Path.of(args[0]),8);
        new EdifConnectivityProbe().export(netlist,out);
    }
}
