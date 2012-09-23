"""
An example of how to use pylab to manage your figure windows, but
modify the GUI by accessing the underlying gtk widgets
"""
import matplotlib
matplotlib.use('module://picoharp_backend')
from picoharp_backend import new_figure_manager
import gtk

manager = new_figure_manager(0)
manager.window.show()
manager.window.connect("destroy", gtk.main_quit)
manager.load_data_file('test-input.phd')
gtk.main()
