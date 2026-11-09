import com.xilinx.rapidwright.edif.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Diagnostic hierarchy inventory; encrypted cell bodies are not elaborated.
 * Counts/properties do not establish full logical or routing equivalence.
 */
public final class EdifHierarchyProbe {
    private static void row(BufferedWriter out,Object... values) throws IOException {
        for(int i=0;i<values.length;i++) {
            if(i>0)out.write(',');
            out.write("\""+Objects.toString(values[i],"").replace("\"","\"\"")+"\"");
        }
        out.newLine();
    }
    private static String properties(EDIFCellInst inst) throws Exception {
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        for(Map.Entry<String,EDIFPropertyValue> e:new TreeMap<>(inst.getPropertiesMap()).entrySet()) {
            EDIFPropertyValue v=e.getValue();
            String s=e.getKey()+"\t"+v.getType()+"\t"+v.getValue()+"\t"+v.getOwner()+"\n";
            digest.update(s.getBytes(StandardCharsets.UTF_8));
        }
        StringBuilder hex=new StringBuilder();
        for(byte b:digest.digest())hex.append(String.format("%02x",b & 255));
        return hex.toString();
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("input.edf new-output.csv");
        Path output=Path.of(args[1]);
        if(Files.exists(output))throw new IllegalArgumentException("refusing existing output");
        EDIFNetlist netlist=EDIFTools.readEdifFile(Path.of(args[0]),8);
        List<EDIFHierCellInst> cells=netlist.getAllDescendants("",null,false);
        cells.sort(Comparator.comparing(EDIFHierCellInst::getFullHierarchicalInstName));
        long nets=netlist.getTopCell().getNets().size();
        try(BufferedWriter out=Files.newBufferedWriter(output,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            row(out,"instance","library","type","primitive","children","nets","ports","instance_properties_sha256");
            for(EDIFHierCellInst cell:cells) {
                EDIFCell type=cell.getInst().getCellType();
                row(out,cell.getFullHierarchicalInstName(),type.getLibrary().getName(),type.getName(),
                    type.isPrimitive(),type.getCellInsts().size(),type.getNets().size(),type.getPorts().size(),
                    properties(cell.getInst()));
                nets+=type.getNets().size();
            }
        }
        System.out.println("hierarchical_instances="+cells.size()+" hierarchical_nets="+nets);
        System.out.println("scope=EDIF_hierarchy_diagnostic_without_encrypted_cell_elaboration");
    }
}
