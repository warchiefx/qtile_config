# -*- coding: utf-8 -*-
from libqtile.config import Screen, Drag, Click
from libqtile.config import Key, Group, Match, Rule
from libqtile.command import lazy
from libqtile import layout, bar, widget, hook
from libqtile.dgroups import simple_key_binder
from subprocess import check_output

from widgets import *
import os
import re
import subprocess

RESOURCE_PATH = os.path.join(os.path.dirname(__file__), "resources")

widget_defaults = {
    "font": "Pragmata Pro",
    "fontsize": 12,
    "background": "#0a0f14",
    "foreground": "#ffffff",
}

layout_defaults = {
    "border_focus": "#555555",
    "border_normal": "#0a0f14"
}

LABEL_COLOR = "#bd2c40"

sep_defaults = {"size_percent": 60, "foreground": "#777777", "padding": 5}


APP_MAP = {
    ("emacs", "Emacs"): {"group": "dev", "cmd": "emacs"},
    ("sakura", "Sakura"): {"group": "dev", "cmd": "emacs"},
    ("krusader", "Krusader"): {"cmd": "krusader", "extra_args": {"floating": True}},
    ("gnome-commander", "Gnome-commander"): {
        "cmd": "gnome-commander",
        "extra_args": {"floating": True},
    },
    ("nautilus", "Nautilus"): {"cmd": "nautilus", "extra_args": {"floating": True}},
    ("variety", "Variety"): {"cmd": "variety", "extra_args": {"floating": True}},
    ("LoLPatcherUx.exe", "Wine"): {"group": "gaming", "extra_args": {"floating": True}},
    ("LolClient.exe", "Wine"): {"group": "gaming", "extra_args": {"floating": True}},
    ("clementine", "Clementine"): {"group": "media", "cmd": "clementine"},
    ("amarok", "Amarok"): {"group": "media", "cmd": "amarok"},
    ("Spotify", "Spotify"): {"group": "media", "cmd": "flatpak run com.spotify.Client"},
    ("evolution", "Evolution"): {"group": "mail", "cmd": "evolution", "extra_args": {}},
    ("geary", "Geary"): {"group": "mail", "cmd": "geary", "extra_args": {}},
    ("slack", "Slack"): {
        "group": "chat",
        "cmd": "flatpak run com.slack.Slack",
        "extra_args": {},
    },
    ("nuvolaplayer", "nuvolaplayer"): {"group": "media", "cmd": "nuvolaplayer"},
    ("vlc", "Vlc"): {"group": "media", "cmd": "vlc"},
    ("xbmc.bin", "xbmc.bin"): {"group": "media", "cmd": "xbmc"},
    ("Pidgin", "Pidgin"): {
        "group": "chat",
        "cmd": "pidgin",
        "extra_args": {"floating": True},
    },
    ("telegram-desktop", "TelegramDesktop"): {
        "group": "chat",
        "cmd": "flatpak run org.telegram.desktop",
        "extra_args": {
            # 'floating': True
        },
    },
    ("franz", "Franz"): {
        "group": "chat",
        "cmd": "franz",
        "extra_args": {"floating": True},
    },
    ("cutegram", "Cutegram"): {
        "group": "chat",
        "cmd": "cutegram",
        "extra_args": {"floating": True},
    },
    # ('skype', 'Skype'): {
    #     'group': 'chat',
    #     'cmd': 'skype',
    #     'extra_args': {
    #         'floating': True
    #     }
    # },
    ("crx_nckgahadagoaajjgafhacjanaoiihapd", "Chromium"): {
        "group": "chat",
        "extra_args": {"floating": True},
    },
    ("crx_knipolnnllmklapflnccelgolnpehhpl", "Chromium"): {
        "group": "chat",
        "extra_args": {"floating": True},
    },
    # ('pidgin', 'Pidgin'): {
    #     'group': 'chat',
    #     'cmd': 'pidgin',
    #     'extra_args': {
    #         'floating': True
    #     }
    # },
    # ('hotot-gtk3', 'Hotot-gtk3'): {
    #     'group': 'twitter',
    #     'cmd': 'hotot-gtk3',
    # },
    ("transmission-gtk", "Transmission-gtk"): {
        "group": "misc",
        "cmd": "transmission-gtk",
    },
    ("sun-awt-X11-XWindowPeer", "jetbrains-pycharm"): {
        "group": None,
        "extra_args": {
            "floating": True
        }
    }
}


floating_layout = layout.floating.Floating(
    **layout_defaults
)


def get_conf(app_spec):
    if isinstance(app_spec, tuple):
        return APP_MAP.get(app_spec, {})
    else:
        for key, conf in APP_MAP.items():
            if app_spec in key:
                return conf
    return {}


def is_running(process):
    s = subprocess.Popen(["ps", "axuw"], stdout=subprocess.PIPE)
    for x in s.stdout:
        if re.search(process, x.decode("utf-8")):
            return True
    return False


def execute_once(process):
    if not is_running(process):
        return subprocess.Popen(process.split())


def spawn_app_or_group(app):
    """ Go to specified group if it exists. Otherwise, run the specified app.
    """

    def f(qtile):
        conf = get_conf(app)
        if is_running(app):
            if "group" in conf:
                qtile.groupMap[conf.get("group")].cmd_toscreen()
        else:
            if "cmd" in conf:
                qtile.cmd_spawn(conf.get("cmd"))
            else:
                qtile.cmd_spawn(app)

    return f


def modify_opacity(incr=0.1):
    def f(qtile):
        curr_opacity = qtile.window.opacity()
        new_opacity = curr_opacity + incr
        if 0.0 <= new_opacity <= 1.1:
            qtile.window.opacity(new_opacity)
        elif new_opacity > 1.0:
            qtile.window.opacity(1.0)
        elif new_opacity < 0.0:
            qtile.window.opacity(0.1)

    return f


PRIMARY_SCREEN_CONFIG = Screen(
    top=bar.Bar(
        [
            widget.GroupBox(
                urgent_alert_method="text",
                font=widget_defaults["font"],
                fontsize=widget_defaults["fontsize"],
                # margin_y = 1,
                # margin_x = 1,
                borderwidth=1,
                padding=1,
                this_current_screen_border="#26a98b",
                background=widget_defaults["background"],
                urgent_border="#BB1100",
                highlight_method="border"
            ),
            widget.Spacer(width=bar.STRETCH),
            # widget.CPUGraph(width=80, line_width=2, border_color='#111111',
            #                 graph_color='#26a98b', fill_color='#D7DD00'),
            # widget.MemoryGraph(width=80, line_width=2, border_color='#111111',
            #                    graph_color='#26a98b', fill_color='#D7DD00'),
            Metrics(
                cpu_label_foreground=LABEL_COLOR,
                download_foreground=LABEL_COLOR,
                mem_label_foreground=LABEL_COLOR,
                upload_foreground="#cccccc",
                net_label_foreground=LABEL_COLOR,
                **widget_defaults
            ),
            widget.Sep(**sep_defaults),
            widget.Battery(
                battery_name="BAT0",
                # energy_now_file='charge_now',
                # energy_full_file='charge_full',
                # power_now_file='current_now',
                foreground="#cccccc",
                charge_char="↑",
                discharge_char="↓",
                padding=4,
                font=widget_defaults["font"],
                fontsize=widget_defaults["fontsize"],
                background=widget_defaults["background"],
                format="Batt: {char} {percent:2.0%} ({hour:d}:{min:02d})",
                update_interval=5,
            ),
            widget.Sep(**sep_defaults),
            widget.Systray(background=widget_defaults["background"]),
            widget.Sep(**sep_defaults),
            widget.Clock(format="%a %d %b", **widget_defaults),
            widget.Clock(
                format="%I:%M",
                foreground=LABEL_COLOR,
                font=widget_defaults["font"],
                fontsize=widget_defaults["fontsize"],
                background=widget_defaults["background"],
            ),
        ],
        20,
        background=widget_defaults["background"],
        opacity=1,
    ),
    # bottom=bar.Bar(
    #     [
    #         HostInfo(separator_color="#777777", **widget_defaults),
    #         widget.Sep(**sep_defaults),
    #         # widget.CPUGraph(width=80, line_width=2, border_color='#111111',
    #         #                 graph_color='#26a98b', fill_color='#D7DD00'),
    #         # widget.MemoryGraph(width=80, line_width=2, border_color='#111111',
    #         #                    graph_color='#26a98b', fill_color='#D7DD00'),
    #         Metrics(
    #             cpu_label_foreground=LABEL_COLOR,
    #             download_foreground=LABEL_COLOR,
    #             mem_label_foreground=LABEL_COLOR,
    #             upload_foreground="#AAAAAA",
    #             net_label_foreground=LABEL_COLOR,
    #             **widget_defaults
    #         ),
    #         widget.Sep(**sep_defaults),
    #         widget.ThermalSensor(
    #             tag_sensor="temp1",
    #             threshold=86,
    #             markup=True,
    #             show_tag=True,
    #             **widget_defaults
    #         ),
    #         widget.Sep(**sep_defaults),
    #         widget.Net(interface="wlan0", markup=True, **widget_defaults),
    #         widget.Spacer(width=bar.STRETCH),
    #         TaskWarriorWidget(label_color=LABEL_COLOR, **widget_defaults),
    #     ],
    #     20,
    #     background=widget_defaults["background"],
    #     opacity=0.94,
    # ),
)


def make_secondary_screen_config():
    return Screen(
        top=bar.Bar(
            [
                # This is a list of our virtual desktops.
                widget.GroupBox(
                    urgent_alert_method="text",
                    font=widget_defaults["font"],
                    fontsize=widget_defaults["fontsize"],
                    # margin_y = 1,
                    # margin_x = 1,
                    borderwidth=1,
                    padding=1,
                    this_current_screen_border="#26a98b",
                    background=widget_defaults["background"],
                    urgent_border="#BB1100",
                ),
                # A prompt for spawning processes or switching groups. This will be
                # invisible most of the time.
                widget.Prompt(
                    foreground="#6A75FF",
                    font=widget_defaults["font"],
                    fontsize=widget_defaults["fontsize"],
                    background=widget_defaults["background"],
                ),
                widget.Spacer(width=bar.STRETCH),
                widget.Clock(format="%a %d %b", **widget_defaults),
                widget.Clock(
                    format="%I:%M",
                    foreground=LABEL_COLOR,
                    font=widget_defaults["font"],
                    fontsize=widget_defaults["fontsize"],
                    background=widget_defaults["background"],
                ),
            ],
            20,
            background=widget_defaults["background"],
            opacity=1,
        ),
        # bottom=bar.Bar(
        #     [
        #         HostInfo(separator_color="#777777", **widget_defaults),
        #         widget.Sep(**sep_defaults),
        #         # widget.CPUGraph(width=80, line_width=2, border_color='#111111',
        #         #                 graph_color='#26a98b', fill_color='#D7DD00'),
        #         # widget.MemoryGraph(width=80, line_width=2, border_color='#111111',
        #         #                    graph_color='#26a98b', fill_color='#D7DD00'),
        #         Metrics(
        #             cpu_label_foreground=LABEL_COLOR,
        #             download_foreground=LABEL_COLOR,
        #             mem_label_foreground=LABEL_COLOR,
        #             upload_foreground="#AAAAAA",
        #             net_label_foreground=LABEL_COLOR,
        #             **widget_defaults
        #         ),
        #         widget.Spacer(width=bar.STRETCH),
        #         TaskWarriorWidget(label_color=LABEL_COLOR, **widget_defaults),
        #         # WCXGcalWidget(www_group='personal', storage_file='/home/warchiefx/.config/qtile/gcal.settings',
        #         #              update_interval=900, calendar='primary',
        #         #             reminder_color="#D7aa00",
        #         #             **widget_defaults),
        #         # AmarokWidget(**widget_defaults),
        #     ],
        #     20,
        #     background=widget_defaults["background"],
        #     opacity=0.94,
        # ),
    )


def get_number_of_screens():
    try:
        out = subprocess.check_output(
            "xrandr | awk /\"connected [0-9]\"/'{print $1}' | wc -l", shell=True
        )
        return int(out) + 1
    except subprocess.CalledProcessError:
        return 1


def make_screen_config(screens):
    # TODO: Allow arbitrarily specifying which screen is primary
    screen_config = [PRIMARY_SCREEN_CONFIG]
    for i in range(screens - 1):
        screen_config.append(make_secondary_screen_config())

    return screen_config


num_screens = get_number_of_screens()

screens = make_screen_config(num_screens)

mod = "mod4"
altkey = "mod1"
# mod1 = Alt
# mod4 = Win Key


keys = [
    Key(["control", "mod4"], "q", lazy.shutdown()),
    Key(["control", "mod4"], "r", lazy.restart()),
    Key([mod], "Left", lazy.screen.prev_group()),
    Key([mod], "Right", lazy.screen.next_group()),
    Key([mod], "k", lazy.layout.down()),
    Key([mod], "j", lazy.layout.up()),
    Key([mod], "h", lazy.layout.previous()),
    # Key([mod, "shift"], "l",              lazy.layout.shuffle_up()),
    # Key([mod, "shift"], "h",              lazy.layout.shuffle_down()),
    Key([mod], "l", lazy.layout.next()),
    Key([mod, "shift"], "space", lazy.layout.rotate()),
    Key([mod, "shift"], "Return", lazy.layout.toggle_split()),
    Key([mod], "space", lazy.next_layout()),
    Key(["mod1"], "Tab", lazy.layout.next()),
    Key(["mod1", "shift"], "Tab", lazy.layout.prev()),
    Key([mod, "shift"], "Right", lazy.layout.increase_ratio()),
    Key([mod, "shift"], "Left", lazy.layout.decrease_ratio()),
    Key([mod], "x", lazy.window.kill()),
    Key([mod], "c", lazy.window.close()),
    Key([mod], "x", lazy.window.kill()),
    Key([mod], "F7", lazy.spawn("autorandr")),
    Key(
        [],
        "XF86MonBrightnessUp",
        lazy.spawn("xbacklight -ctrl intel_backlight -inc 10"),
    ),
    Key(
        [],
        "XF86MonBrightnessDown",
        lazy.spawn("xbacklight -ctrl intel_backlight -dec 10"),
    ),
    Key([], "XF86AudioPlay", lazy.spawn("playerctl play-pause")),
    Key([], "XF86AudioNext", lazy.spawn("playerctl next")),
    Key([], "XF86AudioPrev", lazy.spawn("playerctl previous")),
    Key([], "XF86AudioStop", lazy.spawn("playerctl stop")),
    # interact with prompts
    Key(
        [mod],
        "r",
        lazy.spawn(
            'dmenu_run -p "Run? >" -fn "Iosevka-10" -sb "#dddddd" -sf "#0a0f14" -nb "#0a0f14"'
        ),
    ),
    Key([mod], "g", lazy.switchgroup()),
    Key(
        [mod, "mod1"],
        "j",
        # lazy.function(modify_opacity(-0.1))),
        lazy.window.opacity(0.92),
    ),
    Key(
        [mod, "mod1"],
        "k",
        # lazy.function(modify_opacity(0.1))),
        lazy.window.opacity(1),
    ),
    Key([mod, "mod1"], "f", lazy.window.toggle_fullscreen()),
    Key([mod, "mod1"], "t", lazy.window.toggle_floating()),
    # start specific apps
    Key([mod], "w", lazy.spawn("firefox")),
    Key([mod, "shift"], "w", lazy.spawn("chromium")),
    Key([mod], "m", lazy.function(spawn_app_or_group("evolution"))),
    Key([mod], "s", lazy.function(spawn_app_or_group("slack"))),
    Key([mod], "Return", lazy.spawn("sakura")),
    Key([mod], "a", lazy.function(spawn_app_or_group("Spotify"))),
    Key([mod, "shift"], "a", lazy.spawn("pavucontrol")),
    Key([mod], "v", lazy.function(spawn_app_or_group("vlc"))),
    Key([mod, "shift"], "v", lazy.function(spawn_app_or_group("xbmc"))),
    # Key([mod], "s",              lazy.function(spawn_app_or_group("skype"))),
    Key([mod], "d", lazy.spawn("lxappearance")),
    Key([mod], "p", lazy.function(spawn_app_or_group("telegram-desktop"))),
    Key([mod], "b", lazy.function(spawn_app_or_group("transmission-gtk"))),
    Key([mod], "t", lazy.function(spawn_app_or_group("hotot-gtk3"))),
    Key([mod], "f", lazy.spawn("nautilus")),
    Key([mod], "e", lazy.function(spawn_app_or_group("emacs"))),
    # Special functions
    Key([], "Print", lazy.spawn("gnome-screenshot")),  # Capture full screen
    Key(["shift"], "Print", lazy.spawn("gnome-screenshot -i")),  # Capture interactively
    Key(["mod1"], "Print", lazy.spawn("gnome-screenshot -w")),  # Capture window
    Key([], "Pause", lazy.spawn("gnome-screensaver-command --lock")),
    Key([mod, "mod1"], "l", lazy.spawn("gnome-screensaver-command --lock")),
]

# This allows you to drag windows around with the mouse if you want.
mouse = [
    Drag(
        [mod],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position(),
    ),
    Drag(
        [mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()
    ),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

# Next, we specify group names, and use the group name list to generate an appropriate
# set of bindings for group switching.
groups = [
    Group("main", position=1),
    Group(
        "chat",
        persist=True,
        position=2,
        matches=[
            Match(
                wm_class=[
                    "Pidgin",
                    "Slack",
                    "Discord",
                    "TeamSpeak 3",
                    "TelegramDesktop",
                    "Franz",
                ]
            )
        ],
    ),
    Group(
        "mail",
        position=3,
        exclusive=False,
        matches=[Match(wm_class=["Nylas N1", "Evolution"])],
        init=True,
        persist=True,
    ),
    Group(
        "dev",
        exclusive=False,
        matches=[Match(wm_class=["Terminator", "Emacs", "Sakura"])],
        position=4,
    ),
    Group("work", position=5),
    Group("aux", position=6),
    Group(
        "media",
        persist=True,
        init=True,
        matches=[
            Match(
                wm_class=[
                    "Vlc",
                    "Banshee",
                    "xbmc.bin",
                    "Amarok",
                    "spotify" "Clementine",
                    "nuvolaplayer",
                ]
            )
        ],
    ),
    Group(
        "gaming",
        persist=True,
        init=False,
        matches=[
            Match(wm_class=["LoLPatcherUx.exe", "LoLClient.exe", "Wine", "Steam"])
        ],
    ),
    Group("reference", persist=False, init=False, matches=[Match(wm_class=["Zeal"])]),
]

# dgroup rules that not belongs to any group
dgroups_app_rules = [
    # Everything i want to be float, but don't want to change group
    Rule(Match(title=["nested", "gscreenshot"]), float=True, intrusive=True),
    Rule(
        Match(
            wm_class=[
                "Plugin-container",
                "Gnome-commander",
                "Nautilus",
                "Krusader",
                re.compile(".*keyring.*"),
            ]
        ),
        float=True,
        intrusive=True,
    ),
    Rule(Match(wm_type="dialog"), float=True, intrusive=True),
    # floating windows
    Rule(
        Match(
            wm_class=["Steam"],
            title=[re.compile("[a-zA-Z]*? Steam"), re.compile("Steam - [a-zA-Z]*?")],
        ),
        float=True,
        group="gaming",
    ),
    Rule(Match(wm_class=["LoLPatcherUx.exe", "LoLClient.exe"]), float=True),
    Rule(Match(wm_class=["sun-awt-X11-XWindowPeer", "jetbrains-pycharm"]), float=True),
    Rule(Match(wm_class=["Spotify"]), group="media", intrusive=True),
]

# auto bind keys to dgroups mod+1 to 9
dgroups_key_binder = simple_key_binder(mod)

layouts = [
    layout.Max(**layout_defaults),  # Fullscreen all the things
    layout.Matrix(**layout_defaults),  # Tile evenly in squares
    layout.MonadTall(**layout_defaults),  # 1 tall pane, 2 small ones
    floating_layout,
]


# Hooks
@hook.subscribe.client_new
def dialogs(window):
    if window.window.get_wm_type() == "dialog" or window.window.get_wm_transient_for():
        window.floating = True


@hook.subscribe.client_new
def app_by_conf(window):
    wm_class = window.window.get_wm_class()
    conf = get_conf(wm_class)
    if "extra_args" in conf:
        for arg, val in conf["extra_args"].items():
            setattr(window, arg, val)


@hook.subscribe.startup
def startup():
    execute_once("compton")
    execute_once("nitrogen --restore")
    execute_once("setxkbmap -layout us_intl -option ctrl:swapcaps")
    execute_once("autorandr --change")
    execute_once("volumeicon")
    execute_once("nm-applet")
    execute_once("gnome-screensaver")


@hook.subscribe.screen_change
def restart_on_randr(qtile, ev):
    qtile.cmd_restart()
    execute_once("setxkbmap -layout us_intl -option ctrl:swapcaps")
    execute_once("nitrogen --restore")
