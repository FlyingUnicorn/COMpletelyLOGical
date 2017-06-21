#!/usr/bin/python
import os
import sys
import time
import serial
import platform
import struct
import log_color as lc
import log_interface as li
import com_handler as ch
import misc as misc

from argparse import ArgumentParser
from enum import Enum
from inspect import currentframe, getframeinfo
from threading import Thread
from time import sleep
from enum import Enum
from datetime import datetime
from log_color import highlight_text, color, styles, ColorScheme

if platform.system()== 'Linux':
    print("LINUX")  
    import sys    
    import termios
    import fcntl

    def getch():
        fd = sys.stdin.fileno()

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

        try:        
            while 1:            
                try:
                    c = sys.stdin.read(1)
                    if c:
                        break
                except IOError: pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
     
        return c

    #from getch import getch
    newline = '\n'
    getcmd = lambda cmd : bytes(cmd, 'utf-8')
elif platform.system() == 'Windows':
    from msvcrt import getch
    newline = '\r\n'
    getcmd = lambda cmd : cmd

#global
lst_user_commands = []
dct_user_commands = {}
dct_highlights = {}

class Logger(Thread):
    def __init__(self, dct_keywords, com, ui, newline, kpi):
        Thread.__init__(self)

        self.dct_keywords = dct_keywords
        self.com = com
        self.ui = ui
        self.newline = newline
        self.kpi = kpi

        self.freeze = False
        self.lst_freeze = []

    def run(self):
        for line in self.com.get_line():
            self.log_line(line)

    def log_line(self, line):

        if not self.freeze:
            self.printer(line)
        else:
            self.lst_freeze.append(line)
    
    def add_highlight(self):
        self.freeze = True

        keyword = input(ui.get_cmd('Input string to highlight:'))
        string_fmt_word = input(ui.get_cmd('Input word color (e.g. fg_blue):'))
        string_fmt_text = input(ui.get_cmd('Input line color (e.g. bg_purple):'))

        hl = None
        if keyword and (string_fmt_text or string_fmt_word):
            hl = lc.parse_highlight(string_fmt_text=string_fmt_text, string_fmt_word=string_fmt_word)
        
        if hl:
            self.dct_keywords[keyword] = hl
        else:
            ui.print_alert('Invalid hightlight format')

        self.freeze_log()

    def freeze_log(self):
        if (self.freeze):
            for line in self.lst_freeze:
                self.printer(line, override_fmt=ui.color_scheme.frozen)

            self.lst_freeze = []
            self.ui.print_cmd('Log Unfrozen')
        else:
            self.ui.print_cmd('Log frozen, resume with <Ctrl-F>')

        self.freeze = not self.freeze

    def printer(self, line, override_fmt=None):
        
        hl = None
        for keyword in self.dct_keywords:
            if keyword in line.lower():
                hl = self.dct_keywords[keyword]

        if not hl:
            if override_fmt:
                hl = override_fmt
        else:
            if override_fmt:
                hl = lc.Highlight(override_fmt.fmt_text, hl.fmt_word)

        if hl:
            for keyword in self.dct_keywords:
                found, formatted_line = lc.highlight_text(line, keyword, hl)
                if found:
                    break
        else:
            formatted_line = line
        
        self.kpi.handle_kpi(formatted_line)

        print('[' + datetime.now().strftime('%H:%M:%S.%f')[:-3] + ']', end=' ')
        print(formatted_line)

dct_serial_to_const = {
    'FIVEBITS' : serial.FIVEBITS,
    'SIXBITS' : serial.SIXBITS,
    'SEVENBITS' : serial.SEVENBITS,
    'EIGHTBITS' : serial.EIGHTBITS,

    'PARITY_NONE' : serial.PARITY_NONE,
    'PARITY_EVEN' : serial.PARITY_EVEN,
    'PARITY_ODD' : serial.PARITY_ODD,
    'PARITY_MARK' : serial.PARITY_MARK,
    'PARITY_SPACE' : serial.PARITY_SPACE,

    'STOPBITS_ONE' : serial.STOPBITS_ONE,
    'STOPBITS_ONE_POINT_FIVE' : serial.STOPBITS_ONE_POINT_FIVE,
    'STOPBITS_TWO' : serial.STOPBITS_TWO}
dct_serial_to_string = {v: k for k, v in dct_serial_to_const.items()}


class Config:
    def __init__(self, com, dct_keywords, color_scheme):
        self.com = com
        self.dct_keywords = dct_keywords
        self.color_scheme = color_scheme

    def create(self, path_cfg):
        with open(path_cfg, 'w') as f:
            str_highlights = "{:<20}{:<20}{:<20}\n".format("# Word", "Format Line", "Format Word")
            for keyword, hl in sorted(self.dct_keywords.items()):
                #str_highlights += "{:20}{:20}{:20}{}".format(keyword, fmt_line, fmt_word, newline)
                str_highlights += "{:<20}{:<20}{:<20}\n".format(keyword, str(hl.fmt_text), str(hl.fmt_word))

            str_config = \
"""
###################################################
# COMpletelyLOGical - COM port LOGger config file #
###################################################

######################
# Connection Details #
######################
# Port
port = {}

# Baudrate
baudrate = {}

# Byte size 
# Available: FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
bytesize = {}

# Parity 
# Available: PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE
parity = {}

# Stop bits
# Available: STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO
stopbits = {}

################
# Color Scheme #
################

# Available text formats
#
#  text colors             background colors       styles
#  'fg_black'              'bg_black'              'bold'
#  'fg_red'                'bg_red'                'underline'
#  'fg_green'              'bg_green'              'reverse'
#  'fg_orange'             'bg_orange'             'strike_through'
#  'fg_blue'               'bg_blue'               'invisible'
#  'fg_purple'             'bg_purple'
#  'fg_cyan'               'bg_cyan'
#  'fg_light_grey'         'bg_light_grey'
#  'fg_dark_grey'
#  'fg_light_red'
#  'fg_light_green'
#  'fg_yellow'
#  'fg_light_blue'
#  'fg_pink'
#  'fg_light_cyan'

frozen              {}
information         {}
command             {}
alert               {}

##################
# Highlight text #
##################
# the below example will highlight all words containing 'sensor' with
# bold orange text, the rest of line will be highlighted with light red text
# Note. One of the formats can be empty

{}
""".format( self.com.name,
            self.com.baudrate,
            dct_serial_to_string[self.com.bytesize],
            dct_serial_to_string[self.com.parity],
            dct_serial_to_string[self.com.stopbits],
            self.color_scheme.frozen.fmt_text,
            self.color_scheme.information.fmt_text,
            self.color_scheme.command.fmt_text,
            self.color_scheme.alert.fmt_text,
            str_highlights)

            print(str_config, file=f)


    def load(self, path_cfg):
        if not os.path.isfile(path_cfg):
            print("Config file does not exist!")
            return False

        with open(path_cfg) as f:
            found_hl = False
            for line in f:

                if '# Highlight text #' in line:
                    found_hl = True

                elif line.strip() and line.lstrip()[0] != '#':
                    if found_hl:
                        
                        if False:
                            # if '\"' in line:
                            #     keyword = line.split('\"')[0]

                            #print(line)
                            fields = line.split()

                            keyword = fields[0]
                            #print(' '.join(fields[1:]))
                            hl = lc.parse_highlight(string=line)
                            self.dct_keywords[keyword] = hl
                            # for kw, hl in self.dct_keywords.items():
                                # print(kw, hl)
                            # sys.exit()
                        else:
                            kw = line.split('\"')
                            #print(kw[1])
                            fields = ''.join(kw[2])
                            #print(fields)
                            hl = lc.parse_highlight(string='x'+fields)
                            self.dct_keywords[kw[1]] = hl


                    else:
                        line = line.replace('=', ' ')
                        fields = line.split()
                        
                        if fields[0] == 'port':
                            self.com.port = fields[1]
                            #print(fields[1])
                        elif fields[0] == 'baudrate':
                            self.com.baudrate = fields[1]
                            #print(fields[1])
                        elif fields[0] == 'bytesize':
                            self.com.bytesize = dct_serial_to_const[fields[1]]
                            #print(fields[1])
                        elif fields[0] == 'parity':
                            self.com.parity = dct_serial_to_const[fields[1]]
                            #print(fields[1])
                        elif fields[0] == 'stopbits':
                            self.com.stopbits = dct_serial_to_const[fields[1]]
                            #print(fields[1])
                        elif fields[0] == 'frozen':
                            #print(''.join(fields[1:]))
                            self.color_scheme.frozen = lc.parse_highlight(string_fmt_text=''.join(fields[1:]))
                        elif fields[0] == 'command':
                            #print(''.join(fields[1:]))
                            self.color_scheme.command = lc.parse_highlight(string_fmt_text=''.join(fields[1:]))
                        elif fields[0] == 'information':
                            #print(''.join(fields[1:]))
                            self.color_scheme.information = lc.parse_highlight(string_fmt_text=''.join(fields[1:]))
                        elif fields[0] == 'alert':
                            #print(''.join(fields[1:]))
                            self.color_scheme.alert = lc.parse_highlight(string_fmt_text=''.join(fields[1:]))

        #sys.exit()
        return True



def command_reader():
    while True:
        cmd = getch()
        
        # uncomment to get keyboard command for new commands
        cmd = getcmd(cmd)
        if cmd:
            pass#print('cmd:', cmd, end=newline)
        try:
            exit = dct_user_commands[cmd].callback()
            if exit == True:
                break
        except (KeyError, TypeError) as e:
            pass
        #print(color('Exiting...', color_scheme.command), end=newline)

if __name__ == '__main__':
    global newline
    parser = ArgumentParser(description=" ### COMpletelyLOGical - COM port LOGger ###")
    parser.add_argument("-create", dest="create", required=False, help="Create new config file", metavar="FILE")
    parser.add_argument("-load", dest="load", required=False, help="Load an existing config file", metavar="FILE")
    args = parser.parse_args()

    if (args.create and not args.load) or (not args.create and args.load):
        pass
    else:
        print('Argument format error!')
    
    dct_keywords = {}
    ui = li.UserInterface(color_scheme=lc.color_scheme_default, lst_cmd=lst_user_commands, dct_hl=dct_keywords, newline=newline)

    kpi = misc.Kpi(ui)

    if args.create:
        com = ch.ComPort(ui, '\\.\COM4', 921600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)
        config = Config(com, lc.dct_default_keywords, lc.color_scheme_default)
        config.create(path_cfg=args.create)
        ui.print_info("Config file created at: {}".format(args.create))
        sys.exit()

    elif args.load:
        com = ch.ComPort(ui)
        logger = Logger(dct_keywords, com, ui, newline, kpi)
        config = Config(com, dct_keywords, lc.color_scheme_default)
        print(args.load)
        loaded = config.load(path_cfg=args.load)

        if not loaded:
            sys.exit()

    lst_user_commands.append(li.UserCommands(b'\x12', 'Ctrl-R', 'Reset log', callback=lambda:(os.system('cls' if os.name == 'nt' else 'clear'), ui.print_cmd('Log Cleared'))))
    lst_user_commands.append(li.UserCommands(b'\x07', 'Ctrl-G', 'Create a mark in the log', callback=ui.print_marker))
    lst_user_commands.append(li.UserCommands(b'\x06', 'Ctrl-F', 'Freeze the log input', callback=logger.freeze_log))
    #lst_user_commands.append(li.UserCommands(b'\x04', 'Ctrl-D', 'Connection details', callback=lambda:print(color(com.get_info(), color_scheme.information))))
    lst_user_commands.append(li.UserCommands(b'\x01', 'Ctrl-A', 'Add highlight', callback=logger.add_highlight))
    lst_user_commands.append(li.UserCommands(b'\x0c', 'Ctrl-L', 'List highlight', callback=ui.list_highlight))
    lst_user_commands.append(li.UserCommands(b'\x0f', 'Ctrl-O', 'Open Port', callback=com.open))
    lst_user_commands.append(li.UserCommands(b'\x08', 'Ctrl-H', 'Help', callback=lambda:ui.print_help()))
    lst_user_commands.append(li.UserCommands(b'\x02', 'Ctrl-B', 'Banana?', callback=lambda:ui.banana()))
    lst_user_commands.append(li.UserCommands(b'\x05', 'Ctrl-E', 'Exit', callback=lambda:True))
    dct_user_commands = d = {ucmd.keycmd: ucmd for ucmd in lst_user_commands}

    thread = Thread(target = command_reader)

    ui.print_info(' ### COMpletelyLOGical - COM port LOGger ###')

    com.open()

    thread.start()
    logger.start()

    thread.join()
    com.running = False
    logger.join()
    print('EXIT')

