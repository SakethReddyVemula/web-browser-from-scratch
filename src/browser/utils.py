# Utility functions
def show(body):
    length = len(body)
    i = 0
    in_tag = False
    while i < length:
        if body[i:i + 4] == "&lt;":
            print("<", end="")
            i += 4
            continue
        elif body[i:i + 4] == "&gt;":
            print(">", end="")
            i += 4
            continue
        elif body[i] == "<":
            in_tag = True
        elif body[i] == ">":
            in_tag = False
        elif not in_tag:
            print(body[i], end="")
        i += 1

def load(url):
    body = url.request()
    if url.schema == "view-source":
        # for view-source, print the HTML as plain text (no tag filtering)
        print(body, end="")
    else:
        # other than view-source schema
        show(body)


# Helper Functions


def tree_to_list(tree, list):
    """Turns a tree of nodes into a list of nodes. Works on both HTML and Layout Trees."""
    list.append(tree)
    
    for child in tree.children:
        tree_to_list(child, list)

    return list


def cascade_priority(rule):
    selector, body = rule
    return selector.priority



# Helper function to parse font-sizes properly

def parse_font_size(font_size_str):
        """
        Parse CSS font-size value and return size in pixels.
        Handles px units, keywords, and other common cases.
        """
        font_size_str = font_size_str.strip().lower()
        
        # Handle keyword values
        keyword_sizes = {
            'xx-small': 9,
            'x-small': 10,
            'small': 12,
            'medium': 16,  # default browser font size
            'large': 18,
            'x-large': 24,
            'xx-large': 32
        }
        
        if font_size_str in keyword_sizes:
            return keyword_sizes[font_size_str]
        
        # Handle px values
        if font_size_str.endswith('px'):
            try:
                return int(float(font_size_str[:-2]))
            except ValueError:
                return 16  # fallback to default
        
        # Handle pt values (1pt = 4/3 px approximately)
        if font_size_str.endswith('pt'):
            try:
                pt_value = float(font_size_str[:-2])
                return int(pt_value * 4 / 3)
            except ValueError:
                return 16
        
        # Handle em values (relative to parent, assume 16px base for now)
        if font_size_str.endswith('em'):
            try:
                em_value = float(font_size_str[:-2])
                return int(em_value * 16)  # assuming 16px base
            except ValueError:
                return 16
        
        # Handle percentage values
        if font_size_str.endswith('%'):
            try:
                percent_value = float(font_size_str[:-1])
                return int((percent_value / 100) * 16)  # assuming 16px base
            except ValueError:
                return 16
        
        # Try to parse as a number (assume px)
        try:
            return int(float(font_size_str))
        except ValueError:
            return 16  # fallback to default browser font size