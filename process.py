#!/usr/bin/python3
# Set the above to match a virtualenv if you use one?
import cgi

print("Content-Type: text/html")    # HTML is following
print()                             # blank line, end of headers

form = cgi.FieldStorage()
if "file" in form:
    exit(0)
    # TODO: process file
else:
    page = open("template/error-nofile.html")
    print(page)
