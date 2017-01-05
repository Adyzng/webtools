# -*- coding: utf-8 -*-
from web.webapp import develop

# using flask build-in web server Werkzeug to host application
if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    print("http server port : %u" % port)
    develop(port=port)