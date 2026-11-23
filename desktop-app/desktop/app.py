import webbrowser
import threading
import time
import multiprocessing
import math
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from storage import cached_scan, reviews, review
from smart import discover, render, confidence, spaced_locations
from scanner import cluster, export


CREATOR = 'tobimachtdas'
CREATOR_URL = 'https://www.youtube.com/@tobimachtdas'

BG = '#081612'
PANEL = '#0d211b'
PANEL_ALT = '#102821'
CARD = '#112f27'
CARD_ALT = '#14382f'
OUTLINE = '#245245'
TEXT = '#edf7f1'
MUTED = '#a8c1b6'
ACCENT = '#4fd084'
ACCENT_2 = '#73e39d'
WARN = '#efb64b'
HIGH = '#26d5a0'
SOFT = '#193f35'
INPUT_BG = '#0b1d18'
INPUT_FG = '#eff8f3'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Lost City Finder · Minecraft Java · by tobimachtdas')
        self.geometry('1450x900')
        self.minsize(1180, 780)
        self.configure(bg=BG)
        self.option_add('*Font', '{Segoe UI} 10')
        self._build_styles()

        self.world = None
        self.force_scan = tk.BooleanVar(value=False)
        self.review_label = tk.StringVar(value='Ungeprüft')
        self.hide_false = tk.BooleanVar(value=False)
        self.all_locations = []
        self.entities = []
        self.chunks = {}
        self.locations = []
        self.stats = {}
        self.zoom = 1.0
        self.pan = (0, 0)
        self.drag = None

        self.dim = tk.StringVar(value='overworld')
        self.radius = tk.IntVar(value=32)
        self.city_distance = tk.StringVar(value="2048")
        self.minimum = tk.IntVar(value=4)
        self.status = tk.StringVar(value='Wähle eine Minecraft-Welt oder Server-Backup aus.')

        self.mode = tk.StringVar(value='Städte')
        self.min_score = tk.IntVar(value=60)
        self.chest_filter = tk.IntVar(value=0)
        self.heat = tk.BooleanVar(value=False)
        self.preview_enabled = tk.BooleanVar(value=True)
        self.preview_cache = {}
        self.preview_pending = set()
        self.preview_image = None
        self.world_epoch = 0
        self.scanning = False
        self.scan_current = 0
        self.scan_total = 0
        self.scan_file = ''
        self.scan_percent = tk.IntVar(value=0)
        self.scan_started = 0.0

        self.summary = tk.StringVar(value='Noch keine Welt analysiert')
        self.stat_found = tk.StringVar(value='0 Fundorte')
        self.stat_high = tk.StringVar(value='0 sehr hohe Scores')
        self.stat_chunks = tk.StringVar(value='0 Chunks')
        self.detail_title = tk.StringVar(value='Kein Fundort ausgewählt')
        self.detail_score = tk.StringVar(value='Score: –')
        self.detail_meta1 = tk.StringVar(value='Truhen: –   |   Koordinaten: –')
        self.detail_meta2 = tk.StringVar(value='Dimension: –   |   Strukturen: –')
        self.detail_hint = tk.StringVar(value='Wähle links oder auf der Karte einen Fundort aus. Score = Erkennungshinweis, keine echte Wahrscheinlichkeit.')
        self.footer_right = tk.StringVar(value='0 %')

        self._map_job = None
        self._dragging = False
        self._bounds = {}
        self._levels = {}
        self._scaled = {}
        self._tile_images = []
        self.center = None
        self._build_ui()
        self.redraw()

    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Main.TButton', background=CARD_ALT, foreground=TEXT, borderwidth=1, relief='flat', padding=(12, 10))
        style.map('Main.TButton', background=[('active', '#1a463a')], foreground=[('disabled', MUTED)])
        style.configure('Accent.TButton', background=ACCENT, foreground='#073a20', borderwidth=0, padding=(14, 12), font=('Segoe UI', 11, 'bold'))
        style.map('Accent.TButton', background=[('active', ACCENT_2), ('disabled', '#5f8270')], foreground=[('disabled', '#173a2a')])
        style.configure('Ghost.TButton', background=PANEL_ALT, foreground=TEXT, borderwidth=1, relief='flat', padding=(10, 10))
        style.map('Ghost.TButton', background=[('active', '#1a463a')])
        style.configure('Small.TButton', background=PANEL_ALT, foreground=TEXT, borderwidth=1, relief='flat', padding=(8, 7))
        style.map('Small.TButton', background=[('active', '#1a463a')])
        style.configure('TCombobox', fieldbackground=INPUT_BG, background=INPUT_BG, foreground=INPUT_FG, arrowcolor=TEXT, bordercolor=OUTLINE, lightcolor=OUTLINE, darkcolor=OUTLINE, padding=5)
        style.map('TCombobox', fieldbackground=[('readonly', INPUT_BG)], foreground=[('readonly', INPUT_FG)])
        style.configure('TSpinbox', fieldbackground=INPUT_BG, background=INPUT_BG, foreground=INPUT_FG, arrowcolor=TEXT, bordercolor=OUTLINE, lightcolor=OUTLINE, darkcolor=OUTLINE, padding=5)
        style.configure('TCheckbutton', background=PANEL, foreground=MUTED)
        style.map('TCheckbutton', background=[('active', PANEL)], foreground=[('active', TEXT)])
        style.configure('Horizontal.TProgressbar', background=ACCENT, troughcolor='#17352c', bordercolor='#17352c', lightcolor=ACCENT, darkcolor=ACCENT)

    def _card(self, parent, bg=CARD, padx=18, pady=16):
        frame = tk.Frame(parent, bg=bg, highlightbackground=OUTLINE, highlightthickness=1)
        return frame

    def _section_label(self, parent, title, subtitle=None):
        tk.Label(parent, text=title, bg=parent['bg'], fg=TEXT, font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        if subtitle:
            tk.Label(parent, text=subtitle, bg=parent['bg'], fg=MUTED, font=('Segoe UI', 9)).pack(anchor='w', pady=(2, 10))

    def open_creator(self):
        try:
            if webbrowser.open(CREATOR_URL, new=2):
                return
        except Exception:
            pass
        self.clipboard_clear()
        self.clipboard_append(CREATOR_URL)
        messagebox.showinfo('tobimachtdas', 'YouTube-Link wurde in die Zwischenablage kopiert:\n' + CREATOR_URL)

    def _build_ui(self):
        header = tk.Frame(self, bg='#0a1d17', height=92)
        header.pack(fill='x')
        header.pack_propagate(False)
        left = tk.Frame(header, bg='#0a1d17')
        left.pack(side='left', fill='y', padx=26)
        tk.Label(left, text='🏛', bg='#0a1d17', fg='#d9c48b', font=('Segoe UI Emoji', 30)).pack(side='left', pady=18)
        title_block = tk.Frame(left, bg='#0a1d17')
        title_block.pack(side='left', padx=14, pady=8)
        tk.Label(title_block, text='LOST CITY FINDER', bg='#0a1d17', fg=TEXT, font=('Segoe UI', 24, 'bold')).pack(anchor='w')
        tk.Label(title_block, text='City Discovery · 0.8.3  |  Eine Idee von tobimachtdas', bg='#0a1d17', fg=MUTED, font=('Segoe UI', 11)).pack(anchor='w')
        self.select_btn = ttk.Button(header, text='🗂  Welt auswählen', style='Ghost.TButton', command=self.select_world)
        self.select_btn.pack(side='right', padx=24, pady=24)
        self.creator_btn = ttk.Button(header, text='▶  YouTube · @tobimachtdas', style='Ghost.TButton', command=self.open_creator)
        self.creator_btn.pack(side='right', padx=(8, 0), pady=24)

        shell = tk.Frame(self, bg=BG)
        shell.pack(fill='both', expand=True, padx=18, pady=18)

        sidebar = tk.Frame(shell, bg=PANEL, width=340, highlightbackground=OUTLINE, highlightthickness=1)
        sidebar.pack(side='left', fill='y', padx=(0, 16))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text='Welt & Suchfilter', bg=PANEL, fg=TEXT, font=('Segoe UI', 18, 'bold')).pack(anchor='w', padx=18, pady=(18, 4))
        tk.Label(sidebar, text='Suchbereich und Analyse anpassen', bg=PANEL, fg=MUTED, font=('Segoe UI', 10)).pack(anchor='w', padx=18, pady=(0, 14))
        sep = tk.Frame(sidebar, bg=OUTLINE, height=1)
        sep.pack(fill='x', padx=18, pady=(0, 14))
        self.folder_label = tk.Label(sidebar, text='Noch keine Welt ausgewählt', bg=PANEL, fg=MUTED, wraplength=294, justify='left')
        self.folder_label.pack(anchor='w', padx=18, pady=(0, 12))

        form = tk.Frame(sidebar, bg=PANEL)
        form.pack(fill='x', padx=18)

        self._field(form, 'Suchradius (Blöcke)', self._combobox_radius)
        self._field(form, 'Min. Truhenblöcke (klassisch)', self._spinbox_minimum)
        self._field(form, 'Suchprofil / Mindestscore', self._field_profile)
        self._field(form, 'Truhenfilter (Smart, 0 = alle)', self._combobox_chests)
        self._field(form, 'Dimension', self._combobox_dimension)

        self.scan_btn = ttk.Button(sidebar, text='🔎  Welt analysieren', style='Accent.TButton', command=self.start_scan)
        self.scan_btn.pack(fill='x', padx=18, pady=(8, 10))

        action_row = tk.Frame(sidebar, bg=PANEL)
        action_row.pack(fill='x', padx=18)
        self.export_btn = ttk.Button(action_row, text='⤴  Fundorte exportieren', style='Main.TButton', command=self.save)
        self.export_btn.pack(side='left', fill='x', expand=True)

        options = tk.Frame(sidebar, bg=PANEL)
        options.pack(fill='x', padx=18, pady=(12, 10))
        ttk.Checkbutton(options, text='Cache ignorieren (Vollscan)', variable=self.force_scan).pack(anchor='w')
        ttk.Checkbutton(options, text='Heatmap', variable=self.heat, command=self.redraw).pack(anchor='w', pady=(6, 0))
        ttk.Checkbutton(options, text='Geländevorschau', variable=self.preview_enabled, command=self.redraw).pack(anchor='w', pady=(6, 0))

        list_card = self._card(shell, bg=PANEL_ALT)
        list_card.configure(width=275)
        list_card.pack(side="right", fill="y", padx=(12,0))
        list_card.pack_propagate(False)
        tk.Label(list_card, text='Fundorte nach Score', bg=PANEL_ALT, fg=TEXT, font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=14, pady=(12, 4))
        tk.Label(list_card, text='Mindestabstand (Blöcke)', bg=PANEL_ALT, fg=MUTED, font=('Segoe UI', 9)).pack(anchor='w', padx=14, pady=(0, 4))
        self.distance_box = ttk.Combobox(list_card, textvariable=self.city_distance, values=['0','256','512','1024','2048','4096','8192','16384'], state='readonly')
        self.distance_box.pack(fill='x', padx=14, pady=(0,8))
        self.distance_box.bind('<<ComboboxSelected>>', lambda e: self.refresh_results())
        list_frame = tk.Frame(list_card, bg=PANEL_ALT)
        list_frame.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        self.results = tk.Listbox(list_frame, exportselection=False, border=0, highlightthickness=1, highlightbackground=OUTLINE, bg=INPUT_BG, fg=TEXT, selectbackground=ACCENT, selectforeground='#0a2418', activestyle='none')
        scroll = ttk.Scrollbar(list_frame, orient='vertical', command=self.results.yview)
        self.results.config(yscrollcommand=scroll.set)
        self.results.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.results.bind('<<ListboxSelect>>', self.focus_result)
        self.results.bind('<Double-Button-1>', self.show_target)
        nav=tk.Frame(list_card,bg=PANEL_ALT); nav.pack(side='bottom',fill='x',padx=10,pady=8,before=list_frame)
        ttk.Button(nav,text='‹ Zurück',style='Small.TButton',command=lambda:self.step_result(-1)).pack(side='left',expand=True,fill='x')
        ttk.Button(nav,text='Weiter ›',style='Small.TButton',command=lambda:self.step_result(1)).pack(side='left',expand=True,fill='x')
        self.result_count=tk.StringVar(value='0 Fundorte')
        tk.Label(list_card,textvariable=self.result_count,bg=PANEL_ALT,fg=MUTED).pack(side='bottom',pady=8,before=list_frame)

        main = tk.Frame(shell, bg=BG)
        main.pack(side='left', fill='both', expand=True)

        tabs = tk.Frame(main, bg=BG)
        tabs.pack(fill='x', pady=(0, 12))
        ttk.Button(tabs,text='Weltübersicht',style='Main.TButton',command=self.reset_map).pack(side='left')
        ttk.Button(tabs,text='Heatmap',style='Ghost.TButton',command=lambda:self.set_layer(True,False)).pack(side='left',padx=8)
        ttk.Button(tabs,text='Gelände',style='Ghost.TButton',command=lambda:self.set_layer(False,True)).pack(side='left')

        stats_row = tk.Frame(main, bg=BG)
        stats_row.pack(fill='x', pady=(0, 12))
        self.stat_cards = []
        for label_var in (self.stat_found, self.stat_high, self.stat_chunks):
            card = self._card(stats_row)
            card.pack(side='left', fill='x', expand=True, padx=(0, 10) if len(self.stat_cards) < 2 else 0)
            tk.Label(card, textvariable=label_var, bg=CARD, fg=TEXT, font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=10, pady=12)
            self.stat_cards.append(card)

        map_card = self._card(main, bg=CARD_ALT)
        map_card.pack(fill='both', expand=True)
        topbar = tk.Frame(map_card, bg=CARD_ALT)
        topbar.pack(fill='x', padx=16, pady=(14, 8))
        tk.Label(topbar, text='Scrollen: Zoom · Ziehen: Bewegen', bg=CARD_ALT, fg=MUTED, font=('Segoe UI', 10)).pack(side='left')
        controls = tk.Frame(topbar, bg=CARD_ALT)
        controls.pack(side='right')
        ttk.Button(controls, text='+', style='Small.TButton', command=lambda: self.scale(1.25)).pack(side='left', padx=(0, 6))
        ttk.Button(controls, text='−', style='Small.TButton', command=lambda: self.scale(.8)).pack(side='left')

        self.canvas = tk.Canvas(map_card, bg='#203e35', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=16, pady=(0, 16))
        self.canvas.bind('<Configure>', lambda e: self.schedule_map())
        self.canvas.bind('<MouseWheel>', lambda e: self.scale(1.2 if e.delta > 0 else 1 / 1.2))
        self.canvas.bind('<ButtonPress-1>', self.start_drag)
        self.canvas.bind('<B1-Motion>', self.drag_map)
        self.canvas.bind('<ButtonRelease-1>', self.click_map)

        detail_card = self._card(main, bg=CARD)
        detail_card.pack(fill='x', pady=(14, 0))
        left_detail = tk.Frame(detail_card, bg=CARD)
        left_detail.pack(side='left', fill='both', expand=True, padx=18, pady=16)
        tk.Label(left_detail, textvariable=self.detail_title, bg=CARD, fg=TEXT, font=('Segoe UI', 17, 'bold')).pack(anchor='w')
        tk.Label(left_detail, textvariable=self.detail_score, bg=CARD, fg='#f3d07a', font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(4, 8))
        tk.Label(left_detail, textvariable=self.detail_meta1, bg=CARD, fg=TEXT, font=('Segoe UI', 11)).pack(anchor='w')
        tk.Label(left_detail, textvariable=self.detail_meta2, bg=CARD, fg=TEXT, font=('Segoe UI', 11)).pack(anchor='w', pady=(4, 0))
        tk.Label(left_detail, textvariable=self.detail_hint, bg=CARD, fg=MUTED, wraplength=400, justify='left', font=('Segoe UI', 9)).pack(anchor='w', pady=(10, 0))

        right_detail = tk.Frame(detail_card, bg=CARD)
        right_detail.pack(side='right', fill='y', padx=18, pady=16)
        tk.Label(right_detail, text='Status', bg=CARD, fg=MUTED, font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        ttk.Combobox(right_detail, textvariable=self.review_label, values=['Ungeprüft', 'Eigener Bau', 'Anderer Spielerbau', 'Generierte Struktur', 'Fehlalarm'], state='readonly', width=24).pack(fill='x', pady=(6, 10))
        ttk.Button(right_detail, text='💾  Bewertung speichern', style='Accent.TButton', command=self.save_review).pack(fill='x')
        ttk.Checkbutton(right_detail, text='Fehlalarme ausblenden', variable=self.hide_false, command=self.refresh_results).pack(anchor='w', pady=(12, 0))

        footer = tk.Frame(self, bg='#07120f', height=46)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        self.footer_label = tk.Label(footer, textvariable=self.status, anchor='w', bg='#07120f', fg=MUTED, padx=18)
        self.footer_label.pack(side='left', fill='x', expand=True)
        self.footer_progress = ttk.Progressbar(footer, orient='horizontal', length=280, mode='determinate', maximum=100, variable=self.scan_percent)
        self.footer_progress.pack(side='left', padx=(0, 12), pady=12)
        self.footer_percent = tk.Label(footer, textvariable=self.footer_right, width=8, anchor='e', bg='#07120f', fg=TEXT, padx=18)
        self.footer_percent.pack(side='right')

    def _field(self, parent, title, builder):
        wrapper = tk.Frame(parent, bg=PANEL)
        wrapper.pack(fill='x', pady=(0, 5))
        tk.Label(wrapper, text=title, bg=PANEL, fg='#d9eee5', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 6))
        builder(wrapper)

    def _combobox_radius(self, parent):
        self.radius_box = ttk.Combobox(parent, textvariable=self.radius, values=[8, 16, 24, 32, 48, 64, 96, 128], state='readonly')
        self.radius_box.pack(fill='x')

    def _spinbox_minimum(self, parent):
        self.minimum_box = ttk.Spinbox(parent, from_=2, to=500, textvariable=self.minimum)
        self.minimum_box.pack(fill='x')

    def _field_profile(self, parent):
        self.modebox = ttk.Combobox(parent, textvariable=self.mode, values=['Städte', 'Basen', 'Lager', 'Aktivität', 'Alle', 'Klassische Truhensuche'], state='readonly')
        self.modebox.pack(fill='x')
        self.scorebox = ttk.Spinbox(parent, from_=0, to=100, textvariable=self.min_score)
        self.scorebox.pack(fill='x', pady=(8, 0))

    def _combobox_chests(self, parent):
        self.chestbox = ttk.Combobox(parent, textvariable=self.chest_filter, values=[0, 5, 10, 20, 40, 60, 70, 100], state='readonly')
        self.chestbox.pack(fill='x')

    def _combobox_dimension(self, parent):
        self.dimbox = ttk.Combobox(parent, textvariable=self.dim, values=['overworld', 'nether', 'end'], state='readonly')
        self.dimbox.pack(fill='x')
        self.dimbox.bind('<<ComboboxSelected>>', lambda e: self.reset_map())

    def _tab(self, parent, text, active=False):
        bg = CARD_ALT if active else PANEL_ALT
        fg = TEXT if active else MUTED
        frame = tk.Frame(parent, bg=bg, highlightbackground=OUTLINE, highlightthickness=1)
        tk.Label(frame, text=text, bg=bg, fg=fg, font=('Segoe UI', 11, 'bold' if active else 'normal')).pack(padx=16, pady=10)
        return frame

    def set_controls_enabled(self, enabled: bool):
        state = 'normal' if enabled else 'disabled'
        readonly = 'readonly' if enabled else 'disabled'
        self.select_btn.config(state=state)
        self.scan_btn.config(state=state)
        self.export_btn.config(state=state)
        self.radius_box.config(state=readonly)
        self.distance_box.config(state=readonly)
        self.minimum_box.config(state=state)
        self.dimbox.config(state=readonly)
        self.modebox.config(state=readonly)
        self.scorebox.config(state=state)
        self.chestbox.config(state=readonly)

    def select_world(self):
        path = filedialog.askdirectory(title='Minecraft Weltordner wählen')
        if path:
            self.world = path
            self.world_epoch += 1
            self.preview_cache.clear()
            self.preview_pending.clear()
            self._bounds.clear(); self._levels.clear(); self._scaled.clear(); self.center=None; self.zoom=1
            self.summary.set('Noch keine Welt analysiert')
            self.detail_title.set('Kein Fundort ausgewählt')
            self.detail_score.set('Score: –')
            self.detail_meta1.set('Truhen: –   |   Koordinaten: –')
            self.detail_meta2.set('Dimension: –   |   Strukturen: –')
            self.detail_hint.set('Wähle einen Fundort aus, um Details zu sehen.')
            self.locations = []
            self.all_locations = []
            self.chunks = {}
            self.stats = {}
            self.stat_found.set('0 Fundorte')
            self.stat_high.set('0 sehr hohe Scores')
            self.stat_chunks.set('0 Chunks')
            self.results.delete(0, 'end'); self.result_count.set('0 Fundorte')
            self.redraw()
            self.folder_label.config(text=path)
            self.status.set('Bereit. Das Weltverzeichnis wird ausschließlich gelesen.')

    def start_scan(self):
        if not self.world:
            messagebox.showinfo('Welt auswählen', 'Bitte zuerst einen Weltordner auswählen.')
            return
        try:
            radius, minimum, score = self.radius.get(), self.minimum.get(), self.min_score.get()
            if radius < 1 or minimum < 2 or not 0 <= score <= 100:
                raise ValueError()
        except (ValueError, tk.TclError):
            messagebox.showerror('Suchfilter', 'Bitte gültige Werte eingeben.')
            return
        mode = {'Städte': 'city', 'Basen': 'base', 'Lager': 'storage', 'Aktivität': 'activity', 'Alle': 'all', 'Klassische Truhensuche': 'classic'}[self.mode.get()]
        world = self.world
        force = self.force_scan.get()
        self.scan_started = time.monotonic()
        min_chests = self.chest_filter.get()
        self.world_epoch += 1
        self.preview_cache.clear()
        self.preview_pending.clear(); self._scaled.clear()
        self.scanning = True
        self.scan_current = 0
        self.scan_total = 0
        self.scan_file = ''
        self.scan_percent.set(0)
        self.footer_right.set('0 %')
        self.status.set('Scan läuft. Bitte warten, die Regionsdateien werden analysiert …')
        self.set_controls_enabled(False)
        self.redraw()

        def work():
            try:
                ent, chunks, stats = cached_scan(world, self.on_progress, force=force)
                loc = cluster(ent, radius, minimum) if mode == 'classic' else discover(stats['meta'], mode, score, radius=max(64, radius * 3) if mode == 'city' else radius, min_chests=min_chests)
                labels = reviews(world)
                for l in loc:
                    l['review'] = labels.get(l['id'], 'Ungeprüft')
                self.after(0, lambda: self.done(ent, chunks, stats, loc))
            except Exception as exc:
                self.after(0, lambda exc=exc: self.failed(str(exc)))

        threading.Thread(target=work, daemon=True).start()

    def on_progress(self, current, total, path):
        self.after(0, lambda: self.update_progress(current, total, path))

    def update_progress(self, current, total, path):
        self.scan_current = current
        self.scan_total = total
        self.scan_file = path
        percent = int((current / total) * 100) if total else 0
        self.scan_percent.set(percent)
        self.footer_right.set(f'{percent} %')
        if current >= total and total:
            self.status.set('Scan abgeschlossen. Fundorte werden aufbereitet …')
        else:
            self.status.set(f'Scan läuft: {current}/{total} Regionsdateien · {path}')
        self.redraw()

    def failed(self, msg):
        self.scanning = False
        self.set_controls_enabled(True)
        self.scan_percent.set(0)
        self.footer_right.set('0 %')
        self.redraw()
        messagebox.showerror('Scan fehlgeschlagen', msg)
        self.status.set('Scan fehlgeschlagen')

    def done(self, ent, chunks, stats, loc):
        self.entities, self.chunks, self.stats, self.locations = ent, chunks, stats, loc
        self.all_locations = loc
        self._bounds.clear(); self._levels.clear(); self._scaled.clear(); self.center=None
        self.scanning = False
        self.set_controls_enabled(True)
        self.zoom = 1
        self.pan = (0, 0)
        self.summary.set(f'{len(loc)} Fundorte   |   {sum(l["score"] >= 90 for l in loc)} sehr hohe Scores   |   {stats["chunks"]:,} Chunks')
        self.stat_found.set(f'{len(loc)} Fundorte')
        self.stat_high.set(f'{sum(l["score"] >= 90 for l in loc)} sehr hohe Scores')
        self.stat_chunks.set(f'{stats["chunks"]:,} Chunks')
        self.status.set(f'{stats["cache_hits"]} aus Cache · {stats["scanned_regions"]} neu analysiert · {len(loc)} Fundorte · {time.monotonic() - self.scan_started:.1f} s · Fehler: {stats["failed_regions"]}')
        self.detail_title.set('Kein Fundort ausgewählt'); self.detail_score.set('Score: –'); self.detail_meta1.set('Truhen: –'); self.detail_meta2.set('Koordinaten: –'); self.detail_hint.set('Wähle rechts einen Fundort aus.'); self.review_label.set('Ungeprüft')
        self.refresh_results()

    def result_text(self, l):
        return f'{l["name"]} · {l["score"]}/100 · {l["chests"]} Tr.'

    def refresh_results(self):
        if self.scanning:
            return
        sel=self.results.curselection(); old_id=self.locations[sel[0]]['id'] if sel and sel[0]<len(self.locations) else None
        eligible = [l for l in self.all_locations if not self.hide_false.get() or l.get('review') not in ('Fehlalarm', 'Generierte Struktur')]
        self.locations = spaced_locations(eligible, int(self.city_distance.get()))
        self.stat_found.set(f'{len(self.locations)} Fundorte')
        self.stat_high.set(f'{sum(l["score"] >= 90 for l in self.locations)} sehr hohe Scores')
        self.results.delete(0, 'end')
        self.result_count.set(f'{len(self.locations)} aus {len(self.all_locations)} Fundorten')
        for l in self.locations:
            self.results.insert('end', self.result_text(l))
        for i,l in enumerate(self.locations):
            if l['id']==old_id:self.results.selection_set(i); self.results.see(i); break
        self.redraw()

    def save_review(self):
        sel = self.results.curselection()
        if self.scanning or not sel or not self.world:
            return
        l = self.locations[sel[0]]
        label = self.review_label.get()
        try:
            review(self.world, l['id'], label)
        except Exception as e:
            messagebox.showerror('Bewertung', str(e))
            return
        l['review'] = label
        self.refresh_results()
        self.status.set('Bewertung gespeichert: ' + label)

    def coords(self):
        dim=self.dim.get()
        if dim not in self._bounds:
            cells=self.chunks.get(dim,set())
            self._bounds[dim]=(min(x for x,z in cells)*16,min(z for x,z in cells)*16,(max(x for x,z in cells)+1)*16,(max(z for x,z in cells)+1)*16) if cells else (0,0,100,100)
        return self._bounds[dim]

    def transform(self,x,z):
        x0,z0,x1,z1=self.coords(); w=max(80,self.canvas.winfo_width()); h=max(80,self.canvas.winfo_height())
        u=max(.000001,min((w-70)/max(x1-x0,16),(h-70)/max(z1-z0,16))*self.zoom)
        cx,cz=self.center or ((x0+x1)/2,(z0+z1)/2)
        return w/2+(x-cx)*u,h/2+(z-cz)*u,u

    def reset_map(self):
        if self.scanning:return
        self.center=None; self.zoom=1; self.heat.set(False); self.redraw()

    def set_layer(self,heat,terrain):
        self.heat.set(heat); self.preview_enabled.set(terrain); self.redraw()

    def step_result(self,step):
        if self.scanning or not self.locations:return
        sel=self.results.curselection(); self.select_result((sel[0]+step)%len(self.locations) if sel else (0 if step>0 else len(self.locations)-1))

    def schedule_map(self):
        if self._map_job is not None:self.after_cancel(self._map_job)
        def run():
            self._map_job=None; self.redraw()
        self._map_job=self.after(100,run)

    def overview_level(self,dim,step):
        key=(dim,step)
        if key not in self._levels:
            out={}; meta=self.stats.get('meta',{}).get(dim,{})
            for x,z in self.chunks.get(dim,set()):
                k=(x//step,z//step); act=meta.get((x,z),{}).get('activity',0)
                if act>out.get(k,-1):out[k]=act
            self._levels[key]=out
        return self._levels[key]

    def overview_image(self,w,h,ox,oy,u,dim):
        # Raster instead of tens of thousands of Tk canvas objects.
        step=1
        while 16*u*step<4:step*=2
        cells=self.overview_level(dim,step); size=16*u*step
        raw=bytearray(bytes.fromhex('203e35')*(w*h)); heat=self.heat.get()
        for (x,z),act in cells.items():
            left=math.floor(ox+x*size); top=math.floor(oy+z*size)
            right=min(w,math.ceil(left+size)); bottom=min(h,math.ceil(top+size)); left=max(0,left); top=max(0,top)
            if left>=right or top>=bottom:continue
            color='416951' if not heat else ('e65d42' if act>=720000 else 'e7aa42' if act>=120000 else '92a94d' if act>=12000 else '355b46')
            line=bytes.fromhex(color)*(right-left)
            for y in range(top,bottom):raw[(y*w+left)*3:(y*w+right)*3]=line
        return tk.PhotoImage(data=f'P6\n{w} {h}\n255\n'.encode()+raw,format='PPM')

    def draw_scan_overlay(self):
        c = self.canvas
        w, h = c.winfo_width(), c.winfo_height()
        c.create_rectangle(0, 0, w, h, fill='#173028', outline='')
        bw = min(680, w - 30)
        bh = min(320, h - 20)
        cx = w / 2
        cy = h / 2
        top = cy - bh / 2
        c.create_rectangle(cx - bw / 2, top, cx + bw / 2, top + bh, fill='#23463c', outline='#4f8f78', width=2)
        c.create_arc(cx - 34, top + 28, cx + 34, top + 96, start=28, extent=300, style='arc', outline='#8bf0ab', width=8)
        done = self.scan_total and self.scan_current >= self.scan_total
        c.create_text(cx, top + 134, text='Fundorte werden bewertet …' if done else 'Welt wird gescannt …', fill='white', font=('Segoe UI', 20, 'bold'))
        c.create_text(cx, top + 176, text='Bitte warten – die Welt wird analysiert.', fill='#d9e8e1', font=('Segoe UI', 12))
        c.create_text(cx, top + 218, text=f'{self.scan_current} / {self.scan_total} Regionsdateien', fill='white', font=('Segoe UI', 13, 'bold'))
        x1 = cx - bw * .38
        x2 = cx + bw * .38
        y = top + 244
        pct = self.scan_percent.get()
        c.create_rectangle(x1, y, x2, y + 22, fill='#47635a', outline='')
        c.create_rectangle(x1, y, x1 + (x2 - x1) * pct / 100, y + 22, fill='#44dd72', outline='')
        c.create_text(cx, top + 284, text=f'{pct} % · {self.scan_file}', fill='white', font=('Segoe UI', 10))
        c.create_text(cx, top + 304, text='Große Welten benötigen mehr Zeit.', fill='#bdd3c8', font=('Segoe UI', 9))

    def focus_result(self, e=None):
        sel = self.results.curselection()
        if not sel or self.scanning:
            return
        l = self.locations[sel[0]]
        self.review_label.set(l.get('review', 'Ungeprüft'))
        self.detail_title.set(l['name'])
        self.detail_score.set(f'Score: {l["score"]}/100 · {confidence(l["score"])}')
        self.detail_meta1.set(f'{l["chests"]} Truhenblöcke   |   X: {l["x"]}   Z: {l["z"]}')
        self.detail_meta2.set(f'{l["dimension"]}   |   Strukturen: {", ".join(l.get("structures", [])) or "keine erkannt"}')
        self.detail_hint.set(f'LootTable: {l.get("loot_chests", 0)}   ·   Aktivität: {l.get("activity", 0)} Ticks   ·   Bewertung: {l.get("review", "Ungeprüft")}')
        self.dim.set(l['dimension'])
        self.center=(l['x'],l['z']); self.zoom=1
        _,_,unit=self.transform(0,0)
        self.zoom=max(1,1.4/unit)
        self.redraw()

    def request_preview(self, key):
        if key in self.preview_pending:
            return
        self.preview_pending.add(key)
        epoch, dim, cx, cz, r = key
        root = self.world

        def work():
            try:
                result = render(root, dim, cx, cz, r)
            except Exception:
                result = None

            def finish():
                self.preview_pending.discard(key)
                if epoch != self.world_epoch:
                    return
                self.preview_cache[key] = result
                while len(self.preview_cache) > 128:
                    self.preview_cache.pop(next(iter(self.preview_cache)))
                if not self._dragging:self.schedule_map()

            self.after(0, finish)

        threading.Thread(target=work, daemon=True).start()

    def redraw(self):
        c = self.canvas
        c.delete('all')
        w = c.winfo_width()
        h = c.winfo_height()
        if self.scanning:
            self.draw_scan_overlay()
            return
        dim = self.dim.get()
        cells = self.chunks.get(dim, set())
        self.coords()
        ox, oy, u = self.transform(0, 0)
        meta = self.stats.get('meta', {}).get(dim, {})
        if not cells:
            c.create_text(w / 2, h / 2, text='Welt auswählen und scannen', fill='white', font=('Segoe UI', 18, 'bold'))
            return

        if w<2 or h<2:return
        self._overview_photo=self.overview_image(w,h,ox,oy,u,dim)
        c.create_image(0,0,image=self._overview_photo,anchor='nw')
        self._tile_images=[]
        if self.preview_enabled.get() and not self.heat.get() and u>=.9:
            # Fixed 128-block tile grid. Render only visible tiles and reuse on pan.
            left,top=(-ox/u,-oy/u); right,bottom=((w-ox)/u,(h-oy)/u)
            tiles=[(tx,tz) for tx in range(math.floor(left/128),math.floor(right/128)+1) for tz in range(math.floor(top/128),math.floor(bottom/128)+1)]
            tiles.sort(key=lambda t:((t[0]+.5)*128-(left+right)/2)**2+((t[1]+.5)*128-(top+bottom)/2)**2)
            loading=False
            for tx,tz in tiles:
                key=(self.world_epoch,dim,tx*8+4,tz*8+4,4)
                if key not in self.preview_cache:
                    loading=True
                    if len(self.preview_pending)<1 and not self._dragging:self.request_preview(key)
                    continue
                result=self.preview_cache[key]
                if not result:continue
                side,pixels,x0,z0=result; x,y,_=self.transform(x0,z0)
                # Crop to viewport before scaling; cache bytes by tile and scale/crop.
                dx,dy=round(x),round(y); target=max(1,round(side*u))
                xa,ya=max(0,-dx),max(0,-dy); xb,yb=min(target,w-dx),min(target,h-dy)
                if xa>=xb or ya>=yb:continue
                sk=(key,target,xa,ya,xb,yb)
                photo=self._scaled.get(sk)
                if photo is None:
                    offsets=[min(side-1,int(xx*side/target))*3 for xx in range(xa,xb)]
                    rows={}; data=[]
                    for yy in range(ya,yb):
                        sy=min(side-1,int(yy*side/target))
                        if sy not in rows:
                            row=pixels[sy*side*3:(sy+1)*side*3]; rows[sy]=b''.join(row[i:i+3] for i in offsets)
                        data.append(rows[sy])
                    photo=tk.PhotoImage(data=f'P6\n{xb-xa} {yb-ya}\n255\n'.encode()+b''.join(data),format='PPM')
                    self._scaled[sk]=photo
                    while len(self._scaled)>48:self._scaled.pop(next(iter(self._scaled)))
                self._tile_images.append(photo); c.create_image(dx+xa,dy+ya,image=photo,anchor='nw')
            if loading:c.create_text(w/2,20,text='Geländekacheln werden geladen …',fill='white')

        groups = defaultdict(list)
        sel = self.results.curselection()
        selected = sel[0] if sel else -1
        for i, l in enumerate(self.locations):
            if l['dimension'] != dim:
                continue
            x, y, _ = self.transform(l['x'], l['z'])
            if 0 <= x <= w and 0 <= y <= h:
                groups[(int(x // 38), int(y // 38))].append((i, l, x, y))
        for g in groups.values():
            i, l, x, y = max(g, key=lambda q: (q[0]==selected,q[1]['score']))
            n = len(g)
            col = HIGH if l['score'] >= 90 else '#86d36c' if l['score'] >= 75 else WARN if l['score'] >= 60 else '#a7b6ba'
            rad = 16 if n > 1 else 8
            tag = f'pin{i}'
            c.create_oval(x - rad, y - rad, x + rad, y + rad, fill=col, outline='white', width=2 if i == selected else 1, tags=(tag,))
            if n > 1:
                c.create_text(x, y, text=str(n), fill='#173028', font=('Segoe UI', 10, 'bold'), tags=(tag,))
            elif i == selected:
                c.create_rectangle(x - 10, y - 44, x + 92, y - 16, fill='#15352c', outline='white', width=1)
                c.create_text(x + 41, y - 30, text=l['name'], fill='white', font=('Segoe UI', 10, 'bold'))
            c.tag_bind(tag, '<Button-1>', lambda e, i=i: self.select_result(i))

    def select_result(self, i):
        self.results.selection_clear(0, 'end')
        self.results.selection_set(i)
        self.results.see(i)
        self.focus_result()

    def scale(self, multiplier):
        if self.scanning:
            return
        self.zoom = max(.1, min(100000, self.zoom * multiplier))
        self.schedule_map()

    def start_drag(self,e):
        if self.scanning:return
        self.drag=(e.x,e.y); self._dragging=False

    def drag_map(self,e):
        if self.scanning or not self.drag:return
        dx,dy=e.x-self.drag[0],e.y-self.drag[1]
        if not dx and not dy:return
        self._dragging=True
        x0,z0,x1,z1=self.coords(); cx,cz=self.center or ((x0+x1)/2,(z0+z1)/2)
        _,_,u=self.transform(0,0); self.center=(cx-dx/u,cz-dy/u)
        self.drag=(e.x,e.y); self.canvas.move('all',dx,dy)
        if self._map_job is not None:self.after_cancel(self._map_job); self._map_job=None

    def click_map(self,e):
        self.drag=None
        if self._dragging:
            self._dragging=False; self.schedule_map()

    def show_target(self, e=None):
        if self.scanning:
            return
        sel = self.results.curselection()
        if not sel:
            return
        l = self.locations[sel[0]]
        cmd = f'/tp {l["x"]} {l["y"]} {l["z"]}'
        detail = f'\nScore: {l["score"]} Punkte\nBaumaterialien: {l.get("materials", {})}\nStrukturen: {l.get("structures", [])}\nAufenthaltszeit (Ticks): {l.get("activity", 0)}\nY-Koordinate ggf. nur Schätzwert – nicht sicher teleportieren.'
        self.clipboard_clear()
        self.clipboard_append(cmd)
        messagebox.showinfo(l['name'], f'Dimension: {l["dimension"]}\nX: {l["x"]}  Y: {l["y"]}  Z: {l["z"]}\n{l["chests"]} Truhenblöcke\n\nTeleport-Befehl in Zwischenablage:\n{cmd}{detail}')

    def save(self):
        if not self.locations:
            messagebox.showinfo('Keine Fundorte', 'Bitte zuerst eine Welt scannen.')
            return
        path = filedialog.asksaveasfilename(defaultextension='.json', initialfile='locations.json', filetypes=[('JSON', '*.json')])
        if path:
            export(path, self.locations)
            self.status.set('Exportiert: ' + path)


if __name__ == '__main__':
    multiprocessing.freeze_support()
    App().mainloop()
