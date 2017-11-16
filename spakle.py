#!/usr/bin/env python3

import sys
from http.server import BaseHTTPRequestHandler
from http.client import HTTPSConnection
import json
import socketserver
import urllib

# curl -X POST -d @push.raw http://localhost:8081/ --header "Content-Type:application/json"

class SimpleServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        socketserver.TCPServer.__init__(self, server_address, RequestHandlerClass)

class Spakle(BaseHTTPRequestHandler):

    def save_to_file(self, data, filename):
        """
        useful during testing, use curl command to replay
        """
        with open(filename, 'wb') as f:
            f.write(data)

    def get_post_data(self):
        content_length = int(self.headers['Content-Length'])
        data = self.rfile.read(content_length)
        return data

    def decode_payload(self, data):
        """
        data from gitlab is a x-www-form-urlencoded string
        some hoops must be jumped through to get a useable dict

        WARNING: all data in dict (keys and values) are bytes not strings
        """
        data = urllib.parse.parse_qs(data)
        # print("incoming:", data)

        # data[payload] is a list with one giant string in it
        payload = data[b'payload'][0]

        # decode payload string into dict
        payload = json.loads(payload.decode('utf-8'))

        return payload

    def encode_payload(self, payload):
        """
        opposite of decode_payload, turn our dict back into
        an encoded form, ready to send to slack
        """
        payload = json.dumps(payload)
        payload = {b'payload': [payload]}
        data = urllib.parse.urlencode(payload, doseq=True).encode('ascii')
        #print("outgoing:", data)
        return data

    def forward_to_slack(self, original, payload):
        slack_hook, channel_name = payload.pop('channel', '').split('#', 1)

        if not slack_hook:
            return

        if channel_name:
            channel_name = channel_name.lstrip('#') # just in case
            payload['channel'] = "#{}".format(channel_name)

        #print("parse channel:", slack_hook, channel_name)

        try:
            # data is same as original incoming payload with channel field updated
            data = self.encode_payload(payload)

            headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
            netloc = urllib.parse.urlparse(slack_hook).netloc

            client = HTTPSConnection(netloc)
            client.request("POST", slack_hook, data, headers)
            resp = client.getresponse()

            print("response from slack:", resp.status, resp.reason)

            return resp
        except Exception as e:
            print(e)
            return None

    def respond_to_gitlab(self, resp):
        """
        forward slack response back to gitlab
        """
        if resp is None:
            self.send_response(500)
            self.end_headers()
            return

        self.send_response(resp.status)
        self.end_headers()

        self.wfile.write( resp.read() )

    def do_POST(self):
        """
        entry point from gitlab webhook
        """
        data = self.get_post_data()
        #self.save_to_file(data, 'push.raw')

        payload = self.decode_payload(data)
        resp = self.forward_to_slack(data, payload)

        self.respond_to_gitlab(resp)


def main(host, port):
    port = int(port)
    print("starting server on {}:{}".format(host, port))

    httpd = SimpleServer((host, port), Spakle)

    try:
        print('running server...')
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        httpd.server_close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: {} listen_addr port".format(sys.argv[0]))
        print("eg. {} 0.0.0.0 8081".format(sys.argv[0]))
        sys.exit(1)

    main(*sys.argv[1:])
