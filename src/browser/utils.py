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