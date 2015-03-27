import argparse
import sys
import os
import hashlib

import pyinotify

from tree import build_tree
from db import DataBase


parser = argparse.ArgumentParser()
parser.add_argument('-start', dest='option', action='store_true')
parser.add_argument('-stop', dest='option', action='store_false')
parser.set_defaults(option="no")
parser.add_argument('-p', '--path',  type=str, required=True, help='path to scan directory')
args = parser.parse_args()
watched_dir = args.path
demon_start = True
pid_path = "/tmp/%s.pid" % (hashlib.md5(watched_dir).hexdigest())
if args.option == "no":
        demon_start = False
wm = pyinotify.WatchManager()
database = DataBase()
tree = build_tree(watched_dir)


def demon(option):
    if option and os.path.exists(pid_path):
        with open(pid_path) as this_file:
            pid = int(this_file.read())
        if os.path.exists("/proc/%d" % pid):
            sys.exit("process already running, his pid %d" % pid)
        else:
            os.remove(pid_path)
    if not option:
        if os.path.exists(pid_path):
            with open(pid_path) as this_file:
                pid = int(this_file.read())
            os.remove(pid_path)
            try:
                os.kill(pid, 9)
                sys.exit("demon was killed")
            except OSError:
                sys.exit("demon was not started")
        else:
            sys.exit("demon was not started")
demon(args.option)
if tree:
    for document in tree:
        database.create_new(document["pathname"], document["is_dir"], watched_dir)
mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_ATTRIB \
       | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, db, **kwargs):
        super(EventHandler, self).__init__(**kwargs)
        self.db = db

    def process_IN_DELETE(self, event):
        self.db.delete_file(event.pathname)
        self.db.write_log(event)

    def process_IN_CREATE(self, event):
        self.db.create_new(event.pathname, event.dir, watched_dir)
        self.db.write_log(event)

    def process_IN_CLOSE_WRITE(self, event):
        self.db.put_file_revision(event.pathname)
        self.db.write_log(event)

    def process_IN_ATTRIB(self, event):
        self.db.put_file_revision(event.pathname)
        self.db.write_log(event)

    def process_IN_MOVED_TO(self, event):
        if hasattr(event, 'src_pathname'):
            self.db.move(event.pathname, watched_dir, event.src_pathname)
            self.db.write_log(event)
        else:
            self.db.move(event.pathname, watched_dir)
            self.db.write_log(event)

notifier = pyinotify.Notifier(wm, EventHandler(database))
wm.add_watch(watched_dir, mask, rec=True, auto_add=True)


try:
    notifier.loop(daemonize=demon_start, pid_file=pid_path)
except pyinotify.NotifierError, err:
    print >> sys.stderr, err