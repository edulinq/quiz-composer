"""
The HTTP session objects here provide a way to make HTTP requests in a way that can be recorded and used later for testing.
There are three types of sessions, all of which respond to get(), post(), and path() methods,
while returning a Response object.

RequestsSession lightly wraps a requests.Session.
This class includes the ability to wait between requests to avoid being rate limited.

SessionRecorder wraps RequestsSession,
and will save the requests and responses to a directory.

TestSession can be loaded from a directory saved by a SessionRecorder,
and will replay any (method, URL) pair that comes to it.
If an unknown request is made, an exception will be raised.
"""

import logging
import os
import re
import time
import urllib.parse

import requests

import quizcomp.util.dirent
import quizcomp.util.hash
import quizcomp.util.json

DEFAULT_WAIT_TIME_SECS = 0.25

# {id: [session, ...], ...}
_test_sessions = {}

def get_session(id, save_http = False, **kwargs):
    """
    Get a session (based on requests.Session) to make HTTP requests.
    If id matches a loaded test session (via load_test_session()), then that session will be returned.
    Then if save_http is true, then a new SessionRecorder will be returned.
    Otherwise return a RequestsSession, which wraps a vanilla requests.Session.
    """

    if (id in _test_sessions):
        session = _test_sessions[id].pop(0)
        if (len(_test_sessions[id]) == 0):
            del _test_sessions[id]

        return session

    if (save_http):
        return SessionRecorder(id, **kwargs)

    return requests.Session(**kwargs)

def load_test_session(id, base_dir):
    """
    Load a test session from a directory into the queue for a specific ID.
    When a test session is used, it is removed from the queue.
    """

    session = TestSession.from_dir(base_dir)

    if (id not in _test_sessions):
        _test_sessions[id] = []

    _test_sessions[id].append(session)

class RequestsSession(object):
    def __init__(self,
            *args,
            wait_time = DEFAULT_WAIT_TIME_SECS,
            **kwargs):
        self._session = requests.Session(**kwargs)

        self._wait_time = wait_time
        self._last_request_time = None

    def get(self, url, *args, **kwargs):
        self._ensure_wait()

        response = self._session.get(url, *args, **kwargs)
        response_data = _response_to_dict(response)
        return Response(response_data)

    def post(self, url, *args, **kwargs):
        self._ensure_wait()

        response = self._session.post(url, *args, **kwargs)
        response_data = _response_to_dict(response)
        return Response(response_data)

    def patch(self, url, *args, **kwargs):
        self._ensure_wait()

        response = self._session.patch(url, *args, **kwargs)
        response_data = _response_to_dict(response)
        return Response(response_data)

    def _ensure_wait(self):
        """
        Ensure that we have waited enough time between requests.
        """

        now = time.time()

        if (self._last_request_time is None):
            self._last_request_time = now
            return

        delta = now - self._last_request_time
        wait_time_secs = self._wait_time - delta

        if (wait_time_secs > 0):
            time.sleep(wait_time_secs)

        self._last_request_time = time.time()

class SessionRecorder(object):
    """
    Record all requests and responses to be later played back via a TestSession.
    """

    def __init__(self, *args, **kwargs):
        self._session = RequestsSession(**kwargs)

        self._count = 0

        self._out_dir = quizcomp.util.dirent.get_temp_path('quizcomp-http-recorded-session-', rm = False)
        logging.info("Saving session HTTP data to '%s'.", self._out_dir)

    def get(self, url, *args, **kwargs):
        return self._wrap_request(url, self._session.get, "GET", *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self._wrap_request(url, self._session.post, "POST", *args, **kwargs)

    def patch(self, url, *args, **kwargs):
        return self._wrap_request(url, self._session.patch, "PATCH", *args, **kwargs)

    def _wrap_request(self,
            url, request_func, method,
            *args,
            headers = None, params = None, data = None, files = None,
            **kwargs):
        # Remember that we are already wrapping RequestsSession, so this is a Response.
        response = request_func(url, *args,
                headers = headers, params = params, data = data, files = files,
                **kwargs)

        result = {
            'request': {
                'method': method,
                'url': url,
            },
            'response': response._data,
        }

        if ((headers is not None) and (len(headers) > 0)):
            result['request']['headers'] = headers

        if ((params is not None) and (len(params) > 0)):
            result['request']['params'] = params

        if ((data is not None) and (len(data) > 0)):
            result['request']['data'] = data

        if ((files is not None) and (len(files) > 0)):
            result['request']['files'] = list(sorted(files.keys()))

        out_path = self._make_out_path(self._count, method, url, result)
        quizcomp.util.json.dump_path(result, out_path, indent = 4)

        self._count += 1

        return response

    def _make_out_path(self, count, method, url, data):
        method = method.upper()
        clean_filename_part = _clean_filename(url)
        hash_part = _hash_dict(data)

        out_filename = "%03d-%s-%s-%s.json" % (count, method, clean_filename_part, hash_part)
        return os.path.join(self._out_dir, out_filename)

class TestSession(object):
    """
    A session that will only respond with pre-made responses.
    Any request that is not found will raise an exception.
    """

    def __init__(self, responses):
        self._responses = responses

    def get(self, url, *args, **kwargs):
        return self._fetch_response(url, "GET")

    def post(self, url, *args, **kwargs):
        return self._fetch_response(url, "POST")

    def patch(self, url, *args, **kwargs):
        return self._fetch_response(url, "PATCH")

    def _fetch_response(self, url, method):
        key = TestSession._make_key(method, url)
        if (key not in self._responses):
            raise KeyError("Unknown response key: '%s'.", key)

        return Response(self._responses[key]['response'])

    def from_dir(base_dir):
        responses = {}

        for dirent in sorted(os.listdir(base_dir)):
            path = os.path.join(base_dir, dirent)
            data = quizcomp.util.json.load_path(path)

            key = TestSession._make_key(data['request']['method'], data['request']['url'])

            if (key in responses):
                raise ValueError("Duplicate response key '%s' found in '%s'.", key, path)

            responses[key] = data

        return TestSession(responses)

    def _make_key(method, url):
        return "%s::%s" % (method, url)

class Response(object):
    """
    Wrap the data in a requests.Response to provide a consistent interface.
    The data should come from _response_to_dict().
    """

    def __init__(self, data):
        self._data = data

        self.text = data['body']
        self.history = [Response(item) for item in data['history']]

    def raise_for_status(self):
        """
        See https://docs.python-requests.org/en/latest/api/#requests.Response.raise_for_status
        """

        status = self._data['status']
        if (400 <= status < 600):
            raise RuntimeError("HTTP error %d." % (status))

def _clean_filename(url):
    parts = urllib.parse.urlparse(url)
    return parts.hostname + parts.path.replace('/', '_')

def _hash_dict(data):
    json = quizcomp.util.json.dumps(data)
    return quizcomp.util.hash.sha256(json)

def _response_to_dict(response):
    headers = {}
    for (key, value) in response.headers.lower_items():
        headers[key] = value

    history = []
    if (response.history is not None):
        history = [_response_to_dict(item) for item in response.history]

    return {
        'status': response.status_code,
        'headers': headers,
        'body': response.text,
        'history': history,
    }
