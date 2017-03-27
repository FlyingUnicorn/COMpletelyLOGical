######################
# Connection Details #
######################
config_file_format = \
"""
# Port
# e.g. COMxx        (windows)
#      /dev/ttySxx  (linux)
port = COM4

# Baudrate
baudrate = 1000000

# Byte size 
# Available: FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
bytesize=serial.EIGHTBITS

# Parity 
# Available: PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE
parity = PARITY_NONE

# Stop bits
# Available: STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO
stopbits=serial.STOPBITS_ONE


##################
# Highlight text #
##################

# Available highlight formats       
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


# the below example will highlight all words containing 'sensor' with
# bold orange text, the rest of line will be highlighted with light red text
# Note. One of the formats can be empty

# word       Format line       Format text
sensor       [fg_light_red]    [fg_orange, bold]
"""        
        
        
               
        
        