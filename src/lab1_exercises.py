import socket
import ssl # Secure Sockets Layer
import sys
import urllib.parse

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
            "User-Agent": "MySimpleBrowser/1.0"
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
        response = s.makefile("r", encoding="utf8", newline="\r\n")

        # split the responses into pieces
        '''
            HTTP/1.0 200 OK
        '''
        statusline = response.readline()
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
        '''
        # Headers
        response_headers = {}
        while True:
            line = response.readline()
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
        content = response.read()
        s.close()

        return content # body that we will display



def show(body):
    length = len(body)
    i = 0
    in_tag = False
    while i < length:
        if body[i:i + 4] == "&lt;":
            print("<", end="")
            i += 4
            continue
        elif body[i:i + 4] == "&gt;":
            print(">", end="")
            i += 4
            continue
        elif body[i] == "<":
            in_tag = True
        elif body[i] == ">":
            in_tag = False
        elif not in_tag:
            print(body[i], end="")
        i += 1



def load(url):
    body = url.request()
    if url.schema == "view-source":
        # for view-source, print the HTML as plain text (no tag filtering)
        print(body, end="")
    else:
        # other than view-source schema
        show(body)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <url/file>")
        print("No URL provided. Opening default test file.")
        load(URL("file://README.md"))

        # Test with a simple data URL
        load(URL("data:text/html,<h1>Hello World!</h1><p>This is a test page using the data scheme.</p>"))
    else:
        load(URL(sys.argv[1]))




