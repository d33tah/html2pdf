#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

from pyppeteer import launch
from quart import Quart, Response, request
from async_generator import asynccontextmanager

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


@asynccontextmanager
async def visit_page(url):
    # this lets us work without CAP_SYS_ADMIN:
    options = {'args': ['--no-sandbox']}
    # HACK: we're disabling signals because they fail in system tests
    if threading.currentThread() != threading._main_thread:
        options.update({'handleSIGINT': False, 'handleSIGHUP': False,
                        'handleSIGTERM': False})
    browser = await launch(**options)
    try:
        page = await browser.newPage()
        await page.goto(url)
        yield page
    finally:
        await browser.close()


@app.route('/html2pdf', methods=['POST'])
async def html2pdf():
    call_args = await request.form
    url = call_args.pop('url')
    async with visit_page(url) as page:
        pdf = await page.pdf(**call_args)
        return Response(pdf, mimetype='application/pdf')


@app.route('/html2img', methods=['POST'])
async def html2img():
    call_args = await request.form
    url = call_args.pop('url')
    img_format = call_args.get('type', 'png')
    async with visit_page(url) as page:
        pdf = await page.screenshot(**call_args)
        return Response(pdf, mimetype=('image/' + img_format))


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

    def test_server_renders_about_blank_pdf(self):
        args = {'url': 'about:blank'}
        response = requests.post(self.get_server_url() + '/html2pdf', args)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'application/pdf')
        expected = b'%PDF'
        self.assertEqual(response.content[:len(expected)], expected)

    def test_server_renders_about_blank_png(self):
        args = {'url': 'about:blank'}
        response = requests.post(self.get_server_url() + '/html2img', args)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'image/png')
        expected = b'\x89PNG\r\n\x1a\n\x00'
        self.assertEqual(response.content[:len(expected)], expected)

    def test_server_renders_about_blank_jpg(self):
        args = {'url': 'about:blank', 'type': 'jpeg'}
        response = requests.post(self.get_server_url() + '/html2img', args)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'], 'image/jpeg')
        expected = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        self.assertEqual(response.content[:len(expected)], expected)
