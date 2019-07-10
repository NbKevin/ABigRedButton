"""
This file launches the application and opens its GUI.
Always run this file and keep your hands off from the rest
of the files unless you are fully enabled on what you are
about to do.

Kevin Ni, kevin.ni@nyu.edu.
"""
import sys
import time
import threading
import webbrowser
from _flask_app import app
from _a_big_red_button.support.configuration import BOOT_CFG, RUNNING_IN_DEV_ENV
import threading


class GUILauncher(threading.Thread):
    def run(self) -> None:
        time.sleep(3)
        print("backend should be ready, opening GUI page...")
        webbrowser.open(f'http://{BOOT_CFG.flask.address.host}:'
                        f'{BOOT_CFG.flask.address.port}')


if __name__ == '__main__':
    # POST
    print("\nA BIG RED BUTTON\n"
          "An integrated GUI for the project SOCIAL NETWORK ANALYSIS\n\n"
          "Prof. Yifei Li and Bo Donners, as well as all who have participated\n\n"
          "Written by Kevin Ni, kevin.ni@nyu.edu, integration and GUI\n"
          "And by Yiyun Fan, yf855@nyu.edu, crawler interface and original analysis script\n\n"
          "2019 July 15\n")

    # launch the GUI launcher
    gui_launcher = GUILauncher()
    gui_launcher.daemon = True
    gui_launcher.start()

    # launch the backend
    print("starting backend, press Ctrl-C (Control-C on Mac) to stop...")
    if RUNNING_IN_DEV_ENV and 'NO_DEBUG' not in sys.argv:
        app.run(BOOT_CFG.flask.address.host, BOOT_CFG.flask.address.port, debug=True)
    else:
        app.run(BOOT_CFG.flask.address.host, BOOT_CFG.flask.address.port, debug=False)

