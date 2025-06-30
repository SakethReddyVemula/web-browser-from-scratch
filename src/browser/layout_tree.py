# Layout and font management
import tkinter
import tkinter.font
from constants import WIDTH, HEIGHT, HSTEP, VSTEP, BLOCK_ELEMENTS
from parser import Text, Element

class Rect:
    def __init__(self, left, top, right, bottom):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def contains_point(self, x, y):
        return (x >= self.left and x < self.right and y >= self.top and y < self.bottom)

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
        self.rect = Rect(
            x1, 
            y1,
            x1 + font.measure(text), 
            y1 + font.metrics("linespace")
        )
        self.text = text
        self.font = font
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_text(
            self.rect.left, self.rect.top - scroll,
            text=self.text,
            font=self.font,
            anchor='nw',
            fill=self.color
        )

class DrawRect:
    def __init__(self, rect, color):
        self.rect = rect
        self.color = color

    def execute(self, scroll, canvas):
        canvas.create_rectangle(
            self.rect.left, 
            self.rect.top - scroll,
            self.rect.right, 
            self.rect.bottom - scroll,
            width=0,
            fill=self.color
        )


class LineLayout:
    def __init__(self, node, parent, previous):
        self.node = node
        self.parent = parent
        self.previous = previous
        self.children = []

    def layout(self):
        self.width = self.parent.width
        self.x = self.parent.x

        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            self.y = self.parent.y

        # First, layout all the words to get their dimensions
        for word in self.children:
            word.layout()
        
        # If no words in this line, set minimal height and return
        if not self.children:
            self.height = VSTEP
            return
        
        # Separate metrics calculations for normal and superscript text
        normal_metrics = []
        super_metrics = []
        
        for word in self.children:
            metrics = word.font.metrics()
            if hasattr(word, 'is_superscript') and word.is_superscript:
                super_metrics.append(metrics)
            else:
                normal_metrics.append(metrics)
        
        # Calculate baseline based on normal text (if any)
        if normal_metrics:
            max_normal_ascent = max([metric["ascent"] for metric in normal_metrics])
            baseline_offset = 1.25 * max_normal_ascent
        else:
            # If only superscript text on this line, use superscript metrics
            max_super_ascent = max([metric["ascent"] for metric in super_metrics]) if super_metrics else 0
            baseline_offset = 1.25 * max_super_ascent
        
        # Set baseline relative to line's y position
        baseline = self.y + baseline_offset
        
        # Handle center alignment
        if self.align == "center":
            # Calculate total width of all words plus spaces between them
            total_content_width = 0
            for i, word in enumerate(self.children):
                total_content_width += word.width
                if i < len(self.children) - 1:  # Add space width except for last word
                    total_content_width += word.font.measure(" ")
            
            # Calculate starting x position to center the content
            available_width = self.width
            center_start_x = self.x + (available_width - total_content_width) // 2
            
            # Reposition all words for centering
            current_x = center_start_x
            for word in self.children:
                word.x = current_x
                current_x += word.width + word.font.measure(" ")
        
        # Position each word vertically based on baseline
        for word in self.children:
            is_super = hasattr(word, 'is_superscript') and word.is_superscript
            word.y = self._calculate_word_y(baseline, word.font, is_super, normal_metrics)
        
        # Calculate line height
        all_metrics = normal_metrics + super_metrics
        if all_metrics:
            max_descent = max([metric["descent"] for metric in all_metrics])
            self.height = int(baseline_offset + 1.25 * max_descent)
        else:
            self.height = VSTEP

    def _calculate_word_y(self, baseline, font, is_super, normal_metrics):
        """Calculate y position for a word, handling superscript positioning"""
        if is_super and normal_metrics:
            # Superscript: align top of superscript with top of normal letters
            normal_ascent = max([metric["ascent"] for metric in normal_metrics])
            super_ascent = font.metrics()["ascent"]
            
            # Position so superscript top aligns with normal text top
            normal_top = baseline - normal_ascent
            super_baseline = normal_top + super_ascent
            return int(super_baseline - super_ascent)
        else:
            # Normal text positioning
            return int(baseline - font.metrics()["ascent"])

    def paint(self):
        return []
    


class TextLayout:
    def __init__(self, node, word, parent, previous):
        self.node = node
        self.word = word
        self.parent = parent
        self.previous = previous
        self.children = []

        self.is_superscript = getattr(parent.parent, "superscript", False)

    def layout(self):
        weight = self.node.style["font-weight"]
        style = self.node.style["font-style"]
        if style == "normal": 
            style = "roman"
        
        # Get base size and apply superscript scaling if needed
        base_size = int(float(self.node.style["font-size"][:-2]) * .75)
        if self.is_superscript:
            size = max(8, int(base_size * 0.6))  # 60% of normal size, minimum 8px
        else:
            size = base_size
            
        self.font = get_font(size, weight, style)

        self.width = self.font.measure(self.word)

        # Set initial x position (will be adjusted for centering in LineLayout)
        if self.previous:
            space = self.previous.font.measure(" ")
            self.x = self.previous.x + space + self.previous.width
        else:
            self.x = self.parent.x

        self.height = self.font.metrics("linespace")
        
    def paint(self):
        color = self.node.style["color"]
        return [DrawText(self.x, self.parent.y, self.word, self.font, color)]
    


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

        # self.display_list = []

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

            # alignment tracking
            self.align = "left" # can be "left", "center", or "right"
            self.in_title_h1 = False # track if we are inside <h1 class="title">

            # superscript tracking
            self.superscript = False # track if we are inside <sup> superscript mode

            # Process the tree recursively
            self.newline()
            self.recurse(self.node)

        
        for child in self.children:
            child.layout()

        self.height = sum([child.height for child in self.children])
        


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
                self.newline() # start fresh line for h1
        elif tag == "sup":
            self.superscript = True
        elif tag == "br":
            self.newline()

    def close_tag(self, tag):
        """Handle closing HTML tags"""
        if tag == "h1":
            if self.in_title_h1 == True:
                self.newline() # finish current line
                self.in_title_h1 = False 
                self.align = "left" # reset to left alignment
                self.cursor_y += VSTEP # add some spacing after h1
        elif tag == "sup":
            self.superscript = False
        elif tag == "p":
            self.newline()
            self.cursor_y += VSTEP

    def word(self, node, word):
        weight = node.style["font-weight"]
        style = node.style["font-style"]
        if style == "normal":
            style = "roman"
        curr_size = int(float(node.style["font-size"][:-2]) * 0.75)

        # Use the original size for width calculation (superscript scaling handled in TextLayout)
        font = get_font(curr_size, weight, style)
        
        w = font.measure(word)
        if self.cursor_x + w > self.width:
            self.newline()

        line = self.children[-1] # get the current line
        previous_word = line.children[-1] if line.children else None
        text = TextLayout(node, word, line, previous_word)
        line.children.append(text)

        self.cursor_x += w + font.measure(" ")


    def newline(self):
        self.cursor_x = 0
        last_line = self.children[-1] if self.children else None
        new_line = LineLayout(self.node, self, last_line)
        new_line.align = self.align
        self.children.append(new_line)


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
            rect = DrawRect(Rect(self.x, self.y, x2, y2), bgcolor)
            cmnds.append(rect)

        return cmnds