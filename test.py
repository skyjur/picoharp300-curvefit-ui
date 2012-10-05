import itertools
import unittest
import picoharp
from gui import new_figure_manager


_test_info = """Ident            : PicoHarp 300
Format Version   : 2.0
Creator Name     : PicoHarp Software
Creator Version  : 2.1.0.0
Time of Creation : 21/11/11 02:03:55
File Comment     : Untitled
No of Curves     : 2
Bits per HistoBin: 32
RoutingChannels  : 1
No of Boards     : 1
Active Curve     : 0
Measurement Mode : 0
Sub-Mode         : 1
Range No         : 2
Offset           : 0
AcquisitionTime  : 100000
Stop at          : 10000
Stop on Ovfl.    : 1
Restart          : 0
DispLinLog       : 1
DispTimeAxisFrom : 25
DispTimeAxisTo   : 90
DispCountAxisFrom: 1
DispCountAxisTo  : 36400
---------------------
Curve No 0
 MapTo           : 0
 Show            : true
---------------------
---------------------
Curve No 1
 MapTo           : 1
 Show            : true
---------------------
---------------------
Curve No 2
 MapTo           : 2
 Show            : true
---------------------
---------------------
Curve No 3
 MapTo           : 3
 Show            : true
---------------------
---------------------
Curve No 4
 MapTo           : 4
 Show            : true
---------------------
---------------------
Curve No 5
 MapTo           : 5
 Show            : true
---------------------
---------------------
Curve No 6
 MapTo           : 6
 Show            : true
---------------------
---------------------
Curve No 7
 MapTo           : 7
 Show            : true
---------------------
---------------------
Parameter No 0
 Start           : 0.000000
 Step            : 0.000000
 End             : 0.000000
---------------------
---------------------
Parameter No 1
 Start           : 0.000000
 Step            : 0.000000
 End             : 0.000000
---------------------
---------------------
Parameter No 2
 Start           : 0.000000
 Step            : 0.000000
 End             : 0.000000
---------------------
Repeat Mode      : 0
Repeats per Curve: 1
Repeat Time      : 0
Repeat wait Time : 0
Script Name      : Interactive Mode
---------------------
Board No 0
 HardwareIdent   : 
 HardwareVersion : 
 HardwareSerial  : 0
 SyncDivider     : 8
 CFDZeroCross0   : 10
 CFDLevel0       : 150
 CFDZeroCross1   : 6
 CFDLevel1       : 40
 Resolution      : 0.016000
---------------------
---------------------
Curve Index       : 0
Time of Recording : Fri Nov 04 14:37:27 2011
HardwareIdent     : PicoHarp 300
HardwareVersion   : 2.0
HardwareSerial    : 1006414
SyncDivider       : 8
CFDZeroCross0     : 10
CFDLevel0         : 150
CFDZeroCross1     : 6
CFDLevel1         : 40
Offset            : 0
RoutingChannel    : 0
ExtDevices        : 0
Meas. Mode        : 0
Sub-Mode          : 1
Par. 1            : 0.000000
Par. 2            : 0.000000
Par. 3            : 0.000000
Range No          : 2
Resolution        : 0.016000
Channels          : 65536
Acq. Time         : 10000000
Stop after        : 10696
Stop Reason       : 2
InpRate0          : 2000080
InpRate1          : 42580
HistCountRate     : 42119
IntegralCount     : 450506
reserved          : 0
dataoffset        : 1036
---------------------
Curve Index       : 1
Time of Recording : Fri Nov 04 14:19:17 2011
HardwareIdent     : PicoHarp 300
HardwareVersion   : 2.0
HardwareSerial    : 1006414
SyncDivider       : 8
CFDZeroCross0     : 10
CFDLevel0         : 150
CFDZeroCross1     : 6
CFDLevel1         : 40
Offset            : 0
RoutingChannel    : 0
ExtDevices        : 0
Meas. Mode        : 0
Sub-Mode          : 1
Par. 1            : 0.000000
Par. 2            : 0.000000
Par. 3            : 0.000000
Range No          : 2
Resolution        : 0.016000
Channels          : 65536
Acq. Time         : 10000000
Stop after        : 36179
Stop Reason       : 2
InpRate0          : 2000080
InpRate1          : 35470
HistCountRate     : 36399
IntegralCount     : 1316890
reserved          : 0
dataoffset        : 263180
---------------------"""


class PicoTest(unittest.TestCase):
    def setUp(self):
        self.f = picoharp.PicoharpParser('test-input.phd')

    def test_no_of_curves(self):
        self.assertEqual(self.f.no_of_curves(), 2)

    def test_info(self):
        info1 = self.f.info()
        info1 = info1.splitlines()
        info2 = _test_info.splitlines()
        for i in range(max((len(info1), len(info2)))):
            self.assertEqual(info1[i-3:i], info2[i-3:i])

    def test_curves_data(self):
        res, curve = self.f.get_curve(0)
        b = [0, 0, 0, 0, 0, 1, 2, 0, 0, 2, 0, 0, 3]
        a = list(curve[:len(b)])
        self.assertEqual(a, b)

        res, curve = self.f.get_curve(1)
        b = [0, 2, 3, 1, 3, 2, 2, 1, 2, 3, 2, 2, 2, 2, 2, 2, 0, 0, 0]
        a = list(curve[:len(b)])
        self.assertEqual(a, b)



class BackendTestCase(unittest.TestCase):
    def setUp(self):
        self.manager = new_figure_manager(0)
        self.manager.load_data_file('test-input.phd')

    def _slice(self, data, start, stop):
        d = itertools.islice(data, 0, 10)
        return ['%.3f %d %d' % args for args in d]

    def test_shifting(self):
        data1 = self._slice(self.manager.iter_data(), 0, 15)
        self.assertEqual(data1, [
            '0.016 0 0',
            '0.032 2 0',
            '0.048 3 0',
            '0.064 1 0',
            '0.080 3 0',
            '0.096 2 1',
            '0.112 2 2',
            '0.128 1 0',
            '0.144 2 0',
            '0.160 3 2',
        ])

        self.manager.irf_shift(0.032)
        data = self._slice(self.manager.iter_data(), 0, 15)
        self.assertEqual(data, data1)
        #self.assertEqual(data, [
        #    '0.016 0 0',
        #    '0.032 2 0',
        #    '0.048 3 0',
        #    '0.064 1 0',
        #    '0.080 3 0',
        #    '0.096 2 0',
        #    '0.112 2 0',
        #    '0.128 1 1',
        #    '0.144 2 2',
        #    '0.160 3 0',
        #])

        self.manager.irf_shift(-0.032)
        data = self._slice(self.manager.iter_data(), 0, 15)
        self.assertEqual(data, data1)
        #self.assertEqual(data, [
        #    '0.016 0 0',
        #    '0.032 0 0',
        #    '0.048 0 0',
        #    '0.064 2 0',
        #    '0.080 3 0',
        #    '0.096 1 1',
        #    '0.112 3 2',
        #    '0.128 2 0',
        #    '0.144 2 0',
        #    '0.160 1 2',
        #])



if __name__ == '__main__':
    unittest.main()
