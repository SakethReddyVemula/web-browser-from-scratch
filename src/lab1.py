import socket
import ssl # Secure Sockets Layer
import sys

class URL:
    def __init__(self, url):
        try:
            # example url: http://example.org/index.html
            self.schema, url = url.split("://", 1) # seperate schema from rest of the url, split(s, n) -> splits a string at the first n copies of s.
            assert self.schema in ["http", "https"] # our browser supports these only; HTTPS: HTTP + TLS(Transport Layer Security)

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

        # use \r\n instead of \n for newlines !!!
        # put two \r\n at the end of the request => o/w other computer will keep waiting for newline, we will wait for response !!!
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
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
        assert "transfer-encoding" not in response_headers # for chunking of large web pages
        assert "content-encoding" not in response_headers # for compressing large web pages
        # assert "accept-encoding" not in response_headers # with content-encoding, to list the compression algorithm

        # everything after header, is sent (recieved) data
        content = response.read()
        s.close()

        return content # body that we will display

            
def show(body):
    # print(f"Showing body...")
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")


def load(url):
    body = url.request()
    show(body)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <url>")
        sys.exit(1)
    load(URL(sys.argv[1]))




