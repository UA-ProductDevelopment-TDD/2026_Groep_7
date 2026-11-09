"""Client for the coop hub's HTTP API: how a program outside the simulator joins it (standard library only).

    client = HubClient('fox-detector', 'Fox detector', kind='detector', publishes=['vision/detections'],
                       subscribes=['camera/head-cam'])
    client.register()
    client.start_heartbeat()                  # outside modules count as stale after a few seconds of silence
    png = client.frame('head-cam')            # newest camera image as PNG bytes
    client.publish('vision/detections', {'fox': .92})
    client.close()                            # stops the heartbeat and unregisters

HubError carries the server's own explanation, or says that the simulator cannot be reached.
"""
import json
import threading
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_URL = 'http://127.0.0.1:8780'
TIMEOUT = 5.          # seconds a normal request may take
STREAM_TIMEOUT = 30.  # seconds of silence before a stream reconnects; the hub sends a comment now and then


class HubError(RuntimeError):
    """A failed hub call. status is the HTTP status, or None when the hub could not be reached."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def explanation(error):
    """The `detail` the server sent with an HTTP error, or its reason phrase."""
    try:
        body = error.read().decode('utf-8', 'replace')
    except OSError:
        body = ''
    try:
        detail = json.loads(body).get('detail')
    except (ValueError, AttributeError):
        detail = None
    if detail is None:
        return body.strip()[:300] or str(error.reason)
    return detail if isinstance(detail, str) else json.dumps(detail)


class HubClient:
    def __init__(self, module_id, name, kind='external', publishes=(), subscribes=(), limitations=(), info=None,
                 base_url=DEFAULT_URL):
        self.id, self.name, self.kind = module_id, name, kind
        self.publishes, self.subscribes = list(publishes), list(subscribes)
        self.limitations, self.info = list(limitations), dict(info or {})
        self.base_url = base_url.rstrip('/')
        self.last_error = None            # latest failure of the heartbeat thread, for the program to inspect
        self.thread = None
        self.stopped = threading.Event()  # set by close(): ends the heartbeat and any open stream
        self.streams = set()

    # Plumbing

    def open(self, method, path, body=None, timeout=TIMEOUT):
        data = None if body is None else json.dumps(body).encode('utf-8')
        request = urllib.request.Request(self.base_url + path, data=data, method=method,
                                         headers={'Content-Type': 'application/json'} if data is not None else {})
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as error:
            try:
                raise HubError(f'{method} {path}: {explanation(error)} (HTTP {error.code})', error.code) from None
            finally:
                error.close()
        except OSError as error:  # URLError, refused connections and timeouts
            raise HubError(f'Cannot reach the coop hub at {self.base_url} ({getattr(error, "reason", error)}). '
                           'Is the Coop simulator running?') from None

    def request(self, method, path, body=None, timeout=TIMEOUT, raw=False):
        with self.open(method, path, body, timeout) as response:
            content = response.read()
        if raw:
            return content
        try:
            return json.loads(content) if content else None
        except ValueError:
            raise HubError(f'{method} {path}: the hub did not answer with JSON') from None

    # Hub calls

    def register(self):
        """Announce this module; calling it again replaces the entry (for example after the simulator restarts)."""
        self.stopped.clear()
        return self.request('POST', '/api/hub/register', {
            'id': self.id, 'name': self.name, 'kind': self.kind, 'publishes': self.publishes,
            'subscribes': self.subscribes, 'limitations': self.limitations, 'info': self.info})

    def heartbeat(self):
        return self.request('POST', f'/api/hub/modules/{urllib.parse.quote(self.id, safe="")}/heartbeat')

    def publish(self, topic, value):
        return self.request('POST', '/api/hub/publish', {'module': self.id, 'topic': topic, 'value': value})

    def latest(self, prefix=''):
        """{topic: message} for the newest message of every topic that starts with prefix."""
        return self.request('GET', '/api/hub/topics?' + urllib.parse.urlencode({'prefix': prefix}))

    def frame(self, camera_id):
        """The camera's newest image, PNG bytes."""
        return self.request('GET', f'/api/hub/frame/{urllib.parse.quote(camera_id, safe="")}.png', raw=True)

    def modules(self):
        return self.request('GET', '/api/hub/modules')

    # Staying registered

    def start_heartbeat(self, interval=2.):
        """Send heartbeats from a daemon thread; if the hub forgot this module (it restarted), register again."""
        if self.thread is not None and self.thread.is_alive():
            return
        self.stopped.clear()
        self.thread = threading.Thread(target=self.beat, args=(interval,), name='hub-heartbeat-' + self.id, daemon=True)
        self.thread.start()

    def beat(self, interval):
        while not self.stopped.wait(interval):
            try:
                self.heartbeat()
                self.last_error = None
            except HubError as error:
                self.last_error = error
                if error.status == 404:
                    try:
                        self.register()
                    except HubError as again:
                        self.last_error = again

    def stream(self, prefix='', since=0):
        """Yield messages (dicts with seq, topic, source, time, value) as they are published, after sequence `since`.

        Ends when the hub closes the stream or close() is called; it reconnects by itself after a long silence.
        """
        while not self.stopped.is_set():
            query = urllib.parse.urlencode({'prefix': prefix, 'since': since})
            response = self.open('GET', '/api/hub/stream?' + query, timeout=STREAM_TIMEOUT)
            self.streams.add(response)
            try:
                event = []
                for raw in response:
                    line = raw.decode('utf-8').rstrip('\r\n')
                    if line.startswith('data:'):
                        event.append(line[5:].removeprefix(' '))
                    elif not line and event:
                        data, event = '\n'.join(event), []
                        try:
                            message = json.loads(data)
                        except ValueError:
                            continue
                        since = max(since, message.get('seq', since)) if isinstance(message, dict) else since
                        yield message
                return
            except TimeoutError:
                continue
            except (OSError, ValueError) as error:  # ValueError: the response was closed under us
                if self.stopped.is_set():
                    return
                raise HubError(f'The hub stream broke off: {error}') from None
            finally:
                self.streams.discard(response)
                response.close()

    def close(self):
        """Stop the heartbeat and streams, then unregister (quietly, if the hub is gone or never knew this module)."""
        self.stopped.set()
        for response in list(self.streams):
            response.close()
        if self.thread is not None and self.thread is not threading.current_thread():
            self.thread.join(timeout=2.)
        self.thread = None
        try:
            self.request('DELETE', f'/api/hub/modules/{urllib.parse.quote(self.id, safe="")}')
        except HubError:
            pass

    def __enter__(self):
        self.register()
        self.start_heartbeat()
        return self

    def __exit__(self, *exc):
        self.close()
