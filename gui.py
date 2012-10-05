"""
An example of how to use pylab to manage your figure windows, but
modify the GUI by accessing the underlying gtk widgets
"""
import os
import re
import itertools
import subprocess
import tempfile

import numpy
import gobject
import gtk

from matplotlib.figure import Figure
from matplotlib.backends import backend_gtkagg

from picoharp import PicoharpParser


FigureCanvas = backend_gtkagg.FigureCanvasGTKAgg


def getfloat(value):
    try:
        return float(re.findall('-?[0-9.]+', value)[0])
    except IndexError:
        return 0.0


class Sidebar(object):
    def __init__(self, manager):
        builder = self.builder = gtk.Builder()
        builder.add_from_file('sidebar.glade')
        builder.connect_signals(self)
        self.widget = builder.get_object('toplevel')
        self.manager = manager
        
    def __getitem__(self, key):
        item = self.builder.get_object(key)
        if not item:
            raise KeyError('Object does not exist: %s' % key)
        return item

    def build_kwargs(self):
        kwargs = {
            'model': self['model'].get_active_text()
        }

        for k in ['timestart', 'timeend', 'tau', 'izero', 'tau2', 'izero2',
                  'tau3', 'izero3']:
            if not self[k].get_sensitive():
                continue

            v = self[k].get_text()
            if v.strip():
                kwargs[k] = str(getfloat(v))

        return kwargs

    def on_fitbtn_clicked(self, btn):
        data = self.manager.export_to_tempfile()
        fit = Fit(self.manager, data=data, **self.build_kwargs())
        fit_data, comments = fit.run()
        self['results'].get_buffer().set_text(comments)
        if fit_data:
            self.manager.plot_fit_data(fit_data)

    def on_clear_clicked(self, btn):
        self.manager.clear_fit()
        self['results'].get_buffer().set_text('')

    def on_timestartfill_clicked(self, btn):
        a, b = self.manager.ax.get_xlim()
        self['timestart'].set_text(str(a))

    def on_timeendfill_clicked(self, btn):
        a, b = self.manager.ax.get_xlim()
        self['timeend'].set_text(str(b))

    def on_modelinput_changed(self, combobox):
        exp = combobox.get_active_text()
        exp = {'exp1': 1, 'exp2': 2, 'exp3': 3}[exp]
        self['tau2'].set_sensitive(exp >= 2)
        self['izero2'].set_sensitive(exp >= 2)
        self['tau3'].set_sensitive(exp >= 3)
        self['izero3'].set_sensitive(exp >= 3)

    def on_irfshiftbtn_clicked(self, btn):
        value = getfloat(self['irfshift'].get_text())
        value = self.manager.irf_shift(value)
        self['irfshift'].set_text('%.5f' % value)

    def on_resultsfill_clicked(self, btn):
        buff = self['results'].get_buffer()
        start = buff.get_start_iter()
        end = buff.get_end_iter()
        text = buff.get_text(start, end)
        for line in text.splitlines():
            args = line.split()
            if len(args) != 2:
                continue
            obj = self.builder.get_object(args[0])
            if not obj:
                continue
            if args[0] == 'model':
                continue
            obj.set_text(args[1])


class Menu(gtk.MenuBar):
    def __init__(self, manager):
        gtk.MenuBar.__init__(self)
        self.show()

        self.manager = manager

        fileitem = gtk.MenuItem('File')
        self.append(fileitem)
        fileitem.show()

        filemenu = gtk.Menu()
        fileitem.set_submenu(filemenu)
        filemenu.show()

        openitem = gtk.MenuItem('Open...')
        filemenu.append(openitem)
        openitem.connect('activate', self.on_file_open)
        openitem.show()

    def on_file_open(self, btn):
        dialog = gtk.FileChooserDialog('Open...', None,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
             gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        )
        dialog.set_default_response(gtk.RESPONSE_OK)

        fltr = gtk.FileFilter()
        fltr.set_name('PicoHarp 300 (*.phd)')
        fltr.add_pattern('*.phd')

        dialog.add_filter(fltr)
        resp = dialog.run()

        if resp == gtk.RESPONSE_OK:
            f = dialog.get_filename()
            dialog.destroy()
            print f, 'selected'
            self.manager.load_data_file(f)
        elif resp == gtk.RESPONSE_CANCEL:
            dialog.destroy()
            print 'Closed, no files selected'


class Fit(object):
    def __init__(self, manager, data, model, **kwargs):
        self.manager = manager
        self.data = data
        self.model = model
        self.kwargs = kwargs

    def run(self):
        self.dialog = gtk.MessageDialog(self.manager.window,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_INFO,
            gtk.BUTTONS_CANCEL,
            message_format='Please wait...') 

        box = self.dialog.get_children()[-1]
        bar = self.bar = gtk.ProgressBar()
        bar.show()
        box.add(bar)

        self.sub = self.start_sub_process()
        self.start_loop()
        self.dialog.run()
        self.destroy()

        return self.get_results()
    
    def start_sub_process(self):
        args = ['trfit', 
                'data=%s' % self.data,
                'mode=fit,dump',
                'model=%s' % self.model]

        for k, v in self.kwargs.items():
            args.append('='.join((k, v)))

        #args = ['sh', '-c', ' '.join(['echo '] + args)]

        self.p = subprocess.Popen(args, 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)

    def start_loop(self):
        self._stop_loop = False
        gobject.timeout_add(100, self._loop)

    def stop_loop(self):
        self._stop_loop = True

    def _loop(self):
        if self._stop_loop:
            return False
        self.loop()
        return True

    def loop(self):
        self.bar.pulse()
        r = self.p.poll()
        if r != None:
            self.destroy()

    def destroy(self):
        self.stop_loop()
        self.dialog.destroy()
        if self.p.poll() == None:
            try:
                self.p.kill()
            except OSError:
                pass

    def get_results(self):
        results = self.p.stdout.readlines()
        for line in results:
            if 'wrote ' in line:
                f = line.strip().split('wrote ')[1]
                return self._get_dumped_results(f)
        return None, '\n'.join(results)

    def _get_dumped_results(self, f):
        f = open(f, 'r')
        comments = []
        x = []
        y1 = []
        y2 = []

        for line in f:
            line = line.strip()
            if line.startswith('#'):
                comments.append(line.strip().strip('#').strip())
                continue
            line = line.split()
            if len(line) == 0:
                continue
            x.append(float(line[0]))
            y1.append(float(line[2])) # fit
            y2.append(float(line[3])) # residuals

        x = numpy.array(x)
        y1 = numpy.array(y1)
        y2 = numpy.array(y2)

        return (x,y1,y2), '\n'.join(comments[1:-1])


def iter_data(resolution, decay, irf, irfshift=0.0):
    shift = int(round(irfshift / resolution))
    zeroes = [0] * abs(shift)

    t = resolution

    if shift > 0:
        irf = itertools.chain(zeroes, irf[:-shift])
    elif shift < 0:
        irf = itertools.chain(irf[shift-1:], zeroes)

    for a, b in itertools.izip(decay, irf):
        yield t, a, b
        t += resolution


class Manager(backend_gtkagg.FigureManagerGTKAgg):
    def __init__(self, canvas, num):
        backend_gtkagg.FigureManagerGTKAgg.__init__(self, canvas, num)
        self.window.maximize()

        self.vbox.remove(self.canvas)

        self.menu = Menu(self)
        self.vbox.pack_start(self.menu, False, True)

        self.vbox1 = gtk.VBox()
        self.vbox1.pack_start(self.canvas, True, True)
        self.vbox1.show()

        self.vpane = gtk.HBox()
        self.vbox.pack_start(self.vpane, True, True)

        self.vpane.pack_start(self.vbox1, True, True)
        self.vpane.show()

        self.sidebar = Sidebar(self)
        self.sidebar.widget.show()
        self.vpane.pack_end(self.sidebar.widget, False, True)

        self.ax = self.canvas.figure.add_subplot(1, 1, 1)
        #self.residuals = self.canvas.figure.add_subplot(2, 10, 2)

        self.reset_margins()

    def load_data_file(self, filename):
        for line in self.ax.lines:
            line.remove()

        data = PicoharpParser(filename)
        res, curve1 = data.get_curve(0)
        res, curve2 = data.get_curve(1)
        size = len(curve1)
        X = numpy.arange(0, size*res, res, numpy.float)
        self.resolution = res

        for i, v in enumerate(reversed(curve1)):
            if v > 0:
                break

        curve1 = curve1[:-i]
        curve2 = curve2[:-i]
        X = X[:-i]

        self.decay = self.ax.plot(X, curve1, 'r.')[0]
        self.irf = self.ax.plot(X, curve2, 'b.')[0]
        self.fit = None

        self.ax.set_yscale('log')

        self.canvas.draw()

        self.window.set_title(filename)

    def reset_margins(self):
        w, h = self.window.get_size()
        top = 1 - 5.0/h
        right = 1 - 5.0/h
        bottom = 15.0/h
        left = 15.0/h
        self.canvas.figure.subplots_adjust(
            top=top, right=right, bottom=bottom, left=left)
        self.canvas.draw()

        #self.vpane.set_position(w * 0.8)

    def reset_shift(self, draw=False):
        for curve in (self.decay, self.irf):
            if getattr(curve, '_shift', 0) != 0:
                curve.set_xdata(curve.get_xdata() - curve._shift)
                curve._shift = 0

    def irf_shift(self, value):
        self.reset_shift()
        value = round(value / self.resolution) * self.resolution

        if value > 0:
            curve = self.decay
            curve._shift = value
        else:
            curve = self.irf
            curve._shift = - value

        curve.set_xdata(curve.get_xdata() + curve._shift)
        self.canvas.draw()

        return value

    def iter_data(self):
        shift = getattr(self.decay, '_shift', 0.0)
        decay = self.decay.get_ydata()
        irf = self.irf.get_ydata()
        return iter_data(self.resolution, decay, irf, shift)

    def export_to_tempfile(self):
        f, filename = tempfile.mkstemp()
        
        for t, a, b in self.iter_data():
            os.write(f, '%f,%d,%d\n' % (t, b, a))

        os.close(f)

        return filename

    def plot_fit_data(self, data):
        self.clear_fit()

        x, y1, y2 = data

        maxy = max((max(y1), max(y2)))
        miny = min((min(y1), min(y2)))
        maxx = max(x)
        minx = min(x)

        self.ax.set_xlim((minx, maxx))
        self.ax.set_ylim((miny, maxy))

        self.fit = self.ax.plot(x, y1, 'g-', x, y2, 'c-')
        self.canvas.draw()

    def clear_fit(self):
        if self.fit:
            for line in self.fit:
                self.ax.lines.remove(line)
            self.fit = None
        self.canvas.draw()


def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)
    canvas = FigureCanvas(thisFig)
    return Manager(canvas, num)


def main():
    manager = new_figure_manager(0)
    manager.window.show()
    manager.window.connect("destroy", gtk.main_quit)
    manager.load_data_file('test-input.phd')
    gtk.main()


if __name__ == '__main__':
    main()
