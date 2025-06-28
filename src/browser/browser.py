# Main browser GUI and rendering
import tkinter
from constants import WIDTH, HEIGHT, VSTEP, SCROLL_STEP
# from layout import Layout
# from layout_tree_simple import Layout # Use tree based layout instead of normal lexer based
from layout_tree import DocumentLayout, Element # Use tree based layout instead of normal lexer based
# from lexer import lex
from parser import HTMLParser, print_tree
from css_parser import style, CSSParser
from utils import tree_to_list, cascade_priority

# default user-agent style sheet
DEFAULT_STYLE_SHEET = CSSParser(open("user_agent.css").read()).parse()


def paint_tree(layout_object, display_list):
    """Helper function to recursively call paint() on all layout objects"""
    display_list.extend(layout_object.paint()) # call paint before calling paint_tree recursively -> subtree paints on top of curr_node

    for child in layout_object.children:
        paint_tree(child, display_list)


class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT
        )
        self.canvas.pack()

        # field for tracking how far we have scrolled
        self.scroll = 0
        # bind the down arrow key to scroll
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)


    # load and draw the text, character by character
    def load(self, url):
        # body = url.request()
        # text = []
        # if url.schema == "view-source":
        #     # for view-source, print the HTML as plain text (no tag filtering)
        #     text = body
        # else:
        #     # other than view-source schema
        #     text = lex(body)
        # self.display_list = Layout(text).display_list
        # self.draw()

        body = url.request()
        self.nodes = HTMLParser(body).parse()
        # self.display_list = Layout(self.nodes).display_list
        # self.draw()

        # apply default (from user-agent) style sheets
        rules = DEFAULT_STYLE_SHEET.copy()
        style(self.nodes, sorted(rules, key=cascade_priority)) # cascading, file-order acts as tie-breaker (as required) (python sorted works like that)
        
        links = []

        # parsing <link rel="stylesheet" href="/main.css"> ...
        for node in tree_to_list(self.nodes, []):
            if isinstance(node, Element) and node.tag == "link" and node.attributes.get("rel") == "stylesheet" and "href" in node.attributes:
                links.append(node.attributes["href"])

        for link in links:
            style_url = url.resolve(link)
            try:
                body = style_url.request()
            except:        
                continue
            rules.extend(CSSParser(body).parse())

        
        self.document = DocumentLayout(self.nodes) # constructing layout objects
        self.document.layout() # actually laying out "layout objects" earlier constructed
        # print_tree(self.document.node)
        self.display_list = []
        paint_tree(self.document, self.display_list)
        self.draw()

    
    def draw(self):
        self.canvas.delete("all") # delete the old text before drawing new one, o/w it will lead to blackboxes eventually
        # for x, y, c, font in self.display_list:

        #     # for fast rendering: skip drawing characters that are offscreen
        #     if y > self.scroll + HEIGHT: continue
        #     if y + VSTEP < self.scroll: continue

        #     self.canvas.create_text(x, y - self.scroll, text=c, anchor="nw", font=font) # anchor = "nw" -> tells tkinter that the coordinates are the top-left (northwest), and not the center as assumed in default
        for cmnd in self.display_list:
            if cmnd.top > self.scroll + HEIGHT:
                continue
            if cmnd.bottom < self.scroll:
                continue
            cmnd.execute(self.scroll, self.canvas)



    def scrolldown(self, e):
        max_y = max(self.document.height + 2*VSTEP - HEIGHT, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        self.draw()

    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
        self.scroll = max((-1) * VSTEP, self.scroll - SCROLL_STEP)
        self.draw()