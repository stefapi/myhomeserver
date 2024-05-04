import fcntl
import os
import signal
import sys


def __handle_signal(signum, frame, lockfile, pidfile_path, pid):
    print("Signal SIGTERM reçu. Nettoyage et arrêt du processus...")
    __cleanup(lockfile, pidfile_path, pid)

def __cleanup(lockfile, pidfile_path, pid):
    __release_pidfile(lockfile)
    # Supprime le fichier de verrouillage
    if os.path.exists(pidfile_path):
        os.remove(pidfile_path)
    # Termine le processus fils
    os._exit(0)  # Termine le processus fils immédiatement sans nettoyage supplémentaire

def __acquire_pidfile(pidfile_path):
    try:
        lockfile = open(pidfile_path, 'w')
        fcntl.lockf(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception as e:
        print ("Failed to acquire lockfile: %s" % e)
        sys.exit(1)
    return lockfile

def __release_pidfile(lockfile):
    try:
        fcntl.lockf(lockfile, fcntl.LOCK_UN)
        lockfile.close()
    except Exception as e:
        print ("Failed to release lockfile: %s" % e)

def start_daemon(app_name, pidfile_path, args, detach=True):
    """ Start a daemon process.
        :param app_name: The name of the application.
        :param pidfile: The path to the PID file.
        :param args: A list of arguments to pass to the application.
        :return: ``None``.
    """

    if not os.path.isabs(pidfile_path):
        print ("pidfile path not absolute", pidfile_path)
        sys.exit(1)

    if os.path.exists(pidfile_path):
        print ("pidfile already exists daemon", pidfile_path)
        sys.exit(1)

    # fork off a child
    try:
        if detach:
            # do first fork
            pid = os.fork()
            if pid > 0:
                # exit first parent
                print("first parent exiting process is detached.\nWatching process has PID: ", pid)
                sys.exit(0)
        pid = os.fork()
    except OSError as e:
        print ("fork #1 failed: %d (%s)" % (e.errno, e.strerror))
        sys.exit(1)
    if pid > 0:
        # write pidfile with our pid
        with open(pidfile_path, 'w') as pidfile:
            pidfile.write("%d\n" % os.getpid())

        lockfile = __acquire_pidfile(pidfile_path)

        # Définit le gestionnaire de signal pour SIGTERM
        signal.signal(signal.SIGTERM, lambda signum, frame: __handle_signal(signum, frame, lockfile, pidfile_path, pid))
        # second parent is watching
        print("Second parent is watching process with PID: ", pid)
        try:
            os.waitpid(pid, 0)
        except KeyboardInterrupt:
            print ("child caught keyboard interrupt, exiting")
        return 0

    # in child, launch the application
