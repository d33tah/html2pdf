#!/usr/bin/env python3

from quart import Quart, Response, request

# those imports are for testing purposes:
import asyncio
import unittest
import multiprocessing
import time
import hashlib
import requests

app = Quart(__name__)


def random_string():
    return hashlib.md5(str(time.time()).encode('utf8')).hexdigest()


SHUTDOWN_CODE = random_string()


# this is for testing purposes only - we need a way to turn off the server
# once tests are done
@app.route('/' + SHUTDOWN_CODE, methods=['POST', 'GET'])
def shutdown():
    asyncio.get_event_loop().stop()
    return 'Server shutting down...'


@app.route('/')
def index():
    return '''<!DOCTYPE HTML><html><body>
        <form action="/gen_composition" method="post">
        <p>Characters: <input type="text" name="chars" value="齾"/></p>
        <input type="submit" value="Generate composition">
        </form>

        <form action="/gen_strokes" method="post">
        <p>Characters: <input type="text" name="chars" value="你好"/></p>
        <p>Size: <input type="text" name="size" value="10"/></p>
        <p>Number of repetitions: <input type="text" name="nr" value="3"/></p>
        <input type="submit" value="Generate strokes">
    </form>
    '''


class SystemTest(unittest.TestCase):

    def setUp(self):
        self.server_thread = multiprocessing.Process(target=lambda: app.run())
        self.server_thread.start()
        time.sleep(1.0)

    def tearDown(self):
        requests.post(self.get_server_url() + '/' + SHUTDOWN_CODE, {})
        self.server_thread.terminate()
        self.server_thread.join()

    def get_server_url(self):
        return 'http://localhost:5000'

    def test_server_is_up_and_running(self):
        response = requests.get(self.get_server_url())
        self.assertEqual(response.status_code, 200)
