import serial
from inspect import currentframe, getframeinfo

import log_interface as li

dct_serial = {  'FIVEBITS' : serial.FIVEBITS,
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
    def __init__(self, ui, port=None, baudrate=0, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE):
        serial.Serial.__init__(self)

        self.ui = ui

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

        self.running = True

    def open(self):
        self.running = True
        self.ui.print_cmd("COM open")
        try: 
            super().open()
        except Exception as e:
            self.ui.print_alert("{}:{} > error open serial port: {}".format(getframeinfo(currentframe()).filename.split('/')[-1].split('\\')[-1], getframeinfo(currentframe()).lineno, str(e)))

        if not self.isOpen():
            self.ui.print_alert("{}:{} > cannot open serial port ".format(getframeinfo(currentframe()).filename.split('/')[-1].split('\\')[-1], getframeinfo(currentframe()).lineno))
            #sys.exit()

        #try:
        #    self.flushInput() #flush input buffer, discarding all its contents
        #except Exception as e:
        #    self.ui.print_alert("{}:{} > error communicating...: {}".format(getframeinfo(currentframe()).filename.split('/')[-1].split('\\')[-1], getframeinfo(currentframe()).lineno, str(e)))

    def close(self):
        self.ui.print_cmd("COM Close")
        try:
            super().close()
        except Exception as e:
            self.ui.print_alert("{}:{} > error close serial port: {}".format(getframeinfo(currentframe()).filename.split('/')[-1].split('\\')[-1], getframeinfo(currentframe()).lineno, str(e)))

    def get_line(self):
        while(self.running):
            
            #last = ''
            response = None
            try:
                if self.isOpen():
                    response = self.read(10000).decode('utf-8').rstrip()
            except Exception as e:
                self.ui.print_alert("{}:{} > error communicating...: {}".format(getframeinfo(currentframe()).filename.split('/')[-1].split('\\')[-1], getframeinfo(currentframe()).lineno, str(e)))
                #self.running = False
                self.close()

            if response:

                #final_ending = response[-2:] == '\r\n'

                lines = response.split('\r\n')
                #lines[0] = last + lines[0]
                #print('LINE', lines[0], '###', last)
                #if final_ending:
                #    last = ''
                #else:
                #    last = lines[-1]
                #    lines = lines[:-1]
                #    print('LAST', last)
                
                for line in lines:
                    #logger.log_line(line)
                    yield line

    def get_info(self):
        menu_top, menu_buttom = li.formatted_menu('Connection Info')
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