import picoharp
import sys


def main():
    if len(sys.argv) != 4:
        print 'Usage: %s <*.phd> <first_frame> <last_frame>' % __file__
        sys.exit(1)

    _, datafile, start, stop = sys.argv
    start, stop = int(start), int(stop)

    parser = picoharp.PicoharpParser(datafile)
    name, ext = datafile.rsplit('.', 1)

    res, curve1 = parser.get_curve(0)
    res, curve2 = parser.get_curve(1)

    stop = stop or len(curve1)

    curve1 = curve1[start:stop]
    curve2 = curve2[start:stop]

    csvname = '%s.csv' % name
    csv = open(csvname, 'w')

    for j, (a, b) in enumerate(zip(curve1, curve2)):
        csv.write('%d,%d,%d\n' % (j, a, b))

    csv.close()

    print 'Saved %s.' % csvname


if __name__ == '__main__':
    main()
