# Copyleft (c) 2011 Shanto. No Rights Reserved.

# How to use this plug-in with PkgBrowser?
# Just import it after initializing the window. Assuming this file is under lib/plugins:
# plugpath = os.path.join(os.path.dirname(__file__), 'plugins')
# import imp
# for module in [file for file in os.listdir(plugpath) if file[-2:] == 'py']:
#     try: imp.load_module(module[:-3], *imp.find_module(module[:-3], [plugpath]))
#     except: pass

import os
from PyQt4.QtCore import Qt, SIGNAL, SLOT
from PyQt4.QtGui import qApp, QApplication, QMenu, QIcon, QAction
from lib.window import Window
from lib.enum import State

class Terminal(object): # generic class to represent GUI terminals
    exe = None
    format = None
    hold = "echo -n Press any key to continue...; read continue"

    def __init__(self):
        if not os.path.exists(self.exe):
            raise NotImplementedError("Unable to find %s" % self.exe)

    def execute(self, command, arguments=None):
        shell = os.environ.get('SHELL', '/bin/bash')
        op = "%s %s" % (self.exe, self.format) % {'shell': shell, 'command': command, 'arguments': arguments, 'hold': self.hold}
        return os.system(op)

    @staticmethod
    def default():
        try:
            if os.environ.get('GNOME_DESKTOP_SESSION_ID'):
                return GnomeTerminal()
            elif os.environ.get('KDE_FULL_SESSION') == 'true':
                return KdeTerminal()
            elif ' = "xfce4"' in getoutput('xprop -root _DT_SAVE_MODE'):
                return XfceTerminal()
        except: pass

        for dt in (GnomeTerminal, KdeTerminal, XfceTerminal):
            if os.system(dt.execute("exit 0")) == 0:
                return dt()

        raise NotImplementedError("Failed to detect your desktop terminal program.")

class GnomeTerminal(Terminal):
    exe = "/usr/bin/gnome-terminal"
    format = "-x %(shell)s -c '%(command)s %(arguments)s; %(hold)s'"

class KdeTerminal(Terminal):
    exe = "/usr/bin/konsole"
    format = "-e %(shell)s -c '%(command)s %(arguments)s; %(hold)s'"

class XfceTerminal(Terminal):
    exe = "/usr/bin/terminal"
    format = "-e \"%(shell)s -c '%(command)s %(arguments)s; %(hold)s'\""

class Frontend(object): # generic class to represent (CLI) frontends to ALPM/AUR
    exe = None
    args = None
    window = None

    def execute(self, arguments):
        return Terminal.default().execute(self.exe, arguments=arguments)

    def install(self, package, update=False):
        action = "-S"
        return self.execute("%s %s" % (action, package.get('name')))

    def remove(self, package, force=False):
        action = "-Rdd" if force else "-R"
        return self.execute("%s %s" % (action, package.get('name')))

    @staticmethod
    def default():
        for fe in (Yaourt, Packer, Pacman):
            if os.path.exists(fe.exe):
                return fe()
        raise NotImplementedError("Failed to detect your package manager frontend.")

    @staticmethod
    def handlePackageContextAction(point):
        window = QApplication.activeWindow()
        package = window.currentPackage()
        menu = QMenu(parent=window)

        install = QAction(QIcon(':/icons/installed.png'), "&Install", window.packages)
        install.connect(install, SIGNAL('triggered()'), lambda: Frontend.default().install(package))
        install.setEnabled(package.get('state', False) & (State.NonInstalled | State.AUR))

        update = QAction(QIcon(':/icons/upgrade.png'), "&Update", window.packages)
        update.connect(update, SIGNAL('triggered()'), lambda: Frontend.default().install(package, update=True))
        update.setEnabled(package.get('state', False) & State.Update)

        remove = QAction(QIcon(':/icons/stop.png'), "&Remove", window.packages)
        remove.connect(remove, SIGNAL('triggered()'), lambda: Frontend.default().remove(package))
        remove.setEnabled(package.get('state', False) & (State.Installed | State.Update))

        remove_forced = QAction(QIcon(':/icons/orphan.png'), "&Remove (force)", window.packages)
        remove_forced.connect(remove_forced, SIGNAL('triggered()'), lambda: Frontend.default().remove(package, force=True))
        remove_forced.setEnabled(package.get('state', False) & (State.Installed | State.Update))

        menu.addActions((install, update, remove, remove_forced))
        menu.exec_(window.packages.mapToGlobal(point))

class Packer(Frontend):
    exe = '/usr/bin/packer'

class Yaourt(Frontend):
    exe = '/usr/bin/yaourt'

class Pacman(Frontend):
    exe = '/usr/bin/pacman'

try: # find the main Window object
    Frontend.window = qApp.window()
    if Frontend.window == None:
        raise
except:
    raise RuntimeError("Unable to find parent window")
Frontend.window.packages.setContextMenuPolicy(Qt.CustomContextMenu) # patch packages widget
Frontend.window.packages.customContextMenuRequested.connect(Frontend.handlePackageContextAction)