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

"""
Library for reading data tables (CSV exported from Excel).

Usage:

% cat data.csv
key1;value1;value2
% python
>>> import datatable
>>> dt=datatable.DataDict(file('data.csv'))
>>> print dt['key1'][0]
value1
"""

import csv

class DatatableException(Exception): pass

excelDialect=csv.excel()
excelDialect.delimiter=';'

class DataDict(dict):
    def __init__(self,iterable_source):
        r=csv.reader(iterable_source,excelDialect)
        try: self.header=r.next()
        except StopIteration:
            raise DatatableException("Could not read the header of the table")
        for row in r:
            # Remove empty rows
            if len(row) != 0:
                self[row[0]]=row[1:]
