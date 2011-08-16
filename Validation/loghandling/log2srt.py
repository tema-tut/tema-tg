#!/usr/bin/env python
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


import time
import sys
from optparse import OptionParser

def logtime2epoc(logtimestr):
    y = time.localtime(time.time())[0]
    m = int(logtimestr[:2])
    d = int(logtimestr[2:4])
    h = int(logtimestr[4:6])
    mins = int(logtimestr[6:8])
    secs = int(logtimestr[8:10])
    return time.mktime((y,m,d,h,mins,secs,0,0,0))+int(logtimestr[11:14])/1000.0

def epoc2srttime(timediff):
    ss = timediff - int(timediff)
    strtime = time.strftime("%H:%M:%S", time.gmtime(timediff)) + "," + str(ss)[2:5]
    days = time.strftime("%d", time.gmtime(timediff))
    hours = int(time.strftime("%H", time.gmtime(timediff))) + 24*(int(days)-1)
    if hours < 10:
        hours = "0%i" % hours
    else:
        hours = str(hours)
    
    minutes = time.strftime("%M", time.gmtime(timediff))
    seconds = time.strftime("%S", time.gmtime(timediff)) + "," + str(ss)[2:5]
    while len(strtime) < 12:
        seconds = seconds + '0'
        strtime = strtime + '0'
    return hours + ":" + minutes + ":" + seconds
    return strtime

def print_subs(number, start, end, buffer):
    def cleanup_string(s):
        return s.replace("<","'").replace(">","'")

    try:
        showtime = epoc2srttime(start)
        hidetime = epoc2srttime(end)
    except Exception, e:
        print e
        print "WARNING: garbled time", str(start) + ', ' + str(end)
        return

    print number
    print showtime, "-->", hidetime
    last_aw = None
    for element in buffer:
        time_stamp = element[0]
        aw = cleanup_string(element[1])
        kw = cleanup_string(element[2])
        if aw != "" and aw != last_aw:
            print aw.replace(":",": ")
            last_aw = aw
        print time_stamp + ': ' + kw
    print ""


def readlog(args):
    te_executes = "TestEngine: Executing: "
    ad_sends = "Adapter: Sending ["
    connect = "Adapter: A client"
    line = sys.stdin.readline()
    while line.find(connect) == -1:
        line = sys.stdin.readline()
    epocstart = logtime2epoc(line.split()[0])
    offset = 0.0
    clock_skew = 1.0
    if len(args) > 0:
        offset = float(args[0])
        if len(args) > 1:
            clock_skew = float(args[1])
    aw_being_executed = ""
    kw_being_executed = ""
    INTERVAL = 0.2
    buffer = []
    sub_number = 0
    start_time = -2*INTERVAL
    for line in sys.stdin:
        print_new_subs = 0
        if not te_executes in line and not ad_sends in line:
            continue
        if te_executes in line:
            if ":start_aw" in line or ":start_sv" in line:
                #print_new_subs = 1
                #aw_executed.append(line.split(te_executes)[1].strip())
                aw_being_executed = line.split(te_executes)[1].strip()
            #elif ":end_aw" in line:
                #print_new_subs = 1
                #kw_being_executed = "(" + kw_being_executed + ")"
                #aw_executed[-1] = "(" + aw_executed[-1] + ")"
            elif ": kw" in line:
                print_new_subs = 1
                kw_being_executed = line.split(te_executes)[1].strip()
        elif ad_sends in line:
            print_new_subs = 1
            kw_being_executed = line.split(ad_sends)[1].strip()[:-1] + "...?"

        if print_new_subs:
            try:
                logtime = line.split()[0]
                lineepoctime = logtime2epoc(logtime) - epocstart + offset
            except:
                print "WARNING: garbled time", line.strip()
                continue

            if start_time + INTERVAL < lineepoctime:
                if len(buffer) > 0:
                    sub_number += 1
                    print_subs(sub_number, clock_skew*start_time, \
                               clock_skew*lineepoctime - 0.001, buffer)
                    buffer[:] = []
                start_time = lineepoctime

            buffer.append((logtime, aw_being_executed, kw_being_executed))

    if len(buffer) > 0:
        sub_number += 1
        print_subs(sub_number, start_time, start_time + 10, buffer)
        

if __name__ == '__main__':
    usage = "usage: %prog [delay [skew]]\ndelay: Subtitle delay (default 0.0s)\nskew: Clock skew between server and videorecorder (default 1.0)"
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()
    try:
        readlog(args)
    except KeyboardInterrupt:
        pass
