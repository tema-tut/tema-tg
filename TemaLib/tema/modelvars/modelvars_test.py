#!/usr/bin/env python

import sys
sys.path[1:1]= ["../.."]

PASS, FAIL = "PASS", "FAIL"



def test_pos(test, input, output):
	verdict = FAIL
	extra = ""
	try:
		all, combs = modelvars.parse_vars(input)
		for vars, vals in output.items():
			result = modelvars.get_values(all, combs, vars)
			if result != set(vals):
				extra = "; (for " + str(vars) + " expected: " + str(set(vals)) + ", got: " + str(result)
				break
		else:
			verdict = PASS
	except:
		pass
	finally:
		print(verdict + ' ' + test + extra)



def test_neg(test, input, exc_type):
	verdict = FAIL
	extra = ""
        try:
                all, combs = modelvars.parse_vars(input)
        except modelvars.ModelVarException, e:
		if isinstance(e, exc_type):
	                verdict = PASS
		else:
			extra = "; expected exception of type " + str(exc_type) + ", got " + str(type(e))
	else:
		extra = "; expected exception of type " + str(exc_type) + ", got none"
        finally:
                print(verdict + ' ' + test + extra)



test, verdict = "import modelvars", FAIL
try:
	import tema.modelvars.modelvars as modelvars
	verdict = PASS
finally:
	print(verdict + ' ' + test)



test_pos("integer values", """
a: ((1,), (2,), (3,))
""", {('a',): [(1,), (2,), (3,)]})

test_pos("string values", """
a: (('x',), ('y',), ('z',))
""", {('a',): [('x',), ('y',), ('z',)]})

test_pos("lists of values", """
a: [['x'], ['y'], ['z']]
""", {('a',): [('x',), ('y',), ('z',)]})

test_pos("complex variable name", """
abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789: ((1,), (2,), (3,))
""", {('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789',): [(1,), (2,), (3,)]})

test_pos("empty file", """""", {})

test_pos("comments", """
# comments are marked with the # sign
a: ((1,), (2,), (3,)) # and
# should not affect the results
""", {('a',): [(1,), (2,), (3,)]})

test_pos("lone value", """
a: ((1,),)
""", {('a',): [(1,)]})

test_pos("no values", """
a:
""", {('a',): []})

test_pos("bare values", """
a: 1, 2, 3
""", {('a',): [(1,), (2,), (3,)]})

test_pos("standalone value", """
a: (1,)
""", {('a',): [(1,)]})

test_pos("bare standalone value", """
a: 1
""", {('a',): [(1,)]})

test_pos("values defined in multiple parts", """
a: 1, 2
a: 2, 3
""", {('a',): [(1,), (2,), (3,)]})

test_pos("independent variables", """
a: 'x', 'y', 'z'
b: 1, 2, 3
""", {('a',): [('x',), ('y',), ('z',)], ('b',): [(1,), (2,), (3,)], ('a','b'): [('x',1), ('x', 2), ('x', 3), ('y', 1), ('y', 2), ('y', 3), ('z', 1), ('z', 2), ('z', 3)]})

test_pos("independent variables, no values", """
a: 'x', 'y', 'z'
b:
""", {('a',): [('x',), ('y',), ('z',)], ('b',): [], ('a','b'): []})

test_pos("interdependent variables, unique values", """
a, b: (('x', 1), ('y', 2), ('z', 3))
""", {('a',): [('x',), ('y',), ('z',)], ('b',): [(1,), (2,), (3,)], ('a','b'): [('x',1), ('y', 2), ('z', 3)]})

test_pos("interdependent variables, repeated values", """
a, b: ('x', 1), ('y', 1), ('z', 1)
""", {('a',): [('x',), ('y',), ('z',)], ('b',): [(1,)], ('a','b'): [('x',1), ('y', 1), ('z', 1)]})

test_pos("standalone multi value", """
a, b: ('x', 1)
""", {('a',): [('x',)], ('b',): [(1,)], ('a','b'): [('x',1)]})

test_pos("bare standalone multi value", """
a, b: 'x', 1
""", {('a',): [('x',)], ('b',): [(1,)], ('a','b'): [('x',1)]})

test_pos("interdependent variables, extra individual values", """
b: 1, 2, 3, 4
a, b: ('x', 1), ('y', 2), ('z', 3)
""", {('a',): [('x',), ('y',), ('z',)], ('b',): [(1,), (2,), (3,), (4,)], ('a','b'): [('x',1), ('y', 2), ('z', 3)]})

test_pos("interdependent variables, limited individual values", """
b: 1, 2
a, b: ('x', 1), ('y', 2), ('z', 3)
""", {('a',): [('x',), ('y',), ('z',)], ('b',): [(1,), (2,)], ('a','b'): [('x',1), ('y', 2)]})

test_pos("interdependent variables, vertical limitations", """
a: 1, 2, 3
a, b: (1, 1), (2, 2)
a, b, c: (1, 1, 1)
""", {('a',): [(1,), (2,), (3,)], ('b',): [(1,), (2,)], ('c',): [(1,)], ('a', 'b'): [(1, 1), (2, 2)], ('a', 'c'): [(1, 1), (2, 1), (3, 1)], ('b', 'c'): [(1, 1), (2, 1)], ('a', 'b', 'c'): [(1, 1, 1)]})

test_pos("interdependent variables, horizontal limitations", """
a, b: (1, 1)
a, c: (2, 2)
b, c: (3, 3)
""", {('a',): [(1,), (2,)], ('b',): [(1,), (3,)], ('c',): [(2,), (3,)], ('a', 'b'): [(1, 1)], ('a', 'c'): [(2, 2)], ('b', 'c'): [(3, 3)], ('a', 'b', 'c'): []})

test_pos("indirect interdependence", """
a, b: (1, 1), (2, 2)
b, c: (1, 1), (2, 2)
""", {('a',): [(1,), (2,)], ('b',): [(1,), (2,)], ('c',): [(1,), (2,)], ('a', 'b'): [(1, 1), (2, 2)], ('a', 'c'): [(1, 1), (1, 2), (2, 1), (2, 2)], ('b', 'c'): [(1, 1), (2, 2)], ('a', 'b', 'c'): [(1, 1, 1), (2, 2, 2)]})

#test_pos("", """""", {('a',): []})

test_neg("no variables", """
: 1, 2, 3
""", modelvars.VarSyntaxException)

test_neg("empty variable name", """
a, , c: (1, 2, 3)
""", modelvars.VarSyntaxException)

test_neg("whitespace in variable name", """
a b: 1, 2, 3
""", modelvars.VarSyntaxException)

test_neg("illegal character in variable name", """
a-b: 1, 2, 3
""", modelvars.VarSyntaxException)

test_neg("unparseable value", """
a: abc
""", modelvars.VarSyntaxException)

test_neg("floating point value", """
a: 1.0
""", modelvars.ValTypeException)

test_neg("too deep tuple value", """
a: (((1,),),)
""", modelvars.ValTypeException)

test_neg("too many values", """
a: ((1, 2),)
""", modelvars.ValCountException)

test_neg("too few values", """
a, b: ((1,),)
""", modelvars.ValCountException)

test_neg("list of different depth values 1", """
a: (1, (2,))
""", modelvars.ValCountException)

test_neg("list of different depth values 2", """
a: ((1,), 2)
""", modelvars.ValCountException)

test_neg("bare values of different depth 1", """
a: 1, (2,)
""", modelvars.ValCountException)

test_neg("bare values of different depth 2", """
a: (1,), 2
""", modelvars.ValCountException)

test_neg("duplicate variables 1", """
a, a: (1, 2)
""", modelvars.DuplicateVarException)

test_neg("duplicate variables 2", """
a, b, c, a: (1, 2, 3, 1)
""", modelvars.DuplicateVarException)
