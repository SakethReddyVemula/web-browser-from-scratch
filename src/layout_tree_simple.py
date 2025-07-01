# Layout and font management
import tkinter
import tkinter.font
from constants import WIDTH, HEIGHT, HSTEP, VSTEP
from parser import Text, Element

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
    def __init__(self, tree):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 16

        self.line = [] # to store line-to-be

        # alignment tracking
        self.align = "left" # can be "left", "center", or "right"
        self.in_title_h1 = False # track if we are inside <h1 class="title">

        # superscript tracking
        self.superscript = False # track if we are inside <sup> superscript mode

        # Process the tree recursively
        self.recurse(tree)
        self.flush()

        
    def recurse(self, tree):
        """Recursively process the tree structure"""
        if isinstance(tree, Text):
            # Process text node
            for word in tree.text.split():
                self.word(word)
        elif isinstance(tree, Element):
            # Process element node - opening tag
            self.open_tag(tree.tag, tree.attributes)
            
            # Process all children
            for child in tree.children:
                self.recurse(child)
            
            # Process closing tag
            self.close_tag(tree.tag)

    def open_tag(self, tag, attributes):
        """Handle opening HTML tags"""
        if tag == "h1":
            # check if this h1 has class="title"
            if attributes.get("class") == "title":
                self.in_title_h1 = True
                self.align = "center"
                self.flush() # start fresh line for h1
        elif tag == "sup":
            self.superscript = True
        elif tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.weight = "bold"
        elif tag == "small":
            self.size -= 2
        elif tag == "big":
            self.size += 4
        elif tag == "br":
            self.flush()

    def close_tag(self, tag):
        """Handle closing HTML tags"""
        if tag == "h1":
            if self.in_title_h1 == True:
                self.flush() # finish current line
                self.in_title_h1 = False 
                self.align = "left" # reset to left alignment
                self.cursor_y += VSTEP # add some spacing after h1
        elif tag == "sup":
            self.superscript = False
        elif tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "p":
            self.flush()
            self.cursor_y += VSTEP

    def word(self, word):
        # calculate word size based on superscript state
        curr_size = self.size
        if self.superscript == True:
            curr_size = max(8, int(self.size * 0.6)) # 60% of normal size, minimum 8px

        font = get_font(curr_size, self.weight, self.style)
        
        w = font.measure(word) # width taken by that word
        if self.cursor_x + w > WIDTH - HSTEP:
            self.flush()

        # store superscript flag with each word for positioning
        self.line.append((self.cursor_x, word, font, self.superscript))
        self.cursor_x += w + font.measure(" ")

    def flush(self):
        if not self.line:
            return
        
        # separate metrics calculations for normal and superscript text
        normal_metrics = []
        super_metrics = []

        for x, word, font, is_superscript in self.line:
            metrics = font.metrics()
            if is_superscript:
                super_metrics.append(metrics)
            else:
                normal_metrics.append(metrics)
            
        # calculate baseline based on normal text (if any)
        if normal_metrics:
            max_normal_ascent = max([metric["ascent"] for metric in normal_metrics])
            baseline = self.cursor_y + 1.25 * max_normal_ascent
        else:
            # if only superscript text on this line use superscript metrics
            max_super_ascent = max([metric["ascent"] for metric in super_metrics]) if super_metrics else 0
            baseline = self.cursor_y + 1.25 * max_super_ascent

        # calculate line width for centering
        if self.align == "center":
            # calculate total width of the line
            line_width = 0
            if self.line:
                first_x = self.line[0][0]
                last_x, last_word, last_font, _ = self.line[-1]
                last_word_width = last_font.measure(last_word)
                line_width = (last_x + last_word_width) - first_x

            # calculate offset to center the line
            available_width = WIDTH - 2 * HSTEP
            center_offset = (available_width - line_width) // 2

            # adjust x positions for centering
            for i, (x, word, font, is_superscript) in enumerate(self.line):
                centered_x = center_offset + HSTEP + (x - HSTEP)
                y = self._calculate_word_y(baseline, font, is_superscript, normal_metrics)
                self.display_list.append((centered_x, y, word, font))
        else:
            # now place each word relative to that line and add it to the display list
            for x, word, font, is_superscript in self.line:
                y = self._calculate_word_y(baseline, font, is_superscript, normal_metrics)
                self.display_list.append((x, y, word, font))
        
        all_metrics = normal_metrics + super_metrics
        if all_metrics:
            max_descent = max([metric["descent"] for metric in all_metrics])
            self.cursor_y = baseline + 1.25 * max_descent
        else:
            self.cursor_y += VSTEP

        # update Layout's cursor_x and self.line
        self.cursor_x = HSTEP
        self.line = []

    def _calculate_word_y(self, baseline, font, is_super, normal_metrics):
        """Calculate y position for a word, handling superscript positioning"""
        if is_super and normal_metrics:
            # Superscript: align top of superscript with top of normal letters
            normal_ascent = max([metric["ascent"] for metric in normal_metrics])
            super_ascent = font.metrics()["ascent"]
            
            # Position so superscript top aligns with normal text top
            normal_top = baseline - normal_ascent
            super_baseline = normal_top + super_ascent
            return super_baseline - super_ascent
        else:
            # Normal text positioning
            return baseline - font.metrics()["ascent"]