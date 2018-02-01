import re


class RetainerInventoryParser:

    def __init__(self, logfile):

        # structure...
        # list of retainers
        # each retainer has a name and a list of items
        # each item has an ID, a quantity, and a quality flag
        # quality flags are:
        # 8200 - NQ
        # 8201 - HQ

        self.log = logfile
        self.retainers = []
        self.armoire_items = []

        self.__parse_retainers()

    def __parse_retainers(self):
        resettable = False
        item_finder = re.compile(
            '\d*?\|.*?\|00000060\|[0-9A-F]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|(?P<quantity>[0-9A-Fa-f]{8})\|(?P<item_id>[0-9A-Fa-f]{8})\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{8}\|[0-9A-Fa-f]{4}(?P<quality>[0-9A-Fa-f]{4})')
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
                current_itemlist.append((match.group('item_id'), match.group('quantity'), match.group('quality')))
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

    #  search for Armoire-compatible items
    def __armoire_search(self):
        for retainer in self.retainers:
            name = retainer['Name']
            for item in retainer['Itemlist']:
                exit(99)
    #  search for same-item-on-different-retainer


class InvalidLogError(Exception):
    def __init__(self, message, line_number):
        self.message = message
        self.line_number = line_number
