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


"""
Simulates test model graphically
"""
import os
import sys
import re
import time
import optparse

from tema.model import getModelType,loadModel

class TkGraphics:
    """
    This is a View class in MVC-like model.
    
    Public methods:
    ---------------

    new - initialize display for drawing a new graph
    
    draw_state(stateid, x-coord, y-coord) - draw a state to the coords

    draw_transition(from_stateid,actionname,to_stateid) - draws transition

    listen_to_events() - gui takes control and returns when there is a
    message to the control layer. Returned message (QUIT, REFRESH,
    BACK, INC_DEPTH, DEC_DEPTH, INC_WIDTH, DEC_WIDTH, CHANGE_STATE,
    PRINT_PATH, NEW_REGEXP) is stored in the event attribute.

    Read-only public attributes:
    ----------------------------

    xsize, ysize - dimensions of graph drawing area

    event - carries messages to the control

    regexp, chosen_state - carries message parameter
    
    """
    def __init__(self,xsize,ysize):
        try:
            import Tkinter
            import tkFont
        except:
            print "Cannot import Tkinter or tkFont library."
            sys.exit(1)
        self.Tkinter=Tkinter
        self.xsize,self.ysize=xsize,ysize
        self._delta_x=self._delta_y=0
        self._root=Tkinter.Tk()
        self._transitionfont=tkFont.Font(family="Arial",size=-12)
        self._textframe=Tkinter.Frame(self._root)
        self._textframe.grid(column=1,row=2,sticky='we')
        self._label=Tkinter.Label(self._textframe,font=self._transitionfont,
                                  text='q: quit | b: back | +-: depth' + \
                                  ' | */: width' + \
                                  ' | arrows/home: scroll' + \
                                  ' | btn1: choose | btn2: shortest path' + \
                                  ' | regexp:')
        self._label.grid(column=1,row=1,sticky='w')
        self._textbox=Tkinter.Entry(self._textframe)
        self._textbox.grid(column=2,row=1,sticky='we')
        self._textbox.bind("<Key>",self._regexp_event)
        self._root.rowconfigure(1,weight=1)
        self._root.columnconfigure(1,weight=1)
        self._textframe.columnconfigure(2,weight=1)
        self._root.bind("<Configure>",self._resize)

    def new(self):
        if hasattr(self,'_canvas'): self._canvas.delete('all')
        else:
            self._canvas=self.Tkinter.Canvas(self._root,width=self.xsize,
                                               height=self.ysize)
            self._canvas.config(background='white',takefocus='1',
                            highlightcolor='red')
            self._canvas.bind("<Key>",self._keypress_event)
            self._canvas.bind("<Button>",self._canvas_buttonpress_event)
            self._canvas.grid(column=1,row=1,sticky='nesw')
        self._canvas.focus_set()
        self._states={} # contains graphical objects denoting states

    def draw_state(self,state,x0,y0):
        self._states[state]=self._canvas.create_oval(x0-1,y0-1,x0+1,y0+1,
                                                     fill='blue',
                                                     tag='state:%s' % state)

    def draw_text(self,x,y,txt):
        self._canvas.create_text(x,y,text=txt,font=self._transitionfont,
                                 anchor='w')

    def draw_transition(self,sourcestate,action,deststate):
        x1=self._canvas.coords(self._states[sourcestate])[0]+1
        y1=self._canvas.coords(self._states[sourcestate])[1]+1
        x2=self._canvas.coords(self._states[deststate])[0]+1
        y2=self._canvas.coords(self._states[deststate])[1]+1
        # Tags identify the state that is chosen when the object is clicked
        label=self._canvas.create_text(x2+1,y2-2,
                                       text='%s' % action,
                                       anchor='sw',
                                       font=self._transitionfont,
                                       tag='state:%s' % deststate)
        arrow=self._canvas.create_line(x1,y1,x2,y2,arrow='last',fill='blue',
                                       tag='state:%s' % deststate)

    def listen_to_events(self):
        self._in_mainloop=1
        self._root.mainloop()
        self._in_mainloop=0

    # private:

    def _resize(self,event):
        self.xsize=self._root.winfo_width()-2
        self.ysize=self._root.winfo_height()-24

    def _close(self,pass_event):
        self.event=pass_event
        self._root.quit() # quit mainloop, return control to the
                          # caller of listen_to_events
                          
    def _keypress_event(self,e):

        def scroll_canvas(delta_x,delta_y):
            if delta_x==None and delta_y==None:
                self._canvas.move('all',self._delta_x,self._delta_y)
                self._delta_x=self._delta_y=0
            else:
                self._canvas.move('all',delta_x,delta_y)
                self._delta_x-=delta_x
                self._delta_y-=delta_y
        
        key=e.keysym.lower()
        if   key=='q':     self._close("QUIT")
        elif key=='r':     self._close("REFRESH")
        elif key=='l':     self._close("REFRESH")
        elif key=='b':     self._close("BACK")
        elif key=='plus':  self._close("INC_DEPTH")
        elif key=='minus': self._close("DEC_DEPTH")
        elif key=='kp_add':  self._close("INC_DEPTH")
        elif key=='kp_subtract': self._close("DEC_DEPTH")
        elif key=='asterisk': self._close("INC_WIDTH")
        elif key=='slash': self._close("DEC_WIDTH")
        elif key=='kp_multiply': self._close("INC_WIDTH")
        elif key=='kp_divide': self._close("DEC_WIDTH")
        elif key=='down':  scroll_canvas(0,-self.ysize/10)
        elif key=='up':    scroll_canvas(0,self.ysize/10)
        elif key=='right': scroll_canvas(-self.xsize/10,0)
        elif key=='left':  scroll_canvas(self.xsize/10,0)
        elif key=='home':  scroll_canvas(None,None) # restore orig pos.

    def _canvas_buttonpress_event(self,e):
        x = self._canvas.canvasx(e.x)
        y = self._canvas.canvasx(e.y)
        state=""
        for t in self._canvas.gettags( self._canvas.find_closest(x,y)[0] ):
            if t[:6]=="state:":
                self._show_effect( self._canvas.find_closest(x,y)[0] )
                state=t[6:]
                break
        if state:
            self.chosen_state=state
            if e.num==1:
                self._close("CHANGE_STATE")
            else:
                self._close("PRINT_PATH")

    def _regexp_event(self,e):
        if e.keysym.lower()=='return':
            self._close("NEW_REGEXP")
            return
        elif e.keysym.lower()=='backspace':
            s=self._textbox.get()[:-1]
        else:
            s=self._textbox.get()+e.char
        try:
            regexp=re.compile(s)
            self._textbox.config(background='white')
            self.regexp=s
        except Exception:
            self._textbox.config(background='red')
        self._root.update()

    def _show_effect(self,canvasitem):
        self._canvas.itemconfigure(canvasitem,fill='red')
        self._root.update()
        time.sleep(0.3)
        
        
def draw_states(graphics,stateset,x,y,xdelta,ydelta,depth,stateset_by_id,regexpobj):
    """Draws all possible behaviours starting from the stateset down
    to the given depth. The first node is drawn to (x,y+ydelta). Only
    the transitions matching regexpobj are drawn. Returns last used y
    coordinate."""

    def next_actions(stateset,regexpobj,found_states,action_dests):
        """Search for next actions that match regexpobj. Found actions
        and lists of states to which their execution can lead is
        returned in action_dests"""
        # States that have been seen (uniqueness of their string
        # representation is assumed):
        # found_states[ state_string_representation ] -> state object
        #
        # States to which an action can take:
        # action_dests[ action_string_representation ] -> list of state objects
        all_out_transitions=[] # out transitions from every state in stateset
        for s in stateset:
            all_out_transitions.extend(s.getOutTransitions())
        for t in all_out_transitions:
            t_dest_state=str(t.getDestState())
            t_action=str(t.getAction())
            if regexpobj.search(t_action): # found wanted action!
                if not t_dest_state in found_states:
                    found_states[t_dest_state]=t.getDestState()
                if not t_action in action_dests: action_dests[t_action]=[]
                action_dests[t_action].append(found_states[t_dest_state])
            else: # this action is not particularly interesting
                if t_dest_state in found_states: continue
                found_states[t_dest_state]=t.getDestState()
                next_actions([t.getDestState()],regexpobj,
                             found_states,action_dests)
    
    y+=ydelta
    if not stateset_by_id: # draw the state only on the first call
        stateset_by_id[0]=stateset
        graphics.draw_state(0,x,y)
    this_stateset_id=len(stateset_by_id)-1

    if depth<=0: return y

    action_dests,found_states={},{}
    next_actions(stateset,regexpobj,found_states,action_dests)
    for action,stateset in action_dests.iteritems():
        next_stateset_id=len(stateset_by_id)
        stateset_by_id[next_stateset_id]=stateset
        graphics.draw_state(next_stateset_id,x+xdelta,y+ydelta)
        graphics.draw_transition(this_stateset_id,action,next_stateset_id)
        y=draw_states(graphics,stateset,x+xdelta,y,
                      xdelta,ydelta,depth-1,stateset_by_id,regexpobj)
    return y

def find_shortest_path(starting_state,goal_states):
    states_seen={str(starting_state):1}
    current_states=[(starting_state,[])]
    while 1:
        next_states=[]
        for state,path in current_states:
            if str(state) in goal_states: return path
            
            for t in state.getOutTransitions():
                t_dest_state=str(t.getDestState())
                if not t_dest_state in states_seen:
                    states_seen[t_dest_state]=1
                    next_states.append( (t.getDestState(),path+[t.getAction()]) )
        if next_states==[]: return None # could not find path...
        current_states=next_states
        
def xsimulate(starting_state):
    depth=2
    xsize=800
    ysize=570
    regexp=""
    top_stateset=[starting_state]
    old_statesets=[]
    g=TkGraphics(xsize,ysize)
    width_delta=0
    while 1:
        g.new()
        xdelta=g.xsize/(depth+1)+width_delta
        ydelta=20
        stateset_by_id={}
        print "-"*42
        print "Current state set:",[str(s) for s in top_stateset]
        y=draw_states(g,top_stateset,1,1,xdelta,ydelta,depth,stateset_by_id,re.compile(regexp))
        if y==ydelta+1: # nothing was drawn
            g.draw_text(xdelta,ydelta+ydelta,"No transitions. Press 'b'")
        g.listen_to_events()
        try:
            if g.event=="QUIT": break
        except: # g has been destroyed
            break
        if g.event=="REFRESH": continue
        elif g.event=="BACK" and old_statesets: top_stateset=old_statesets.pop()
        elif g.event=="CHANGE_STATE":
            old_statesets.append(top_stateset)
            top_stateset=stateset_by_id[int(g.chosen_state)]
        elif g.event=="PRINT_PATH":
            goal_states={}
            for s in stateset_by_id[int(g.chosen_state)]: goal_states[str(s)]=1
            path=find_shortest_path(starting_state,goal_states)
            print "-"*42
            print "A shortest path to any of states",goal_states.keys()
            for index,action in enumerate(path):
                print index+1,action
        elif g.event=="INC_DEPTH": depth+=1
        elif g.event=="DEC_DEPTH" and depth>1: depth-=1
        elif g.event=="INC_WIDTH": width_delta+=2
        elif g.event=="DEC_WIDTH": width_delta-=2
        elif g.event=="NEW_REGEXP": regexp=g.regexp

# main program

try: import psyco
except: pass

def readArgs():

    usagemessage = "usage: %prog [filename] [options]"
    description = "If no filename is given or filename is -, reads from standard input"

    parser = optparse.OptionParser(usage=usagemessage,description=description)

    parser.add_option("-f", "--format", action="store", type="str",
                      help="Format of the model file")

    options, args = parser.parse_args(sys.argv[1:])

    if len(args) == 0:
        modelfile = "-"
    elif len(args) == 1:
        modelfile = args[0]
    else:
        parser.error("More than one filename given")

    if not options.format and modelfile == "-":
        parser.error("Reading from standard input requires format parameter")
    
    return modelfile,options

def main():
    modelfile,options=readArgs()
    
    try:
        modeltype=options.format
        if not modeltype:
            modeltype = getModelType(modelfile)

        if not modeltype:
            print >>sys.stderr, "%s: Error. Unknown model type. Specify model type using '-f'" % os.path.basename(sys.argv[0])
            sys.exit(1)

        if modelfile == "-": 
            file_object=sys.stdin
        else:
            file_object=open(modelfile)

        m=loadModel(modeltype,file_object)
    except Exception,  e:
        print >>sys.stderr,e
        sys.exit(1)

    xsimulate(m.getInitialState())

if __name__ == "__main__":
    main()
