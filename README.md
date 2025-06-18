# web-browser-from-scratch
Simple yet complete Web Browser in Python from Scratch

### Lab-1 Specifications (Browser acts like a command line tool)
- Parses the URL into a schema, host, port and path.
- Connects to that host using the `socket` and `ssl` library.
- Sends an HTTP (supports both http and https) request to that host, including a `Host` header.
- Splits the HTTP response into status line, headers, and a body.
- Prints the text (and not the tags) in the body.
- Supports file URLs, to read the file when schema is `file` instead of setting up socket and sending request to remote server.
- Supports `data:` schema, allows embedding content directly in the URL (like `data:text/html,Hello World!`)
- Support the following additional features: HTTP/1.1, File, data, Entities, view-source. To-Do: Keep-alive, Redirects, Caching, Compression.
