#!/usr/bin/env python
#-*- coding: iso-8859-1 -*-
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

import sys
import os
import optparse

import tema.eini.svg_base as svg_base
import tema.eini.mdmparser as mdmparser
from tema.eini.mdm_objects import State, Transition, markers, pict_size, \
    set_font_size, set_label_offset

def readArgs():

    usagemessage = "usage: %prog [filename] [options]"
    description = "If no filename is given or filename is -, reads from standard input"

    parser = optparse.OptionParser(usage=usagemessage,description=description)

    parser.add_option("--font-size", action="store", type="str",
                      metavar="SIZE", help="Set font size")

    parser.add_option("--label-offset", action="store", type="str",
                      metavar="OFFSET", help="Set label offset")

    parser.add_option("-o", "--output", action="store", type="str", 
                      metavar="FILENAME", default="-",
                      help="Specifies the output file. If no file is specified or filename is '-', model will be printed into standard output.")

    options, args = parser.parse_args()

    if len(args) == 0:
        modelfile = "-"
    elif len(args) == 1:
        modelfile = args[0]
    else:
        parser.error("More than one filename given")
    
    return modelfile,options

filename,options = readArgs()
if options.label_offset:
    set_label_offset(options.label_offset)
if options.font_size:
    set_font_size(options.font_size)


outputfilename = options.output

parser_obj = mdmparser.Parser()
try:
    if filename == "-":
        modelfile = sys.stdin
    else:
        modelfile = open(filename)
    try:
        data = parser_obj.parse(modelfile)
    finally:
        modelfile.close()
except KeyboardInterrupt:
    sys.exit(1)
except IOError,e:
    print >> sys.stderr, "Can not open file:", filename
    raise SystemExit(1)

# State collection have to be dict, because it items are referenced
# using identifiers. Transition collection is dict because of similarity.
states = dict()
transitions = dict()

# Dictionary for state propositions for convenience
state_attribs = dict()
for att_id, att_data in data['stateattributes'].iteritems():
    state_attribs[att_id] = att_data['name']

# Extracting states from parsed data
for st_id, st_data in data['states'].iteritems():
    _st_att = []
    if st_data['attributes']:
        _st_att = [ state_attribs[num] for num in st_data['attributes'] ]
    _st = State(st_data['location'], st_data['size'], _st_att )
    _st.build_visual()
    states[st_id]=_st

# Extracting transitions from parsed data
for tr_id, tr_data in data['transitions'].iteritems():
    _tr = Transition(states[tr_data['source']],
                     tr_data['bendpoints'],
                     states[tr_data['dest']],
                     data['actions'][tr_data['action']]['name'])
    _tr.build_visual()
    transitions[tr_id]=_tr

# Extracting initial state and initial marker from parsed data
initial_state = states[data['properties']['initial_state']['value']]
init_marker = State(data['properties']['init_marker']['location'],
                    data['properties']['init_marker']['size'],
                    [])
init_marker.build_visual(True)

begin_arr = Transition(init_marker, [], initial_state,
                       data['properties']['name']['value'])
begin_arr.build_visual(True)

# The size of the picture
pict_rect = pict_size(begin_arr, states, transitions)

# Outputing the picture
try:
    if outputfilename == "-":
        outputfile = sys.stdout
    else:
        outputfile = open(outputfilename,'w')
    try:
        SVG = svg_base.SVG_file(outputfile, pict_rect)
        markers(SVG)
        SVG.begin("g")
        for st in states.itervalues():
            st.into_SVG(SVG)
        begin_arr.into_SVG(SVG)
        for tr in transitions.itervalues():
            tr.into_SVG(SVG)

        # Frame used in testing commented out
        if False:
            ox,oy,W,H = [ eval(num) for num in pict_rect['viewBox'].split() ]
            del pict_rect['viewBox']
            pict_rect['x'] = ox
            pict_rect['y'] = oy
            pict_rect['width'] = W-1
            pict_rect['height'] = H-1
            pict_rect['fill']='none'
            pict_rect['stroke']='red'
            SVG.element("rect", pict_rect)

        SVG.end()
        SVG.close()
    finally:
        if outputfilename != "-":
            outputfile.close()

except IOError,e:
    print >> sys.stderr, "Can not write to file:", outputfilename
    raise SystemExit(1)        

# End of program
