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

import re

class ExtRulesParser:
    def parseLstsFiles(self,rules_file_contents):
        """Parse the lsts files in the given string. The string is
        assumed to be in TVT extended rules format, that is
        <lsts#1> = "<lstsfilename1>"
        <lsts#2> = "<lstsfilename2>"
        ...
        Returns list of numbers and lsts filenames:
        [ (lsts#1, "lstsfilename1"), (lsts#2, "lstsfilename2"), ... ]
        """
        procrowre = re.compile('\s*([-/_a-zA-Z0-9%]+)\s*=\s*"([^"]+)"')
        lstss = []
        for line in rules_file_contents.split('\n'):
            s = line.strip()
            m = procrowre.match(s)
            if not m: continue # line is not a process row
            lstss.append( (m.group(1),m.group(2)) )

        return lstss
    
    def parseRules(self,rules_file_contents):
        """Parse the rules in the given string. Assumes that the
        string is in TVT extended rules format with one rule per
        row. That is,
        (<lsts#1>,"<actname1>") (<lsts#2>,"<actname2>") ... -> "<resultname>"
        Returns the rules in a list of lists:
        [
          [ (lsts#11,"actname11"), (lsts#12,"actname12"), ..., "resultname1" ],
          [ (lsts#21,"actname21"), (lsts#22,"actname22"), ..., "resultname2" ],
          ...
         ]
        """
        rulerowre = re.compile('^\s*([0-9]*\(.*\))\s*->\s*"([^"]+)"\s*$')
        # single syncronisating action on the left hand side of "->"
        syncactre = re.compile('\(\s*([^,\s]*)\s*,\s*"([^"]+)"\s*\)')

        allrules=[]
        
        for line in rules_file_contents.split('\n'):
            s = line.strip()
            m = rulerowre.match(s)
            if not m: continue # this line does not contain a rule
            rule=[]
            for lstsnum,actname in syncactre.findall(m.group(1)):
                # find all actions in the left hand side of "->"
                rule.append( (lstsnum,actname) )
            rule.append(m.group(2))
            allrules.append(rule)

        return allrules
