# coding: iso-8859-1
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

"""A ModelGui class. It's used by guiadapter and guiguidance.
"""

import Tkinter, tkFont
import math
import time
import re

# TODO: refactor...


# Don't create ModelGui directly but via getTheModelGui().
# That'll make sure there's at most one gui.
_theGui = None
def getTheModelGui(createIfDoesntExist=True):
    global _theGui
    if _theGui is None and createIfDoesntExist:
        _theGui = ModelGui(800,600)
    return _theGui

STATE_RADIUS = 6

DEPTH_MIN = 1
DEPTH_MAX = 20
DEPTH_DEFAULT = 10

TRAN_LEN_X = 60
TRAN_LEN_Y = 22


def _isKeyword(temaTransition):
    strAct = str(temaTransition.getAction())
    return strAct.startswith('kw_') or strAct.startswith('~kw_')

def _toCanvasStr(txt):
    return txt.decode("ascii","ignore").replace('%20',' ')


_trans = {}
def _tranByTag(tag):
    if tag.startswith('transition:'):
        tid = int(tag.split(':',1)[1])
        if tid > 0:
            return _trans[tid]
    return None

class CanvasTransition(object):
    """A transition seen on the screen"""
    _lastId = 100
    _font = None
    TransitionTypes = ()
    def __init__(self,precedingCanvasTransition,temaTransitionsInside):
        self.precedingCanvasTransition = precedingCanvasTransition
        self.temaTransitionsInside = temaTransitionsInside
        CanvasTransition._lastId += 1
        self.id = CanvasTransition._lastId
        _trans[self.id] = self

    def nextTransitions(self,TransitionTypes,maxDepth):
        nt = transitionsFromState(self.destTemaState(),TransitionTypes,
                                      maxDepth,prev=self)
        nt.sort(key=lambda t:t.actionStr())
        nt.sort(key=lambda t:t.distance())
        return nt


    def __eq__(self,other):
        return self.actionStr() == other.actionStr()

    @classmethod
    def getListOfContents(cls,firstTransition):
        assert cls.isStart(firstTransition)
        return [ (firstTransition,) ]

    @classmethod
    def getTransitionsStartingFrom(cls,firstTemaTransition):
        assert cls.isStart(firstTransition)

    @classmethod
    def isEnd(cls,temaTransition):
        return cls.isStart()

    def sourceTemaState(self):
        return temaTransitionsInside[0]

    def destTemaState(self):
        return self.temaTransitionsInside[-1].getDestState()

    def getTemaPathFromInitialState(self):
        myTrans = self.temaTransitionsInside
        precTrans = self.precedingCanvasTransition.getTemaPathFromInitialState()
        return precTrans + myTrans

    def getPathFromInitialState(self):
        return self.precedingCanvasTransition.getPathFromInitialState() +(self,)

    def tag(self):
        return 'transition:%i'%(self.id,)

    @classmethod
    def color(cls):
        return 'black'

    def actionStr(self):
        return _toCanvasStr(str(self.temaTransitionsInside[0].getAction()))
    def __str__(self):
        return self.actionStr()

    def drawOn(self,canvas,x1,y1,x2,y2):
        self.drawArrowOn(canvas,x1,y1,x2,y2)
        self.drawActionOn(canvas,x1,y1,x2,y2,self.actionStr())
        self.drawDestStateOn(canvas,x2,y2)

    def drawArrowOn(self,canvas,x1,y1,x2,y2):
        ox, oy = self._stateRadiusOffset(x1,y1,x2,y2)
        canvas.create_line(x1+ox,y1+oy,x2-ox,y2-oy,
                           arrow='last',
                           fill=self.color(),
                           tag=('arrow',self.tag()))

    def drawActionOn(self,canvas,x1,y1,x2,y2,action,component=None):
        yy = y2 - 15
        xx = x2 - 15*(x2-x1)/(y2-y1) + 6
        if component:
            canvas.create_text(xx,yy-12,
                               text=component,
                               font=CanvasTransition._font,
                               fill="gray",
                               anchor="w",
                               tag=('actionname',self.tag()))
        canvas.create_text(xx,yy,
                           text=action,
                           font=CanvasTransition._font,
                           fill=self.color(),
                           anchor="w",
                           tag=('actionname',self.tag()))

    def drawDestStateOn(self,canvas,x,y):
        r = STATE_RADIUS
        canvas.create_oval(x-r,y-r,x+r,y+r, outline='black',fill='lightyellow', tag=self.tag())
        canvas.create_text(x,y,
                           text="%i"%(self.distance(),),
                           font=CanvasTransition._font,
                           fill='black')#self.color())

    def _stateRadiusOffset(self,x1,y1,x2,y2):
        dx, dy = x2-x1, y2-y1
        le = math.sqrt(dx*dx + dy*dy)
        return dx/le*STATE_RADIUS, dy/le*STATE_RADIUS

    def highlightOn(self,canvas):
        canvas.itemconfigure(self.tag(),fill='red')

    def distance(self):
        d = len(self.temaTransitionsInside)
        return d + self.precedingCanvasTransition.distance()



class InitialTransition(CanvasTransition):
    def __init__(self,temaState):
        self.temaState = temaState
        self.id = 0
    def getTemaPathFromInitialState(self):
        return ()
    def getPathFromInitialState(self):
        return ()
    def distance(self):
        return 0
    def destTemaState(self):
        return self.temaState
    def actionStr(self):
        return "(You are here)"
    @classmethod
    def color(cls):
        return 'red'

class UnintrestingTransition(CanvasTransition):
    def __init__(self,precedingCanvasTransition, temaTransitionsInside):
        CanvasTransition.__init__(self,precedingCanvasTransition,
                                  temaTransitionsInside)
        self.succeedingCanvasTransitions = []
    def addSucceedingTransition(self,t):
        self.succeedingCanvasTransitions.append(t)
    def nextTransitions(self,xxx,yyy):
        return self.succeedingCanvasTransitions
    def __str__(self):
        return "%s" % (self.temaTransitionsInside,)
    def actionStr(self):
        return ""
        return "(%i)" % (len(self.temaTransitionsInside),)
    @classmethod
    def isStart(cls,t):
        return True
    @classmethod
    def color(cls):
        return 'gray'
    @classmethod
    def buttonText(cls):
        return "xxx"
    def drawArrowOn(self,canvas,x1,y1,x2,y2):
        dx = x2-x1
        dy = y2-y1
        xi1 = x1+dx*0.33
        xi2 = x1+dx*0.66
        yi1 = y1+dy*0.1
        yi2 = y1+dy*0.9
        ox, oy = self._stateRadiusOffset(x1,y1,x2,y2)
        canvas.create_line(x1+ox,y1+oy,xi1,yi1,xi2,yi2,x2-ox,y2-oy,
                           arrow='last',
                           joinstyle=Tkinter.ROUND,
                           dash=(8,2),
                           smooth=1,
                           fill=self.color(),
                           tag=('arrow',self.tag()))

class AnyTransition(CanvasTransition):
    @classmethod
    def isStart(cls,t):
        return True
    @classmethod
    def color(cls):
        return 'grey30'
    @classmethod
    def buttonText(cls):
        return "Other"

class ActivatesTransition(CanvasTransition):
    @classmethod
    def isStart(cls,t):
        strAct = str(t.getAction())
        return ' ACTIVATES ' in strAct
    @classmethod
    def color(cls):
        return 'darkorange'
    @classmethod
    def buttonText(cls):
        return "ACTIVATES"

class AllowTransition(CanvasTransition):
    @classmethod
    def isStart(cls,t):
        strAct = str(t.getAction())
        return ' ALLOWS ' in strAct or ' WAS ALLOWED' in strAct
    @classmethod
    def color(cls):
        return 'brown'
    @classmethod
    def buttonText(cls):
        return "ALLOWS"

class CommentTransition(CanvasTransition):
    @classmethod
    def isStart(cls,t):
        strAct = str(t.getAction())
        splitted = strAct.split(':',1)
        return len(splitted) == 2 and splitted[1].strip().startswith('--')
    @classmethod
    def color(cls):
        return 'darkviolet'
    def modelAndAction(self):
        model,act = self.actionStr().split(':',1)
        model += ':'
        return model,act
    def drawOn(self,canvas,x1,y1,x2,y2):
        self.drawArrowOn(canvas,x1,y1,x2,y2)
        model,action = self.modelAndAction()
        self.drawActionOn(canvas,x1,y1,x2,y2,action,model)
        self.drawDestStateOn(canvas,x2,y2)
    @classmethod
    def buttonText(cls):
        return "Comment"

class StartEndTransition(CanvasTransition):

    @classmethod
    def getListOfContents(cls,firstTransition):
        assert cls.isStart(firstTransition)
        ps = findPathsToTransitions(firstTransition.getDestState(),
                                    lambda t: cls.isEnd(t), 1000)

        return [tuple((firstTransition,)+p) for p,T in ps]

    def containedKeywords(self):
        return [str(t.getAction()) for t in self.temaTransitionsInside if _isKeyword(t)]

    def drawOn(self,canvas,x1,y1,x2,y2):
        self.drawArrowOn(canvas,x1,y1,x2,y2)
        model,action = self.modelAndAction()
        self.drawActionOn(canvas,x1,y1,x2,y2,action,model)
        self.drawDestStateOn(canvas,x2,y2)


class AWTransition(StartEndTransition):
    @classmethod
    def isStart(cls,t):
        strAct = str(t.getAction())
        return 'start_aw' in strAct
    @classmethod
    def isEnd(cls,t):
        strAct = str(t.getAction())
        return 'end_aw' in strAct

    def modelAndAction(self):
        model,act = self.actionStr().split(':',1)
        model += ':'
        act = act.replace('start_aw','aw',1)
        kwStr = "; ".join([kw for kw in self.containedKeywords()])
        act += (" (%s)" % (_toCanvasStr(kwStr),))
        return model,act
    @classmethod
    def buttonText(cls):
        return "AW(kw's)"
    @classmethod
    def color(cls):
        return 'black'

class SVTransition(StartEndTransition):
    @classmethod
    def isStart(cls,t):
        strAct = str(t.getAction())
        return 'start_sv' in strAct
    @classmethod
    def isEnd(cls,t):
        strAct = str(t.getAction())
        return 'end_sv' in strAct

    @classmethod
    def color(cls):
        return 'darkgreen'
    def modelAndAction(self):
        model,act = self.actionStr().split(':',1)
        model += ':'
        act = act.replace('start_sv','sv',1)
        kwStr = "; ".join([kw for kw in self.containedKeywords()])
        act += (" (%s)" % (_toCanvasStr(kwStr),))
        return model,act
    @classmethod
    def buttonText(cls):
        return "SV(kw's)"

def findPathsToTransitions(temaState,transFilterFunc,maxDepth):
    found = []
    seenTrans = set()
    paths = [[t] for t in temaState.getOutTransitions()]
    depth = 0
    while paths and depth < maxDepth:
        newPaths = []
        for p in paths:
            T = transFilterFunc(p[-1])
            if T:
                found.append( (tuple(p),T) )
            else:
                newPaths += [p + [t] for t in
                             p[-1].getDestState().getOutTransitions()
                            if t not in seenTrans]
            seenTrans.add(p[-1])
        paths = newPaths
        depth += 1
    return tuple(found)

def findPathsToNearestTransitionsOfType(temaState,TransitionTypes,maxDepth):
    def transFilter(t):
        for T in TransitionTypes:
            if T.isStart(t):
                return T
        return None
    return findPathsToTransitions(temaState,transFilter,maxDepth)

def groupPathsToLast(paths):
    d = {}
    for p,T in paths:
        pathToLast = p[:-1]
        last = p[-1]
        if pathToLast in d:
            d[pathToLast].append( (last,T) )
        else:
            d[pathToLast] = [(last,T)]
    return d


def transitionsFromState(temaState,TransitionTypes,maxDepth,prev=None):
    tpaths = findPathsToNearestTransitionsOfType(temaState,
                                                 TransitionTypes,
                                                 maxDepth)
    ttt = []
    for ptl,lt in groupPathsToLast(tpaths).iteritems():
        if ptl:
            uit = UnintrestingTransition(prev,ptl)
            for last,T in lt:
                conts = T.getListOfContents(last)
                for c in conts:
                    uit.addSucceedingTransition( T(uit,c) )
            ttt.append(uit)
        else:
            for last,T in lt:
                conts = T.getListOfContents(last)
                for c in conts:
                    ttt.append( T(prev,c) )
    return ttt


_debug = file("_debug.txt",'w')
def debug(s):
    _debug.write(s+'\n')

class ModelGui:
    """ModelGui let's the user to
        1) click transitions to be executed next
            - selectPath
        2) decide whether to execute positive or negative action
            - executePosOrNeg
    """
    _MODES = (SELECT_PATH, CHOOSE_NEG_OR_POS, PASSIVE) = range(3)

    def __init__(self, w, h):
        self._w,self._h = w,h
        self._root = Tkinter.Tk()
        self._root.title(string="ModelGui")
        self._font1 = tkFont.Font(family='Arial',size=9)
        self._font2 = tkFont.Font(family='Arial',size=10, weight='bold')
        CanvasTransition._font = tkFont.Font(family='Arial',size=8)

        self._createSideBar()
        self._createSettingsBar()
        self._createInfoBar()
        #self._createInfoBar2()
        self._createQuestionAskingBar()
        self._createCanvas()


        self._drawnFromState = None
        self._props = None


    def _createSideBar(self):
        frame = Tkinter.Frame(self._root)
        frame.grid(column=2,row=2,sticky='ns')

        hasFrame = Tkinter.Frame(frame)
        hasFrame.pack()
        hasLabel = Tkinter.Label(hasFrame,text="HAS:")
        hasLabel.pack(side=Tkinter.LEFT)
        self._spHasText = Tkinter.Entry(hasFrame)
        self._spHasText.pack(side=Tkinter.LEFT,expand=True)

        notFrame = Tkinter.Frame(frame)
        notFrame.pack()
        notLabel = Tkinter.Label(notFrame,text="NOT:")
        notLabel.pack(side=Tkinter.LEFT)
        self._spNotText = Tkinter.Entry(notFrame)
        self._spNotText.insert(0,'SleepState')
        self._spNotText.pack(side=Tkinter.LEFT,expand=True)

        spButton = Tkinter.Button(frame,text="Filter state propositions",
                                 command=self._spChanged)
        spButton.pack()

        self._spList = Tkinter.Listbox(frame)
        self._spList.pack(fill=Tkinter.BOTH,expand=True)



    def _createSettingsBar(self):
        frame = Tkinter.Frame(self._root)
        frame.grid(column=1,row=3,sticky='we')

        Tkinter.Label(frame,font=self._font1,
                      text="View transitions:").pack(side=Tkinter.LEFT)

        TTypes = [(AWTransition,1),
                  (SVTransition,0),
                  (ActivatesTransition,0),
                  (AllowTransition,0),
                  (CommentTransition,0),
                  (AnyTransition,0)]

        self._transitionButtons = []
        for TT,initval in TTypes:
            var = Tkinter.IntVar()
            var.set(initval)
            b = Tkinter.Checkbutton(frame,font=self._font1,text=TT.buttonText(),
                                    variable=var, fg=TT.color(),
                                    command=self._transitionTypesChanged)
            self._transitionButtons.append( (TT,b,var) )

        for T,b,v in self._transitionButtons:
            b.pack(side=Tkinter.LEFT)


        self._depthVar = Tkinter.IntVar()
        self._depthVar.set(DEPTH_DEFAULT)
        Tkinter.Frame(frame,width=25).pack(side=Tkinter.LEFT)
        Tkinter.Label(frame,font=self._font1,
                      text="Search transitions till depth",
                      anchor='e'
                     ).pack(side=Tkinter.LEFT)
        Tkinter.Scale(frame,font=self._font1,from_=DEPTH_MIN, to=DEPTH_MAX,
                      orient=Tkinter.HORIZONTAL,
                      variable=self._depthVar, command=self._depthChanged
                      ).pack(side=Tkinter.LEFT)

    def _createInfoBar(self):
        frame = Tkinter.Frame(self._root)
        frame.grid(column=1,row=4,sticky='we')

        self._infoText = Tkinter.StringVar()
        label = Tkinter.Label(frame, font=self._font1,
                              textvariable=self._infoText)
        label.pack(side=Tkinter.LEFT)

    def _createInfoBar2(self):
        frame = Tkinter.Frame(self._root)
        frame.grid(column=1,row=5,sticky='we')

        self._infoText2 = Tkinter.StringVar()
        label = Tkinter.Label(frame, font=self._font1,
                              textvariable=self._infoText2)
        label.pack(side=Tkinter.LEFT)

    def _createQuestionAskingBar(self):
        self._frame1 = Tkinter.Frame(self._root,background='yellow')
        self._frame1.grid(column=1,row=1,sticky='we')
        Tkinter.Label(self._frame1,font=self._font1,bg='yellow',
                      text="Execute positive or negative action:"
                     ).grid(column=1,row=1,sticky='w')
        self._question = Tkinter.StringVar()
        Tkinter.Label(self._frame1,font=self._font2,
                      anchor="w",wraplength=self._w-200,
            background='yellow',textvariable=self._question
        ).grid(column=2,row=1,sticky='')
        self._posButton = Tkinter.Button(self._frame1,text="Positive",
                                         command=self._answeredPositive)
        self._posButton.grid(column=3,row=1,sticky='')
        self._negButton = Tkinter.Button(self._frame1,text="Negative (~)",
                                          command=self._answeredNegative)
        self._negButton.grid(column=4,row=1,sticky='')
        self._frame1.columnconfigure(2,weight=1)
        self._frame1.rowconfigure(1,pad=5)
        self._frame1.columnconfigure(2,pad=5)
        self._frame1.columnconfigure(3,pad=5)

    def _createCanvas(self):
        self._frame2 = Tkinter.Frame(self._root)
        self._frame2.grid(column=1,row=2,sticky='wens')
        self._frame2.rowconfigure(1,weight=1)
        self._frame2.columnconfigure(1,weight=1)
        self._modelCanvas = Tkinter.Canvas(self._frame2,
                                           width=self._w,height=self._h,
                                           background='white')
        self._modelCanvas.grid(column=1,row=1,sticky='wens')
        self._modelCanvas.bind('<Button-1>',self._mouse1clicked)
        self._modelCanvas.bind('<Key>',self._keyPressed)

        self._root.columnconfigure(1,weight=1)
        self._root.rowconfigure(2,weight=1)

        self._modelCanvas.focus_set()

    def _clearModelCanvas(self):
        self._modelCanvas.delete('all')

    def _setMode(self,mode):
        if mode==ModelGui.SELECT_PATH:
            self._frame1.grid_forget()
            self.setInfo("Left click a transition to select a path. Arrows to scroll.")
        elif mode==ModelGui.PASSIVE:
            self._frame1.grid_forget()
        elif mode==ModelGui.CHOOSE_NEG_OR_POS:
            self._frame1.grid(row=1,column=1,sticky='we')
        self._mode = mode

    def _spChanged(self):
        self._filterProps()
        self._modelCanvas.focus_set()

    def _filterProps(self):
        hasText = self._spHasText.get()
        notText = self._spNotText.get()
        reHas = re.compile(hasText)
        reNot = re.compile(notText)
        self._spList.delete(0,Tkinter.END)
        for p in self._props:
            if ((not hasText or reHas.search(p)) and
                (not notText or not reNot.search(p))):
                self._spList.insert(Tkinter.END,p)

    def _transitionTypesChanged(self):
        self._updateTransitionTypes()
        self.draw(self._drawnFromState)

    def _updateTransitionTypes(self):
        TTs = []
        for T,b,v in self._transitionButtons:
            if v.get():
                TTs.append(T)
        self.TransitionTypes = TTs

    def _updateStateProps(self,from_state):
        props = [str(sp) for sp in from_state.getStateProps()]
        propsSet = set(props)
        uniqProps = [p for p in propsSet]
        uniqProps.sort()
        self._props = uniqProps
        self._filterProps()

    def _depthChanged(self,e):
        self.draw(self._drawnFromState)

    def _answeredPositive(self):
        self.answer = True
        self._root.quit()
    def _answeredNegative(self):
        self.answer = False
        self._root.quit()

    def _keyPressed(self,e):
        key = e.keysym.lower()
        step = 50
        if key in ('down',):
            self._modelCanvas.move('all',0,-step)
        elif key in ('up',):
            self._modelCanvas.move('all',0,step)
        elif key in ('right',):
            self._modelCanvas.move('all',-step,0)
        elif key in ('left',):
            self._modelCanvas.move('all',step,0)
        else:
            pass

    def _mouse1clicked(self,e):
        self._modelCanvas.focus_set()
        if self._mode != ModelGui.SELECT_PATH:
            return
        x = self._modelCanvas.canvasx(e.x)
        y = self._modelCanvas.canvasx(e.y)
        t = self._transitionIn(x,y)
        if t is None:
            return

        self.modelPath = t.getTemaPathFromInitialState()
        for tranInPath in t.getPathFromInitialState():
            tranInPath.highlightOn(self._modelCanvas)

        self._setMode(ModelGui.PASSIVE)
        self._root.after(500,self._root.quit)

    def _transitionIn(self,x,y):
        r = 50
        closest = self._modelCanvas.find_overlapping(x-r,y-r,x+r,y+r)
        if len(closest) == 0:
            return None
        elif len(closest) == 1:
            closest = closest[0]
        else:
            closest = self._modelCanvas.find_closest(x,y)

        for t in self._modelCanvas.gettags(closest):
            tr = _tranByTag(t)
            if tr is not None:
                return tr
        return None

    def _drawFromTrans(self,t,x,y,x2,y2,maxDepth):
        t.drawOn(self._modelCanvas,x,y,x2,y2)
        y3 = y2 + TRAN_LEN_Y
        distanceToGo = maxDepth - t.distance()
        hasChildren = False
        if distanceToGo > 0:
            for nt in t.nextTransitions(self.TransitionTypes,distanceToGo):
                hasChildren = True
                y3 = self._drawFromTrans(nt,x2,y2,x2+TRAN_LEN_X,y3,maxDepth)
        if hasChildren:
            return y3
        else:
            return y3+TRAN_LEN_Y


    def draw(self,from_state):
        """Draws the model starting from the given state up to the given depth.
        """
        self._updateStateProps(from_state)
        self._clearModelCanvas()
        self._updateTransitionTypes()

        initial = InitialTransition(from_state)

        self._drawFromTrans(initial,20,20,20+TRAN_LEN_X,20+TRAN_LEN_Y,
                            self._depthVar.get())
        self._drawnFromState = from_state

    def setInfo(self, infoText):
        """Sets the info text."""
        self._infoText.set(infoText.decode('ascii','ignore'))

    def setInfo2(self, infoText):
        """Sets the info text."""
        self._infoText2.set(infoText)

    def selectPath(self,from_state):
        """Lets the user select a path with a mouse."""
        self._setMode(ModelGui.SELECT_PATH)
        self.draw(from_state)
        self._root.mainloop()
        self._setMode(ModelGui.PASSIVE)
        return self.modelPath

    def executePosOrNeg(self,actionname,pos=True,neg=True):
        """ Lets the user decide whether to execute positive or negative
            version of the given transition.
        """
        self._setMode(ModelGui.CHOOSE_NEG_OR_POS)
        self._modelCanvas.itemconfigure('state',fill='gray')
        q = "Adapter asks: execute a positive or negative '''%s'''?"\
            % actionname.decode('ascii','ignore')
        self.setInfo(q)
        self._question.set(actionname.decode('ascii','ignore'))

        if pos:
            pos_state = Tkinter.NORMAL
        else:
            pos_state = Tkinter.DISABLED

        if neg:
            neg_state = Tkinter.NORMAL
        else:
            neg_state = Tkinter.DISABLED

        self._posButton.config(state = pos_state )
        self._negButton.config(state = neg_state )

        self._root.mainloop()

        self._setMode(ModelGui.PASSIVE)
        return self.answer


    def stepTo(self,state):
        """Just draws the model starting from a given state.
        """
        self.draw(state)

