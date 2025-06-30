# web-browser-from-scratch
Simple yet complete Web Browser in Python from Scratch

Components of a Typical Browser:

![Browser_Image](browser-components.png)

### Lab-1 Specifications (Browser acts like a command line tool)
- Parses the URL into a schema, host, port and path.
- Connects to that host using the `socket` and `ssl` library.
- Sends an HTTP (supports both http and https) request to that host, including a `Host` header.
- Splits the HTTP response into status line, headers, and a body.
- Prints the text (and not the tags) in the body.
- Supports file URLs, to read the file when schema is `file` instead of setting up socket and sending request to remote server.
- Supports `data:` schema, allows embedding content directly in the URL (like `data:text/html,Hello World!`)
- Support the following additional features: HTTP/1.1, File, data, Entities, view-source, compression. To-Do: Keep-alive, Redirects, Caching.


### Lab-2 Drawing the Screen
- creating windows using `tkinter`
- Drawing the window with defined `WIDTH` and `HEIGHT`
- Laying out text using `HSTEP` and `VSTEP`
- Supporting scrolling of text with layout
- Fast rendering of page contents so that the user "Feel Fluid".


## Assumptions
- The browser doesn't support whitespace-only text nodes. Real browser retain such whitespaces to correctly render make<span> </span>up as two. This browser won't. Ignoring whitespaces simplifies complexities, by avoiding a special case for whitespaces only text tags.
- The browser doesn't support parenthesis in CSS property values. This inhibits us from parsing things like `calc` and `url` functions (are supported in real browsers).
- Each word that will be rendered by the browser will have a single font for all the letters. Hence the browser cannot accomodate letters with different font in between a word.