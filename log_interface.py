import log_color as lc

def formatted_menu(str):
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


class UserInterface:
    def __init__(self, color_scheme, lst_cmd, dct_hl, newline):
        self.color_scheme = color_scheme
        self.lst_cmd = lst_cmd
        self.dct_hl = dct_hl
        self.newline = newline

    def get_info(self, str):
        return lc.color(str, self.color_scheme.information.fmt_text)

    def get_cmd(self, str):
        return lc.color(str, self.color_scheme.command.fmt_text)

    def get_frozen(self, str):
        return lc.color(str, self.color_scheme.frozen.fmt_text)

    def get_alert(self, str):
        return lc.color(str, self.color_scheme.alert.fmt_text)

    def print_info(self, str, endl=None):
        if not endl:
            endl = self.newline
        print(self.get_info(str), end=endl)

    def print_cmd(self, str):
        print(self.get_cmd(str), end=self.newline)

    def print_frozen(self, str):
        print(self.get_frozen(str), end=self.newline)

    def print_alert(self, str, endl=None):
        if not endl:
            endl = self.newline
        print(self.get_alert(str), end=endl)

    def print_help(self):
        menu_top, menu_buttom = formatted_menu('Help')
        self.print_info(menu_top)
        for ucmd in self.lst_cmd:
            self.print_info(str(ucmd))
        self.print_info(menu_buttom)

    def banana(self):
        print(lc.color('BANANA!!', ['fg_yellow']), end=self.newline)
        print(lc.color(" _ \n//\\ \nV  \\ \n \\  \\_ \n  \\,'.`-. \n   |\\ `. `. \n   ( \\  `. `-.                        _,.-/\\ \n    \\ \\   `.  `-._             __..--' ,-'\\/ \n     \\ `.   `-.   `-..___..---'   _.--' ,'/ \n      `. `.    `-._        __..--'    ,' / \n        `. `-_     ``--..''       _.-' ,' \n          `-_ `-.___        __,--'   ,' \n             `-.__  `----\"\"\"    __.-' \nhh                `--..____..--'\n", ['fg_yellow', 'bold']), end=self.newline)

    def list_highlight(self):
        menu_top, menu_buttom = formatted_menu('Highlights')
        self.print_info(menu_top)
        for keyword, hl in self.dct_hl.items():
            self.print_info('Keyword: {}'.format(keyword))
            print(self.get_info('    format text:     ') + hl.get_fmt_text(str(hl.fmt_text)), end=self.newline)
            print(self.get_info('    format keyword:  ') + hl.get_fmt_word(str(hl.fmt_word)), end=self.newline)
        self.print_info(menu_buttom)

    def print_marker(self):
        self.print_cmd('='*75)

class UserCommands:
    def __init__(self, keycmd, str_keycmd, desc, callback=None):
        self.keycmd = keycmd
        self.str_keycmd = str_keycmd
        self.desc = desc
        self.callback = callback

    def __str__(self):
        return '< {} >   - {}'.format(self.str_keycmd, self.desc)