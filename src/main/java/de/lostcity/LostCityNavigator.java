package de.lostcity;

import com.google.gson.*;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.serializer.legacy.LegacyComponentSerializer;
import org.bukkit.*;
import org.bukkit.command.*;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.inventory.InventoryClickEvent;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.*;
import org.bukkit.inventory.meta.CompassMeta;
import org.bukkit.inventory.meta.ItemMeta;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scoreboard.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Lost City Navigator: private destinations, compass, right sidebar and permission-gated safe teleport. */
public final class LostCityNavigator extends JavaPlugin implements Listener, CommandExecutor, TabCompleter {
    private record Destination(String id, String name, String dimension, int x, int y, int z, int chests, int score, boolean isPublic) {}
    private final List<Destination> locations = new ArrayList<>();
    private final Map<UUID, Destination> active = new HashMap<>();
    private final Map<UUID, Integer> pages = new HashMap<>();
    private final Set<UUID> sidebarHidden = new HashSet<>();
    private final Map<UUID, Scoreboard> sideboards = new HashMap<>();
    private NamespacedKey compassKey;
    private static final String MENU = "Lost City - Ziele";
    private static final int PER_PAGE = 36;
    private static final LegacyComponentSerializer LEGACY = LegacyComponentSerializer.legacySection();

    @Override public void onEnable() {
        compassKey = new NamespacedKey(this, "navigator");
        if (!getDataFolder().exists() && !getDataFolder().mkdirs()) getLogger().warning("Could not create plugin data folder");
        saveDefaultConfig();
        getServer().getPluginManager().registerEvents(this, this);
        PluginCommand command = Objects.requireNonNull(getCommand("lostcity"));
        command.setExecutor(this); command.setTabCompleter(this);
        reloadDestinations();
        getServer().getScheduler().runTaskTimer(this, this::refreshPlayers, 20L, 40L);
        getLogger().info("Navigator enabled: /lostcity list, /lostcity map, /lostcity tp");
    }
    @Override public void onDisable() {
        for (Player p : Bukkit.getOnlinePlayers()) clearSidebar(p);
        sideboards.clear(); active.clear(); pages.clear(); sidebarHidden.clear();
    }
    private void refreshPlayers() {
        for (Player p : Bukkit.getOnlinePlayers()) {
            if (!p.hasPermission("lostcity.use")) { clearSidebar(p); continue; }
            Destination d = active.get(p.getUniqueId());
            if (d != null && !canSee(p,d)) { active.remove(p.getUniqueId()); d = null; }
            if (d != null) {
                World world = getWorld(d.dimension());
                if (world == null || !p.getWorld().equals(world))
                    p.sendActionBar(LEGACY.deserialize("§e"+d.name()+" §7- andere Dimension"));
                else {
                    long dist = Math.round(p.getLocation().distance(new Location(world,d.x(),p.getLocation().getY(),d.z())));
                    p.sendActionBar(LEGACY.deserialize("§6"+d.name()+" §f- §e"+dist+" Blöcke"+(dist<15?" §a✓ Angekommen!":"")));
                }
                // Only navigator compasses are updated.
                for (ItemStack item : p.getInventory().getContents()) if (isNavigator(item)) configureCompass(item,d);
            }
            if (!sidebarHidden.contains(p.getUniqueId()) && getConfig().getBoolean("sidebar.enabled-by-default",true)) renderSidebar(p);
            else clearSidebar(p);
        }
    }
    private World getWorld(String dimension) {
        String configured = getConfig().getString("worlds."+dimension, "");
        if (configured != null && !configured.isBlank()) return Bukkit.getWorld(configured);
        World.Environment environment = switch (dimension) {
            case "nether" -> World.Environment.NETHER;
            case "end" -> World.Environment.THE_END;
            default -> World.Environment.NORMAL;
        };
        for (World w : Bukkit.getWorlds()) if (w.getEnvironment() == environment) return w;
        return null;
    }
    private boolean canSee(Player p, Destination d) { return p.hasPermission("lostcity.admin") || d.isPublic(); }
    private List<Destination> visible(Player p) { return locations.stream().filter(d -> canSee(p,d)).toList(); }
    private void reloadDestinations() {
        locations.clear(); active.clear(); pages.clear();
        for (Player p : Bukkit.getOnlinePlayers()) {
            if (MENU.equals(p.getOpenInventory().getTitle())) p.closeInventory();
            for (ItemStack item : p.getInventory().getContents()) if (isNavigator(item) && item.getItemMeta() instanceof CompassMeta meta) {
                meta.setLodestone(null);item.setItemMeta(meta);
            }
        }
        File file = new File(getDataFolder(), "locations.json");
        if (!file.isFile()) { getLogger().info("Export locations.json to plugins/LostCityNavigator/"); return; }
        try (Reader reader = new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            if (!"lostcityfinder".equals(root.get("format").getAsString()) || root.get("version").getAsInt()!=1)
                throw new IllegalArgumentException("Unsupported locations format");
            for (JsonElement e : root.getAsJsonArray("locations")) {
                JsonObject o = e.getAsJsonObject();
                locations.add(new Destination(o.get("id").getAsString(),o.get("name").getAsString(),o.get("dimension").getAsString(),
                    o.get("x").getAsInt(),o.get("y").getAsInt(),o.get("z").getAsInt(),o.get("chests").getAsInt(),
                    o.has("score")?o.get("score").getAsInt():0,o.has("public")&&o.get("public").getAsBoolean()));
            }
            getLogger().info("Loaded "+locations.size()+" destinations; nonpublic remain admin-only");
        } catch (Exception e) { getLogger().severe("Invalid locations.json: "+e.getMessage()); }
    }
    private boolean isNavigator(ItemStack item) {
        return item!=null && item.getType()==Material.COMPASS && item.hasItemMeta() &&
            item.getItemMeta().getPersistentDataContainer().has(compassKey,PersistentDataType.BYTE);
    }
    private void configureCompass(ItemStack item, Destination d) {
        if (!(item.getItemMeta() instanceof CompassMeta meta)) return;
        World w=getWorld(d.dimension());if(w==null)return;
        meta.setLodestone(new Location(w,d.x(),d.y(),d.z())); meta.setLodestoneTracked(false);
        meta.setDisplayName("§6Lost City Navigator");
        meta.setLore(List.of("§7Ziel: "+d.name(),"§7Rechtsklick: Ziele auswählen"));
        item.setItemMeta(meta);
    }
    private ItemStack newCompass() {
        ItemStack item=new ItemStack(Material.COMPASS);
        CompassMeta meta=(CompassMeta)item.getItemMeta();
        meta.setDisplayName("§6Lost City Navigator");meta.setLore(List.of("§7Rechtsklick: Ziele auswählen"));
        meta.getPersistentDataContainer().set(compassKey,PersistentDataType.BYTE,(byte)1);
        item.setItemMeta(meta);return item;
    }
    private ItemStack icon(Material material, String name, String... lore) {
        ItemStack item=new ItemStack(material);ItemMeta meta=item.getItemMeta();
        meta.setDisplayName(name);meta.setLore(Arrays.asList(lore));item.setItemMeta(meta);return item;
    }
    private void openMenu(Player p) { openMenu(p,pages.getOrDefault(p.getUniqueId(),0)); }
    private void openMenu(Player p, int page) {
        List<Destination> all=visible(p);
        int maxPage=Math.max(0,(all.size()-1)/PER_PAGE);
        page=Math.max(0,Math.min(page,maxPage));pages.put(p.getUniqueId(),page);
        Inventory inv=Bukkit.createInventory(null,54,MENU);
        Destination selected=active.get(p.getUniqueId());
        inv.setItem(0,icon(Material.COMPASS,"§6Aktuelles Ziel",selected==null?"§7Noch kein Ziel gewählt":"§e"+selected.name()));
        inv.setItem(1,icon(Material.ENDER_PEARL,"§bZum Ziel teleportieren", "§7Nur mit Berechtigung lostcity.teleport", "§7Klicken zum Teleportieren"));
        inv.setItem(2,icon(Material.FILLED_MAP,"§aRechte Übersicht an/aus", "§7Klicken: Fundorte rechts anzeigen"));
        inv.setItem(3,icon(Material.ARROW,"§eVorheriges Ziel", "§7Vorherigen Fundort wählen"));
        inv.setItem(4,icon(Material.ARROW,"§eNächstes Ziel", "§7Nächsten Fundort wählen"));
        inv.setItem(7,icon(Material.PAPER,"§eVorherige Seite", "§7Seite "+(page+1)+" / "+(maxPage+1)));
        inv.setItem(8,icon(Material.PAPER,"§eNächste Seite", "§7Seite "+(page+1)+" / "+(maxPage+1)));
        for (int i=0;i<PER_PAGE && page*PER_PAGE+i<all.size();i++) {
            Destination d=all.get(page*PER_PAGE+i);
            boolean chosen=d.equals(selected);
            inv.setItem(9+i,icon(chosen?Material.EMERALD:Material.CHEST,"§e"+d.name()+(chosen?" §a✓":""),
                "§7"+d.dimension()+"  X:"+d.x()+" Z:"+d.z(), "§7"+d.chests()+" Truhenblöcke", "§7Score: "+d.score()+"/100",
                "§aKlicken: Navigationsziel setzen"));
        }
        inv.setItem(49,icon(Material.BOOK,"§7Lost City Finder §8· §aby tobimachtdas", "§7youtube.com/@tobimachtdas"));
        p.openInventory(inv);
    }
    @EventHandler public void onClick(InventoryClickEvent event) {
        if (!MENU.equals(event.getView().getTitle()))return;
        event.setCancelled(true);
        if (!(event.getWhoClicked() instanceof Player p) || !p.hasPermission("lostcity.use"))return;
        int slot=event.getRawSlot();
        if(slot<0 || slot>=54)return;
        switch(slot) {
            case 1 -> {p.closeInventory();teleport(p);return;}
            case 2 -> {toggleSidebar(p);openMenu(p);return;}
            case 3 -> {shiftTarget(p,-1);openMenu(p);return;}
            case 4 -> {shiftTarget(p,1);openMenu(p);return;}
            case 7 -> {openMenu(p,pages.getOrDefault(p.getUniqueId(),0)-1);return;}
            case 8 -> {openMenu(p,pages.getOrDefault(p.getUniqueId(),0)+1);return;}
            default -> {}
        }
        if(slot<9 || slot>=45)return;
        List<Destination> available=visible(p);
        int index=pages.getOrDefault(p.getUniqueId(),0)*PER_PAGE+(slot-9);
        if(index>=available.size())return;
        setTarget(p,available.get(index));p.closeInventory();
    }
    private void setTarget(Player p,Destination d) {
        active.put(p.getUniqueId(),d);
        for (ItemStack item : p.getInventory().getContents())if(isNavigator(item))configureCompass(item,d);
        p.sendMessage("§aZiel gewählt: §e"+d.name()+" §7("+d.dimension()+") §a- /lostcity tp oder Kompass folgen");
        if(!sidebarHidden.contains(p.getUniqueId()))renderSidebar(p);
    }
    private void shiftTarget(Player p,int offset) {
        List<Destination> all=visible(p);
        if(all.isEmpty()){p.sendMessage("§eKeine freigegebenen Ziele vorhanden.");return;}
        Destination old=active.get(p.getUniqueId());int index=all.indexOf(old);
        int next=index<0?0:Math.floorMod(index+offset,all.size());setTarget(p,all.get(next));
    }
    private void toggleSidebar(Player p) {
        if(sidebarHidden.remove(p.getUniqueId())){renderSidebar(p);p.sendMessage("§aZielübersicht eingeblendet.");}
        else {sidebarHidden.add(p.getUniqueId());clearSidebar(p);p.sendMessage("§7Zielübersicht ausgeblendet.");}
    }
    private void clearSidebar(Player p) {
        Scoreboard board=sideboards.remove(p.getUniqueId());
        if(board!=null && p.getScoreboard()==board) {
            ScoreboardManager manager=Bukkit.getScoreboardManager();
            if(manager!=null)p.setScoreboard(manager.getMainScoreboard());
        }
    }
    private void renderSidebar(Player p) {
        ScoreboardManager manager=Bukkit.getScoreboardManager();if(manager==null)return;
        // Only replace our own scoreboard; avoid clobbering other plugins' scoreboards.
        Scoreboard ours=sideboards.get(p.getUniqueId());
        if(ours==null && p.getScoreboard()!=manager.getMainScoreboard())return;
        if(ours==null){ours=manager.getNewScoreboard();sideboards.put(p.getUniqueId(),ours);p.setScoreboard(ours);}
        Objective old=ours.getObjective("lostcity");if(old!=null)old.unregister();
        Objective obj=ours.registerNewObjective("lostcity",Criteria.DUMMY,Component.text("Lost City Navigator"));
        obj.setDisplaySlot(DisplaySlot.SIDEBAR);
        Destination target=active.get(p.getUniqueId());
        List<String> lines=new ArrayList<>();
        lines.add("§6§lLOST CITY FINDER");
        lines.add("§7by tobimachtdas");
        if(target==null)lines.add("§eKein Ziel gewählt");
        else {
            lines.add("§aZiel: §f"+trim(target.name(),18));
            if(!p.getWorld().equals(getWorld(target.dimension())))lines.add("§eDimension wechseln");
            else lines.add("§e"+Math.round(Math.hypot(p.getLocation().getX()-target.x(),p.getLocation().getZ()-target.z()))+" Blöcke");
            lines.add("§7X:"+target.x()+" Z:"+target.z());
        }
        lines.add("§8----------------");
        List<Destination> all=visible(p);
        World w=p.getWorld();
        all.stream().filter(d->getWorld(d.dimension())==w).sorted(Comparator.comparingDouble(d->Math.hypot(p.getLocation().getX()-d.x(),p.getLocation().getZ()-d.z())))
            .limit(5).forEach(d->lines.add("§7"+trim(d.name(),14)+" §f"+Math.round(Math.hypot(p.getLocation().getX()-d.x(),p.getLocation().getZ()-d.z()))));
        lines.add("§b/lostcity list");
        lines.add("§b/lostcity tp");
        // Unique entry per row using legacy formatting so duplicate names do not overwrite scores.
        for(int i=0;i<lines.size() && i<15;i++) {
            String entry=trim(lines.get(i),36)+ChatColor.values()[i].toString();
            obj.getScore(entry).setScore(lines.size()-i);
        }
    }
    private String trim(String text,int max){return text.length()>max?text.substring(0,max):text;}

    private void teleport(Player p) {
        if(!p.hasPermission("lostcity.teleport")){p.sendMessage("§cTeleport ist nur für berechtigte Spieler erlaubt.");return;}
        Destination d=active.get(p.getUniqueId());if(d==null){p.sendMessage("§eBitte erst ein Ziel im Navigator auswählen.");return;}
        if(!canSee(p,d)){p.sendMessage("§cDieses Ziel ist nicht freigegeben.");return;}
        World w=getWorld(d.dimension());if(w==null){p.sendMessage("§cZielwelt ist nicht geladen.");return;}
        if(!getConfig().getBoolean("teleport.enabled",true)){p.sendMessage("§cTeleportieren wurde deaktiviert.");return;}
        // Prefer an open-air surface near the chest, not the chest block itself.
        Location safe=null;
        for(int radius=0;radius<=12 && safe==null;radius+=3) {
            for(int dx=-radius;dx<=radius && safe==null;dx+=3)for(int dz=-radius;dz<=radius && safe==null;dz+=3) {
                int x=d.x()+dx,z=d.z()+dz;
                int groundY=w.getHighestBlockYAt(x,z);
                if(groundY>=w.getMaxHeight()-3 || groundY<w.getMinHeight()+1)continue;
                Material floor=w.getBlockAt(x,groundY,z).getType();
                Material feet=w.getBlockAt(x,groundY+1,z).getType();
                Material head=w.getBlockAt(x,groundY+2,z).getType();
                if(floor.isSolid() && !floor.name().contains("LEAVES") && !floor.name().contains("MAGMA") && !floor.name().contains("CACTUS") && feet.isAir() && head.isAir())
                    safe=new Location(w,x+.5,groundY+1,z+.5,p.getLocation().getYaw(),p.getLocation().getPitch());
            }
        }
        if(safe==null){p.sendMessage("§cKein sicherer Oberflächenpunkt gefunden. Bitte mit dem Kompass hinreisen.");return;}
        if(p.teleport(safe))p.sendMessage("§aTeleportiert in die Nähe von §e"+d.name()+"§a. Umgebung bitte prüfen.");
        else p.sendMessage("§cTeleport wurde abgebrochen.");
    }
    @EventHandler public void onUse(PlayerInteractEvent event) {
        if(!event.getAction().name().contains("RIGHT_CLICK") || !isNavigator(event.getItem()))return;
        event.setCancelled(true);
        if(event.getHand()!=EquipmentSlot.HAND || !event.getPlayer().hasPermission("lostcity.use"))return;
        openMenu(event.getPlayer());
    }
    @Override public boolean onCommand(CommandSender sender,Command command,String label,String[] args) {
        if(args.length>0 && args[0].equalsIgnoreCase("reload")) {
            if(!sender.hasPermission("lostcity.admin")){sender.sendMessage("§cKeine Berechtigung.");return true;}
            reloadDestinations();sender.sendMessage("§aFundorte neu geladen: "+locations.size());return true;
        }
        if(!(sender instanceof Player p)){sender.sendMessage("Only players can use this command.");return true;}
        if(!p.hasPermission("lostcity.use")){p.sendMessage("§cKeine Berechtigung.");return true;}
        if(args.length>0) switch(args[0].toLowerCase(Locale.ROOT)) {
            case "list","karte" -> {openMenu(p);return true;}
            case "tp","teleport" -> {teleport(p);return true;}
            case "map" -> {toggleSidebar(p);return true;}
            case "next" -> {shiftTarget(p,1);return true;}
            case "prev" -> {shiftTarget(p,-1);return true;}
            case "compass" -> {giveCompass(p);return true;}
            default -> {p.sendMessage("§e/lostcity [compass|list|map|next|prev|tp|reload]");return true;}
        }
        giveCompass(p);return true;
    }
    private void giveCompass(Player p){
        Map<Integer,ItemStack> leftovers=p.getInventory().addItem(newCompass());
        if(!leftovers.isEmpty())p.sendMessage("§cInventar voll. Bitte Platz schaffen.");
        else p.sendMessage("§aNavigator erhalten! Rechtsklick: Ziele · /lostcity map: rechte Übersicht.");
    }
    @Override public List<String> onTabComplete(CommandSender sender,Command cmd,String alias,String[] args) {
        if(args.length!=1)return List.of();
        List<String> options=new ArrayList<>(List.of("compass","list","map","next","prev","tp"));
        if(sender.hasPermission("lostcity.admin"))options.add("reload");
        return options.stream().filter(s->s.startsWith(args[0].toLowerCase(Locale.ROOT))).toList();
    }
}
