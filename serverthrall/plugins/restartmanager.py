from .discord import Discord
from .intervaltickplugin import IntervalTickPlugin
from .remoteconsole import RemoteConsole
from datetime import datetime, timedelta
from string import Template
import time
import sys


class RestartInformation():

    def __init__(self, plugin, rcon_warning, rcon_restart, discord_warning, discord_restart, restart_time):
        self.plugin = plugin
        self.rcon_warning = rcon_warning
        self.rcon_restart = rcon_restart
        self.discord_warning = discord_warning
        self.discord_restart = discord_restart
        self.restart_time = restart_time


class RestartManager(IntervalTickPlugin):

    def __init__(self, config):
        super(RestartManager, self).__init__(config)
        self.enabled = True
        config.set_default('interval.interval_seconds', 60)
        config.set_default('warning_minutes', 5)
        config.set_default('warning_send_discord', True)
        config.set_default('warning_send_rcon', True)
        config.set_default('restart_send_discord', True)
        config.set_default('restart_send_rcon', True)
        config.queue_save()

    def ready(self, steamcmd, server, thrall):
        super(RestartManager, self).ready(steamcmd, server, thrall)
        self.warning_minutes = self.config.getint('warning_minutes')
        self.warning_send_discord = self.config.getboolean('warning_send_discord')
        self.warning_send_rcon = self.config.getboolean('warning_send_rcon')
        self.restart_send_discord = self.config.getboolean('restart_send_discord')
        self.restart_send_rcon = self.config.getboolean('restart_send_rcon')

        self.discord = thrall.get_plugin(Discord)
        self.rcon = thrall.get_plugin(RemoteConsole)
        self.active_restart_info = None
        self.offline_callbacks = {}

    def notify_offline_callbacks(self):
        for plugin_name, (plugin, callback) in self.offline_callbacks.items():
            try:
                callback()
            except Exception as ex:
                self.logger.error('Plugin %s failed to handle on offline callback' % plugin_name)
                self.thrall.unload_plugin(plugin, ex)

        self.offline_callbacks.clear()

    def start_restart(self, plugin, rcon_warning, rcon_restart, discord_warning, discord_restart, offline_callback=None):
        if plugin.name not in self.offline_callbacks and offline_callback is not None:
            self.offline_callbacks[plugin.name] = (plugin, offline_callback)

        if self.active_restart_info is not None:
            return

        self.logger.info('Beginning restart for ' + plugin.name)

        template = {
            'timeleft': self.warning_minutes,
            'timeunit': 'minute' if self.warning_minutes == 1 else 'minutes',
            'newline': '\n'
        }

        self.active_restart_info = RestartInformation(
            plugin=plugin,
            rcon_warning=Template(rcon_warning).safe_substitute(template),
            rcon_restart=Template(rcon_restart).safe_substitute(template),
            discord_warning=Template(discord_warning).safe_substitute(template),
            discord_restart=Template(discord_restart).safe_substitute(template),
            restart_time=datetime.now() + timedelta(minutes=self.warning_minutes))

        if self.warning_minutes > 0:
            self.send_warning_message()

        self.tick_early()

    def send_warning_message(self):
        self.logger.info('The server is being restarted in %s minutes.' % self.warning_minutes)

        if self.warning_send_rcon and self.rcon is not None:
            self.rcon.broadcast(self.active_restart_info.rcon_warning)

        if self.warning_send_discord and self.discord is not None:
            self.discord.send_message(self.active_restart_info.plugin.name, self.active_restart_info.discord_warning)

    def send_restart_message(self):
        if self.restart_send_rcon and self.rcon is not None:
            self.rcon.broadcast(self.active_restart_info.rcon_restart)

        if self.restart_send_discord and self.discord is not None:
            self.discord.send_message(self.active_restart_info.plugin.name, self.active_restart_info.discord_restart)

    def tick_interval(self):
        if self.active_restart_info is None:
            return

        if datetime.now() < self.active_restart_info.restart_time:
            return

        self.send_restart_message()
        time.sleep(1)
        self.active_restart_info = None
        self.server.close()
        self.notify_offline_callbacks()
        self.server.start()