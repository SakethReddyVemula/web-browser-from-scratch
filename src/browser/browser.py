# Main browser GUI and rendering
import tkinter
from constants import WIDTH, HEIGHT, VSTEP, SCROLL_STEP
# from layout import Layout
# from layout_tree_simple import Layout # Use tree based layout instead of normal lexer based
from layout_tree import DocumentLayout, Element, Text # Use tree based layout instead of normal lexer based
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
        self.tabs = []
        self.active_tab = None
        
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=WIDTH,
            height=HEIGHT,
            bg="white"
        )
        self.canvas.pack()

        
        # bind the down arrow key to scroll
        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)

        self.window.bind("<Button-1>", self.handle_click)

    def new_tab(self, url):
        new_tab = Tab()
        new_tab.load(url)
        self.active_tab = new_tab
        self.tabs.append(new_tab)
        self.draw()
    
    def handle_down(self, e):
        self.active_tab.scrolldown()
        self.draw()

    def handle_up(self, e):
        self.active_tab.scrollup()
        self.draw()

    def handle_click(self, e):
        self.active_tab.click(e.x, e.y)
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.active_tab.draw(self.canvas)
    



class Tab:
    def __init__(self):
        # click handling
        self.url = None # for storing the current page's URL

        # field for tracking how far we have scrolled
        self.scroll = 0

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
        self.url = url
        body = url.request()
        self.nodes = HTMLParser(body).parse()
        # self.display_list = Layout(self.nodes).display_list
        # self.draw()

        # apply default (from user-agent) style sheets
        rules = DEFAULT_STYLE_SHEET.copy()

        links = []

        # parsing <link rel="stylesheet" href="/main.css"> ...
        for node in tree_to_list(self.nodes, []):
            if isinstance(node, Element) and node.tag == "link" and node.attributes.get("rel") == "stylesheet" and "href" in node.attributes:
                links.append(node.attributes["href"])

        for link in links:
            # print(f"css links: {link}")
            style_url = url.resolve(link)
            try:
                body = style_url.request()
            except:        
                continue
            rule = CSSParser(body).parse()
            # for property, value in rules:
                # print(f"{property} -> {value}")
            rules.extend(rule)

        style(self.nodes, sorted(rules, key=cascade_priority)) # cascading, file-order acts as tie-breaker (as required) (python sorted works like that)
        
        self.document = DocumentLayout(self.nodes) # constructing layout objects
        self.document.layout() # actually laying out "layout objects" earlier constructed
        # print_tree(self.document.node)
        self.display_list = []
        paint_tree(self.document, self.display_list)
        # self.draw()

    
    def draw(self, canvas):
        # self.canvas.delete("all") # delete the old text before drawing new one, o/w it will lead to blackboxes eventually
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
            cmnd.execute(self.scroll, canvas)



    def scrolldown(self):
        max_y = max(self.document.height + 2*VSTEP - HEIGHT, 0)
        self.scroll = min(self.scroll + SCROLL_STEP, max_y)
        # self.draw()


    def scrollup(self):
        self.scroll -= SCROLL_STEP
        self.scroll = max((-1) * VSTEP, self.scroll - SCROLL_STEP)
        # self.draw()

    
    def click(self, x, y):
        y += self.scroll 

        objs = []
        for obj in tree_to_list(self.document, []):
            if obj.x <= x < obj.x + obj.width and obj.y <= y < obj.y + obj.height:
                objs.append(obj)

        # clicked on empty space
        if not objs:
            return
        
        elt = objs[-1].node

        while elt:
            if isinstance(elt, Text):
                pass
            elif elt.tag == "a" and "href" in elt.attributes:
                url = self.url.resolve(elt.attributes["href"])
                self.scroll = 0 # set scroll of new page to 0
                return self.load(url)
            
            elt = elt.parent
        
