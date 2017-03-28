#!/usr/bin/python
import os
import sys
import time
import serial
import platform
import struct

from enum import Enum
from inspect import currentframe, getframeinfo
from threading import Thread
from time import sleep
from enum import Enum

from log_color import highlight_text, color, styles

if platform.system()== 'Linux':
    from getch import getch
    newline = '\r\n'
    getcmd = lambda cmd : bytes(cmd, 'utf-8')
elif platform.system() == 'Windows':
    from msvcrt import getch
    newline = '\r\n'
    getcmd = lambda cmd : cmd

#global
running = True
lst_user_commands = []
dct_user_commands = {}
dct_highlights = {}
dct_default_highlight = {   'begin' : (['fg_light_red'], ['fg_orange', 'bold']),
                    'arm' : ([], ['fg_green', 'bold']),
                    'mcu' : (['fg_purple'], ['fg_red'])}


def get_formatted_menu(str):
    menu_len = 50

    markers = menu_len - len(str) - 2

    if markers < 0:
        print('Cannot format menu for {}'.format(str))
        sys.exit()

    if markers % 2 == 0:
        markers_begin = int(markers / 2)
        markers_end = int(markers / 2)
    else:
        markers_begin = int(markers / 2)
        markers_end = int(markers / 2) + 1

    menu_top = '-' * markers_begin + ' ' + str + ' ' + '-' * markers_end
    menu_buttom = '-' * menu_len

    return menu_top, menu_buttom


dct_serial = {
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

class ComPort(serial.Serial):
    def __init__(self):
        serial.Serial.__init__(self)

        self.port = None
        self.baudrate = 0
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        
        self.timeout = 0.1          
        self.xonxoff = False        
        self.rtscts = False         
        self.dsrdtr = False         
        self.writeTimeout = 2 

    def open(self):
        try: 
            super().open()
        except Exception as e:
            print("{}:{} > error open serial port: {}".format(getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno, str(e)), end=newline)
            sys.exit()

        if not self.isOpen():
            print("{}:{} > cannot open serial port ".format(getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno), end=newline)
            sys.exit()

        try:
            self.flushInput() #flush input buffer, discarding all its contents
        except Exception as e:
            print("{}:{} > error communicating...: {}".format(getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno, str(e)), end=newline)


    def get_info(self):
        menu_top, menu_buttom = get_formatted_menu('Connection Info')
        return \
"""
{}
Port:       {}
Baudrate:   {}
Bytesize:   {}
Parity:     {}
Stopbits:   {}
{}
""".format(menu_top, self.port, self.baudrate, self.bytesize, self.parity, self.stopbits, menu_buttom)

com = ComPort()

class ColorScheme:
    def __init__(self, frozen, information, command):
        self.frozen = frozen
        self.information = information
        self.command = command



color_scheme_default = ColorScheme( frozen=['fg_light_blue'],
                                    information=['fg_yellow', 'bold'],
                                    command=['fg_cyan', 'bold', 'underline'])

color_scheme = color_scheme_default


def print_help(lst_cmd=lst_user_commands):
    menu_top, menu_buttom = get_formatted_menu('Help')
    print(color(menu_top, color_scheme.information), end=newline)
    for ucmd in lst_cmd:
        print(color(str(ucmd), color_scheme.information), end=newline)
    print(color(menu_buttom, color_scheme.information), end=newline)

def quit_logger():
    global running
    print(color('Exiting...', color_scheme.command), end=newline)
    running = False

class UserCommands:
    def __init__(self, keycmd, str_keycmd, desc, callback=None):
        self.keycmd = keycmd
        self.str_keycmd = str_keycmd
        self.desc = desc
        self.callback = callback

    def __str__(self):
        return '< {} >   - {}'.format(self.str_keycmd, self.desc)

class Logger:
    def __init__(self, dct_default_highlight):

        self.dct_default_highlight = dct_default_highlight

        self.freeze = False
        self.lst_freeze = []

    def log_line(self, line):

        if not self.freeze:
            self.printer(line)
        else:
            self.lst_freeze.append(line)

        
    def add_highlight(self):
        self.freeze = True

        str = input(color('Input string to highlight:', color_scheme.command))
        
        fmt_word = input(color('Input word color (e.g. fg_blue):', color_scheme.command))
        fmt_line = input(color('Input line color (e.g. bg_purple):', color_scheme.command))
        
        if not fmt_word:
            fmt_word = []
        else:
            fmt_word = [fmt_word]

        if not fmt_line:
            fmt_line = []
        else:
            fmt_line = [fmt_line]

        if str and (fmt_word or fmt_line):
            self.dct_default_highlight[str] = (fmt_line, fmt_word)
        self.freeze_logger()

    def freeze_logger(self):
        if (self.freeze):
            for line in self.lst_freeze:
                
                self.printer(line, override_fmt_line=color_scheme.frozen)

            self.lst_freeze = []
            print(color('Log Unfrozen', color_scheme.command), end=newline)
        else:
            print(color('Log frozen, resume with <Ctrl-F>', color_scheme.command), end=newline)

        self.freeze = not self.freeze

    def list_highlight(self):
        menu_top, menu_buttom = get_formatted_menu('Highlights')
        print(color(menu_top, color_scheme.information), end=newline)
        for hl, (fmt_line, fmt_word) in self.dct_default_highlight.items():
            print(color('Keyword: ', color_scheme.information) + color('{}'.format(hl), fmt_word), end=newline)
            print(color('    format keyword: {}'.format(fmt_word), color_scheme.information), end=newline)
            print(color('    format line:    {}'.format(fmt_line), color_scheme.information), end=newline)
        print(color(menu_buttom, color_scheme.information), end=newline)

    def printer(self, line, override_fmt_line=None):
        

        hit = False
        fmt_line = []
        
        for hl in self.dct_default_highlight:
            if hl in line.lower():
                hit = True
                (fmt_line, _) = self.dct_default_highlight[hl]

        if override_fmt_line:
            fmt_line = override_fmt_line

        if not hit:
            formatted_line = color(line, fmt_line)
        else:
            words = line.lower().split(' ')

            formatted_line = ''
            for word in words:
                formatted_word = ''
                for hl in self.dct_default_highlight:
                    if hl in word:
                        (_, fmt_word) = self.dct_default_highlight[hl]
                        word = color(word, fmt_word)
                        break


                if not formatted_word:
                    formatted_line += color(word + ' ', fmt_line)
                else:
                    formatted_line += word + color(' ', formatted_line)
        
        print(formatted_line.rstrip(), end=newline)

logger = Logger(dct_default_highlight)


def banana():
    print(color('BANANA!!', ['fg_yellow']), end=newline)
    print(color(" _ \n//\\ \nV  \\ \n \\  \\_ \n  \\,'.`-. \n   |\\ `. `. \n   ( \\  `. `-.                        _,.-/\\ \n    \\ \\   `.  `-._             __..--' ,-'\\/ \n     \\ `.   `-.   `-..___..---'   _.--' ,'/ \n      `. `.    `-._        __..--'    ,' / \n        `. `-_     ``--..''       _.-' ,' \n          `-_ `-.___        __,--'   ,' \n             `-.__  `----\"\"\"    __.-' \nhh                `--..____..--'\n", ['fg_yellow', 'bold']), end=newline)


def command_reader(arg):
    global running
    while running:
        cmd = getch()
        
        # uncomment to get keyboard command for new commands
        cmd = getcmd(cmd)
        #print('cmd:', cmd, end=newline)
        # 
        try:
            dct_user_commands[cmd].callback()
        except (KeyError, TypeError):
            pass

def open_com():
    global running
    global logger
    global com
    print('open_com', end=newline)

    #com = ComPort('\\.\COM4', 921600)
    com.open()
    
    while(running):
        try:
            response = com.read(10000).decode('utf-8').rstrip()
        except Exception as e:
            print("{}:{} > error communicating...: {}".format(getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno, str(e)), end=newline)
            sys.exit()

        if response:
            lines = response.split('\r\n')
            
            for line in lines:
                logger.log_line(line)


def close_com():
    print('close_com', end=newline)
    
    try:
        ser.close()
    except Exception as e:
        print("{}:{} > error communicating...: ".format(getframeinfo(currentframe()).filename, getframeinfo(currentframe()).lineno, str(e)), end=newline)


def start_logger():
    print('start_logger', end=newline)

def str_to_list(str):
    fmt = str.replace('[', '').replace("'", '').replace(']', '').split(',')
    if fmt:
        return fmt
    else:
        return []

class Settings:
    def __init__(self):
        self.dct_config = { 'port' : [None, 'COM4'],
                            'baudrate' : [None, 921600],
                            'bytesize' : [None, 'EIGHTBITS'],
                            'parity' : [None, 'PARITY_NONE'],
                            'stopbits' : [None, 'STOPBITS_ONE'],
                            'frozen' : [None, color_scheme_default.frozen],
                            'information' : [None, color_scheme_default.information],
                            'command' : [None, color_scheme_default.command]}
        self.highlights =  ({}, dct_default_highlight)

    def get(self, str_setting, default_value=False):
        try:
            (setting, default) = self.dct_config[str_setting]
            if setting and not default_value:
                return setting
            else:
                return default
        except KeyError:
            return None

    def set(self, str_setting, value):
        #print(str_setting, value)
        try:
            if str_setting in ['frozen', 'information', 'command']:
                self.dct_config[str_setting][0] = str_to_list(value)
            else:
                self.dct_config[str_setting][0] = value
        except KeyError:
            return None

    def add_highlight(self, keyword, fmt_line, fmt_word):

        self.highlights[0][keyword] = [str_to_list(fmt_line), str_to_list(fmt_word)]

    def get_highlights(self):
        (setting, default) = self.highlights
        if setting:
            return setting
        else:
            return default

    def apply(self):

        port = self.get('port')
        if 'com' in port.lower():
            port = '\\.\\' + port
        com.port = port
        com.baudrate = self.get('baudrate')
        com.bytesize = dct_serial[self.get('bytesize')]
        com.parity = dct_serial[self.get('parity')]
        com.stopbits = dct_serial[self.get('stopbits')]

        color_scheme.frozen = self.get('frozen')
        color_scheme.information = self.get('information')
        color_scheme.command = self.get('command')

        dct_highlights = self.get_highlights()
        #for keyword, (str_fmt_line, str_fmt_word) in self.get_highlights().items():
            #print(keyword, str_fmt_line, str_fmt_word)
            #dct_highlights


    def __str__(self):
        str_highlights = ', '.join(self.get_highlights().keys())
        str_settings = \
"""Connections
    port:           {}
    baudrate:       {}
    bytesize:       {}
    parity:         {}
    stopbits:       {}
Color Scheme
    frozen:         {}
    information:    {}
    command:        {}
Highlights
    {}""".format(self.get('port'), self.get('baudrate'), self.get('bytesize'), self.get('parity'), self.get('stopbits'), self.get('frozen'), self.get('information'), self.get('command'), str_highlights)
        return str_settings



class Setting:
    def __init__(self, name, desc, default_value, avail_values, command_line, fmt_color, source):
        self.name = name
        self.desc = desc
        self.default_value = default_value
        self.avail_values = avail_values
        self.command_line = command_line
        self.fmt_color = fmt_color
        self.source = source

        self.value = None

    def str_arg(self):

        str_arg = "{:<20}".format(self.name)
        if self.desc:
            str_arg += self.desc
        if self.avail_values:
            str_arg += "Available values: {}\n".format(', '.join(self.avail_values))

        if self.default_value:
            str_arg += "{:20}Default value: {}".format('', self.default_value)
        return str_arg + '\n'

    def get_arg(self):
        if self.value:
            return self.value
        elif self.default_value:
            return self.default_value
        elif self.desc:
            return self.desc
        else:
            return ''

class SettingX(list):
    def __init__(self):
        list.__init__(self)

    def print_arg(self):
        for setting in self:
            if setting.command_line:
                print(setting.str_arg())

    def get_arg(self, name):
        for setting in self:
            #print(setting.name, name)
            if setting.name == name:
                return setting.get_arg()

settingsx = SettingX()

settings = Settings()
def open_config_file(path_cfg):

    with open(path_cfg) as f:

        found_hl = False
        for line in f:

            if '# Highlight text #' in line:
                found_hl = True

            elif line.strip() and line.lstrip()[0] != '#':
                if found_hl:
                    fields = line.split()

                    field_fmt_line = line.split('[')[1]
                    field_fmt_word = line.split('[')[2]
                    
                    settings.add_highlight(fields[0], field_fmt_line, field_fmt_word)
                    
                else:
                    line = line.replace('=', ' ')
                    fields = line.split()
                    settings.set(fields[0], "".join(fields[1:]))

def save_config_file(path_cfg):

    port = settings.get('port')
    baudrate = settings.get('baudrate')
    bytesize = settings.get('bytesize')
    parity = settings.get('parity')
    stopbits = settings.get('stopbits')
    frozen = settings.get('frozen')
    information = settings.get('information')
    command = settings.get('command')
    dct_hl = settings.get_highlights()

    str_highlights = "{:<20}{:<20}{:<20}\n".format("# Word", "Format Line", "Format Word")
    for keyword, (fmt_line, fmt_word) in sorted(dct_hl.items()):
        #str_highlights += "{:20}{:20}{:20}{}".format(keyword, fmt_line, fmt_word, newline)
        str_highlights += "{:<20}{:<20}{:<20}\n".format(keyword, str(fmt_line), str(fmt_word))

    str_config = \
"""
###################################################
# COMpletelyLOGical - COM port LOGger config file #
###################################################

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
frozen              {}
information         {}
command             {}

##################
# Highlight text #
##################
# the below example will highlight all words containing 'sensor' with
# bold orange text, the rest of line will be highlighted with light red text
# Note. One of the formats can be empty

{}
""".format(
    settingsx.get_arg('port'),
    settingsx.get_arg('baudrate'),
    settingsx.get_arg('bytesize'),
    settingsx.get_arg('parity'),
    settingsx.get_arg('stopbits'),
    settingsx.get_arg('frozen'),
    settingsx.get_arg('information'),
    settingsx.get_arg('command'),
    settingsx.get_arg('str_highlights'))

    with open(path_cfg, 'w') as f:
        print(str_config, file=f)

lst_user_commands.append(UserCommands(b'\x03', 'Ctrl-C', 'Clear log', callback=lambda:(os.system('cls'), print(color('Log Cleared', color_scheme.command), end=newline))))
lst_user_commands.append(UserCommands(b'\x07', 'Ctrl-G', 'Create a mark in the log', callback=lambda : print(color('='*75, color_scheme.command), end=newline)))
lst_user_commands.append(UserCommands(b'\x06', 'Ctrl-F', 'Freeze the log input', callback=logger.freeze_logger))
lst_user_commands.append(UserCommands(b'\x04', 'Ctrl-D', 'Connection details', callback=lambda:print(color(com.get_info(), color_scheme.information))))
lst_user_commands.append(UserCommands(b'\x01', 'Ctrl-A', 'Add highlight', callback=logger.add_highlight))
lst_user_commands.append(UserCommands(b'\x0c', 'Ctrl-L', 'List highlight', callback=logger.list_highlight))
lst_user_commands.append(UserCommands(b'\x08', 'Ctrl-H', 'Help', callback=print_help))
lst_user_commands.append(UserCommands(b'\x02', 'Ctrl-B', 'Banana?', callback=banana))
lst_user_commands.append(UserCommands(b'\x11', 'Ctrl-Q', 'Quit', callback=quit_logger))

dct_user_commands = d = {ucmd.keycmd: ucmd for ucmd in lst_user_commands}

settingsx.append(Setting(name='port', desc="e.g. COMx  (windows) or /dev/ttySxx  (linux)", default_value=None, avail_values=None, command_line=True, fmt_color=False, source=com.name))
settingsx.append(Setting(name='baudrate', desc="e.g. 115200, 921600, etc.", default_value=None, avail_values=None, command_line=True, fmt_color=False, source=com.baudrate))
settingsx.append(Setting(name='bytesize', desc=None, default_value='EIGHTBITS', avail_values=['FIVEBITS', 'SIXBITS', 'SEVENBITS', 'EIGHTBITS'], command_line=True, fmt_color=False, source=com.bytesize))
settingsx.append(Setting(name='parity', desc=None, default_value='PARITY_NONE', avail_values=['PARITY_NONE', 'PARITY_EVEN', 'PARITY_ODD', 'PARITY_MARK', 'PARITY_SPACE'], command_line=True, fmt_color=False, source=com.parity))
settingsx.append(Setting(name='stopbits', desc=None, default_value='STOPBITS_ONE', avail_values=['STOPBITS_ONE', 'STOPBITS_ONE_POINT_FIVE', 'STOPBITS_TWO'], command_line=True, fmt_color=False, source=com.stopbits))

settingsx.append(Setting(name='frozen', desc=None, default_value=color_scheme_default.frozen, avail_values=styles.keys(), command_line=False, fmt_color=True, source=color_scheme.frozen))
settingsx.append(Setting(name='information', desc=None, default_value=color_scheme_default.information, avail_values=styles.keys(), command_line=False, fmt_color=True, source=color_scheme.information))
settingsx.append(Setting(name='command', desc=None, default_value=color_scheme_default.command, avail_values=styles.keys(), command_line=False, fmt_color=True, source=color_scheme.command))


if __name__ == '__main__':
    arg = sys.argv[1]
    if '-h' in arg or '--help' in arg:
        print('HELP!')
        print('Command line arguments, not yet implemented :(')
        print(settingsx.print_arg())
        sys.exit()
    elif '-create' in arg:
        if len(sys.argv) == 3:
            file_path = sys.argv[2]
            save_config_file(sys.argv[2])
            print('--- CREATE DEFAULT SETTINGS ---')
            print(settings)
        else:
            print('Invalid or missing config file path.')
            sys.exit()

    elif '-load' in arg:
        if len(sys.argv) == 3:
            file_path = sys.argv[2]
            if os.path.isfile(sys.argv[2]):
                open_config_file(sys.argv[2])
                settings.apply()
                print(color('--- LOAD SETTINGS ---', color_scheme.information))
                print(color(str(settings), color_scheme.information))
            else:
                print('Invalid or missing config file path.')
        else:
            print('Invalid or missing config file path.')
            sys.exit()


    thread = Thread(target = command_reader, args = (10, ))
    thread.start()
    
    print("thread finished...exiting", end=newline)

    start_logger()
    open_com()
    thread.join()



