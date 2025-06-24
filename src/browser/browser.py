# Main browser GUI and rendering
import tkinter
from constants import WIDTH, HEIGHT, VSTEP, SCROLL_STEP
from layout import Layout
from lexer import lex

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
        body = url.request()
        text = []
        if url.schema == "view-source":
            # for view-source, print the HTML as plain text (no tag filtering)
            text = body
        else:
            # other than view-source schema
            text = lex(body)
        self.display_list = Layout(text).display_list
        self.draw()
    
    def draw(self):
        self.canvas.delete("all") # delete the old text before drawing new one, o/w it will lead to blackboxes eventually
        for x, y, c, font in self.display_list:

            # for fast rendering: skip drawing characters that are offscreen
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue

            self.canvas.create_text(x, y - self.scroll, text=c, anchor="nw", font=font) # anchor = "nw" -> tells tkinter that the coordinates are the top-left (northwest), and not the center as assumed in default

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        self.draw()

    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
        self.draw()