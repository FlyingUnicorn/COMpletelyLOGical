


class Kpi:
    def __init__(self, ui):

        self.ui = ui


        self.dct_kpis = {}
        self.lst_kpis = ['KPI.finger_down:', 'KPI.tuning:', 'KPI.read_image:', 'KPI.total_capture:', 'KPI.wait_host:', 'KPI.transfer:', 'KPI.total:']
    
        for kpi in self.lst_kpis:
            self.dct_kpis[kpi] = []


    def handle_kpi(self, line):
    
    #for line in codecs.open(path_log,'r','utf-8'):
        #print(line)
        for str_kpi in self.dct_kpis:
            if str_kpi in line:
                #print(line)
                try:
                    self.dct_kpis[str_kpi].append(int(line.split(str_kpi)[-1].split()[-1]))
                except IndexError:
                    self.ui.print_error('Error line: {}'.format(line))

                if len(self.dct_kpis[self.lst_kpis[-1]]) % 5 == 0 and str_kpi == self.lst_kpis[-1]:
                    self.print_stats()

    def print_stats(self):
        self.ui.print_info('KPI results (touches: {}'.format(len(self.dct_kpis[self.lst_kpis[0]])))
        for kpi in self.lst_kpis:
            lst = self.dct_kpis[kpi]
            if lst:
                #print(lst)
                self.ui.print_info('{:20} {:10.2f}     max: {:4}'.format(kpi, sum(lst)/len(lst), max(lst)))
            else:
                self.ui.print_info('{}> Nothing'.format(kpi))