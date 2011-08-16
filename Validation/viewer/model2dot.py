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

import sys,optparse,os,re,copy
from tema.model import loadModel,getModelType
try:
    from hashlib import md5
except ImportError:
    from md5 import md5

DEFAULT_COLORS={'default':'black','aw':'red','kw':'blue','sv':'green','ts':'purple'}

def print_header(layout, name, compact ):
    layout.write('digraph "%s" {\n' % name)
    if compact:
        layout.write('edge [arrowsize=0.3];\n')
        layout.write('ranksep=.4; ratio="compress";\n')
        layout.write('node [label="",shape=point];\n')
    else:
        layout.write('node [label="",shape=circle];\n')

_aw = re.compile("(^aw|~aw)|((.*?)(start_aw|end_aw))")
_sv = re.compile("(.*?)(start_sv|end_sv)")
_kw = re.compile("(.*?)kw_")
_ts = re.compile("(.*?)(WAKE|SLEEP)")
_color_mappings = {'aw' : _aw, 'sv' : _sv, 'kw' : _kw, 'ts' : _ts }

def get_color(label,color_scheme):
    for color in _color_mappings:
        if _color_mappings[color].match(label):
            return color_scheme[color]
    else:
        return color_scheme['default']

def print_transition(layout, source, dest, label, color):
    s = int(md5(str(source)).hexdigest(),16)
    d = int(md5(str(dest)).hexdigest(),16)
    params = []
    if color:
        params.append('color="%s"' % color)
    if label:
        params.append('label="%s"' % label)
    if len(params) > 0:
        param_str = "[" + ",".join(params) + "]"    
    else:
        param_str = ""
    layout.write('%d -> %d %s;\n' % 
                 (s, d, param_str ) )

def print_state(layout,state,state_labels,initial_state, colored):
    if initial_state:
        shape = "oval"
    else:
        shape = "box"
    s = int(md5(str(state)).hexdigest(),16)
    layout.write('%d [label="%s",shape=%s];\n' %
                 ( s, "\\n".join(state_labels), shape ))
def print_footer(layout):
    layout.write('}\n')

def visualise( model, layout, stateprops = True, actions = True , name = "TEMA-Model", compact = False, colored = False, color_scheme = None):
    """
    Visualize model using graphviz dot-notation
    """
    print_header(layout,name, compact )

    states = set()
    initial_state =  model.getInitialState()
    stack = [initial_state]
    state_labels = {initial_state : set(['START']) }
    counter = 0
    cache_clear_interval = 20000
    while len(stack) > 0:
        counter += 1
        if counter > cache_clear_interval:
            try:
                model.clearCache()
            except AttributeError,e:
                pass
            counter = 0
        state = stack.pop()
        if stateprops:
            try:
                current_props = frozenset(state.getStateProps())
                for stateprop in current_props:
                    if state not in state_labels:
                        state_labels[state] = set([str(stateprop)])
                    else:
                        state_labels[state].add(str(stateprop))
            except AttributeError, e:
                pass
        states.add(str(state))
        for transition in state.getOutTransitions():

            if colored or actions:
                current_action = transition.getAction()
                if colored:
                    color = get_color(str(current_action),color_scheme)
                else:
                    color = None
            else:
                color = None
            if not actions:
                current_action = None
            dest_state = transition.getDestState()
            
            print_transition(layout,state,dest_state,current_action,color)
            if str(dest_state) not in states:
                stack.append(dest_state)
    for state in state_labels:
        print_state(layout,state,state_labels[state],state==initial_state,colored)

    print_footer(layout)

def parse_color_scheme(color_scheme_str):
    param_scheme = dict([ color.split(':') for color in color_scheme_str.split(',') ])
    param_keys = set(param_scheme.keys())
    color_scheme = copy.deepcopy(DEFAULT_COLORS)
    color_keys = set(color_scheme.keys())
    diff = param_keys.difference(color_keys)
    color_scheme.update(param_scheme)
    return color_scheme,diff

def parse_args():

    usagemessage = "usage: %prog [filename] [options]"
    description = "If no filename is given or filename is -, reads from standard input"
    colors_str = ",".join([ ":".join(x) for x in DEFAULT_COLORS.iteritems() ])
    parser = optparse.OptionParser(usage=usagemessage,description=description)

    parser.add_option("-f", "--format", action="store", type="str",
                      help="Format of the model file")

    parser.add_option("-o", "--output", action="store", type="str", 
                      metavar="FILENAME", default="-",
                      help="Specifies the output file. If no file is specified or filename is '-', model will be printed into standard output.")

    parser.add_option("--no-stateprops", action="store_true", 
                      default=False,
                      help="Don't print statepropositions as labels")

    parser.add_option("--no-actions", action="store_true", 
                      default=False,
                      help="Don't print actions as transition labels")

    parser.add_option("--compact", action="store_true", 
                      default=False,
                      help="Try to use default values that result in compact-looking model")
    parser.add_option("--colored", action="store_true", 
                      default=False,
                      help="Use colors")

    parser.add_option( "--color-scheme", action="store", type="str",
                      default=colors_str, help="Specifies the coloring to use. Default is '%s'" % colors_str)

    options, args = parser.parse_args(sys.argv[1:])

    if len(args) == 0:
        modelfile = "-"
    elif len(args) == 1:
        modelfile = args[0]
    else:
        parser.error("More than one filename given")

    if not options.format and modelfile == "-":
        parser.error("Reading from standard input requires format parameter")
    
    color_scheme,unknown_keys = parse_color_scheme(options.color_scheme)
    if len(unknown_keys) > 0:
        parser.error("Unknown color key(s): '%s'. Valid keys are '%s'" % (", ".join(unknown_keys),", ".join(DEFAULT_COLORS.keys())))
    return modelfile,color_scheme, options.output, options


def main():
    model_file, color_scheme, dot_file, options = parse_args()

    dot_object = None
    file_object = None
    try:
        try:
            model_type = options.format
            if not model_type:
                model_type = getModelType(model_file)

            if not model_type:
                print >>sys.stderr, "%s: Error. Unknown model type. Specify model type using '-f'" % os.path.basename(sys.argv[0])
                sys.exit(1)
            if model_file == "-": 
                file_object=sys.stdin
            else:
                file_object=open(model_file)
            if dot_file == "-": 
                dot_object=sys.stdout
            else:
                dot_object=open(dot_file,'w')

            m=loadModel(model_type, file_object)
            visualise(m,dot_object,not options.no_stateprops, not options.no_actions, "TEMA-Model %s" % model_file, options.compact, options.colored, color_scheme )
        except Exception,  e:
            print >>sys.stderr,e
            sys.exit(1)
    finally:
        if file_object and model_file != "-":
            file_object.close()
        if dot_object and dot_file != "-":
            dot_object.close()

if __name__ == '__main__':
    main()
