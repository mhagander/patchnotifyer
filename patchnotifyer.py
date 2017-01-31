#!/usr/bin/env python3

import argparse
from io import StringIO
import socket

import smtplib
from email.mime.text import MIMEText

import apt_pkg

class _DevNullProgress(object):
    # Need this class to make the apt output not go to the console
    def update(self, percent = None):
        pass
    def done(self, item = None):
        pass
    def stop(self):
        pass
    def pulse(self, owner = None):
        pass
    def update_status(self, a, b, c, d):
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Patch status notifyer")
    parser.add_argument('--fromaddr', type=str, help='From email address')
    parser.add_argument('--toaddr', type=str, help='To email address')
    parser.add_argument('--subject', type=str, help='Subject', default="Patch status on {0}".format(socket.gethostname()))
    parser.add_argument('--ignorepkg', type=str, nargs='+', default='Ignore packages by exact name')

    args = parser.parse_args()

    if args.fromaddr and not args.toaddr:
        parser.error("Can't specify from without to")
    if args.toaddr and not args.fromaddr:
        parser.error("Can't specify to without from")

    status = StringIO()

    apt_pkg.init()

	# Turn off cache to avoid concurrency issues
    apt_pkg.config.set("Dir::Cache::pkgcache","")

    # "apt-get update"
    sl = apt_pkg.SourceList()
    sl.read_main_list()
    tmpcache = apt_pkg.Cache(_DevNullProgress())
    tmpcache.update(_DevNullProgress(), sl)

    # Now do the actual check
    cache = apt_pkg.Cache(_DevNullProgress())
    depcache = apt_pkg.DepCache(cache)
    depcache.read_pinfile()
    depcache.init()

    if depcache.broken_count > 0:
        status.write("Depcache broken count is {0}\n\n".format(depcache.broken_count))

    depcache.upgrade(True)

    if depcache.del_count > 0:
        status.write("Dist-upgrade generated {0} pending package removals!\n\n".format(depcache.del_count))

    for pkg in cache.packages:
        if depcache.marked_install(pkg) or depcache.marked_upgrade(pkg):
            if pkg.name in args.ignorepkg:
                continue
            status.write("Package {0} requires an update\n".format(pkg.name))

    if status.tell() > 0:
        if args.fromaddr:
            # Send email!
            msg = MIMEText(status.getvalue())
            msg['Subject'] = args.subject
            msg['From'] = args.fromaddr
            msg['To'] = args.toaddr
            s = smtplib.SMTP('localhost')
            s.send_message(msg)
            s.quit()
        else:
            print(status.getvalue())
