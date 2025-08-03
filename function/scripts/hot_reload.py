import os
import subprocess
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ReloadHandler(FileSystemEventHandler):
    def __init__(self, script):
        self.script = script
        self.process = None
        self.start_script()

    def start_script(self):
        if self.process:
            self.process.terminate()
        self.process = subprocess.Popen([sys.executable, self.script])

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"Detected change in {event.src_path}, restarting script...")
            self.start_script()


if __name__ == "__main__":
    script = "scripts/polling.py"  # 監視対象のスクリプト
    path_to_watch = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # 一つ上のディレクトリ
    event_handler = ReloadHandler(script)
    observer = Observer()
    observer.schedule(event_handler, path=path_to_watch, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
