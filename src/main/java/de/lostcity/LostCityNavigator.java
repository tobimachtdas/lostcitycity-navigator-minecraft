package de.lostcity;

import com.google.gson.*;
import org.bukkit.*;
import net.md_5.bungee.api.ChatMessageType;
import net.md_5.bungee.api.chat.TextComponent;
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
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public final class LostCityNavigator extends JavaPlugin implements Listener, CommandExecutor {
    private final List<Destination> locations = new ArrayList<>();
    private final Map<UUID, Destination> active = new HashMap<>();
    private NamespacedKey compassKey;
    private static final String MENU = "Lost City - Ziele";

    private record Destination(String id, String name, String dimension, int x, int y, int z, int chests, int score, boolean isPublic) {}
    @Override public void onEnable() {
        compassKey = new NamespacedKey((org.bukkit.plugin.Plugin) this, "navigator");
        if (!getDataFolder().exists() && !getDataFolder().mkdirs()) {
            getLogger().warning("Could not create plugin data directory: " + getDataFolder());
        }
        getServer().getPluginManager().registerEvents(this, (org.bukkit.plugin.Plugin) this);
        Objects.requireNonNull(getCommand("lostcity")).setExecutor(this);
        reloadDestinations();
        getServer().getScheduler().runTaskTimer((org.bukkit.plugin.Plugin) this, () -> {
            for (Player player : Bukkit.getOnlinePlayers()) {
                Destination d = active.get(player.getUniqueId());
                if (d == null) continue;
                if (!player.hasPermission("lostcity.use") || (!d.isPublic && !player.hasPermission("lostcity.admin"))) { active.remove(player.getUniqueId()); continue; }
                World world = getWorld(d.dimension);
                if (world == null || !player.getWorld().equals(world)) {
                    actionBar(player, "§eZiel: " + d.name + " §7- andere Dimension"); continue;
                }
                double dist = Math.hypot(player.getLocation().getX() - d.x, player.getLocation().getZ() - d.z);
                actionBar(player, "§6" + d.name + " §f- §e" + (int)Math.round(dist) + " Blöcke" + (dist < 15 ? " §a✓ Angekommen!" : ""));
                // Refresh any owned navigator compass so its needle follows the selected target.
                for (ItemStack item : player.getInventory().getContents()) {
                    if (isNavigator(item)) configureCompass(item, d);
                }
            }
        }, 20L, 40L);
    }
    private void actionBar(Player p, String text) { p.spigot().sendMessage(ChatMessageType.ACTION_BAR, TextComponent.fromLegacyText(text)); }
    private World getWorld(String dimension) {
        for (World world : Bukkit.getWorlds()) {
            switch (dimension) {
                case "overworld": if (world.getEnvironment() == World.Environment.NORMAL) return world; break;
                case "nether": if (world.getEnvironment() == World.Environment.NETHER) return world; break;
                case "end": if (world.getEnvironment() == World.Environment.THE_END) return world; break;
            }
        }
        return null;
    }
    private void reloadDestinations() {
        locations.clear();
        active.clear();
        for (Player p : Bukkit.getOnlinePlayers()) { if (MENU.equals(p.getOpenInventory().getTitle())) p.closeInventory(); for (ItemStack item : p.getInventory().getContents()) if (isNavigator(item)) { CompassMeta meta = (CompassMeta)item.getItemMeta(); meta.setLodestone(null); item.setItemMeta(meta); } }
        File file = new File(getDataFolder(), "locations.json");
        if (!file.isFile()) {getLogger().info("Place exported locations.json in plugins/LostCityNavigator/");return;}
        try (Reader reader = new InputStreamReader(new FileInputStream(file), StandardCharsets.UTF_8)) {
            JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
            if (!"lostcityfinder".equals(root.get("format").getAsString()) || root.get("version").getAsInt() != 1) throw new IllegalArgumentException("Unknown file format");
            for (JsonElement element : root.getAsJsonArray("locations")) {
                JsonObject o = element.getAsJsonObject();
                // Never expose imported locations to ordinary players until explicitly approved.
                boolean isPublic = o.has("public") && o.get("public").getAsBoolean();
                locations.add(new Destination(o.get("id").getAsString(),o.get("name").getAsString(),o.get("dimension").getAsString(),o.get("x").getAsInt(),o.get("y").getAsInt(),o.get("z").getAsInt(),o.get("chests").getAsInt(),o.has("score") ? o.get("score").getAsInt() : 0,isPublic));
            }
            getLogger().info("Loaded " + locations.size() + " locations (private ones remain admin-only)");
        } catch (Exception e) {getLogger().severe("Invalid locations.json: " + e.getMessage());}
    }
    private boolean isNavigator(ItemStack item) {
        if (item == null || item.getType() != Material.COMPASS || !item.hasItemMeta()) return false;
        return item.getItemMeta().getPersistentDataContainer().has(compassKey, PersistentDataType.BYTE);
    }
    private void configureCompass(ItemStack item, Destination d) {
        ItemMeta meta = item.getItemMeta();
        if (!(meta instanceof CompassMeta compass)) return;
        World world = getWorld(d.dimension);
        if (world == null)return;
        compass.setLodestone(new Location(world,d.x,d.y,d.z));
        compass.setLodestoneTracked(false);
        compass.setDisplayName("§6🧭 Lost City Navigator");
        item.setItemMeta(compass);
    }
    private ItemStack newCompass() {
        ItemStack item = new ItemStack(Material.COMPASS);
        CompassMeta meta = (CompassMeta)item.getItemMeta();
        meta.setDisplayName("§6Lost City Navigator");
        meta.setLore(List.of("§7Rechtsklick: Ziele auswählen"));
        meta.getPersistentDataContainer().set(compassKey,PersistentDataType.BYTE,(byte)1);
        item.setItemMeta(meta);
        return item;
    }
    private List<Destination> visible(Player p) {
        if (p.hasPermission("lostcity.admin")) return locations;
        return locations.stream().filter(Destination::isPublic).toList();
    }
    private void openMenu(Player p) {
        List<Destination> shown = visible(p);
        Inventory inv = Bukkit.createInventory(null, 54, MENU);
        for (int i=0;i<Math.min(54,shown.size());i++) {
            Destination d = shown.get(i);
            ItemStack icon = new ItemStack(Material.CHEST);
            ItemMeta meta = icon.getItemMeta();meta.setDisplayName("§e"+d.name);
            meta.setLore(List.of("§7"+d.dimension,"§7"+d.chests+" Truhenblöcke", "§7Erkennung: "+d.score+"/100","§aKlicken zum Navigieren"));
            icon.setItemMeta(meta);inv.setItem(i,icon);
        }
        p.openInventory(inv);
    }
    @EventHandler public void onClick(InventoryClickEvent event) {
        if (!MENU.equals(event.getView().getTitle()))return;
        event.setCancelled(true);
        if (!(event.getWhoClicked() instanceof Player p) || !p.hasPermission("lostcity.use"))return;
        int slot=event.getRawSlot();
        List<Destination> shown = visible(p);
        if (slot<0 || slot>=Math.min(54,shown.size()))return;
        Destination d = shown.get(slot);
        active.put(p.getUniqueId(),d);
        for (ItemStack item : p.getInventory().getContents())if (isNavigator(item))configureCompass(item,d);
        p.closeInventory();p.sendMessage("§aZiel gewählt: §e"+d.name+" §7("+d.dimension+")");
    }
    @EventHandler public void onUse(PlayerInteractEvent event) {
        if (!event.getAction().name().contains("RIGHT_CLICK"))return;
        if (!isNavigator(event.getItem()))return;
        event.setCancelled(true);
        if (event.getHand()!=org.bukkit.inventory.EquipmentSlot.HAND)return;
        if (!event.getPlayer().hasPermission("lostcity.use"))return;
        openMenu(event.getPlayer());
    }
    @Override public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        if (args.length>0 && args[0].equalsIgnoreCase("reload")) {
            if (!sender.hasPermission("lostcity.admin")){sender.sendMessage("§cKeine Berechtigung.");return true;}
            reloadDestinations();sender.sendMessage("§aFundorte neu geladen.");return true;
        }
        if (!(sender instanceof Player p)){sender.sendMessage("Only players can use this command.");return true;}
        if (!p.hasPermission("lostcity.use")){p.sendMessage("§cKeine Berechtigung.");return true;}
        if (args.length>0 && args[0].equalsIgnoreCase("list")){openMenu(p);return true;}
        p.getInventory().addItem(newCompass());p.sendMessage("§aNavigator erhalten! Rechtsklick zum Auswählen.");return true;
    }
}
