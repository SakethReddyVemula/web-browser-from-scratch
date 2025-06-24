# Layout and font management
import tkinter
import tkinter.font
from constants import WIDTH, HEIGHT, HSTEP, VSTEP
from lexer import Text, Tag

FONTS = {}

# font management system
def get_font(size, weight, style):
    key = (size, weight, style)
    if key not in FONTS:
        font = tkinter.font.Font(size=size, weight=weight,
            slant=style)
        label = tkinter.Label(font=font)
        FONTS[key] = (font, label)
    return FONTS[key][0]


class Layout:
    def __init__(self, tokens):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.line = [] # to store line-to-be

        # alignment tracking
        self.align = "left" # can be "left", "center", or "right"
        self.in_title_h1 = False # track if we are insider <h1 class="title">

    
        for tok in tokens:
            self.token(tok)

        self.flush()

        
    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
        elif isinstance(tok, Tag):
            if tok.tag == "h1":
                # check if this h1 has class="title"
                if tok.attributes.get("class") == "title":
                    self.in_title_h1 = True
                    self.align = "center"
                    self.flush() # start fresh line for h1
            elif tok.tag == "/h1":
                if self.in_title_h1 == True:
                    self.flush() # finish current line
                    self.in_title_h1 = False 
                    self.align = "left" # reset to left alignment
                    self.cursor_y += VSTEP # add some spacing after h1

            elif tok.tag == "i":
                self.style = "italic"
            elif tok.tag == "/i":
                self.style = "roman"
            elif tok.tag == "b":
                self.weight = "bold"
            elif tok.tag == "/b":
                self.weight = "normal"
            elif tok.tag == "small":
                self.size -= 2
            elif tok.tag == "/small":
                self.size += 2
            elif tok.tag == "big":
                self.size += 4
            elif tok.tag == "/big":
                self.size -= 4
            elif tok.tag == "br":
                self.flush()
            elif tok.tag == "/p":
                self.flush()
                self.cursor_y += VSTEP


    def word(self, word):
        font = get_font(self.size, self.weight, self.style)
        
        w = font.measure(word) # width taken by that word
        if self.cursor_x + w > WIDTH - HSTEP:
            self.flush()

        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ")
    
    def flush(self):
        if not self.line:
            return
        
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.25 * max_ascent

        # calculate line width for centering
        if self.align == "center":
            # calculate total width of the line
            line_width = 0
            if self.line:
                first_x = self.line[0][0]
                last_x, last_word, last_font = self.line[-1]
                last_word_width = last_font.measure(last_word)
                line_width = (last_x + last_word_width) - first_x

            # calculate offset to center the line
            available_width = WIDTH - 2 * HSTEP
            center_offset = (available_width - line_width) // 2

            # adjust x positions for centering
            for i, (x, word, font) in enumerate(self.line):
                centered_x = center_offset + HSTEP + (x - HSTEP)
                y = baseline - font.metrics()["ascent"]
                self.display_list.append((centered_x, y, word, font))
        
        else:
            # now place each word relative to that line and add it to the display list
            for x, word, font in self.line:
                y = baseline - font.metrics("ascent")
                self.display_list.append((x, y, word, font))
        
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent

        # update Layout's cursor_x and self.line
        self.cursor_x = HSTEP
        self.line = []