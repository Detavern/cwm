#!/usr/bin/python 
"""
Trigonometrical Built-Ins for CWM

Allows CWM to do do trigonometrical
http://www.python.org/doc/2.3/lib/module-math.html

This module is inspired by the math module.
See http://www.w3.org/2000/10/swap/cwm_math.py

cf. http://www.w3.org/2000/10/swap/cwm.py
See http://ilrt.org/discovery/chatlogs/rdfig/2003-09-23.html#T22-37-54
http://rdfig.xmlhack.com/2003/09/23/2003-09-23.html#1064356689.846120

"""

__author__ = 'Karl Dubost'
__cvsid__ = '$Id: cwm_trigo.py,v 1.1 2003-09-23 23:25:26 kdubost Exp $'
__version__ = '$Revision: 1.1 $'

import sys, string, re, urllib, math

from term import LightBuiltIn, Function, ReverseFunction
import types

# from RDFSink import DAML_LISTS, RDF_type_URI, DAML_sameAs_URI

MATH_NS_URI = 'http://www.w3.org/2000/10/swap/math#'

from diag import progress
import sys, traceback

def obsolete():
    progress("Warning: Obsolete math built-in used.")
    traceback.print_stack()

def tidy(x):
    #DWC bugfix: "39.03555" got changed to "393555"
    if x == None: return None
    s = str(x)
    if s[-2:] == '.0': s=s[:-2]
    return s


def isString(x):
    # in 2.2, evidently we can test for isinstance(types.StringTypes)
    return type(x) is type('') or type(x) is type(u'')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Trigonometrical Features
#
#
# Light Built-in classes - these are all reverse functions

# sinus, cosinus

def numeric(s):
    if type(s) == types.IntType or type(s) is types.FloatType: return s
    if s.find('.') < 0 and s.find('e') < 0 : return int(s)
    return float(s)

class BI_acos(LightBuiltIn, Function):
	"""
	acos (x)
	Return the arc cosine of x.
	"""
    def evaluateObject(self, subj_py):
	return acos(numeric(subj_py))

class BI_asin(LightBuiltIn, Function):
	"""
	asin (x)
	Return the arc sine of x.
	"""
    def evaluateObject(self, subj_py):
	return asin(numeric(subj_py))

class BI_atan(LightBuiltIn, Function):
	"""
	atan (x)
	Return the arc tangent of x.
	"""
    def evaluateObject(self, subj_py):
	return atan(numeric(subj_py))

class BI_atan2(LightBuiltIn, Function):
	"""
	atan2 (y,x)
	Return atan(y/x).
	"""
    def evaluateObject(self, subj_py): 
        if len(subj_py) == 2:
	    return atan2(numeric(subj_py[0]) - numeric(subj_py[1]))

class BI_cos(LightBuiltIn, Function):
	"""
	cos (x)
	Return the cosine of x.
	"""
    def evaluateObject(self, subj_py):
	return cos(numeric(subj_py))

class BI_cosh(LightBuiltIn, Function):
	"""
	cosh (x)
	Return the hyperbolic cosine of x.
	"""
    def evaluateObject(self, subj_py):
	return cosh(numeric(subj_py))

class BI_degrees(LightBuiltIn, Function):
	"""
	degrees (x)
	Converts angle x from radians to degrees.
	"""
    def evaluateObject(self, subj_py):
	return degrees(numeric(subj_py))

class BI_radians(LightBuiltIn, Function):
	"""
	radians (x)
	Converts angle x from degrees to radians.
	"""
    def evaluateObject(self, subj_py):
	return radians(numeric(subj_py))

class BI_sin(LightBuiltIn, Function):
	"""
	sin (x)
	Return the sine of x.
	"""
    def evaluateObject(self, subj_py):
	return sin(numeric(subj_py))

class BI_sinh(LightBuiltIn, Function):
	"""
	sinh (x)
	Return the hyperbolic sine of x.
	"""
    def evaluateObject(self, subj_py):
	return sinh(numeric(subj_py))

class BI_tan(LightBuiltIn, Function):
	"""
	tan (x)
	Return the tan of x.
	"""
    def evaluateObject(self, subj_py):
	return tan(numeric(subj_py))

class BI_tanh(LightBuiltIn, Function):
	"""
	tanh (x)
	Return the hyperbolic tangent of x.
	"""
    def evaluateObject(self, subj_py):
	return tanh(numeric(subj_py))

#  Register the string built-ins with the store

def register(store):
    str = store.internURI(MATH_NS_URI[:-1])
    str.internFrag('acos', BI_acos)
    str.internFrag('asin', BI_asin)
    str.internFrag('atan', BI_atan)
    str.internFrag('atan2', BI_atan2)
    str.internFrag('cos', BI_cos)
    str.internFrag('cosh', BI_cosh)
    str.internFrag('degrees', BI_degrees)
    str.internFrag('radians', BI_radians)
    str.internFrag('sin', BI_sin)
    str.internFrag('sinh', BI_sinh)
    str.internFrag('tan', BI_tan)
    str.internFrag('tanh', BI_tanh)
 
if __name__=="__main__": 
   print string.strip(__doc__)
