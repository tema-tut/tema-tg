# -*- coding: iso-8859-1 -*-

svg_preample =\
r'''<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'''

# See: http://groups.yahoo.com/group/svg-developers/message/48562
# svg_preample = ""

class SVG_file(object):
    def __init__(self, stream, size):
        self.__handle = stream
        self.__env_stack=[]
        print >> self.__handle, svg_preample
        base_tags=dict(size)
        base_tags['version']="1.1"
        base_tags['baseProfile']="full"
        base_tags['xmlns']="http://www.w3.org/2000/svg"
        self.begin("svg", base_tags)
        
    def close(self):
        self.end()
        if self.__env_stack :
            raise Exception, ("There are open environments", self.__env_stack)

    def __element(self, tag, params, standalone):
        tag_stack = [tag]
        for name, value in params.iteritems():
            tag_stack.append(name+'="'+str(value)+'"')
        beginmark = "<"
        endmark=">"
        if standalone:
            endmark = " />"
        print >> self.__handle,\
              beginmark + " ".join(tag_stack) + endmark
    def element(self, tag, params={}):
        self.__element(tag,params, True)
    def begin(self, tag, params={}):
        self.__env_stack.append(tag)
        self.__element(tag,params, False)

    def end(self):
        tag = self.__env_stack.pop()
        self.__element("/"+tag, {}, False)
    def raw(self, data):
        print >> self.__handle, data
    def plain_text(self, text):
        self.raw("<![CDATA["+text+"]]>")


