class RetainerInventoryParser:
    LANG_EN = "name_en"
    LANG_JA = "name_ja"
    LANG_DE = "name_de"
    LANG_FR = "name_fr"

    def __init__(self, logfile, lang):
        self.lang = lang
        assert self.lang is self.LANG_DE or lang is self.LANG_EN or lang is self.LANG_FR or lang is self.LANG_JA
        # structure...
        # list of retainers
        # each retainer has a name and a list of items
        # each item has an ID, a quantity, and a quality flag
        # quality flags are:
        # 8200 - NQ
        # 8201 - HQ

        self.log = logfile
        self.retainers = []
        self.armoire_alerts = []
        #  each element is a dict with keys "retainer" and "item"
        self.split_stack_alerts = []
        #  each element is a tuple of ID, HQ bool, and list of owners
        self.error_strings = []
        self.__parse_retainers()
        self.__find_optimizations()

    def __parse_retainers(self):
        import re
        resettable = False
        item_finder = re.compile(
            '\d*?\|.*?\|00000060\|[0-9A-F]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|'
            '[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|'
            '(?P<quantity>[0-9A-Fa-f]{8})\|(?P<item_id>[0-9A-Fa-f]{8})\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]'
            '{8}\|[0-9A-Fa-f]{4}(?P<quality>[0-9A-Fa-f]{4})')
        retainer_name_finder = re.compile('\d*\|.*\|003d\|(?P<retainer_name>.*?)\|')
        current_retainer = {"Name": "(Failed to detect name!)", "Itemlist": []}
        current_itemlist = []
        for line in self.log:
            if "FFXIV PLUGIN VERSION" in line:  # if ACT has been run multiple times in a day, use the latest session.
                resettable = True  # ...unless there's no inventory data in the latest session.
            match = item_finder.match(line)
            if match is not None:
                if resettable:
                    resettable = False
                    self.retainers = []
                    current_retainer = {"Name": "(Failed to detect name!)", "Itemlist": []}
                    current_itemlist = []
                if match.group('quality') == "8201":
                    is_high_quality = True
                elif match.group('quality') == "8200":
                    is_high_quality = False
                else:
                    raise InvalidLogError("Anomalous item quality:" + match.group("quality"))
                current_itemlist.append((match.group('item_id'), match.group('quantity'), is_high_quality))
            else:
                if current_itemlist:  # if we don't have an itemlist, any matches would be unrelated retainer dialog
                    match = retainer_name_finder.match(line)
                    if match is not None:
                        current_retainer['Name'] = match.group('retainer_name')
                        current_retainer['Itemlist'] = current_itemlist.copy()
                        self.retainers.append(current_retainer)
                        current_itemlist = []
                        current_retainer = []
        if current_itemlist:
            current_retainer['Name'] = "(Missing retainer name - logfile may have ended early?)"
            current_retainer['Itemlist'] = current_itemlist.copy()
            self.retainers.append(current_retainer)
        #  retainer inventory list parsing is done - now we search for optimizations

    def __find_optimizations(self):
        import json
        #  search for Armoire-compatible items
        armoire_capable = []

        for key, obj in json.load(open("data/armoire.json")).items():
            armoire_capable.append(obj['item'])
        itemlist_json = json.load(open("data/itemlist.json"))
        itemid_owners = {}
        self.armoire_alerts = []
        for retainer in self.retainers:
            name = retainer['Name']
            for item in retainer['Itemlist']:
                if int(item[0]) in armoire_capable:
                    self.armoire_alerts.append({'retainer': name, 'item': item})
                itemid_owners.setdefault((item[0], item[2]), []).append((name, item[1]))
        for item_uuid, owners in itemid_owners.items():
            if len(owners) > 1:
                if itemlist_json[item_uuid[0]]["stack_size"] > 1:
                    self.split_stack_alerts.append((item_uuid[0], item_uuid[1], owners))

        for alert in self.armoire_alerts:
            self.error_strings.append("Item <strong>{item}</strong> on <strong>{retainer}</strong> can be placed in "
                                      "the armoire.".format(retainer=alert['retainer'], item=itemlist_json[alert[
                'item']][self.lang]))

        for alert in self.split_stack_alerts:
            ownerstring = ""
            for owner in alert[2]:
                ownerstring.join("{0} (x{1}), ".format(owner[0], owner[1]))
            if alert[1]:
                hq_string = "HQ"
            else:
                hq_string = "NQ"
            self.error_strings.append(
                "Item <strong>{item}({HQ})</strong> is on multiple retainers: <strong>{ownerstring}</strong>".format(
                    item=itemlist_json[alert[1]][self.lang], HQ=hq_string, ownerstring=ownerstring))


class InvalidLogError(Exception):
    def __init__(self, message):
        self.message = message
