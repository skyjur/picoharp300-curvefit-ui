import unittest
import picoharp
import picoharp_backend


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
    def test_iter_data(self):
        y1 = [1, 2, 3, 4, 5]
        y2 = [11, 22, 33, 44, 55]
        r = 0.16

        shift = 0
        d = picoharp_backend.iter_data(r, y1, y2, shift)
        d = ['%.2f %d %d' % i for i in d]
        self.assertEqual(d, [
            '0.16 1 11',
            '0.32 2 22',
            '0.48 3 33',
            '0.64 4 44',
            '0.80 5 55',
        ])

        shift = 0.32
        d = picoharp_backend.iter_data(r, y1, y2, shift)
        d = ['%.2f %d %d' % i for i in d]
        self.assertEqual(d, [
            '0.16 1 0',
            '0.32 2 0',
            '0.48 3 11',
            '0.64 4 22',
            '0.80 5 33',
        ])

        shift = -0.32
        d = picoharp_backend.iter_data(r, y1, y2, shift)
        d = ['%.2f %d %d' % i for i in d]
        self.assertEqual(d, [
            '0.16 1 33',
            '0.32 2 44',
            '0.48 3 55',
            '0.64 4 0',
            '0.80 5 0',
        ])


if __name__ == '__main__':
    unittest.main()
