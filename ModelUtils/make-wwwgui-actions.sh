#!/bin/bash
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


# for f in *.info; do

#     APPLICATION=`gawk '/APPLICATION:/{print $2}' < "$f"`
#     if [ -z "$APPLICATION" ]; then continue; fi

#     MODELCOMPONENT=${f/.info/}

#     if [ ! -f "$MODELCOMPONENT.lsts" ]; then continue; fi

#     gawk -F\" -v A="$APPLICATION" -v MC="$MODELCOMPONENT" '/[0-9]+ = "aw/{print A";"MC";end_"$2";"}/[0-9]+ = "~aw/{print A";"MC";~end_"$2";"}' < "$MODELCOMPONENT.lsts" | sed 's/~end_~/~end_/g'

# done


# make rules.ext, kun ACTIONMACHINES=ALL
gawk '/[0-9]+=/{
    split($0,a,"=");
    proc=substr(a[2],2,length(a[2])-12);
    num_to_proc[a[1]]=proc;
    cmd="echo `egrep ^APPLICATION: "proc".info 2>/dev/null | cut -b 13-`";
    cmd | getline app;
    proc_to_app[proc]=app;
}
/->.*end_aw/{
    split($0,aws,")");
    stripped=substr(aws[1],2,length(aws[1])-2);
    split(stripped,a,",\"");
    proc=num_to_proc[a[1]]; aw=a[2]; app=proc_to_app[proc];
    if (app != "") print app";"proc";"aw";"
    else print "Z "proc";"proc";"aw";"
}
' < rules.ext | gawk -F\; '{print $1";"$3";"$2}' | sort \
| gawk -F\; '{print $1";"$3";"$2}'
