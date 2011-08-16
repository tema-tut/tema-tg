# -*- coding: iso-8859-1 -*-
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

import math
import sys

_text_offset = 4
_text_height = 6
_text_size = 10
_baseline_skip = 12
_min_margin = 80
_label_offset = 0

def set_font_size(f_size):
    global _text_offset
    global _text_height
    global _text_size
    global _baseline_skip

    if f_size == _text_size:
        return
    if not f_size:
        return
    _text_size = int(f_size)
    _text_height = _text_size - _text_offset
    _baseline_skip = _text_size + 2

def set_label_offset(l_offset):
    global _label_offset
    _label_offset=int(l_offset)

def __lanka(alpha,cx,dx,X,cy,Y):
    term1 = alpha * X - alpha * cx + dx
    term2 = alpha * (Y-cy)
    term3 = alpha * X - alpha * cx - dx
    temp = term2*term2
    half1 = term1*term1 + temp
    half2 = term3*term3 + temp
    return math.sqrt(half1) + math.sqrt(half2)

def __mean(alpha):
    return (alpha[0]+alpha[1])/2.0

def _State__search(target_val, cx, dx, X, cy, Y):
    alpha = (0.0,1.0)
    refval = __lanka(__mean(alpha), cx, dx, X, cy, Y)
    while abs( refval - target_val ) > 0.001 :
        if refval < target_val :
            alpha = (__mean(alpha), alpha[1])
        else:
            alpha = (alpha[0], __mean(alpha))
        refval = __lanka(__mean(alpha), cx, dx, X, cy, Y)
    return __mean(alpha)
    

class State(dict):
    def __init__(self, topLeft, size, attributes, *args, **kwargs):
        super(State, self).__init__(*args, **kwargs)
        center = [ a+b/2.0 for a,b in zip( topLeft, size) ]
        self.center = tuple(center)
        self.size = tuple(size)
        self.topLeft = tuple(topLeft)
        self.attributes = tuple(attributes)

    def build_visual(self, init_marker = False):
        self['x'],self['y'] = self.topLeft
        self['rx'] = 14 # Radius of rounded corners
        self.is_init = init_marker
        if init_marker:
            self['cx'],self['cy'] = self.center
            self['rx'],self['ry'] = [dim for dim in self.size ]
            self['fill'] = "none"
            self['stroke'] = "none"
        else:
            #self['rx'],self['ry'] = [dim/2.0 for dim in self.size ]
            self['width'],self['height'] = self.size
            self['fill'] = "lightyellow"
            self['stroke'] = "darkblue"

    def edge(self, to_dir ):
        cx,cy= self.center
        rx,ry= [ dim/2.0 for dim in self.size ]
        X,Y = to_dir
        if self.is_init:
            if rx >= ry :
                dx = math.sqrt(rx*rx-ry*ry)
                alpha = __search(2*rx, cx, dx, X, cy, Y)
            else:
                dy = math.sqrt(ry*ry - rx*rx)
                alpha = __search(2*ry, cy, dy, Y, cx, X)
            return (cx + alpha * (X-cx), cy + alpha * (Y-cy))
        else:
            dx = X-cx
            dy = Y-cy
            if abs(dx)+abs(dy) < 0.001 :
                return (cx,cy)
            scale = 1.0 / max( abs(dx)/rx, abs(dy)/ry)
            return ( cx+scale*dx, cy+scale*dy)

    def into_SVG(self, SVG):
        if self.is_init:
            SVG.element("ellipse", self)
        else:
            SVG.element("rect", self)
        X = self.center[0]
        Y = self.topLeft[1]+self.size[1] - _text_offset
        dy = _baseline_skip
        text_properties = { 'x': X, 'font-size': _text_size,
                            'style': "text-anchor: middle" }
        for att in self.attributes :
            text_properties['y'] = Y
            Y -= dy
            SVG.begin("text", text_properties )
            SVG.raw(att)
            SVG.end()
            

class Transition(dict):
    def __init__(self, source, bendpoints, dest, action_name,
                  *args, **kwargs):
        super(Transition, self).__init__( *args, **kwargs)
        self.action = action_name
        self.points = []
        self.points.append( source.center )
        if bendpoints :
            for p in bendpoints:
                self.points.append(tuple(p))
        self.points.append( dest.center )
        p1 = source.edge(self.points[1])
        p2 = dest.edge(self.points[-2])
        self.points[0] = p1
        self.points[-1] = p2

    def build_visual(self, init_marker=False):
        self.__init_mark = init_marker
        self['fill'] = 'none'
        self['stroke'] = 'black'
        self['stroke-width'] = 1
        self['marker-end'] = 'url(#ArrHead)'
        cmd = 'M'
        format = "%.3f"
        line_data = []
        for x,y in self.points:
            line_data.append(cmd)
            line_data.append(format % x)
            line_data.append(format % y)
            cmd = 'L'
        self['d'] = ' '.join(line_data)

    def __text_point(self):
        length=0.0
        sub_lengths = [0.0 ]
        for start, end in zip( self.points[0:-1], self.points[1:] ):
            dx = end[0]-start[0]
            dy = end[1]-start[1]
            length += math.sqrt( dx*dx + dy*dy )
            sub_lengths.append( length )
        target = length / 2.0
        pn = self.points[-1]
        if target < 0.01 :
            x,y = self.points[0]
        else:
            begg = [(p,l) for p, l in zip( self.points, sub_lengths)\
                               if l < target ]
            begg.append((self.points[len(begg)],sub_lengths[len(begg)]))
            alpha = (target - begg[-2][1]) / (begg[-1][1] - begg[-2][1])
            p1 = begg[-2][0]
            p2 = begg[-1][0]
            x = p1[0]+ alpha * (p2[0]-p1[0])
            y = p1[1]+ alpha * (p2[1]-p1[1])

        if y <= pn[1] :
            dy = - _text_offset
        else:
            dy= _text_offset + _text_height
        return (x,y+dy)

    def __name_point(self):
        pn_x, pn_y = self.points[-1]
        x,y = self.points[0]
        dy = - _text_offset
        if y > pn_y :
            dy = _text_offset + _text_height
        return (x,y+dy)

    def into_SVG(self, SVG):
        SVG.element("path", self)
        text_properties = dict()
        text_properties['style'] = "text-anchor: middle"
        if self.__init_mark :
            text_properties['x'], text_properties['y'] = self.__name_point()
            text_properties['x'] += _label_offset
            text_properties['font-size'] = 14
        else:
            text_properties['font-size'] = _text_size
            text_properties['x'],text_properties['y'] = self.__text_point()
        SVG.begin("text", text_properties )
        SVG.plain_text(self.action)
        SVG.end()

def markers(SVG):
    SVG.begin("defs")
    SVG.begin("marker", {'id': "ArrHead", 'viewBox': "0 0 8 8",
                         'refX': 9, 'refY': 4, 'orient': "auto",
                         'markerWidth': 4, 'markerHeight': 4,
                         'stroke': 'black', 'fill': 'black'})
    SVG.element("path", {'d': 'M 0 0 L 8 4 L 0 8 z'})
    SVG.end()
    SVG.end()

def _min(p1, p2):
    return (min(p1[0],p2[0]), min(p1[1],p2[1]))
def _max(p1, p2):
    return (max(p1[0],p2[0]), max(p1[1],p2[1]))
def _plus(p1,p2):
    return (p1[0]+p2[0], p1[1]+p2[1])

def pict_size(init_arr, states, transitions):
    st_min = st_max = states.itervalues().next().topLeft
    for _ss in states.itervalues():
        st_min = _min( st_min, _ss.topLeft )
        st_max = _max( st_max, _plus(_ss.topLeft, _ss.size ) )

    minpoint = _min( st_min, init_arr.points[0])
    maxpoint = _max( st_max, init_arr.points[0])

    for _tr in transitions.itervalues():
        for p_i in _tr.points:
            minpoint = _min( minpoint, p_i )
            maxpoint = _max( maxpoint, p_i )
    #print >> sys.stderr, st_min, st_max
    #print >> sys.stderr, minpoint, maxpoint
    
    margin = 2.0 * max(( _min_margin/2,
                         abs(st_min[0]-minpoint[0]),
                         abs(st_max[0]-maxpoint[0]),
                         abs(st_min[1]-minpoint[1]),
                         abs(st_max[1]-maxpoint[1]) ))
    width = 2*margin + st_max[0]-st_min[0]
    height = 2*margin + st_max[1]-st_min[1]
    origo_X = st_min[0]-margin
    origo_Y = st_min[1]-margin
    viewbox = " ".join([ "%.3f"% dim for dim in [origo_X, origo_Y, width, height]])
        
    rval = { 'width': width,
             'height': height,
             'viewBox': viewbox }

    return rval
