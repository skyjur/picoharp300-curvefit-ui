import picoharp
import numpy
import sys


def main():
    if len(sys.argv) != 2:
        print 'Usage: %s <*.phd>' % __file__
        sys.exit(1)

    _, datafile = sys.argv

    parser = picoharp.PicoharpParser(datafile)
    name, ext = datafile.rsplit('.', 1)

    res, curve1 = parser.get_curve(0)
    res, curve2 = parser.get_curve(1)
    size = len(curve1)
    X = numpy.arange(0, size*res, res, numpy.float)

    csvname = '%s.csv' % name
    csv = open(csvname, 'w')

    for x, y1, y2 in zip(X, curve1, curve2):
        csv.write('%f,%d,%d\n' % (x, y1, y2))

    csv.close()

    print 'Saved %s.' % csvname


if __name__ == '__main__':
    main()
