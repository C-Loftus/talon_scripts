'''
this program keeps track of the current mode in talon
it does not have the normal .py  extension so that
it will be ignored by talon if the user places this 
repository in the .talon directory.

however, on unix systems, this program will be
run fine with python3 interpreter regardless of
extension.

this program is intended to be run as a background
process at startup. 
'''
APPINDICATOR_ID = 'scriptindicator'

import os, sys
ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
TRAY_DIR = os.path.join(ROOT_DIR, "tray")

import gi
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')
gi.require_version('Gtk', '3.0')

import time as t
from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify
from gi.repository import GLib
from socket import socket   
from threading import Thread
from multiprocessing import Process
import subprocess


def get_port():
    config_path = os.path.join(ROOT_DIR, "tray/tray.py")
        
    with open(config_path) as fp:
        for line in fp:
            if "PORT" in line:
                return int(line.split("=")[1].strip())


def screen_print(message,  delay=2, font="-*-*-medium-*-*-*-*-*-*-*-*-120-*-*", position="bottom"):
    
    thread = Thread(target=os.system, \
        args=("echo {} | osd_cat --delay={} \
             -A center --pos {} --color white -u blue -O 2 -f {}"
             .format(message, delay, position, font),)
        )
    thread.start()

# detect how long user has been working on the keyboard
def timer_create(min_until_break, delay):
    seconds_until_break = min_until_break * 60

    screen_print("Timer starting with {} min intervals".format(min_until_break), delay)

    def idle_time():
        #xprintidle
        p = subprocess.Popen(["xprintidle"], stdout=subprocess.PIPE)
        out = p.stdout.read()
        p.kill()
        return float(out) / 1000 / 60

    def work_time():
        time = 0
        while True:
            # We can use slow polling since only long breaks matter
            t.sleep(30)
            time += 30
            # 5 min in milliseconds
            # If this is true then that means the user took a break 
            # and thus don't need to take another one

            # round to 4 decimal places
            print(f'Idle time = {round(idle_time(), 4)} minutes')

            if idle_time() > 5.0:
                time = 0
                print("break detected")
            elif (time) > (seconds_until_break):
                screen_print('Time to take a break!', delay=delay)

    p = Process(target=work_time, daemon=True)
    p.start()

    return p

PORT = get_port()

class ProgramIndicator:
    timer = None
    link_pid =None

    def __init__(self):
        self.indicator = appindicator.Indicator.new(APPINDICATOR_ID, os.path.join(TRAY_DIR, "blue.svg"), appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())
        notify.init(APPINDICATOR_ID)

        p = Process(target=timer_create, args=(20, 5))
        p.start()
        self.timer = p

        self.s = socket()    
        self.s.bind(('localhost', PORT))    
        self.s.listen()    
        GLib.io_add_watch(GLib.IOChannel(self.s.fileno()), 0, GLib.IOCondition.IN, self.listener, self.s)    
        return gtk.main()

    def build_menu(self):
        menu = gtk.Menu()

        enable = gtk.MenuItem('enable auto break timer')
        enable.connect('activate', self.script)
        menu.append(enable)

        disable = gtk.MenuItem('disable auto break timer')
        disable.connect('activate', self.kill_script)
        menu.append(disable)

        item_quit1 = gtk.MenuItem('Quit')
        item_quit1.connect('activate', self.quit1)
        menu.append(item_quit1)

        menu.show_all()
        return menu

    def set_command(self, source):
        COMMAND_PATH = os.path.join(TRAY_DIR, "command.svg")
        self.indicator.set_icon(os.path.abspath(COMMAND_PATH))

    def set_mixed(self, source):
        MIXED_PATH = os.path.join(TRAY_DIR, "mixed.svg")
        self.indicator.set_icon(os.path.abspath(MIXED_PATH))

    def set_dictation(self, source):

        DICTATION_PATH = os.path.join(TRAY_DIR, "dictation.svg")
        self.indicator.set_icon(os.path.abspath(DICTATION_PATH))

    def set_sleep(self, source):
        SLEEP_PATH = os.path.join(TRAY_DIR, "sleep.svg")
        self.indicator.set_icon(os.path.abspath(SLEEP_PATH))

    def script(self, source):
        # delay of 5 is a sensible default for printing msg to screen 
        if self.timer == None:
            timer = timer_create(min_until_break=20, delay=5)
            self.timer=timer
        else:
            screen_print("Timer already running", delay=2)
            
        return self.script

    def kill_script(self, source):
        try:
            if self.timer != None:
                screen_print("Timer disabled")
                self.timer.kill()
        finally:
            self.timer = None
        return self.kill_script


    def quit1(self, source):
        self.kill_script(self)
        notify.uninit()
        gtk.main_quit()
        if self.s != None:
            self.s.close()
        if self.timer != None:
            self.timer.kill()

    def listener(self, io, cond, sock):    
        conn = sock.accept()[0]    
        GLib.io_add_watch(GLib.IOChannel(conn.fileno()),0,GLib.IOCondition.IN, self.handler, conn)    
        return True    

    def handler(self, io, cond, sock): 
        recv = (sock.recv(100)).decode()

        try:
            pid = int(recv.split(":")[0])
            mode = recv.split(":")[1]
            if recv != "":
                print(mode, pid)
            if 'command' in mode:
                self.set_command(self)    
            elif 'dictation' in mode:
                self.set_dictation(self)
            elif 'mixed' in mode:
                self.set_mixed(self)
            elif 'sleep' in mode:
                self.set_sleep(self)
            elif 'quit_application'in recv:
                self.quit1(self)
            elif 'start timer' in mode:
                self.script(self)
            elif 'stop timer' in mode:
                self.kill_script(self)
            else:
                pass

        finally:
            return True    
    
if __name__ == '__main__':
    try:
        p = ProgramIndicator()
    except KeyboardInterrupt:
        sys.exit(0)