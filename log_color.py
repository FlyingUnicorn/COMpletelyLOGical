styles = {
    # styles
    'reset': '\033[0m',
    'bold': '\033[01m',
    'disabled': '\033[02m',
    'underline': '\033[04m',
    'reverse': '\033[07m',
    'strike_through': '\033[09m',
    'invisible': '\033[08m',
    'blink' : '\033[06m',
    #CBLINK2   = '\33[6m'
    # text colors
    'fg_black': '\033[30m',
    'fg_red': '\033[31m',
    'fg_green': '\033[32m',
    #'fg_orange': '\033[33m',
    'fg_blue': '\033[34m',
    'fg_purple': '\033[35m',
    'fg_cyan': '\033[36m',
    'fg_light_grey': '\033[37m',
    'fg_dark_grey': '\033[90m',
    'fg_light_red': '\033[91m',
    'fg_light_green': '\033[92m',
    'fg_yellow': '\033[93m',
    'fg_light_blue': '\033[94m',
    'fg_pink': '\033[95m',
    'fg_light_cyan': '\033[96m',
    # background colors
    'bg_black': '\033[40m',
    'bg_red': '\033[41m',
    'bg_green': '\033[42m',
    'bg_orange': '\033[43m',
    'bg_blue': '\033[44m',
    'bg_purple': '\033[45m',
    'bg_cyan': '\033[46m',
    'bg_light_grey': '\033[47m'
    }


class ColorScheme:
    def __init__(self, frozen, information, command, alert):
        self.frozen = frozen
        self.information = information
        self.command = command
        self.alert = alert

def color(text, lst_styles):
    color_text = ''
    for style in lst_styles:
        try:
            color_text += styles[style]
        except KeyError:
            raise KeyError('def color: parameter `{}` does not exist'.format(style))
     
    color_text += text
    return '\033[0m{}\033[0m'.format(color_text)


def highlight_text(string, keyword, hl):
    def split_keep(string, delim):
        lst_chunks = []
        ongoing_string = ''

        if delim in string:
            
            #print(string.split(delim))
            
            for f in string.split(delim)[:-1]:
                lst_chunks.append(f)
                lst_chunks.append(delim)

            lst_chunks.append(string.split(delim)[-1])

            return lst_chunks


        else:

            for word in string.split():
                if delim.lower() in word.lower():
                    lst_chunks.append(ongoing_string)
                    lst_chunks.append(word) 
                    ongoing_string = ' '
                else:
                    ongoing_string += word + ' '
            if ongoing_string:
                lst_chunks.append(ongoing_string)

            lst_chunks[-1] = lst_chunks[-1].rstrip()
            return lst_chunks

    ###########################

    
    fields = split_keep(string, keyword)
    found_hl = False
    fmt_str = ''
    for f in fields:
        
        if keyword.strip().lower() in f.strip().lower():
            fmt_str += hl.get_fmt_word(f)
            found_hl = True
        else:
            fmt_str += hl.get_fmt_text(f)

    return (found_hl, fmt_str)

class Highlight:
    def __init__(self, fmt_text=[], fmt_word=[]):
        self.fmt_text = fmt_text
        self.fmt_word = fmt_word

    def get_fmt_text(self, string):
        return color(string, self.fmt_text)

    def get_fmt_word(self, string):
        return color(string, self.fmt_word)

    def valid(self):
        for fmt in self.fmt_text + self.fmt_word:
            if fmt not in styles:
                return None
        return self

    def __str__(self):
        return '{} {}'.format(self.fmt_text, self.fmt_word)

def parse_highlight(string=None, string_fmt_text=None, string_fmt_word=None):
    def str_to_list(string):
        string = ''.join(string.split())
        fmt = string.replace('[', '').replace("'", '').replace(']', '').split(',')
        if fmt:
            return fmt
        else:
            return []

    ###########################
    if string and not string_fmt_text and not string_fmt_word:
        f = string.split()
        keyword = f[0]
        string_fmt = ''.join(f[1:])
        string_fmt_text = string_fmt.split('[')[1].replace(']', '')
        string_fmt_word = string_fmt.split('[')[2].replace(']', '')
    elif not string and string_fmt_text or string_fmt_word:
        pass
    else:
        print('ERROR invalid format')

    lst_fmt_text = []
    lst_fmt_word = []
    if string_fmt_text:
        lst_fmt_text = str_to_list(string_fmt_text)

    if string_fmt_word:
        lst_fmt_word = str_to_list(string_fmt_word)

    return Highlight(lst_fmt_text, lst_fmt_word).valid()

dct_default_keywords = {
    'sensor' : Highlight(['fg_black'], ['fg_pink', 'bold']),
    'arm' : Highlight([], ['fg_green', 'bold']),
    'mcu' : Highlight(['fg_pink'], ['fg_cyan'])}

color_scheme_default = ColorScheme( 
    frozen=Highlight(fmt_text=['fg_light_blue']),
    information=Highlight(fmt_text=['fg_yellow', 'bold']),
    command=Highlight(fmt_text=['fg_cyan', 'bold', 'underline']),
    alert=Highlight(fmt_text=['fg_light_red', 'bold', 'underline']))
