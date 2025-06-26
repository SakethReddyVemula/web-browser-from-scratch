from layout_tree import Element


# Selectors Classes

class TagSelector:
    def __init__(self, tag):
        self.tag = tag

    def matches(self, node):
        return isinstance(node, Element) and self.tag == node.tag
    


class DescendantSelector:
    def __init__(self, ancestor, descendant):
        self.ancestor = ancestor
        self.descendant = descendant

    def matches(self, node):
        if not self.descendant.matches(node):
            return False
        while node.parent:
            if self.ancestor.matches(node.parent):
                return True
            node = node.parent
        return False


# CSS Parser

class CSSParser:
    def __init__(self, s):
        self.s = s
        self.i = 0

    def whitespace(self):
        while self.i < len(self.s) and self.s[self.i].isspace():
            self.i += 1

    def word(self):
        start = self.i
        while self.i < len(self.s):
            if self.s[self.i].isalnum() or self.s[self.i] in "#-.%":
                self.i += 1
            else:
                break
        if not (self.i > start):
            raise Exception("Parsing error")
        return self.s[start:self.i]
    
    def literal(self, literal):
        if self.i >= len(self.s) or self.s[self.i] != literal:
            raise Exception("Parsing Error")
        self.i += 1

    def pair(self):
        self.whitespace()
        prop = self.word() # property
        self.whitespace()
        self.literal(":") # ":"
        self.whitespace()
        val = self.word() # value
        return prop.casefold(), val
    
    def body(self):
        """returns a list of pair of `property-value`"""
        pairs = {}

        while self.i < len(self.s) and self.s[self.i] != "}":
            try: # remove try (debugging)
                prop, val = self.pair()
                pairs[prop.casefold()] = val
                self.whitespace()
                self.literal(";")
                self.whitespace()
            except Exception:
                why = self.ignore_until([";", "}"])
                if why == ";":
                    self.literal(";")
                    self.whitespace()
                else:
                    break
        
        return pairs
    
    def ignore_until(self, chars):
        """Function to skip property-value pairs that don't parse"""
        while self.i < len(self.s):
            if self.s[self.i] in chars:
                return self.s[self.i]
            else:
                self.i += 1
        
        return None
    
    # Selector related method
    
    def selector(self):
        """returns an object of type `TagSelector` with descendants (if any)"""
        out = TagSelector(self.word().casefold())
        self.whitespace()

        while self.i < len(self.s) and self.s[self.i] != "{":
            tag = self.word()
            descendant = TagSelector(tag.casefold())
            out = DescendantSelector(out, descendant)
            self.whitespace()
        
        return out
    

    def parse(self):
        rules = []
        
        while self.i < len(self.s):
            try:
                self.whitespace()
                selector = self.selector() # h, p, ul

                self.literal("{")
                
                self.whitespace()
                body = self.body() # "background-color": "blue"; ...;
                
                self.literal("}")

                rules.append((selector, body))

            except Exception:
                why = self.ignore_until(["}"])
                if why == "}":
                    self.literal("}")
                    self.whitespace()
                else:
                    break

        return rules
    

def style(node, rules):
    # store CSS styles in node.style dictionary
    node.style = {}

    # apply default rules (aka "user agent" style sheet. User agent, like the Memex)
    for selector, body in rules:
        if not selector.matches(node):
            continue
        for property, value in body.items():
            node.style[property] = value


    # overwrite the default style sheets
    if isinstance(node, Element) and "style" in node.attributes:
        pairs = CSSParser(node.attributes["style"]).body()
        for property, value in pairs.items():
            node.style[property] = value
    
    # recurse through the HTML tree, to set all the children's style also the same
    for child in node.children:
        style(child, rules)







    
    


    

    

    

