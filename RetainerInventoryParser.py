class RetainerInventoryParser:
    LANG_EN = "name_en"
    LANG_JA = "name_ja"
    LANG_DE = "name_de"
    LANG_FR = "name_fr"
    NQ_VALUE = ["00", "02"]
    HQ_VALUE = ["01", "03"]
    MYSTERY_QUALITIES = ["7C"]  # peach confetti has a 'quality' of 7C for some reason. ????????

    def __init__(self, logfile, lang):
        self.lang = lang
        self.unhandled_qualities = []
        assert self.lang is self.LANG_DE or lang is self.LANG_EN or lang is self.LANG_FR or lang is self.LANG_JA
        # structure...
        # list of retainers
        # each retainer has a name and a list of items
        # each item has an ID, a quantity, and a quality flag
        # quality flags are:

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
            '[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|(?P<frame>[0-9A-Fa-f]{8})\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}'
            '\|[0-9A-Fa-f]{5}(?P<quantity>[0-9A-Fa-f]{3})\|(?P<mystery_tag>[0-9A-Fa-f]{4})(?P<item_id>[0-9A-Fa-f]{4})'
            '\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]'
            '{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{6}(?P<quality>[0-9A-Fa-f]{2})')
        retainer_name_finder = re.compile('.*?\|.*\|003d\|(?P<retainer_name>.*?)\|')
        reset_flag_finder = re.compile('\d*?\|.*?\|00000028\|')
        current_retainer = {"Name": "(Failed to detect name!)", "Itemlist": []}
        current_itemlist = []
        for line in iter(self.log.split("\\n")):
            match = item_finder.match(line)
            if match is not None and match.group('quality') != "FF" and match.group('frame') != "FFFFFFFF" \
                    and match.group("item_id") != "00000000" and match.group('quantity') != "000" and \
                    match.group('quality') != "08" and match.group('mystery_tag') == "0000":
                if resettable:
                    current_itemlist = []
                    resettable = False
                if match.group('quality') in self.HQ_VALUE:
                    is_high_quality = True
                elif match.group('quality') in self.NQ_VALUE:
                    is_high_quality = False
                elif match.group('quality') in self.MYSTERY_QUALITIES:
                    is_high_quality = False
                else:
                    self.unhandled_qualities.append(match.group('quality'))
                    is_high_quality = False
                if int(match.group('quantity'), 16) > 0:
                    current_itemlist.append((int(match.group('item_id'), 16), int(match.group('quantity'), 16),
                                             is_high_quality))
            else:
                match = reset_flag_finder.match(line)
                if match is not None:
                    resettable = True
                if current_itemlist:  # if we don't have an itemlist, any matches would be unrelated retainer dialog
                    match = retainer_name_finder.match(line)
                    if match is not None:
                        current_retainer['Name'] = match.group('retainer_name')
                        current_retainer['Itemlist'] = current_itemlist.copy()
                        self.retainers.append(current_retainer.copy())
                        current_itemlist = []
                        current_retainer = {"Name": "(Failed to detect name!)", "Itemlist": []}
                        resettable = False
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
                if item[0] in armoire_capable:
                    self.armoire_alerts.append({'retainer': name, 'item': item})
                if item[0] > 20:  # ignore gil, crystals, etc
                    tuple_id = (str(item[0]) + str(item[2]))
                    itemid_owners.setdefault(tuple_id, []).append(((name, item[1]), item[0], item[2]))
        for item_uuid, owners in itemid_owners.items():
            if len(owners) > 1:
                item_max = next(item_dict for item_dict in itemlist_json if item_dict["id"] == owners[0][1])
                if item_max["stack_size"] > 1:
                    self.split_stack_alerts.append((owners[0][1], owners[0][2], owners))

        for alerty in self.armoire_alerts:
            item_names = next(item_dict for item_dict in itemlist_json if item_dict["id"] == int(alerty['item'][0]))
            self.error_strings.append("Item <strong>{item}</strong> on <strong>{retainer}</strong> can be placed in "
                                      "the armoire.".format(retainer=alerty['retainer'],
                                                            item=item_names[self.lang]))

        for alert in self.split_stack_alerts:
            ownerstring = ""
            for owner in alert[2]:
                ownerstring = ownerstring + ("{0} (x{1}), ".format(owner[0][0], owner[0][1]))
            ownerstring = ownerstring.replace('\\', '')
            if alert[1]:
                hq_string = "HQ"
            else:
                hq_string = "NQ"
            item_names = next(item_dict for item_dict in itemlist_json if item_dict["id"] == alert[0])
            self.error_strings.append(
                "Item <strong>{item}({HQ})</strong> is on multiple retainers: <strong>{ownerstring}</strong>".format(
                    item=item_names[self.lang], HQ=hq_string, ownerstring=ownerstring))


class InvalidLogError(Exception):
    def __init__(self, message):
        self.message = message
