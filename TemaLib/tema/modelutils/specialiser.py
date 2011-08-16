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
Usage: tema.specialiser ModelName.info ModelName.lsts

Opens ModelName.info file, and reads its APPLICATION and
ABSTRACTSOURCE values.

If ABSTRACTSOURCE was not found the program stops. Otherwise, the
corresponding LSTS is loaded. Then, if also APPLICATION was found,
@APPLICATION strings in the action names of the LSTS will be replaced
with the APPLICATION value. If APPLICATION was not found, nothing is
replaced. In any case, the resulting LSTS will be written to
ModelName.lsts file. Existing file will be overwritten. The
program returns 0 on success and 1 on error.
"""

import sys
import os
import tema.lsts.lsts as lsts

class SpecialiserError(Exception): pass

def error(s,exitval=1):
    print >>sys.stderr,"specialiser: %s" % s
    sys.exit(exitval)

def parse_args(argv):

    argv=argv[1:]

    # options
    arg_input_file = None
    arg_output_file = None

    for arg in argv:
        if arg in ["--help","-help","-h"]:
            print __doc__
            sys.exit(1)

    if len(argv)<2:
        print __doc__
        sys.exit(1)

    # input file
    if argv[0]=="-":
        arg_input_file = "-"
    else:
        arg_input_file = argv[0]

    # output file
    if argv[1]=="-": 
        arg_output_file = argv[1]
    else:
        arg_output_file = argv[1]
    return (arg_input_file,arg_output_file)

def specialiser(targetdir,input_fileobj,output_fileobj):

    # Read APPLICATION and ABSTRACTSOURCE tags
    abstract_lsts_name, application_name = None, None

#    for line in file(infofilename):
    for line in input_fileobj:
        if line[:15]=="ABSTRACTSOURCE:":
            abstract_lsts_name=os.path.join(targetdir,line.split(":")[1].strip()+".lsts")

        elif line[:12]=="APPLICATION:":
            application_name=line.split(":")[1].strip()

    if abstract_lsts_name==None: 
        raise SpecialiserError("ABSTRACTSOURCE not found")

    # Open abstract LSTS file
    abslsts=lsts.reader( open(abstract_lsts_name,'r') )
    # the new lsts is based on the abslsts
    newlsts=lsts.writer( lsts_object=abslsts ) 

    # Specialise the abstract LSTS by replacing @APPLICATION with concrete
    # application name in the action names of the LSTS
    newactionnames=[]
    for index,action in enumerate(abslsts.get_actionnames()):
        if application_name!=None and "@APPLICATION" in action:
            newactionnames.append(action.replace('@APPLICATION', application_name))
        else:
            newactionnames.append(action)

    # Write out the specialised LSTS.
    newlsts.set_actionnames(newactionnames)
    newlsts.write( output_fileobj )

if __name__ == "__main__":

    input_filename,output_filename = parse_args(sys.argv)

    infile = None
    outfile = None
    try:
        try:
            if input_filename == "-":
                infile = sys.stdin
            else:
                infile = open(input_filename,'r')
            if output_filename == "-":
                outfile = sys.stdout
            else:
                outfile = open(output_filename,'w')

            specialiser(os.getcwd(),infile,outfile)
        except SpecialiserError,e:
            error(e)
        except KeyboardInterrupt,e:
            sys.exit(1)
        except:
            import traceback
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)
    finally:
        if outfile and output_filename != "-":
            outfile.close()
        if infile and input_filename != "-":
            infile.close()
    
