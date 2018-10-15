# -*- coding: utf-8 -*-
from libqtile.widget.base import _TextBox, ThreadedPollText
from libqtile.widget.mpriswidget import Mpris
from libqtile.widget.battery import Battery
#from libqtile.widget.wlan import Wlan, Wireless
#from libqtile.widget import GoogleCalendar
from libqtile import bar
from libqtile import config as settings
from libqtile.pangocffi import markup_escape_text
import dbus
import os
import re
import platform
from collections import defaultdict
#from cache import configure_cache
import subprocess
from tasklib import TaskWarrior, local_zone, Task
from datetime import datetime, timedelta
import html


#cache = configure_cache({'warchiefx.qtile.caching.expiration_time': 10})


def ensure_connected(f):
    """
    Tries to connect to the player. It *should* be succesful if the player
    is alive. """
    def wrapper(*args, **kwargs):
        self = args[0]
        try:
            self.iface.GetMetadata()
        except (dbus.exceptions.DBusException, AttributeError):
            # except AttributeError because
            # self.iface won't exist if we haven't
            # _connect()ed yet
            self._connect()
        return f(*args, **kwargs)
    return wrapper


class AmarokWidget(Mpris):
    defaults = [
            ("font", "Arial", "Mpd widget font"),
            ("fontsize", None, "Mpd widget pixel size. Calculated if None."),
            ("fontshadow", None,
                "font shadow color, default is None(no shadow)"),
            ("padding", None, "Mpd widget padding. Calculated if None."),
            ("background", None, "Background colour"),
            ("foreground", "ffffff", "Foreground colour"),
            ("separator_color", "#FDA53C", "Separator colour"),
            ("status_color", "#A6D4E0", "Status colour"),
            ("rating_color", "#666666", "Rating colour"),
        ]

    def __init__(self, name="org.mpris.MediaPlayer2.amarok", player_name="Amarok", width=bar.CALCULATED,
                 objname='org.mpris.MediaPlayer2.amarok', **config):
        super(AmarokWidget, self).__init__('', width, objname, **config)
        self.add_defaults(self.defaults)
        self.player_name = player_name

    def _configure(self, qtile, bar):
        super(AmarokWidget, self)._configure(qtile, bar)
        self.layout = self.drawer.textlayout(
            self.text, self.foreground, self.font,
            self.fontsize, self.fontshadow, markup=True)

    def _connect(self):
        """ Try to connect to the player if it exists. """
        try:
            self.player = self.bus.get_object(self.objname, '/Player')
            self.iface = dbus.Interface(
                self.player, dbus_interface='org.freedesktop.MediaPlayer')
            # See: http://xmms2.org/wiki/MPRIS for info on signals
            # and what they mean.
            self.iface.connect_to_signal(
                "TrackChange", self.handle_track_change)
            self.iface.connect_to_signal(
                "StatusChange", self.handle_status_change)
            self.iface.connect_to_signal(
                "PropertiesChanged", self.handle_metadata_change)
            self.connected = True
        except dbus.exceptions.DBusException:
            self.connected = False

    def handle_metadata_change(self, *args, **kwargs):
        self.update()

    @ensure_connected
    def update(self):
        if not self.configured:
            return True
        if not self.connected:
            playing = ''
        else:
            try:
                metadata = self.iface.GetMetadata()
                (status, random, repeat, stop_after_last) = self.iface.GetStatus()

                status = "Playing" if status == 0 else "Stopped"

                track_info = utils.escape('{artist} - {title}'.format(**metadata))

                playing = '<span weight="bold">{player_name}</span>' + \
                '<span color="{separator_color}"> // </span><span color="{status_color}">{status}</span><span color="{separator_color}"> // </span>' + \
                '{track_info} <span color="{rating_color}">(R:{rating})</span>'
                playing = playing.format(status=status, separator_color=self.separator_color,
                                         player_name=self.player_name, status_color=self.status_color,
                                         rating_color=self.rating_color, track_info=track_info, **metadata)

            except dbus.exceptions.DBusException:
                self.connected = False
                playing = '{player_name} - DBus error'.format(player_name=self.player_name)

        if playing != self.text:
            self.text = playing
            self.bar.draw()


# class WcxWlan(object):
#     defaults = [
#         ("font", "Arial", "Font"),
#         ("fontsize", None, "Pixel size. Calculated if None."),
#         ("fontshadow", None,
#             "font shadow color, default is None(no shadow)"),
#         ("padding", None, "Padding. Calculated if None."),
#         ("background", None, "Background colour"),
#         ("foreground", "ffffff", "Foreground colour")
#     ]

#     def __init__(self, interface="wlan0", width=bar.CALCULATED, **kwargs):
#         super(WcxWlan, self).__init__(interface=interface, **kwargs)

#     def update(self):
#         if self.configured:
#             interface = Wireless(self.interface)
#             essid = interface.getEssid()
#             text = "{}".format(essid)
#             if self.text != text:
#                 self.text = text
#                 self.bar.draw()
#         return "Not Connected"


class WcxBatteryWidget(ThreadedPollText, Battery):
    defaults = [
        ('low_foreground', 'FF0000', 'font color when battery is low'),
        (
            'format',
            '{char} {percent:2.0%} {hour:d}:{min:02d}',
            'Display format'
        ),
        ('charge_char', '^', 'Character to indicate the battery is charging'),
        (
            'discharge_char',
            'V',
            'Character to indicate the battery'
            ' is discharging'
        ),
        (
            'low_percentage',
            0.10,
            "0 < x < 1 at which to indicate battery is low with low_foreground"
        ),
        ('hide_threshold', None, 'Hide the text when there is enough energy'),
        ('update_interval', 10, 'The update interval.'),
    ]

    def __init__(self, **config):
        super(WcxBatteryWidget, self).__init__(**config)
        self.add_defaults(self.defaults)

    def poll(self):
        return self._get_text()


class EmacsTask(ThreadedPollText):
    defaults = [
        ("font", "Arial", "Font"),
        ("fontsize", None, "Pixel size. Calculated if None."),
        ("fontshadow", None,
            "font shadow color, default is None(no shadow)"),
        ("padding", None, "Padding. Calculated if None."),
        ("background", None, "Background colour"),
        ("foreground", "ffffff", "Foreground colour"),
        ("label_color", "#5555dd", "Color for the task label"),
        ('update_interval', 5, 'The update interval.'),
    ]

    def __init__(self, **config):
        super(EmacsTask, self).__init__(**config)
        self.add_defaults(self.defaults)

    def _configure(self, qtile, bar):
        super(EmacsTask, self)._configure(qtile, bar)
        self.layout = self.drawer.textlayout(
            self.text, self.foreground, self.font,
            self.fontsize, self.fontshadow, markup=True)

    def poll(self):
        text = ''
        try:
            line = subprocess.check_output(['emacsclient', '-e', '(wcx/org-get-clocked-time)']).decode('utf-8')
            line = line.replace('"', '')
            line = line.replace('\n', '')
            if line != 'nil':
                line = markup_escape_text(line)
                text = '<span weight="bold" color="{label_color}">Task:</span><span> {}</span>'.format(line, label_color=self.label_color)
            else:
                text = "(No current task)"
        except subprocess.CalledProcessError:
            text = "(No current task)"

        return text

    def button_press(self, x, y, button):
        if button == 1:
            subprocess.check_output(['emacsclient', '-e', '(org-clock-out)'])
        super(EmacsTask, self).button_press(x, y, button)


class TaskWarriorWidget(ThreadedPollText):
    defaults = [
        ("font", "Arial", "Font"),
        ("fontsize", None, "Pixel size. Calculated if None."),
        ("fontshadow", None,
            "font shadow color, default is None(no shadow)"),
        ("padding", None, "Padding. Calculated if None."),
        ("background", None, "Background colour"),
        ("foreground", "ffffff", "Foreground colour"),
        ("label_color", "#5555dd", "Color for the task label"),
        ('update_interval', 5, 'The update interval.'),
    ]

    TASK_RE = re.compile(r"#(\d+):\[\S+\] [\S ]+")
    OPTION_RE = re.compile(r'([\S]+):([\S]+)')
    TAG_RE = re.compile(r' \+([\S]+)')

    def __init__(self, **config):
        super(TaskWarriorWidget, self).__init__(**config)
        self.add_defaults(self.defaults)
        self.tw = TaskWarrior()

    def _configure(self, qtile, bar):
        super(TaskWarriorWidget, self)._configure(qtile, bar)
        self.layout = self.drawer.textlayout(
            self.text, self.foreground, self.font,
            self.fontsize, self.fontshadow, markup=True)

    def format_timer(self, task):
        delta = local_zone.localize(datetime.now()) - task['start']
        hours, mins, seconds = str(delta).split(":", 3)

        total_active_time = re.sub(r'\D+', '', task['totalactivetime'] or '')
        if total_active_time and 'ongoing' not in task['tags']:
            total = timedelta(seconds=int(total_active_time))
            total_hours, total_mins, total_seconds = str(total).split(":", 3)
            return "{hh}:{mm}|{hht}:{hhm}".format(hh=hours, mm=mins,
                                                  hht=total_hours, hhm=total_mins)

        return "{hh}:{mm}".format(hh=hours, mm=mins)

    def poll(self):
        text = ''
        active_tasks = self.tw.tasks.filter('+ACTIVE')
        if active_tasks:
            task = active_tasks.get()
            time = self.format_timer(task)
            text = '<span weight="bold" color="{label_color}">Task:</span><span> {timer} [<i>#{id}</i>|{project}] {description}</span>'.format(timer=time, description=html.escape(task['description']),
                                                                                                                                               project=task['project'], label_color=self.label_color,
                                                                                                                                               id=task['id'])
        else:
            text = '(No current task) / O:<span color="#ffffff" weight="bold">{overdue_count}</span> | T:<span color="#ffffff" weight="bold">{today_count}</span> | B:<span color="#ffffff" weight="bold">{blocker_count}</span>'.format(blocker_count=len(self.tw.tasks.pending().filter('+BLOCKING')),
                                                                                                        overdue_count=len(self.tw.tasks.pending().filter('+OVERDUE')),
                                                                                                        today_count=len(self.tw.tasks.pending().filter('+DUETODAY')))
        return text

    def button_press(self, x, y, button):
        if button == 1:
            active_tasks = self.tw.tasks.filter('+ACTIVE')
            if active_tasks:
                task = active_tasks.get()
                task.stop()
            else:
                tasks = "\n".join("#{id}:[{project}] {desc} | +{tags}".format(id=t['id'],
                                                                              project=t['project'],
                                                                              desc=t['description'],
                                                                              tags=" +".join(t['tags']) or "(untagged)"
                )
                                  for t in sorted(self.tw.tasks.pending(), key=lambda x: x['urgency'],
                                                  reverse=True))
                cmd = 'dmenu -p "Start task? >" -fn "Iosevka-10" -sb "#DDDDDD" -sf "#000000" -nb "#000000" -i -l 10 -b'
                try:
                    result = subprocess.run(cmd, input=tasks,
                                            stdout=subprocess.PIPE, check=True,
                                            universal_newlines=True, shell=True)
                    selection = result.stdout
                    match = self.TASK_RE.match(selection)
                    if match:
                        task_id = match.group(1)
                        task = self.tw.tasks.get(id=task_id)
                        task.start()
                    else:
                        options = dict(self.OPTION_RE.findall(selection))
                        tags = self.TAG_RE.findall(selection)
                        descr = self.OPTION_RE.sub('', selection).strip()
                        descr = self.TAG_RE.sub('', descr).strip()
                        task = Task(self.tw, description=descr)
                        if options:
                            for k, v in options.items():
                                task[k] = v
                        if tags:
                            task['tags'] = tags
                        task.save()

                        task.start()
                except subprocess.CalledProcessError:
                    pass
        elif button == 2:
            active_tasks = self.tw.tasks.filter('+ACTIVE')
            if active_tasks:
                task = active_tasks.get()
                if 'ongoing' not in task['tags']:
                    task.done()
                else:
                    task.stop()
        elif button == 3:
            self.tw.execute_command(['sync'])
        super(TaskWarriorWidget, self).button_press(x, y, button)


class HototWidget(_TextBox):
    defaults = [
        ("font", "Arial", "Font"),
        ("fontsize", None, "Pixel size. Calculated if None."),
        ("fontshadow", None,
            "font shadow color, default is None(no shadow)"),
        ("padding", None, "Padding. Calculated if None."),
        ("background", None, "Background colour"),
        ("foreground", "ffffff", "Foreground colour"),
    ]


def humanize_bytes(value):
    suff = ["B", "K", "M", "G", "T"]
    while value > 1024. and len(suff) > 1:
        value /= 1024.
        suff.pop(0)
    return "% 4s%s" % ('%.4s' % value, suff[0])


# Taken from: https://github.com/qtile/qtile-examples/blob/master/user-configs/ei-grad/config.py
class Metrics(ThreadedPollText):
    defaults = [
        ("font", "Arial", "Metrics font"),
        ("fontsize", None, "Metrics pixel size. Calculated if None."),
        ("fontshadow", None, "font shadow color, default is None(no shadow)"),
        ("padding", None, "Metrics padding. Calculated if None."),
        ("background", "000000", "Background colour"),
        ("foreground", "ffffff", "Foreground colour"),
        ("cpu_label_foreground", "#5555dd", "CPU stat label foreground color"),
        ("mem_label_foreground", "#5555dd", "Mem stat label foreground color"),
        ("net_label_foreground", "#5555dd", "Net stat label foreground color"),
        ("download_foreground", "#5555dd", "Color for the download reading"),
        ("upload_foreground", "#5555dd", "Color for the upload reading"),
        ("separator_color", "#444444", "Separator colour"),
        ('update_interval', 1, 'The update interval.'),
    ]

    def __init__(self, **config):
        super(Metrics, self).__init__(**config)
        self.add_defaults(self.defaults)
        self.cpu_usage, self.cpu_total = self.get_cpu_stat()
        self.interfaces = {}
        self.idle_ifaces = {}

    def _configure(self, qtile, bar):
        super(Metrics, self)._configure(qtile, bar)
        self.layout = self.drawer.textlayout(
            self.text, self.foreground, self.font,
            self.fontsize, self.fontshadow, markup=True)

    def get_cpu_stat(self):
        stat = [int(i) for i in open('/proc/stat').readline().split()[1:]]
        return sum(stat[:3]), sum(stat)

    def get_cpu_usage(self):
        new_cpu_usage, new_cpu_total = self.get_cpu_stat()
        cpu_usage = new_cpu_usage - self.cpu_usage
        cpu_total = new_cpu_total - self.cpu_total
        self.cpu_usage = new_cpu_usage
        self.cpu_total = new_cpu_total
        return '<span weight="bold" color="%s">Cpu:</span> %3d%%' % (self.cpu_label_foreground, float(cpu_usage) / float(cpu_total) * 100.)

    def get_mem_usage(self):
        info = {}
        for line in open('/proc/meminfo'):
            key, val = line.split(':')
            info[key] = int(val.split()[0])
        mem = info['MemTotal']
        mem -= info['MemFree']
        mem -= info['Buffers']
        mem -= info['Cached']
        return '<span weight="bold" color="%s">Mem:</span> %d%% <span color="#444444">%s/%s</span>' % (self.mem_label_foreground, float(mem) / float(info['MemTotal']) * 100, humanize_bytes(float(mem) * 1000), humanize_bytes(float(info['MemTotal']) * 1000))

    def get_load_avg(self):
        stat = open('/proc/loadavg').readline().split(" ")[:3]
        return '<span weight="bold" color="{cpu_label_foreground}">Load Avg:</span> {stat}'.format(stat=", ".join(stat), cpu_label_foreground=self.cpu_label_foreground)

    #@cache.cache_on_arguments()
    def read_sensors(self):
        # TODO: Find another sensor library, this one breaks qtile
        results = defaultdict(dict)
        # sensors.init()

        # for chip in sensors.ChipIterator():
        #     chip_name = chip.prefix.decode('utf-8')
        #     if chip_name.startswith('nouveau'):
        #         continue
        #     for feature in sensors.FeatureIterator(chip):
        #         sfs = list(sensors.SubFeatureIterator(chip, feature))
        #         label = sensors.get_label(chip, feature).encode('utf-8')
        #         vals = [sensors.get_value(chip, sf.number) for sf in sfs]
        #         skipname = len(feature.name) + 1  # skip common prefix
        #         names = [sf.name[skipname:].encode("utf-8") for sf in sfs]
        #         data = dict(zip(names, vals))
        #         results[chip_name][label] = data.get('input')

        # sensors.cleanup()

        return results

    def format_fan_speed(self, sensors_output=None):
        if not sensors_output:
            sensors_output = self.read_sensors()
        template = '<span weight="bold" color="{cpu_label_foreground}">Fan:</span> {fan_speed:.1f} RPM'
        return template.format(cpu_label_foreground=self.cpu_label_foreground,
                               fan_speed=sensors_output.get('thinkpad', {}).get('fan1', -1))

    def format_cpu_temp(self, sensors_output=None):
        if not sensors_output:
            sensors_output = self.read_sensors()
        template = '<span weight="bold" color="{cpu_label_foreground}">Temp:</span> {avg_temp:.0f}C'
        # core_temps = {label: value for label, value in sensors_output.get('coretemp',
        #                                                                   {}).items() if label.startswith('Core')}
        return template.format(cpu_label_foreground=self.cpu_label_foreground,
                               avg_temp=sensors_output.get('coretemp', {}).get('Physical id 0', 0))
                               # avg_temp=sum(val for val in core_temps.values()) / len(core_temps))

    def get_net_usage(self):
        interfaces = []
        basedir = '/sys/class/net'
        for iface in os.listdir(basedir):
            if iface == "lo": continue
            if iface.startswith(tuple(['veth', 'docker', 'br'])): continue
            j = os.path.join
            ifacedir = j(basedir, iface)
            statdir = j(ifacedir, 'statistics')
            idle = iface in self.idle_ifaces
            try:
                if int(open(j(ifacedir, 'carrier')).read()):
                    rx = int(open(j(statdir, 'rx_bytes')).read())
                    tx = int(open(j(statdir, 'tx_bytes')).read())
                    if iface not in self.interfaces:
                        self.interfaces[iface] = (rx, tx)
                    old_rx, old_tx = self.interfaces[iface]
                    self.interfaces[iface] = (rx, tx)
                    rx = rx - old_rx
                    tx = tx - old_tx
                    if rx or tx:
                        idle = False
                        self.idle_ifaces[iface] = 0
                        rx = humanize_bytes(rx)
                        tx = humanize_bytes(tx)
                        text = '<span weight="bold" color="{net_label_foreground}">{iface}:</span>' + \
                          ' <span color="{download_foreground}">{rx}</span> / <span color="{upload_foreground}">{tx}</span>'
                        text = text.format(net_label_foreground=self.net_label_foreground, iface=iface, rx=rx, tx=tx,
                                           upload_foreground=self.upload_foreground, download_foreground=self.download_foreground)
                        interfaces.append(text)
            except:
                pass
            if idle:
                text = '<span weight="bold" color="{net_label_foreground}">{iface}:</span>' + \
                    ' <span color="{download_foreground}">{rx}</span> / <span color="{upload_foreground}">{tx}</span>'
                text = text.format(net_label_foreground=self.net_label_foreground, iface=iface, rx=humanize_bytes(0), tx=humanize_bytes(0),
                                   upload_foreground=self.upload_foreground, download_foreground=self.download_foreground)
                interfaces.append(text)
                self.idle_ifaces[iface] += 1
                if self.idle_ifaces[iface] > 30:
                    del self.idle_ifaces[iface]
        return ('<span color="%s"> | </span>' % (self.separator_color)).join(interfaces)

    def poll(self):
        text = ""
        stat = []
        # sensors_output = self.read_sensors()
        stat = [self.get_cpu_usage(),  # self.format_cpu_temp(sensors_output), self.format_fan_speed(sensors_output),
                self.get_mem_usage(), self.get_load_avg()]
        net = self.get_net_usage()
        if net:
            stat.append(net)
        text = ('<span color="%s"> | </span>' % (self.separator_color)).join(stat)

        return text


class HostInfo(ThreadedPollText):
    defaults = [
        ("font", "Arial", "Font"),
        ("fontsize", None, "Pixel size. Calculated if None."),
        ("fontshadow", None,
            "font shadow color, default is None(no shadow)"),
        ("padding", None, "Padding. Calculated if None."),
        ("background", None, "Background colour"),
        ("foreground", "ffffff", "Foreground colour"),
        ("separator_color", "#550000", "Color for the task label"),
    ]

    def __init__(self, **config):
        super(HostInfo, self).__init__(**config)
        self.add_defaults(self.defaults)

    def _configure(self, qtile, bar):
        super(HostInfo, self)._configure(qtile, bar)
        self.layout = self.drawer.textlayout(
            self.text, self.foreground, self.font,
            self.fontsize, self.fontshadow, markup=True)

    def poll(self):
        (os, node, kernel_ver, compile_date, arch, misc) = platform.uname()
        text = '<span weight="bold">{node}</span><span color="{separator_color}"> // </span><span>{kernel_ver}</span>'.format(node=node, separator_color=self.separator_color, kernel_ver=kernel_ver)
        return text


# #from apiclient.discovery import build
# from oauth2client.client import AccessTokenRefreshError
# from oauth2client.client import OAuth2WebServerFlow
# from oauth2client.tools import run
# import oauth2client.file
# import httplib2
# import datetime
# import re
# import dateutil.parser
# from libqtile import utils


# def istoday(date):
#     today = datetime.datetime.now()
#     return all([getattr(date, attr) == getattr(today, attr) for attr in ['year', 'month', 'day']])


# class WCXGcalWidget(object):
#     def __init__(self, **config):
#         super(WCXGcalWidget, self).__init__(**config)
#         # Run once, at start
#         self.cal_updater()

#     def update(self, data):
#         if data:
#             info = data.get('next_event', {})
#             date = info.get('date')
#             if date:
#                 if istoday(info['date']):
#                     info['date'] = date.strftime('%I:%M%p')
#                 else:
#                     info['date'] = date.strftime('%a %d %b %I:%M%p')
#             else:
#                 info['date'] = '...'
#             template = '<span weight="bold" color="#D7FF00">Next Event:</span>' + \
#                        '<span> <span color="#bbbbbb">{date}</span><span color="#444444">' + \
#                        '/</span>{description}</span>'
#             self.text = template.format(**info)
#         else:
#             self.text = 'No calendar data available'
#         self.bar.draw()
#         return False

#     def button_press(self, x, y, button):
#         super(WCXGcalWidget, self).button_press(x, y, button)

#     def fetch_calendar(self):
#         # if we don't have valid credentials, update them
#         if not hasattr(self, 'credentials') or self.credentials.invalid:
#             self.cred_init()
#             data = {'next_event': {'description': 'Credentials updating'}}
#             return data

#         # Create an httplib2.Http object to handle our HTTP requests and
#         # authorize it with our credentials from self.cred_init
#         http = httplib2.Http()
#         http = self.credentials.authorize(http)

#         service = build('calendar', 'v3', http=http)

#         # current timestamp
#         now = datetime.datetime.utcnow().isoformat('T')+'Z'
#         data = {}

#         calendars = service.calendarList().list().execute()

#         all_events = []
#         for calendar in calendars.get('items', []):
#             # grab the next event
#             events = service.events().list(
#                 calendarId=calendar['id'],
#                 singleEvents=True,
#                 timeMin=now,
#                 maxResults='1',
#                 orderBy='startTime'
#             ).execute()

#             # get items list
#             try:
#                 event = events.get('items', [])[0]
#                 all_events.append(event)
#             except IndexError:
#                 continue

#         print(all_events)
#         event = sorted(all_events, key=get_event_start)[0]

#         # get reminder time
#         try:
#             remindertime = datetime.timedelta(
#                 0,
#                 int(
#                     event.get('reminders').get('overrides')[0].get('minutes')
#                 ) * 60
#             )
#         except:
#             remindertime = datetime.timedelta(0, 0)

#         #format the data
#         event_start = dateutil.parser.parse(get_event_start(event),
#                                             ignoretz=True)

#         data = {
#             'next_event': {
#                 'description': event['summary'],
#                 'date': event_start
#             }
#         }
#         if dateutil.parser.parse(
#                 get_event_start(event),
#                 ignoretz=True
#                 ) - remindertime <= datetime.datetime.now():
#             template = '<span color="{color}">{description}</span>'
#             data['next_event']['description'] = template.format(color=utils.hex(self.reminder_color),
#                                                                 description=data['next_event']['description'])

#         # return the data
#         return data


# def get_event_start(event):
#     if 'dateTime' in event['start']:
#         return event['start']['dateTime']
#     elif 'date' in event['start']:
#         return event['start']['date']
