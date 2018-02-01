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
        if form["language"] == "de":
            lang = RetainerInventoryParser.LANG_DE
        elif form["language"] == "ja":
            lang = RetainerInventoryParser.LANG_JA
        elif form["language"] == "fr":
            lang = RetainerInventoryParser.LANG_FR
        else:
            lang = RetainerInventoryParser.LANG_EN
    else:
        lang = RetainerInventoryParser.LANG_EN
    filename = str(form["file"].value)
    parser = RetainerInventoryParser(filename, lang)

    stringify = ""
    if parser.error_strings:
        x = parser.error_strings
        for message in x:
            stringify = stringify + ("<li>{0}</li>".format(message))
    else:
        stringify = "<li>No optimizations found, you seem pretty organized!</li>"
    print(open("template/results.html").read().format(stringify))
else:

    print(open("template/error-nofile.html").read())
