# Entry point and main execution logic
import sys
import tkinter
from url import URL
from browser import Browser
from utils import load
from parser import HTMLParser, print_tree

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <url/file>")
        print("No URL provided. Opening default test file.")
        load(URL("file://README.md"))

        # Test with a simple data URL
        load(URL("data:text/html,<h1>Hello World!</h1><p>This is a test page using the data scheme.</p>"))
    else:
        # Browser().load(URL(sys.argv[1]))
        # tkinter.mainloop()
        body = URL(sys.argv[1]).request()
        nodes = HTMLParser(body).parse()
        print_tree(nodes)