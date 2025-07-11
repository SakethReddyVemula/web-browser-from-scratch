# All URL-related functionality
import socket
import ssl
import sys
import urllib.parse
import gzip

class URL:
    def __init__(self, url):
        try:
            # example url: http://example.org/index.html
            if url.startswith("view-source:"): # support for view-source:http://example.org/
                self.schema = "view-source"
                self.inner_url = url[12:]
                # parse the inner url
                self.inner_url_obj = URL(self.inner_url)
                return
            elif "://" in url:
                self.schema, url = url.split("://", 1) # seperate schema from rest of the url, split(s, n) -> splits a string at the first n copies of s.
            elif url.startswith("data:"):
                self.schema = "data"
                url = url[5:] # remove "data:" prefix
            else:
                raise ValueError("Unsupported URL format")
            
            assert self.schema in ["http", "https", "file", "data", "view-source"] # our browser supports these only; HTTPS: HTTP + TLS(Transport Layer Security)


            if self.schema == "file":
                self.path = url.lstrip("/") # Ensure absolute path
                return
            
            if self.schema == "data":
                # parse data URL: data:[<mediatype][;base64],<data>
                if "," in url:
                    self.media_info, self.data_content = url.split(",", 1)
                    # URL decode the data content
                    self.data_content = urllib.parse.unquote(self.data_content)
                else:
                    # malformed data URL
                    raise ValueError("Invalid data URL format")
                return


            # seperate host from path
            if "/" not in url:
                url = url + "/"
            self.host, url = url.split("/", 1) # host comes before the first "/", path is "/"+everything else
            self.path = "/" + url # optional "/" is part of the path!!!

            if self.schema == "http":
                self.port = 80
            elif self.schema == "https":
                self.port = 443

            if ":" in self.host:
                self.host, port = self.host.split(":", 1)
                self.port = int(port)
        except:
            print("Malformed URL found, falling back to the Home Page.")
            print(" URL was: " + url)
            self.__init__("https://google.com") # fallback to google.com

    
    # download the web page at that URL
    def request(self):
        if self.schema == "view-source":
            return self.inner_url_obj.request()
        
        # handle file first
        if self.schema == "file":
            try:
                with open(self.path, "r", encoding="utf8") as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading file {self.path}: {e}")
                sys.exit(1)

        # handle data schema
        if self.schema == "data":
            return (self.data_content + "\r\n")


        # step-1: connecting the host e.g., telnet self.host

        # use feature provided by OS -> sockets
        # Sockets:
        # -> has address family: tells how to find the other computer. Have names starting with "AF": AF_INET, AF_BLUETOOTH...
        # -> has type: describes sort of conversation that is going to happen. Names starting with "SOCK": SOCK_STREAM (means, each computer can send arbitray amount of data), SOCK_DGRAM (means, each send each other packets of some fixed size)
        # -> has protocol: describes steps by which the two computers will establish a connection. Eg., IPPROTO_TCP (our version sticks to HTTP1.0 only)
        s = socket.socket(
            family=socket.AF_INET, # we use AF_INET, IPv4 addresses only are supported
            type=socket.SOCK_STREAM, # we want to send arbitrary amount of data b/w each other
            proto=socket.IPPROTO_TCP # reliable protocol, but comprimises speed over relibality
        ) # these are default values, s = socket.socket() would also work here

        # connect to other computer => needs {host, port}, port depends on the protocol we are using, IPPROTO_TCP -> 80
        # s.connect ( takes single argument -> pair of host and a port). Different address families have different no.of arguments. Ours (AF_INET) takes two host+port
        s.connect((self.host, self.port)) # talks to `example.org`


        # create a default context and wrap the socket with it
        if self.schema == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host) # server_hostname used to check that we have connected to the right server. It should match the Host header


        # step-2: make a request to the other server

        # define headers as a dictionary for easier extension
        headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": "MySimpleBrowser/1.0",
            "Accept-Encoding": "gzip" # inform the server that compressed data is acceptable
        }

        # use \r\n instead of \n for newlines !!!
        # put two \r\n at the end of the request => o/w other computer will keep waiting for newline, we will wait for response !!!
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        for key, value in headers.items():
            request += f"{key}: {value}\r\n"

        request += "\r\n"
        # .encode to send `bytes` instead of `str` type
        s.send(request.encode("utf8")) # return number (here 47), how many bytes sent, useful when connections fail

        # step-3: read server's response
        # read and while loop (or) python's makefile shortcut
        response = s.makefile("rb")

        # split the responses into pieces
        '''
            HTTP/1.0 200 OK
        '''
        statusline = self._read_line(response).decode("utf8")
        version, status, explanation = statusline.split(" ", 2)
        
        '''
            Example Header

            Age: 545933
            Cache-Control: max-age=604800
            Content-Type: text/html; charset=UTF-8
            Date: Mon, 25 Feb 2019 16:49:28 GMT
            Etag: "1541025663+gzip+ident"
            Expires: Mon, 04 Mar 2019 16:49:28 GMT
            Last-Modified: Fri, 09 Aug 2013 23:54:35 GMT
            Server: ECS (sec/96EC)
            Vary: Accept-Encoding
            X-Cache: HIT
            Content-Length: 1270
            Connection: close
            Content-Encoding: gzip
        '''
        # Headers
        response_headers = {}
        while True:
            line = self._read_line(response).decode("utf8")
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            # headers are case-insensitive -> normalize using casefold(more language coverage)/lower()
            response_headers[header.casefold()] = value.strip()

        # make sure no unwanted headers are present
        # assert "transfer-encoding" not in response_headers # for chunking of large web pages
        # assert "content-encoding" not in response_headers # for compressing large web pages
        # assert "accept-encoding" not in response_headers # with content-encoding, to list the compression algorithm

        # everything after header, is sent (recieved) data
        content = self._read_body(response, response_headers)
        s.close()

        return content # body that we will display
    
    def _read_line(self, response):
        """
            Read a single file from binary response, including CRLF
        """
        line = b""
        while True:
            char = response.read(1)
            if not char:
                break
            line += char
            if line.endswith(b"\r\n"):
                break
        return line
    
    
    def _read_body(self, response, headers):
        """Read and decode the response body based on transfers and content encoding"""
        # check for chunked transfer encoding
        if headers.get("transfer-encoding", "").lower() == "chunked":
            body = self._read_chunked_body(response)
        else:
            # Read based on content length or until connection closes
            if "content-length" in headers:
                content_length = int(headers["content-length"])
                body = response.read(content_length)
            else:
                body = response.read()

        # Handle content encoding (compression)
        content_encoding = headers.get("content-encoding", "").lower()
        if content_encoding == "gzip":
            try:
                body = gzip.decompress(body)
            except Exception as e:
                print(f"Error decompression gzip content: {e}")
                pass
        
        # convert to string
        try:
            return body.decode("utf8")
        except UnicodeDecodeError:
            # fallback to latin-1 if utf8 fails
            return body.decode("latin-1")
        
    def _read_chunked_body(self, response):
        """Read chunked transfer encoding body"""
        body = b""
        while True:
            # Read chunk size line
            chunk_size_line = self._read_line(response)
            chunk_size_str = chunk_size_line.decode("utf8").strip()
            
            # Parse chunk size (hex format, may have extensions after semicolon)
            if ";" in chunk_size_str:
                chunk_size_str = chunk_size_str.split(";")[0]
            
            try:
                chunk_size = int(chunk_size_str, 16)
            except ValueError:
                print(f"Invalid chunk size: {chunk_size_str}")
                break
            
            # If chunk size is 0, we've reached the end
            if chunk_size == 0:
                # Read trailing headers (if any) until empty line
                while True:
                    line = self._read_line(response)
                    if line == b"\r\n":
                        break
                break
            
            # Read the chunk data
            chunk_data = response.read(chunk_size)
            body += chunk_data
            
            # Read the trailing CRLF after chunk data
            trailing_crlf = response.read(2)
            if trailing_crlf != b"\r\n":
                print("Warning: Expected CRLF after chunk data")
        
        return body
    

    def resolve(self, url):
        # schema relative URL that starts with "//" followed by a full URL, which use the existing schema
        # https://cdn.example.com/style.css (example)
        if "://" in url:
            return URL(url)
        
        # path-relative URL, doesn't start with a slash and is resolved like a file name would be
        # url = "styles/main.css"
        if not url.startswith("/"):
            dir, _ = self.path.rsplit("/", 1)
            while url.startswith("../"): # to resolve parent directory
                _, url = url.split("/", 1)
                if "/" in dir:
                    dir, _ = dir.rsplit("/", 1)
            url = dir + "/" + url

        # url = "//static.example.com/style.css" (example)
        if url.startswith("//"):
            return URL(self.schema + ":" + url)
        else:
            # url = "/styles/main.css"
            return URL(self.schema + "://" + self.host + ":" + str(self.port) + url)
        
    def __str__(self):
        # Handle view-source URLs
        if self.schema == "view-source":
            return f"view-source:{self.inner_url}"
        
        # Handle data URLs
        if self.schema == "data":
            return f"data:{self.media_info},{urllib.parse.quote(self.data_content)}"
        
        # Handle file URLs
        if self.schema == "file":
            return f"file://{self.path}"
        
        # Handle HTTP and HTTPS URLs
        port_part = ":" + str(self.port)
        if self.schema == "https" and self.port == 443:
            port_part = ""
        if self.schema == "http" and self.port == 80:
            port_part = ""
        
        return self.schema + "://" + self.host + port_part + self.path
    
