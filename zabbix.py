from errbot import BotPlugin
from pyzabbix import ZabbixAPI
import logging


class Zabbix(BotPlugin):
    """A plugin for interacting with Zabbix and OSBS"""
    min_err_version = '1.6.0'  # Optional, but recommended
    max_err_version = '2.0.0'  # Optional, but recommended

    itemids = {
        'prod': {
            '160728': "name",
            '160731': "phase"
        },
        'osd-qa': {
            '157192': "name",
            '157195': "phase"
        },
        'osd': {
            '188519': "name",
            '188522': "phase"
        }
    }

    last_message = {}

    def get_configuration_template(self):
        """Defines the configuration structure this plugin supports"""
        return {'URL': "http://zabbix.example.com",
                'ROOM': 'FOO',
                'USER': 'USER',
                'PASSWORD': 'PASS'}

    def get_zabbix_news(self):
        if not self.config or \
           'USER' not in self.config.keys() or \
           'PASSWORD' not in self.config.keys() or \
           'ROOM' not in self.config.keys():
            return

        self.zapi = ZabbixAPI(self.config['URL'])
        self.zapi.login(self.config['USER'], self.config['PASSWORD'])

        for host in self.itemids.keys():
            itemids = [int(x) for x in self.itemids[host].keys()]
            result = self.zapi.do_request('item.get', {'itemids': itemids, "sortfield": "itemid"})

            message = ''
            for item in result['result']:
                item_name = self.itemids[host][item['itemid']]
                item_value = item['lastvalue']
                message += " %s: %s" % (item_name, item_value)

            logging.info("[ZABBIX] message: %s" % message)
            if message:
                message = '%s:%s' % (host, message)

            if self.last_message[host] != message:
                self.last_message[host] = message

                room = self.query_room(self.config['ROOM'])
                logging.info("[ZABBIX] sending '%s' to room %s" % (message, room))
                self.send(room, message)

    def activate(self):
        super().activate()
        for host in self.itemids.keys():
            self.last_message[host] = ''
        self.start_poller(30, self.get_zabbix_news)
