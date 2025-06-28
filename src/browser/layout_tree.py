# Layout and font management
import tkinter
import tkinter.font
from constants import WIDTH, HEIGHT, HSTEP, VSTEP, BLOCK_ELEMENTS
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


class DocumentLayout:
    def __init__(self, node):
        self.node = node
        self.parent = None
        self.children = []

        self.x = None
        self.y = None
        self.width = None
        self.height = None 

    def layout(self):
        child = BlockLayout(self.node, self, None)
        self.children.append(child)

        self.width = WIDTH - 2 * HSTEP
        self.x = HSTEP
        self.y = VSTEP 

        child.layout() # recursive call to layout

        self.height = child.height

    def paint(self):
        return []
    
class DrawText:
    def __init__(self, x1, y1, text, font, color):
        self.top = y1
        self.left = x1
        self.text = text
        self.font = font
        self.color = color
        self.bottom = y1 + font.metrics("linespace")

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.left, self.top - scroll,
            text = self.text,
            font = self.font,
            anchor = "nw",
            fill = self.color
        )

class DrawRect:
    def __init__(self, x1, y1, x2, y2, color):
        self.top = y1
        self.left = x1
        self.bottom = y2
        self.right = x2
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.left, self.top - scroll,
            self.right, self.bottom - scroll,
            width = 0,
            fill = self.color
        )


class BlockLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

        # computing size and position of each BlockLayout separately
        self.x = None
        self.y = None
        self.width = None
        self.height = None

        self.display_list = []

    def layout_intermediate(self):
        # this code constructs the layout tree from the HTML tree, so it reads from node.children (in the HTML tree) and writes to self.children (in the layout tree)
        previous = None
        # self.node is to HTML Tree
        # self, previous, next are corresponding to Layout Tree
        for child in self.node.children: 
            next = BlockLayout(child, self, previous)
            self.children.append(next)
            previous = next

    def layout_mode(self):
        """Determine which way to lay out text, inline/blocks"""
        if isinstance(self.node, Text):
            return "inline"
        elif any([isinstance(child, Element) and child.tag in BLOCK_ELEMENTS for child in self.node.children]):
            return "block"
        elif self.node.children:
            return "inline"
        else:
            return "block"
        
    def layout(self):

        # computing size and position of each BlockLayout separately

        # x position must be computed before the recursive layout call of childrens
        self.x = self.parent.x
        self.width = self.parent.width
        if self.previous: # if there is a previous sibling, then start right after it
            self.y = self.previous.y + self.previous.height
        else: # otherwise, start at its parent's top edge
            self.y = self.parent.y

        
        mode = self.layout_mode()

        if mode == "block":
            previous = None
            for child in self.node.children:
                next = BlockLayout(child, self, previous)
                self.children.append(next)
                previous = next
        else: # mode == "inline"
            self.cursor_x = 0 # not HSTEP/VSTEP, since we are not relative to the block's x, y
            self.cursor_y = 0
            self.weight = "normal"
            self.style = "roman"
            self.size = 12

            self.line = [] # to store line-to-be

            # alignment tracking
            self.align = "left" # can be "left", "center", or "right"
            self.in_title_h1 = False # track if we are inside <h1 class="title">

            # superscript tracking
            self.superscript = False # track if we are inside <sup> superscript mode

            # Process the tree recursively
            self.recurse(self.node)
            self.flush()

        
        for child in self.children:
            child.layout()


        # element's height field depends on the children's height, so must be computed after the layout call of childrens
        if mode == "block":
            self.height = sum([child.height for child in self.children])
        else:
            self.height = self.cursor_y # if it is normal text, all the text must be insider, right...


        


    def recurse(self, node):
        """Recursively process the tree structure"""
        if isinstance(node, Text):
            # Process text node
            for word in node.text.split():
                self.word(node, word)
        elif isinstance(node, Element):
            # Process element node - opening tag
            self.open_tag(node.tag, node.attributes)
            
            # Process all children
            for child in node.children:
                self.recurse(child)
            
            # Process closing tag
            self.close_tag(node.tag)


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

    def word(self, node, word):
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        # translate CSS's normal to tkinter "roman"
        if style == "normal":
            style = "roman"
        curr_size = int(float(node.style["font-size"][:-2]) * 0.75) # convert CSS's pixels to Tkinter points

        # calculate word size based on superscript state
        if self.superscript == True:
            curr_size = max(8, int(curr_size * 0.6)) # 60% of normal size, minimum 8px

        font = get_font(curr_size, weight, style)
        
        w = font.measure(word) # width taken by that word
        if self.cursor_x + w > self.width:
            self.flush()

        # store superscript flag with each word for positioning
        color = node.style["color"]
        self.line.append((self.cursor_x, word, font, self.superscript, color))
        self.cursor_x += w + font.measure(" ")


    def flush(self):
        if not self.line:
            return
        
        # separate metrics calculations for normal and superscript text
        normal_metrics = []
        super_metrics = []

        for rel_x, word, font, is_superscript, color in self.line:
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
                first_rel_x = self.line[0][0]
                last_rel_x, last_word, last_font, _, color = self.line[-1]
                last_word_width = last_font.measure(last_word)
                line_width = (last_rel_x + last_word_width) - first_rel_x

            # calculate offset to center the line
            available_width = WIDTH - 2 * HSTEP
            center_offset = (available_width - line_width) // 2

            # adjust x positions for centering
            for i, (rel_x, word, font, is_superscript, color) in enumerate(self.line):
                centered_rel_x = center_offset + HSTEP + (rel_x - HSTEP)
                centered_abs_x = self.x + centered_rel_x
                abs_y = self.y + self._calculate_word_y(baseline, font, is_superscript, normal_metrics)
                self.display_list.append((centered_abs_x, abs_y, word, font, color))
        else:
            # now place each word relative to that line and add it to the display list
            for rel_x, word, font, is_superscript, color in self.line:
                abs_x = self.x + rel_x
                abs_y = self.y + self._calculate_word_y(baseline, font, is_superscript, normal_metrics)
                self.display_list.append((abs_x, abs_y, word, font, color))
        
        all_metrics = normal_metrics + super_metrics
        if all_metrics:
            max_descent = max([metric["descent"] for metric in all_metrics])
            self.cursor_y = baseline + 1.25 * max_descent
        else:
            self.cursor_y += VSTEP

        # update Layout's cursor_x and self.line
        self.cursor_x = 0 # 0 instead of HSTEP, since relative to the block's x and y
        self.line = []



    def _calculate_word_y(self, baseline, font, is_super, normal_metrics):
        """Calculate relative y position for a word, handling superscript positioning"""
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
        

    def paint(self):
        cmnds = [] # commands can be Text, Rectangle...

        # background has to be before Text (always)
        bgcolor = self.node.style.get("background-color", "transparent")

        if bgcolor != "transparent":
            x2, y2 = self.x + self.width, self.y + self.height
            rect = DrawRect(self.x, self.y, x2, y2, bgcolor)
            cmnds.append(rect)

        # if isinstance(self.node, Element) and self.node.tag == "pre":
        #     x2, y2 = self.x + self.width, self.y + self.height
        #     rect = DrawRect(self.x, self.y, x2, y2, "gray")
        #     cmnds.append(rect)

        if self.layout_mode() == "inline":
            for x, y, word, font, color in self.display_list:
                cmnds.append(DrawText(x, y, word, font, color))
        

        return cmnds