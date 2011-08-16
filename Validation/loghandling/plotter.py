#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2006-2010 Tampere University of Technology
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""
Plotter - draws plots using gnuplot.

Input: gnuplot datafile(s) created by 'tema logreader --gnuplot'
Output: command that draws a plot when given to gnuplot (via stdin)

Examples:

Help:
tema plotter -h

View default (-y=awcov, -x=kw ) graph from gnuplot file my.plotdat:
tema plotter my.plotdat | gnuplot -persist

View default graph from data received via stdin from logreader:
tema logreader --gnuplot my.log | tema plotter | gnuplot -persist

View a graph showing unique states (uniqstates) as a function of time (t):
tema plotter -y uniqstates -x t

Create a png: (term can be any gnuplot term)
tema plotter my.plotdat --term=png | gnuplot > my.png

List of possible -y and -x values:
tema plotter --listcols

"""

import sys
import re
from optparse import Option, OptionParser, OptionValueError
from copy import copy

_COL_NAMES = {
    "s": "Time (Seconds)",
    "kw": "Keywords Executed",
    "aw": "Action Words Executed",
    "awcov": "Action Word Coverage",
    "switches": "Application Switches",
    "uniqswitches": "Unique Application Switches",
    "states": "States",
    "uniqstates": "Unique States",
    "transitions": "Transitions",
    "uniqtransitions": "Unique Transitions",
    "comptransitions": "Transitions of model components",
    "uniqcomptransitions": "Unique transitions of model components",
    "appcovstddev": "Std deviation of AW-coverages of Applications",
    "leastcoveredapp": "The AW-coverage of The Least Covered Application",
    "awcov(APPNAME)": "The AW-coverage of the given APPNAME",
    "asp": "Action word-State Proposition Pairs Found",
}

_AWCOW_APP = re.compile("awcov\(([^)]*)\)")
_COMPTRANS = re.compile("comptrans\(([^)]*)\)")
def colName(colType):
    if _AWCOW_APP.match(colType):
        return "AW-Coverage of application '%s'"  % (
            _AWCOW_APP.match(colType).groups()[0], )
    elif _COMPTRANS.match(colType):
        return "Transitions of component %s executed"  % (
            _COMPTRANS.match(colType).groups()[0], )
    else:
        return _COL_NAMES[colType]

def validCol(colType):
    try:
        colName(colType)
        return True
    except:
        return False


def _opDiv(a, b):
    try:
        return float(a) / float(b)
    except:
        return 'NaN'
def _opPlus(*items):
    return sum([float(i) for i in items])
def _opMinus(a,b):
    return float(a) - float(b)

def _axisTitle(cols,separator=None):
    if not cols:
        return ""
    elif len(cols)==1:
        return colName(cols[0])
    elif separator:
        return (" %s "%separator).join([colName(c) for c in cols])
    assert False



def readSysArgs(argv):

    def checkOneCol(option,opt,value):
        if not validCol(value):
            raise OptionValueError(
                "'%s' is not a proper column name.\n"\
                "Give --listcols for a list of column names.\n"%(value,))
        return (value,), lambda x:x, colName(value)

    def createCheckColsSeparatedBy(separator,opFunc):
        errStr = "Invalid arg '%%s', should be COL%sCOL" % (separator,)
        def checkColsSeparatedBy(option,opt,value):
            cols = value.split(separator)
            for c in cols:
                checkOneCol(None,None,c)
            return cols, opFunc, _axisTitle(cols,separator)
        return checkColsSeparatedBy

    def createCheckColsSeparatedByAnyOf(sepsAndFuncs):
        checkFuncs = [createCheckColsSeparatedBy(*x) for x in sepsAndFuncs]
        def checkCol(option,opt,value):
            for cf in checkFuncs:
                try:
                    return cf(option,opt,value)
                except OptionValueError:
                    pass
            raise OptionValueError("Invalid col: '%s'" % (value,))
        return checkCol

    def createCheckOneOrMoreColsSeparatedByAnyOf(sepsAndFuncs):
        checkMany = createCheckColsSeparatedByAnyOf(sepsAndFuncs)
        def checkOneColOrTwoColsAny(option,opt,value):
            try:
                return checkOneCol(option,opt,value)
            except OptionValueError:
                pass
            return checkMany(option,opt,value)
        return checkOneColOrTwoColsAny

    def checkColVal(option,opt,value):
        try:
            col,val = value.split(':')
            checkOneCol(None,None,col)
            return (col,float(val))
        except ValueError, ve:
            raise OptionValueError(
                "Invalid arg '%s', it should be of type COL:VAL"%value)


    class MyOption(Option):
        TYPES = Option.TYPES + ("col","col:val")
        TYPE_CHECKER = copy(Option.TYPE_CHECKER)
        TYPE_CHECKER["col"] = createCheckOneOrMoreColsSeparatedByAnyOf(
            (('/',_opDiv),
             ('+',_opPlus),
             ('-',_opMinus) ) )
        TYPE_CHECKER["col:val"] = checkColVal

    usage = "plotter [plotdatafiles] [options]"
    description = "Plots data from plotdatafiles using gnuplot. "+\
            "If no filenames are given or a filename is -,"+\
            " reads from standard input."
    op = OptionParser(usage=usage,description=description,
                              option_class=MyOption)
    op.add_option("-x", "--x", action="store", type="col", default="kw",
                  metavar="COL",
                  help="X column type. "+
                  "Give --listcols for possible COL values. "+
                  "Also accepted: COL/COL, COL+COL, COL-COL. Default: kw")
    op.add_option("-y", "--y", action="store", type="col", default="awcov",
                  help="Y column type. "+
                  "Give --listcols for possible COL values. "+
                  "Also accepted: COL/COL, COL+COL, COL-COL. Default: awcov")
    op.add_option("--bar", action="store_true",
                  help="Draws bar graphs.")
    op.add_option("--barsat", action="store", type="str",
                  help="Draw bars at certain values of x. Eg. 100,200,300")
    op.add_option("--until", action="store", type="col:val",
                  metavar="COL:VAL",
                  help="Data is read until the value of COL >= VAL. Eg. 's:10'")
    op.add_option("--term", action="store", type="str",
                  help="gnuplot terminal type.")
    op.add_option("--with", action="store", type="str", dest="withstr",
                  default="lines",
                  help="'with' string for gnuplot, default: lines")
    op.add_option("--custom", action="store", type="str",
                  help="custom string passed to gnuplot, eg. 'set a; set b;'")
    op.add_option("--listcols", action="store_true",
                  help="list available column types and exit.")

    options, filenames = op.parse_args(sys.argv[1:])

    if options.barsat:
        options.bar = True

    if options.withstr and not options.withstr.startswith('with '):
        options.withstr = 'with ' + options.withstr

    # if no filename given, read from stdin
    if len(filenames) == 0:
        # "-" is the stdin "filename" of gnuplot
        return ["-"], options
    else:
        return filenames, options


def titleFromOptions(options):
    t = options.y[-1]
    if options.until:
        col,val = options.until
        if options.bar:
            t += " after %s %s" % (val,colName(col))
        else:
            t += " As a Function of %s" % (options.x[-1],)
    return t


class NoDataError(ValueError):
    pass

class PlotDataFile:

    OPERATORS = (OP_NONE,OP_DIV) = range(2)

    def __init__(self, f, xCol, yCol, untilColVal=None):

        self.xCol, self.xOpFunc, self.xTitleFunc = xCol
        self.yCol, self.yOpFunc, self.yTitleFunc = yCol

        self.filename = f.name

        self.stopi = None
        if untilColVal:
            self.untilCol,self.untilVal = untilColVal
        else:
            self.untilCol = None

        self._readInfo(f)
        self._readData(f)

    def _readInfo(self,f):
        colsRead = False
        for line in f:
            stripped = line.strip()
            if stripped.startswith(_LINE_TITLE):
                self.title = stripped[len(_LINE_TITLE):].strip()
            elif stripped.startswith(_LINE_COLS):
                cols = {}
                for i,col in [icol.split(":") for icol in
                              stripped[len(_LINE_COLS):].strip().split()]:
                    cols[col] = int(i)
                self.xi = [cols[c]-1 for c in self.xCol]
                self.yi = [cols[c]-1 for c in self.yCol]
                if self.untilCol is not None:
                    self.stopi = cols[self.untilCol]-1
                colsRead = True
            elif not stripped.startswith("#"):
                break
        if not colsRead:
            raise NoDataError("'%s' doesn't seem like a plotdat file!"%(self.filename,))


    def _readData(self,f):
        self._data = []
        self.untilValReached = False
        for line in f:
            d = line.strip().split()
            if not d:
                # empty line marks the end of data
                break
            if not self.untilValReached:
                self._data.append( self._dataFromRow(d) )
                if self.untilCol is not None and float(d[self.stopi]) > self.untilVal:
                    self.untilValReached=True
                    # TODO: for non-stdin files, we could break here.
                    # for stdin, have to read the unneeded lines somewhere,
                    # now we do it here
        else:
            if self.untilCol is not None:
                self._data.append( ('NaN','NaN' ) )

    def _dataFromRow(self, row):
        x = self.xOpFunc(*[row[i] for i in self.xi])
        y = self.yOpFunc(*[row[i] for i in self.yi])
        return (x,y)

    def plotStr(self,withStr=None):
        return '"-" using 1:2 %s title "%s"' % (withStr or "",self.title)

    def shortTitle(self):
        # TODO: taking the last word of a title may not always be a good
        # way to make a short title...
        splat = self.title.split()
        return splat[-1] if splat else ""

    def getLastValue(self):
        if self.untilCol is not None and not self.untilValReached:
            return None
        else:
            return self._data[-1][1]

    def getValueAt(self,x=None,y=None):
        for vx,vy in self._data:
            fx,fy = float(vx),float(vy)
            if (x is None or fx >= x) and (y is None or fy >= y):
                return fy
        return None

    def getValue(self,yCol,limCol=None,limVal=None):

        if limCol is None or limVal is None:
            return self.getLastValue(yCol)
        limInd = self.cols[limCol]-1
        for line in self.file:
            currVal = float(line.split()[limInd])
            if currVal >= limVal:
                yVal = float(line.split()[self.cols[yCol]-1])
                break
        else:
            yVal = 'NaN'
        return yVal

    def getColIter(self,col1,col2):
        return None
        ci1 = self.cols[col1]-1
        ci2 = self.cols[col2]-1
        class ColIter:
            def __iter__(ciself):
                for line in self.file:
                    lineVals = line.strip().split()
                    if not lineVals:
                        break
                    yield (lineVals[ci1], lineVals[ci2])
        return ColIter

    def __iter__(self):
        return self._data.__iter__()


    def xTitle(self):
        return self.xTitleFunc



_LINE_TITLE = "# Title:"
_LINE_COLS = "# Columns:"

def createPlotDataFiles(filenames, xCol, yCol, untilColVal):
    """Reads the given files and returns a list of corresp. PlotDataFiles.
    """
    dats = []
    for fn in filenames:
        if fn=='-':
            stdinHadData = False
            while not sys.stdin.closed:
                try:
                    dats.append( PlotDataFile(sys.stdin,xCol,yCol,untilColVal) )
                except NoDataError:
                    break
                stdinHadData = True
            if not stdinHadData:
                raise NoDataError('Data from stdin is invalid!')
        else:
            f = open(fn,"r")
            while True:
                try:
                    dats.append( PlotDataFile(f,xCol,yCol,untilColVal) )
                except NoDataError:
                    break
            f.close()

    return dats


def printPlotCommand(dats,options):
    """ """
    xCol = options.x
    yCol = options.y

    print 'set title "%s";' % "" #(titleFromOptions(options),)
    print 'set xlabel "%s"; ' % (xCol[-1])
    print 'set ylabel "%s"; ' % (yCol[-1])
    print 'set xrange [0:]; '
    if options.term:
        print 'set term %s; ' % options.term
    if options.custom: print options.custom

    print 'plot '+', '.join([df.plotStr(options.withstr) for df in dats])
    print len(dats)

    for pd in dats:
        for x,y in pd:
            print x,y
        print 'e' # 'e' is kindof an end symbol for gnuplot


def printBarPlotCommand(dats,options):
    """ """

    if options.barsat:
        values = sorted([float(v.strip()) for v in options.barsat.split(',')],
                        reverse=True)
        titles = ["%s: %s"%(options.x[-1],v) for v in values]
        tvs = []
        for v in values:
            titlesAndVals = []
            for df in dats:
                val = df.getValueAt(x=v)
                if val is None:
                    print >> sys.stderr, (
                        "WARNING: Data of %s (source: %s) ends before %s >= %s!")%(df.title, df.filename, df.xCol, v)
                    print >> sys.stderr, "WARNING: Its bar won't be drawn."
                    titlesAndVals.append( (df.shortTitle(), 'NaN') )
                else:
                    titlesAndVals.append( (df.shortTitle(), val) )
            tvs.append(titlesAndVals)
    else:
        titlesAndVals = []
        for df in dats:
            val = df.getLastValue()
            if val is None:
                print >> sys.stderr, (
                    "WARNING: no data for %s. Not drawing its bar."%(df.title,))
                titlesAndVals.append( (df.shortTitle(), 'NaN') )
            else:
                titlesAndVals.append( (df.shortTitle(), val) )
        tvs = [titlesAndVals]


    print 'set title "%s";' % "" #(titleFromOptions(options),)
    print 'set xlabel "%s"; ' % ""
    print 'set ylabel "%s"; ' % (options.y[-1])
    if options.term:
        print 'set term %s; ' % options.term
    print 'set boxwidth 0.9; '
    print 'set yrange [0:]; '
    print 'set style fill pattern border'
    #print 'set xtics nomirror rotate by -30'
    if options.custom: print options.custom

    n = len(tvs)
    if not options.barsat:
        print 'plot "-" using 2:xticlabels(1) with boxes lt -1 notitle'
    else:
        print 'plot "-" using 2:xticlabels(1) with boxes lt -1 title "%s"'%str(titles[0]),
        for t in titles[1:]:
            print ', "-" using 2:xticlabels(1) with boxes lt -1 title "%s"'%(str(t),),
        print
    for tv in tvs:
        for t,v in tv:
            print "%s %s" % (t,v)
        print 'e'

def main(argv):
    filenames, options = readSysArgs(argv)
    if options.listcols:
        print "Available column types:"
        for short,long in sorted(_COL_NAMES.iteritems()):
            print ("%s"%short).ljust(20," "), long
        return True
    try:
        dats = createPlotDataFiles(filenames,options.x,options.y,options.until)
    except KeyboardInterrupt:
        return False
    except Exception, e:
        print >> sys.stderr, "ERROR: %s" % e
        return False

    if options.bar:
        printBarPlotCommand(dats,options)
    else:
        printPlotCommand(dats,options)

    return True

if __name__ == "__main__":
    ok = main(sys.argv)
    sys.exit(0 if ok else -1)
