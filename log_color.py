def color(text, lst_styles):

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
        'fg_orange': '\033[33m',
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

    color_text = ''
    for style in lst_styles:
        try:
            color_text += styles[style]
        except KeyError:
            raise KeyError('def color: parameter `{}` does not exist'.format(style))
     

    color_text += text
    return '\033[0m{}\033[0m'.format(color_text)

def split_keep(str, delim):
    lst_chunks = []
    ongoing_str = ''

    for word in str.split():
        if delim.lower() in word.lower():
            lst_chunks.append(ongoing_str)
            lst_chunks.append(word) 
            ongoing_str = ' '
        else:
            ongoing_str += word + ' '
    if ongoing_str:
        lst_chunks.append(ongoing_str)


    lst_chunks[-1] = lst_chunks[-1].rstrip()
    return lst_chunks



def highlight_text(str, fmt, hl_str, hl_fmt=['bold']):
    fields = split_keep(str, hl_str)
    #print(fields)
    found_hl = False
    fmt_str = ''
    for f in fields:
        
        if hl_str.strip().lower() in f.strip().lower():
            fmt_str += color(f, hl_fmt)
            found_hl = True
        else:
            fmt_str += color(f, fmt)

    return (found_hl, fmt_str)





   


#X = highlight_text('hej jag heter jonas', ['fg_blue'], 'hej', ['fg_purple', 'bold'])
#print(X)
#print('hej')