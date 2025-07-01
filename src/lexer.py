import re

# Text parsing and tokenization
class Text:
    def __init__(self, text):
        self.text = text

class Tag:
    def __init__(self, tag):
        self.tag = tag
        self.attributes = {}
        self._parse_attributes()

    def _parse_attributes(self):
        """Parse HTML attributes from tag string"""
        parts = self.tag.split()
        if len(parts) > 1:
            # first part is tag name, rest are attributes
            self.tag = parts[0]
            attr_string = ' '.join(parts[1:])
            self._parse_attr_string(attr_string)

        # handle closing tags
        if self.tag.startswith('/'):
            self.tag = self.tag # keep as is for closing tags
        
    def _parse_attr_string(self, attr_string):
        """Parse attribute string into key-value pairs"""
        # simple regex to match key="value" or key='value' or key=value
        pattern = r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+))'
        matches = re.findall(pattern, attr_string)
        
        for match in matches:
            key = match[0].lower()
            value = match[1] or match[2] or match[3]
            self.attributes[key] = value


def lex(body):
    out = []
    buffer = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if buffer:
                out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += c
    
    if not in_tag and buffer:
        out.append(Text(buffer))
    
    return out