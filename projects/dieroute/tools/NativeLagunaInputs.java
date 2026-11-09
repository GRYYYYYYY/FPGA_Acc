import com.xilinx.rapidwright.device.*;
import com.xilinx.rapidwright.util.Utils;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Export the SDK's Laguna input topology directly; no design routing. */
public final class NativeLagunaInputs {
    private static void writeKeys(Path path,Collection<Long> keys)throws IOException {
        try(DataOutputStream file=new DataOutputStream(new BufferedOutputStream(Files.newOutputStream(path,StandardOpenOption.CREATE_NEW)))){
            for(long key:keys){file.writeInt(Integer.reverseBytes((int)(key>>>32)));file.writeInt(Integer.reverseBytes((int)key));}
        }
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("device new-output-directory");
        Path out=Path.of(args[1]);Files.createDirectory(out);Device dev=Objects.requireNonNull(Device.getDevice(args[0]));
        TreeSet<Long> inputs=new TreeSet<>(),sll=new TreeSet<>();int visited=0;
        for(Tile tile:dev.getAllTiles())if(Utils.getLagunaTileTypes().contains(tile.getTileTypeEnum()))
            for(int wire=0;wire<tile.getWireCount();++wire)if(tile.getWireName(wire).startsWith("UBUMP")){
                Node node=Node.getNode(tile,wire);if(node==null)throw new IllegalStateException("null UBUMP");++visited;
                sll.add(((long)node.getTile().getUniqueAddress()<<32)|(node.getWireIndex()&0xffffffffL));
                for(Node first:node.getAllUphillNodes())for(Node second:first.getAllUphillNodes()){
                    if(!Utils.isInterConnect(second.getTile().getTileTypeEnum()))continue;
                    if(second.getIntentCode()!=IntentCode.NODE_PINFEED)throw new IllegalStateException("unexpected Laguna input intent");
                    inputs.add(((long)second.getTile().getUniqueAddress()<<32)|(second.getWireIndex()&0xffffffffL));
                }
            }
        writeKeys(out.resolve("inputs.bin"),inputs);writeKeys(out.resolve("ubump_nodes.bin"),sll);
        String report="{\"schema\":\"dieroute.native_laguna_inputs.v2\",\"ubump_wire_visits\":"+visited+",\"native_ubump_nodes\":"+sll.size()+",\"native_input_nodes\":"+inputs.size()+",\"scope\":\"SDK topology export includes single-SLR device-edge UBUMPs; not a crossing count, design legality or timing\"}\n";
        Files.writeString(out.resolve("audit.json"),report,StandardOpenOption.CREATE_NEW);System.out.print(report);
    }
}
