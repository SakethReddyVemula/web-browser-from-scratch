class Text:
    def __init__(self, text, parent):
        self.text = text
        self.children = [] # always empty, just for consistency kept here
        self.parent = parent

    def __repr__(self):
        return repr(self.text)


class Element:
    def __init__(self, tag, attributes, parent):
        self.tag = tag
        self.attributes = attributes
        self.children = []
        self.parent = parent
        

    def __repr__(self):
        return "<" + self.tag + ">"


class HTMLParser:
    def __init__(self, body):
        self.body = body
        self.unfinished = []
        self.SELF_CLOSING_TAGS = [
            "area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr",
        ]
        self.HEAD_TAGS = [
            "base", "basefont", "bgsound", "noscript",
            "link", "meta", "title", "style", "script",
        ]


    def parse(self):
        text = ""
        in_tag = False
        for c in self.body:
            if c == "<":
                in_tag = True
                if text:
                    self.add_text(text)
                text = ""
            elif c == ">":
                in_tag = False
                self.add_tag(text)
                text = ""
            else:
                text += c
        
        if not in_tag and text:
            self.add_text(text)

        return self.finish()
    
    
    def add_text(self, text):
        # add a text node as child of the last unfinished node
        if text.isspace():
            return # skip all whitespaces-only text nodes such as "\n" after docstring. Otherwise leads to complexity in our simple browser
        self.implicit_tags(None)
        parent = self.unfinished[-1]
        node = Text(text, parent)
        parent.children.append(node)
        

    def add_tag(self, tag):
        tag, attributes= self.get_attributes(tag)

        if tag.startswith('!'):
            return # ignore the "!DOCTYPE html" as it doesn't make any difference to our simple, cute browser
            # this also throws out comments :))
        self.implicit_tags(tag)
        if tag.startswith('/'):
            # pop from unfinished, and add the popped node as the child of the unifinished[-1]
            if len(self.unfinished) == 1: # handle last node
                return
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)
        elif tag in self.SELF_CLOSING_TAGS:
            parent = self.unfinished[-1]
            node = Element(tag, attributes, parent)
            parent.children.append(node)
        else:
            parent = self.unfinished[-1] if self.unfinished else None # handle first node also
            node = Element(tag, attributes, parent)
            self.unfinished.append(node)


    def finish(self):
        """Completes the Incomplete Tree to final, complete tree"""
        if not self.unfinished:
            self.implicit_tags(None)
        while len(self.unfinished) > 1:
            node = self.unfinished.pop()
            parent = self.unfinished[-1]
            parent.children.append(node)

        return self.unfinished.pop()
    
    def get_attributes(self, text):
        parts = text.split()
        tag = parts[0].casefold()
        attributes = {}

        for attr_pair in parts[1:]:
            if "=" in attr_pair:
                key, value = attr_pair.split("=", 1)
                if len(value) > 2 and value[0] in ["'", "\""]:
                    value = value[1:-1]  # Remove quotes first
                attributes[key.casefold()] = value  # Then store the unquoted version
            else:
                attributes[attr_pair.casefold()] = ""

        return tag, attributes  
    
    def implicit_tags(self, tag):
        while True:
            open_tags = [node.tag for node in self.unfinished]
            
            if open_tags == [] and tag != "html":
                self.add_tag("html")
            elif open_tags == ["html"] and tag not in ["head", "body", "/html"]:
                if tag in self.HEAD_TAGS:
                    self.add_tag("head")
                else:
                    self.add_tag("body")
            elif open_tags == ["html", "head"] and tag not in ["/head"] + self.HEAD_TAGS:
                self.add_tag("/head")
            else:
                break # exit out of the loop
    

def print_tree(node, indent=0):
    print(" " * indent, node)

    for child in node.children:
        print_tree(child, indent + 2)
