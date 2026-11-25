package de.lostcity;

import org.bukkit.Bukkit;
import org.bukkit.Material;
import org.bukkit.World;
import org.bukkit.Chunk;
import org.bukkit.block.BlockState;
import org.bukkit.command.CommandSender;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitTask;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;

/**
 * Deliberately conservative main-thread coordinator. Only generated chunks are inspected;
 * never call Bukkit block APIs asynchronously and never generate new world terrain.
 */
final class ChunkCityScanner {
    record Finding(String worldName, String dimension, int x, int y, int z, int chests, int score) {}
    private record ChestPoint(int x, int y, int z) {}
    private final JavaPlugin plugin;
    private final Consumer<List<Finding>> onComplete;
    private Run run;

    ChunkCityScanner(JavaPlugin plugin, Consumer<List<Finding>> onComplete) {
        this.plugin = plugin;
        this.onComplete = onComplete;
    }

    boolean isRunning() { return run != null; }

    void begin(CommandSender sender, World world, int radius) {
        if (run != null) {
            sender.sendMessage("§eEs läuft bereits ein Scan. /lostcity scan status");
            return;
        }
        int max = plugin.getConfig().getInt("scanner.max-radius", 8192);
        if (radius < 128 || radius > max) {
            sender.sendMessage("§cSuchradius muss zwischen 128 und " + max + " liegen.");
            return;
        }
        int centerX = sender instanceof org.bukkit.entity.Player p ? p.getLocation().getBlockX() : 0;
        int centerZ = sender instanceof org.bukkit.entity.Player p ? p.getLocation().getBlockZ() : 0;
        int minX = Math.floorDiv(centerX - radius, 16);
        int maxX = Math.floorDiv(centerX + radius, 16);
        int minZ = Math.floorDiv(centerZ - radius, 16);
        int maxZ = Math.floorDiv(centerZ + radius, 16);
        long total = (long)(maxX - minX + 1) * (maxZ - minZ + 1);
        if (total > plugin.getConfig().getLong("scanner.max-chunk-positions", 1100000L)) {
            sender.sendMessage("§cZu großes Gebiet für den konfigurierten Scan-Limit.");
            return;
        }
        Run task = new Run(sender, world, minX, maxX, minZ, maxZ, total);
        run = task;
        task.timer = Bukkit.getScheduler().runTaskTimer(plugin, () -> tick(task), 1L, 1L);
        sender.sendMessage("§aScanner gestartet: §e" + world.getName() + "§a, Radius §e" + radius +
            "§a Blöcke (" + total + " Chunkpositionen). Es werden keine neuen Chunks generiert.");
        sender.sendMessage("§7/lostcity scan status | /lostcity scan stop");
    }

    void status(CommandSender sender) {
        Run r = run;
        if (r == null) { sender.sendMessage("§eKein Scan aktiv."); return; }
        double pct = r.total == 0 ? 100 : 100.0 * (r.processed + r.inFlight) / r.total;
        sender.sendMessage(String.format(Locale.ROOT,
            "§aScan: §e%s §7%.1f%% §8| §7%d/%d geprüft §8| §7%d geladene Chunks §8| §7%d Truhenblöcke §8| §7%d ausstehend",
            r.world.getName(), pct, r.processed, r.total, r.loaded, r.points.size(), r.inFlight));
    }

    void stop(CommandSender sender) {
        Run r = run;
        if (r == null) { sender.sendMessage("§eKein Scan aktiv."); return; }
        if (r.timer != null) r.timer.cancel();
        run = null;
        // In-flight callbacks are intentionally ignored; no partial results committed.
        sender.sendMessage("§eScan abgebrochen. Es wurden keine Teilfunde gespeichert.");
    }

    void shutdown() {
        if (run != null && run.timer != null) run.timer.cancel();
        run = null;
    }

    private void tick(Run r) {
        if (run != r) return;
        int batch = Math.max(1, Math.min(32, plugin.getConfig().getInt("scanner.checks-per-tick", 4)));
        int parallel = Math.max(1, Math.min(8, plugin.getConfig().getInt("scanner.max-in-flight", 2)));
        for (int n = 0; n < batch && r.hasNext() && r.inFlight < parallel; n++) {
            int cx = r.nextX, cz = r.nextZ;
            r.advance();
            // isChunkGenerated is a Paper/Bukkit world query performed only on the main thread.
            if (!r.world.isChunkGenerated(cx, cz)) { r.processed++; continue; }
            boolean wasLoaded = r.world.isChunkLoaded(cx, cz);
            r.inFlight++;
            CompletableFuture<Chunk> future;
            try {
                future = r.world.getChunkAtAsync(cx, cz, false);
            } catch (Exception exception) {
                r.inFlight--; r.processed++; r.errors++;
                continue;
            }
            future.whenComplete((chunk, error) -> Bukkit.getScheduler().runTask(plugin, () -> {
                if (run != r) return;
                r.inFlight--;
                r.processed++;
                if (error != null || chunk == null) { r.errors++; return; }
                try {
                    r.loaded++;
                    for (BlockState state : chunk.getTileEntities()) {
                        Material type = state.getType();
                        if (type == Material.CHEST || type == Material.TRAPPED_CHEST) {
                            if (r.points.size() < 300000)
                                r.points.add(new ChestPoint(state.getX(), state.getY(), state.getZ()));
                            else r.truncated = true;
                        }
                    }
                } catch (Exception ex) {
                    r.errors++;
                }
                // Never unload chunks previously loaded by a player or another plugin.
                // For newly acquired chunks, let the server's normal chunk lifecycle manage unloading.
            }));
        }
        if (!r.hasNext() && r.inFlight == 0) finish(r);
    }

    private void finish(Run r) {
        if (run != r) return;
        if (r.timer != null) r.timer.cancel();
        run = null;
        int clusterRadius = Math.max(8, Math.min(128, plugin.getConfig().getInt("scanner.cluster-radius", 48)));
        int minimum = Math.max(1, plugin.getConfig().getInt("scanner.min-chests", 3));
        int minDistance = Math.max(0, plugin.getConfig().getInt("scanner.min-city-distance", 1024));
        List<Finding> findings = cluster(r.points, r.world, clusterRadius, minimum, minDistance);
        try {
            onComplete.accept(findings);
            r.sender.sendMessage("§aScan beendet! §e" + findings.size() + "§a mögliche Fundorte gespeichert. §7/lostcity list");
        } catch (Exception ex) {
            plugin.getLogger().severe("Could not save scan results: " + ex.getMessage());
            r.sender.sendMessage("§cScan abgeschlossen, aber Ergebnisse konnten nicht gespeichert werden.");
        }
        if (r.errors > 0) r.sender.sendMessage("§eHinweis: " + r.errors + " Chunks konnten nicht ausgewertet werden.");
        if (r.truncated) r.sender.sendMessage("§cTruhenlimit erreicht; die Ergebnisse sind möglicherweise unvollständig.");
    }

    private static List<Finding> cluster(List<ChestPoint> points, World world,
                                         int radius, int minCount, int minDistance) {
        if (points.isEmpty()) return List.of();
        int n = points.size();
        int[] parent = new int[n], size = new int[n];
        Map<Long, List<Integer>> cells = new HashMap<>();
        for (int i = 0; i < n; i++) { parent[i] = i; size[i] = 1; }
        long radius2 = (long)radius * radius;
        for (int i = 0; i < n; i++) {
            ChestPoint point = points.get(i);
            int gx = Math.floorDiv(point.x(), radius), gz = Math.floorDiv(point.z(), radius);
            for (int dx=-1; dx<=1; dx++) for (int dz=-1; dz<=1; dz++) {
                List<Integer> near = cells.get(key(gx + dx, gz + dz));
                if (near == null) continue;
                for (int j : near) {
                    ChestPoint other = points.get(j);
                    long ddx=(long)point.x()-other.x(), ddz=(long)point.z()-other.z();
                    if (ddx*ddx + ddz*ddz <= radius2) union(parent,size,i,j);
                }
            }
            cells.computeIfAbsent(key(gx,gz), ignored -> new ArrayList<>()).add(i);
        }
        Map<Integer, Group> groups = new HashMap<>();
        for (int i=0;i<n;i++) {
            Group g=groups.computeIfAbsent(root(parent,i),ignored->new Group());
            ChestPoint p=points.get(i);
            g.count++;g.sumX+=p.x();g.sumY+=p.y();g.sumZ+=p.z();
        }
        String dimension = switch (world.getEnvironment()) {
            case NETHER -> "nether";
            case THE_END -> "end";
            default -> "overworld";
        };
        List<Finding> candidates=new ArrayList<>();
        for (Group g:groups.values()) {
            if (g.count < minCount) continue;
            int x=(int)(g.sumX/g.count), y=(int)(g.sumY/g.count), z=(int)(g.sumZ/g.count);
            int score=Math.min(100, 10 + g.count * 3);
            candidates.add(new Finding(world.getName(),dimension,x,y,z,g.count,score));
        }
        candidates.sort(Comparator.comparingInt(Finding::chests).reversed());
        List<Finding> result=new ArrayList<>();
        for (Finding next:candidates) {
            boolean nearby=false;
            for (Finding kept:result) {
                long dx=(long)next.x()-kept.x(),dz=(long)next.z()-kept.z();
                if (dx*dx+dz*dz < (long)minDistance*minDistance) { nearby=true;break; }
            }
            if (!nearby) result.add(next);
        }
        return result;
    }

    private static long key(int x, int z) { return ((long)x << 32) ^ (z & 0xffffffffL); }
    private static int root(int[] p,int x){while(p[x]!=x){p[x]=p[p[x]];x=p[x];}return x;}
    private static void union(int[] p,int[] s,int a,int b){
        a=root(p,a);b=root(p,b);if(a==b)return;
        if(s[a]<s[b]){int tmp=a;a=b;b=tmp;}
        p[b]=a;s[a]+=s[b];
    }
    private static final class Group { long sumX,sumY,sumZ; int count; }
    private static final class Run {
        final CommandSender sender;
        final World world;
        final int minX,maxX,minZ,maxZ;
        final long total;
        final List<ChestPoint> points=new ArrayList<>();
        BukkitTask timer;
        int nextX,nextZ,inFlight,loaded,errors;
        long processed;
        boolean truncated;
        Run(CommandSender sender,World world,int minX,int maxX,int minZ,int maxZ,long total){
            this.sender=sender;this.world=world;this.minX=minX;this.maxX=maxX;this.minZ=minZ;this.maxZ=maxZ;
            this.nextX=minX;this.nextZ=minZ;this.total=total;
        }
        boolean hasNext(){return nextZ<=maxZ;}
        void advance(){if(++nextX>maxX){nextX=minX;nextZ++;}}
    }
}
