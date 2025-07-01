# Main browser GUI and rendering
import tkinter
from constants import WIDTH, HEIGHT, VSTEP, SCROLL_STEP
# from layout import Layout
# from layout_tree_simple import Layout # Use tree based layout instead of normal lexer based
from layout_tree import DocumentLayout, Element, Text, get_font, DrawText, DrawRect, Rect # Use tree based layout instead of normal lexer based
# from lexer import lex
from parser import HTMLParser, print_tree
from css_parser import style, CSSParser
from utils import tree_to_list, cascade_priority
from url import URL

# default user-agent style sheet
DEFAULT_STYLE_SHEET = CSSParser(open("user_agent.css").read()).parse()


def paint_tree(layout_object, display_list):
    """Helper function to recursively call paint() on all layout objects"""
    display_list.extend(layout_object.paint()) # call paint before calling paint_tree recursively -> subtree paints on top of curr_node

    for child in layout_object.children:
        paint_tree(child, display_list)


class DrawOutline:
    def __init__(self, rect, color, thickness):
        self.rect = rect
        self.color = color
        self.thickness = thickness

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.rect.left,
            self.rect.top - scroll,
            self.rect.right,
            self.rect.bottom - scroll,
            width = self.thickness,
            outline = self.color
        )

class DrawLine:
    def __init__(self, x1, y1, x2, y2, color, thickness):
        self.rect = Rect(x1, y1, x2, y2)
        self.color = color
        self.thickness = thickness

    def execute(self, scroll, canvas):
        canvas.create_line(
            self.rect.left,
            self.rect.top - scroll,
            self.rect.right,
            self.rect.bottom - scroll,
            fill = self.color,
            width = self.thickness
        )


class Chrome:
    def __init__(self, browser):
        self.browser = browser

        self.font = get_font(15, "normal", "roman")
        self.font_height = self.font.metrics("linespace")

        self.padding = 5
        self.tabbar_top = 0
        self.tabbar_bottom = self.font_height + 2 * self.padding

        plus_width = self.font.measure("+") + 2 * self.padding
        self.newtab_rect = Rect(
            self.padding,
            self.padding,
            self.padding + plus_width,
            self.padding + self.font_height
        )

        self.urlbar_top = self.tabbar_bottom
        self.urlbar_bottom = self.urlbar_top + self.font_height + 2 * self.padding
        self.bottom = self.urlbar_bottom

        back_width = self.font.measure("<") + 2 * self.padding
        self.back_rect = Rect(
            self.padding, # left
            self.urlbar_top + self.padding, # top
            self.padding + back_width, # right
            self.urlbar_bottom - self.padding # bottom
        )

        self.address_rect = Rect(
            self.back_rect.top + self.padding, # left
            self.urlbar_top + self.padding, # top
            WIDTH - self.padding, # right
            self.urlbar_bottom - self.padding # bottom
        )

        self.focus = None
        self.address_bar = ""


    def tab_rect(self, i):
        tabs_start = self.newtab_rect.right + self.padding
        tab_width = self.font.measure("Tab X") + 2 * self.padding
        return Rect(
            tabs_start + tab_width * i,
            self.tabbar_top,
            tabs_start + tab_width * (i + 1),
            self.tabbar_bottom
        )
    

    def click(self, x, y):
        self.focus = None
        if self.newtab_rect.contains_point(x, y):
            self.browser.new_tab(URL("https://browser.engineering/chrome.html"))
        elif self.back_rect.contains_point(x, y):
            self.browser.active_tab.go_back()
        elif self.address_rect.contains_point(x, y):
            self.focus = "address_bar"
            self.address_bar = ""
        else:
            for i, tab in enumerate(self.browser.tabs):
                if self.tab_rect(i).contains_point(x, y):
                    self.browser.active_tab = tab
                    break
    
    def keypress(self, char):
        if self.focus == "address_bar":
            self.address_bar += char


    def enter(self):
        if self.focus == "address_bar":
            self.browser.active_tab.load(URL(self.address_bar))
            self.focus = None

    def backspace(self):
        if self.focus == "address_bar":
            self.address_bar = self.address_bar[:-1]
    

    def paint(self):
        cmnds = []

        cmnds.append(DrawRect(
            Rect(0, 0, WIDTH, self.bottom), "white"
        ))
        cmnds.append(DrawLine(
            0, self.bottom, WIDTH, self.bottom, "black", 1
        ))

        cmnds.append(DrawOutline(self.newtab_rect, "black", 1))
        cmnds.append(DrawText(
            self.newtab_rect.left + self.padding,
            self.newtab_rect.top,
            "+",
            self.font,
            "black"
        ))

        for i, tab in enumerate(self.browser.tabs):
            bounds = self.tab_rect(i)

            cmnds.append(DrawLine(
                bounds.left, 0, bounds.left, bounds.bottom, "black", 1
            ))
            cmnds.append(DrawLine(
                bounds.right, 0, bounds.right, bounds.bottom, "black", 1
            ))
            cmnds.append(DrawText(
                bounds.left + self.padding,
                bounds.top + self.padding,
                "Tab {}".format(i),
                self.font,
                "black"
            ))

            # to identify the active tab
            if tab == self.browser.active_tab:
                cmnds.append(DrawLine(
                    0, bounds.bottom, bounds.left, bounds.bottom, "black", 1
                ))

                cmnds.append(DrawLine(
                    bounds.right, bounds.bottom, WIDTH, bounds.bottom, "black", 1
                ))

        cmnds.append(DrawOutline(
            self.back_rect, # rect
            "black", # color
            1 # thickness
        ))

        cmnds.append(DrawText(
            self.back_rect.left + self.padding, # x1
            self.back_rect.top, # y1
            "<", # text
            self.font, # font
            "black" # color
        ))

        cmnds.append(DrawOutline(
            self.address_rect, # rect
            "black", # color
            1 # thickness
        ))

        if self.focus == "address_bar":
            cmnds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                self.address_bar,
                self.font,
                "black"
            ))

            # draw a cursor while typing
            w = self.font.measure(self.address_bar)
            cmnds.append(DrawLine(
                self.address_rect.left + self.padding + w,
                self.address_rect.top,
                self.address_rect.left + self.padding + w,
                self.address_rect.bottom,
                "red",
                1
            ))
        else:
            url = str(self.browser.active_tab.url)
            cmnds.append(DrawText(
                self.address_rect.left + self.padding,
                self.address_rect.top,
                url,
                self.font,
                "black"
            ))

        return cmnds



    

    
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

        self.chrome = Chrome(self)
        
        # bind the down arrow key to scroll
        self.window.bind("<Down>", self.handle_down)
        self.window.bind("<Up>", self.handle_up)

        self.window.bind("<Button-1>", self.handle_click)
        
        # bind key presses
        self.window.bind("<Key>", self.handle_key)
        self.window.bind("<Return>", self.handle_enter)
        self.window.bind("<BackSpace>", self.handle_backspace)


    def new_tab(self, url):
        new_tab = Tab(HEIGHT - self.chrome.bottom)
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
        if e.y < self.chrome.bottom:
            self.chrome.click(e.x, e.y)
        else:
            tab_y = e.y - self.chrome.bottom
            self.active_tab.click(e.x, tab_y)
        self.draw()

    def handle_key(self, e):
        if len(e.char) == 0:
            return
        if not (0x20 <= ord(e.char) < 0x7f): # ASCII range
            return
        
        self.chrome.keypress(e.char)
        self.draw()

    def handle_enter(self, e):
        self.chrome.enter()
        self.draw()

    def handle_backspace(self, e):
        self.chrome.backspace()
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        self.active_tab.draw(self.canvas, self.chrome.bottom)

        # draw the tabs after main content
        for cmnd in self.chrome.paint():
            cmnd.execute(0, self.canvas)
    



class Tab:
    def __init__(self, tab_height):
        # click handling
        self.url = None # for storing the current page's URL

        # field for tracking how far we have scrolled
        self.scroll = 0

        # changes for accounting for tab
        self.tab_height = tab_height # tab height means the height of the remaining window after the bar on top (and not the height of the "tab")

        self.history = []

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
        self.history.append(url)
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

    
    def draw(self, canvas, offset):
        # self.canvas.delete("all") # delete the old text before drawing new one, o/w it will lead to blackboxes eventually
        # for x, y, c, font in self.display_list:

        #     # for fast rendering: skip drawing characters that are offscreen
        #     if y > self.scroll + HEIGHT: continue
        #     if y + VSTEP < self.scroll: continue

        #     self.canvas.create_text(x, y - self.scroll, text=c, anchor="nw", font=font) # anchor = "nw" -> tells tkinter that the coordinates are the top-left (northwest), and not the center as assumed in default
        for cmnd in self.display_list:
            if cmnd.rect.top > self.scroll + self.tab_height:
                continue
            if cmnd.rect.bottom < self.scroll:
                continue
            cmnd.execute(self.scroll - offset, canvas)



    def scrolldown(self):
        max_y = max(self.document.height + 2*VSTEP - self.tab_height, 0)
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

        
    def go_back(self):
        if len(self.history) > 1:
            self.history.pop()
            back = self.history.pop()
            self.load(back) # load will again push the back into the self.history list later
        
