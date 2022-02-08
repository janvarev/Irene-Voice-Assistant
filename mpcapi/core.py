# -*- coding: utf-8 -*-

# python std lib
import pprint
from collections.abc import Callable

# 3rd party imports
import requests

# from  import command_mapping
import mpcapi.commands as commands


class MpcAPI():

    def __init__(self, host=None, port=None, https=False):
        self.host = host if host else "127.0.0.1"
        self.port = str(port) if port else "13579"
        self.https = "https" if https else "http"

        self.commands = commands.command_mapping.copy()
        self.browse_commands = commands.browse_mapping.copy()

        for command_id, command_data in self.commands.items():
            setattr(self, command_data["command_name"], Command(self, command_id, command_data.get("descr", "No Descr")))

        for command_id, command_data in self.browse_commands.items():
            setattr(self, command_data["command_name"], Browser(self, command_id, command_data.get("descr", "No Descr")))

    def url(self, endpoint):
        """
        File should be for example browser.html that tells what endpoint to use
        """
        return "{}://{}:{}/{}".format(self.https, self.host, self.port, endpoint)

    def _post_browser(self, path):
        """
        Send command to /browser.html endpoint
        """
        post_data = {"path": path}
        print("_posting browser", post_data)
        requests.get(self.url("browser.html"), params=post_data)

    def _post_command(self, command_id):
        """
        Post command to remote MPC instance.
        """
        post_data = {
            "wm_command": command_id,
            "submit": "Go!",
        }

        print("_posting command", post_data)

        requests.post(self.url("command.html"), data=post_data)

    def methods(self):
        pprint.pprint(dir(self))


class BaseCallable(Callable):

    def __init__(self, api, method, descr):
        self.api = api
        self.method = method
        self.descr = descr


class Command(BaseCallable):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        print("Calling command: {}".format(self.descr))
        self.api._post_command(self.method)


class Browser(BaseCallable):

    def __init__(self, api, method, descr):
        super(Browser, self).__init__(api, method, descr)

    def __call__(self, *args, **kwargs):
        print("Calling Browse command: {}".format(self.descr))
        self.api._post_browser(kwargs.get("path", ""))


if __name__ == "__main__":
    api = MpcAPI(host="127.0.0.1", port="13579")

    # api.play_pause()
    api.methods()
