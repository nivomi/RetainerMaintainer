#!/usr/bin/env python3
# Set the above to match a virtualenv if you use one?
import cgi
import cgitb

from RetainerInventoryParser import RetainerInventoryParser

cgitb.enable()
print("Content-Type: text/html")  # HTML is following
print()  # blank line, end of headers

form = cgi.FieldStorage()
if "file" in form:
    if "language" in form:
        if form["language"].value == "de":
            lang = RetainerInventoryParser.LANG_DE
        elif form["language"].value == "ja":
            lang = RetainerInventoryParser.LANG_JA
        elif form["language"].value == "fr":
            lang = RetainerInventoryParser.LANG_FR
        else:
            lang = RetainerInventoryParser.LANG_EN
    else:
        lang = RetainerInventoryParser.LANG_EN
    filename = str(form["file"].value)
    parser = RetainerInventoryParser(filename, lang)

    stringify = ""
    if parser.unhandled_qualities:
        x = ', '.join(parser.unhandled_qualities)
        stringify = stringify + '<li class="is-danger">Your logfile contains item data that is unhandled in the ' \
                                'current version of our parser. Usually, this is just because of the strange, ' \
                                'strange ways Retainer data is stored, and doesn\t affect any results. If you\'d ' \
                                'like, feel free to email us your ' \
                                'logfile so that we can improve our parser. ' \
                                'Error code: OddQual{0}</li>'.format(x)
    if parser.error_strings:
        x = parser.error_strings
        for message in x:
            stringify = stringify + ("<li>{0}</li>".format(message))
    else:
        stringify = "<li>No optimizations found, you seem pretty organized!</li>"
    print(open("template/results.html").read().format(stringify))
else:

    print(open("template/error-nofile.html").read())
