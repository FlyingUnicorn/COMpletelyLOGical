#!/usr/bin/python
import os
import sys
import time
import serial
import platform
import struct

from inspect import currentframe, getframeinfo
from threading import Thread
from time import sleep
from enum import Enum

from log_color import highlight_text, color
import default_input_config

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
com = None
lst_user_commands = []
dct_user_commands = {}
dct_highlight = {   'begin' : (['fg_light_red'], ['fg_orange', 'bold']),
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


class ComPort(serial.Serial):
    def __init__(self, port, baudrate, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE):
        serial.Serial.__init__(self)

        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize    
        self.parity = parity        
        self.stopbits = stopbits           
        
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


class ColorScheme:
    def __init__(self, frozen, information, command):
        self.frozen = frozen
        self.information = information
        self.command = command



color_scheme_default = ColorScheme( frozen=['fg_light_blue'],
                                    information=['fg_yellow', 'bold'],
                                    command=['fg_cyan', 'bold', 'underline'])

color_scheme = color_scheme_default


                    
class Settings:
    def __init__(self):
        pass

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
    def __init__(self, dct_highlight):

        self.dct_highlight = dct_highlight

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
            self.dct_highlight[str] = (fmt_line, fmt_word)
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
        for hl, (fmt_line, fmt_word) in self.dct_highlight.items():
            print(color('Keyword: ', color_scheme.information) + color('{}'.format(hl), fmt_word), end=newline)
            print(color('    format keyword: {}'.format(fmt_word), color_scheme.information), end=newline)
            print(color('    format line:    {}'.format(fmt_line), color_scheme.information), end=newline)
        print(color(menu_buttom, color_scheme.information), end=newline)

    def printer(self, line, override_fmt_line=None):
        

        hit = False
        fmt_line = []
        
        for hl in self.dct_highlight:
            if hl in line.lower():
                hit = True
                (fmt_line, _) = self.dct_highlight[hl]

        if override_fmt_line:
            fmt_line = override_fmt_line

        if not hit:
            formatted_line = color(line, fmt_line)
        else:
            words = line.lower().split(' ')    

            formatted_line = ''
            for word in words:
                formatted_word = ''
                for hl in self.dct_highlight:
                    if hl in word:
                        (_, fmt_word) = self.dct_highlight[hl]
                        word = color(word, fmt_word)
                        break


                if not formatted_word:
                    formatted_line += color(word + ' ', fmt_line)
                else:
                    formatted_line += word + color(' ', formatted_line)
        
        print(formatted_line.rstrip(), end=newline)

logger = Logger(dct_highlight)


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
        
        try:
            dct_user_commands[cmd].callback()
        except (KeyError, TypeError):
            pass

def open_com():
    global running
    global logger
    global com
    print('open_com', end=newline)

    com = ComPort('\\.\COM4', 921600)
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
    settings = Settings()


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

if __name__ == '__main__':
    #print(colored('hello', 'red'), colored('world', 'green'), end=newline)
    
    lst_arg = sys.argv[1:]
    #print(lst_arg)
    # if '-h' in lst_arg or '--help' in lst_arg:
    #     print('HELP!')
    # elif '-create' in lst_arg:
    #     print(default_input_config.config_file_format)

    # sys.exit()
    thread = Thread(target = command_reader, args = (10, ))
    thread.start()
    
    print("thread finished...exiting", end=newline)

    start_logger()
    open_com()
    thread.join()



