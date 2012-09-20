# encoding: utf-8
import subprocess
import gtk
import gobject
import IPython
import sys
import picoharp
import matplotlib.pyplot as plt
import numpy


fig = plt.figure()
ax = fig.add_subplot(1,1,1)
manager = plt.get_current_fig_manager()


class Main(object):
    def __init__(self, fig, ax):
        self.fig = fig
        self.ax = ax

    def clear(self):
        lines = self.ax.lines
        if lines:
            [l.remove() for l in lines]
            self.fig.canvas.draw()

    def has_data(self):
        return len(self.ax.lines) >= 2

    def load_phd(self, filename):
        self.clear()
        data = picoharp.PicoharpParser(filename)
        res, curve1 = data.get_curve(0)
        res, curve2 = data.get_curve(1)
        size = len(curve1)
        X = numpy.arange(0, size*res, res, numpy.float)
        self.ax.plot(X, curve1, 'r.', X, curve2, 'b.')
        self.ax.set_yscale('log')
        self.fig.canvas.draw()


class FitRun(object):
    def __init__(self):
        #self.dialog = gtk.Dialog('Fitting...', 
        #    manager.window,
        #    gtk.DIALOG_MODAL,
        #    ('Abort', gtk.RESPONSE_DELETE_EVENT),
        #)
        self.dialog = gtk.MessageDialog(manager.window,
            gtk.DIALOG_MODAL,
            gtk.MESSAGE_INFO,
            gtk.BUTTONS_CANCEL,
            message_format='2, 4, 256, next?') 
        self.start_loop()

        box = self.dialog.children()[-1]
        bar = self.bar = gtk.ProgressBar()
        bar.show()
        box.add(bar)

        self.sub = self.start_sub_process()
        self.dialog.run()
        self.destroy()
    
    def start_sub_process(self):
        args = ['sleep', '10']
        #args = ['sh', '-c', 'trfit data=test-input.csv mode=fit'
        #                    ' timestart=25 model=exp1 timeend=55']
        self.p = subprocess.Popen(args, 
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)

    def start_loop(self):
        self._stop_loop = False
        gobject.timeout_add(50, self._loop)

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

    def show_result(self):
        pass

    def destroy(self):
        self.stop_loop()
        self.dialog.destroy()
        if self.p.poll() == None:
            try:
                self.p.kill()
            except OSError:
                pass
        else:
            self.show_result()


FitRun()


class FitDialog(object):
    _inputs = [
        'model',
        'timestart',
        'timeend',
        'tau1',
        'izero1',
        'tau2',
        'izero2',
        'tau3',
        'izero3',
    ]

    def __init__(self, parent):
        self.parent = parent
        builder = self.builder = gtk.Builder()
        builder.add_from_file('fit.glade')
        builder.connect_signals(self)
        self.dialog = builder.get_object('dialog')
        for key in self._inputs:
            widget = builder.get_object('%sinput' % key)
            assert widget, 'No widget: %s' % key
            setattr(self, key, widget)
        self.close = self.builder.get_object('close')
        self.dialog.show()

    def on_dialog_close(self, *args):
        pass

    def on_dialog_response(self, dialog, code):
        if code == gtk.RESPONSE_DELETE_EVENT:
            self.dialog.destroy()
            self.parent.on_fitdialog_close(self)

    def get_values(self):
        d = {}
        for key in self._inputs:
            widget = getattr(self, key)
            if hasattr(self, 'get_%s_value' % key):
                value = getattr(self, 'get_%s_value' % key)(widget)
            else:
                value = widget.get_text()
            d[key] = value
        return d

    def get_model_value(self, widget):
        return widget.get_active_text()

    def set_values(self, values):
        for key, value in values.items():
            widget = getattr(self, key)
            if hasattr(self, 'set_%s_value' % key):
                getattr(self, 'set_%s_value' % key)(widget, value)
            else:
                widget.set_text(value)

    def set_model_value(self, widget, value):
        pass

    def on_fit_clicked(self, btn):
        FitRun()

    def on_close_clicked(self, btn):
        self.dialog.response(gtk.RESPONSE_DELETE_EVENT)


class ToolbarButtons(object):
    def __init__(self, main):
        self.main = main
        self.fit_dialog = None

        open_btn = self.open_btn = gtk.ToolButton(label='Open')
        open_btn.connect('clicked', self.on_open_clicked)
        open_btn.show()

        fit_btn = self.fit_btn = gtk.ToolButton(label='Fit')
        fit_btn.connect('clicked', self.on_fit_clicked)
        fit_btn.set_sensitive(False)
        fit_btn.show()

    def add_on(self, container):
        container.add(self.open_btn)
        container.add(self.fit_btn)

    def on_fit_clicked(self, btn):
        if not self.fit_dialog:
            self.fit_dialog = FitDialog(self)
            self.disable()

    def on_fitdialog_close(self, dialog):
        self.enable()
        self.dialog = None

    def on_open_ok(self, filename):
        try:
            self.main.load_phd(filename)
            self.enable()
        except Exception, e:
            msg = gtk.MessageDialog(manager.window,
                gtk.DIALOG_MODAL,
                gtk.MESSAGE_ERROR,
                gtk.BUTTONS_CLOSE,
                message_format=unicode(e)
            )
            msg.run()
            msg.destroy()

    def disable(self):
        self.open_btn.set_sensitive(False)
        self.fit_btn.set_sensitive(False)

    def enable(self):
        self.open_btn.set_sensitive(True)
        if not self.main.has_data():
            self.fit_btn.set_sensitive(False)
        else:
            self.fit_btn.set_sensitive(True)

    def on_open_clicked(self, btn):
        self.disable()

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
            self.on_open_ok(f)
        elif resp == gtk.RESPONSE_CANCEL:
            dialog.destroy()
            print 'Closed, no files selected'

        self.enable()



main = Main(fig, ax)
buttons = ToolbarButtons(main)
buttons.add_on(manager.toolbar)


plt.show()
