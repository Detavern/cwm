#  Export Outlook data to N3 - and synch and import?!!

# An attempt to se how one can get into MS Outlook from Python
# Ideal - to export to RDF.

# To do:
#
# Check Date format vs ISO/XML date

#-----------------------------------------------------

# Refs:
# http://www.oreilly.com/catalog/pythonwin32/chapter/ch12.html

# Derived from
# <http://www.w3.org/Tools/1998/07contactlog/contactlog.py>
# Dan writes:
# This code sort of works, at least to demonstrate python/Outlook
# integration. I got through two of the categories of stylized
# data that I keep in my Pilot Address book (caller-id info,
# and business cards; the others are email, post, etc.)
# Then I got bored.
# Especially watch out for stuff marked with @@.
#
# But I'm documenting it carefully,
# because I've been looking for these clues for
# *months* and I don't want to lose them.
# And I'm releasing it. Share and Enjoy.

# Dan Connolly
# <connolly@w3.org>
# http://www.w3.org/People/Connolly/

# Copyright � 1998 World Wide Web Consortium,
# (Massachusetts Institute of Technology, Institut National de
# Recherche en Informatique et en Automatique, Keio University). All
# Rights Reserved. 
#
# Permission to use, copy, modify, and distribute this software
# and its documentation for any purpose and without fee or
# royalty is hereby granted, per the terms and conditions in
#
# W3C IPR SOFTWARE NOTICE
# http://www.w3.org/COPYRIGHT
# September 1997 

# This module depends on standard and built-in python modules, per
# Python Library Reference
#                        April 14, 1998
#                        Release 1.5.1
# http://www.python.org/doc/lib/lib.html

import string, StringIO

# It also uses the win32com package
# maintained by Mark Hammond
# http://www.python.org/windows/win32com/
#
# specifically, as documented in
# PythonWin Help
# Help file built: 04/26/98
# available in http://www.python.org/windows/win32all/win32all.exe

# Here we bind to the the actual Outlook 98 runtime,
# whose interface is documented in a
# Microsoft help file, "Microsoft Outlook Visual Basic"
#
# I found the help file via the Microsoft Knowledge Base:
#
# "OL98: How to Install Visual Basic Help"
# Last reviewed: April 1, 1998
# Article ID: Q183220
# http://support.microsoft.com/support/kb/articles/q183/2/20.asp

from win32com.client import gencache

PREFIX = "ms:"

DETAILS = [
#		"Attachments" # Links to follow for details we want
#			, "Recipients"
			]
# Many of the fields whicha re available are heuristic reformattings of real data.
# for example: LastFirstSpaceOnly.  Some, like "unread", and "saved" are local and don't have
# a global significance in that form. Some I just don't understand.
# The read-only ones are in general less useful.

BORING = [			# Example value:
  "LastFirstSpaceOnly",     #        "Layman Andrew" ; # r
  "Email2EntryID",          #        "x\000x\000" ; # r
  "Email3EntryID",          #       "0" ; # r
  "MessageClass",           #        "IPM.Contact" ; # rw
  "Class",                  #        "40" ; # r
  "Saved",                  #        "1" ; # r
  "Size",                   #        "228" ; # r
  "LastNameAndFirstName"    #       "Layman, Andrew" ; # r
#  "LastModificationTime:,  #         "2001-04-10T20:33:41Eastern Daylight Time
  "Journal",                #        "0" ; # rw
   "EntryID",               #         "00000000244B683ABE71D211A4D300A02443E5B8E00A02443E5B800000000042F0000F29E49725C70D211A4CE00A02443E5B80000031906020000
   "MAPIOBJECT",            #         <PyIUnknown at 0xcb41d4 with obj at 0x147
   "ConversationTopic",     #         "Andrew Layman" ; # r
   "UnRead",                #                         "0" ; # r
#  ms:FullName                       "Andrew Layman" ; # rw
   "OutlookInternalVersion",         "93821" ; # r
#  CreationTime                   "2001-04-10T20:33:41Eastern Daylight Time
#   "FileAs",                         "Layman, Andrew" ; # rw
#  ms:Email1EntryID                  "x\000x\000" ; # r    @@@@@@@@@@@@
#  ms:Sensitivity                    "0" ; # rw
#  ms:Initials                       "A.L." ; # rw
#  ms:Subject                        "Andrew Layman" ; # rw
  "LastFirstNoSpace",               "LaymanAndrew" ; # r
#  ms:Email1DisplayName              "Andrew Layman (E-mail)" ; # r
#  ms:Importance                     "1" ; # r
#  ms:SelectedMailingAddress         "0" ; # r
  "NoAging",                        "0" ; # r
  ms:Email3DisplayName              "Andrew Layman (E-mail 3)" ; # r
  ms:OutlookVersion                 "9.0" #  ConversationIndex  cannot be rea	    
	    
	    
BORING = [ ]
OTHERS = ["Size", "OutlookInternalVersion", "NetMeetingAutoStart", "OutlookVersion",
			"FormDescription",
			"StoreID", "EntryID",  # UUIDs mess up the file but might be useful
			"ConversationIndex",   # Cannot be read for some reason
			]

# The following lines are generated by makepy
#
#Outlook 98 Type Library
# {00062FFF-0000-0000-C000-000000000046}, lcid=0, major=8, minor=5
# Use these commands in Python code to auto generate .py support
#outlook = gencache.EnsureModule('{00062FFF-0000-0000-C000-000000000046}', 0, 8, 5)

# Try python /Python16/win32com/client/makepy.py -i -d to get the magic numbers:
# This is for Outlook 2000 9.0:
outlook = gencache.EnsureModule('{00062FFF-0000-0000-C000-000000000046}', 0, 9, 0)

# The only namespace supported in Outlook '98
# see "Microsoft Outlook Visual Basic"
MAPI = "MAPI"


# Hard-coded configuration
# probably should use sys.argv, but I didn't bother...
Inf = "C:\\winnt\\profiles\\connolly\\desktop\\980728pilot-addr.txt"

# for other folks to do testing, here are a couple lines from that file:
_test_data = \
"""Last Name	First Name	Job Title	Company	Business Phone	Home Phone	Business Fax	Other Phone	E-mail	Street Address	City	State	Zip/Postal Code	Country	Location	Birthday	User Field 1	User Field 2	User Field 3	Private	Categories
"AAbrahamson"	"Dr. David M"			"+353-1-608-1716"				"cavid@cs.tcd.ie"	"Trinity College"	"Dublin 2, Ireland"						"1996-11"		"lunch 96-11-13 ISO HTML Boston lunch"	"0"	"Business Card"
"""

def main():
	oapp = outlookToN3()

	_version = "$Id: lookout.py,v 1.7 2001-09-07 02:11:20 timbl Exp $"[1:-1]

	print "# Outlook data extractded by"
	print "#   ", _version
	print "#"
	print "@prefix", PREFIX, "<http://www.w3.org/2000/10/swap/pim/mso.n3#>."
	print "@prefix util: <http://www.w3.org/2000/10/swap/util.n3#>."
	print
#	print "# Calendar:"
#	oapp.getFolder(outlook.constants.olFolderCalendar, [])
	
	print "# Contacts:"
	oapp.getFolder(outlook.constants.olFolderContacts, [
#		"Attachments" , # Links to follow for details we want
			"Recipients" ]
			)

	print "# ENDS"
	


# DWC: outlook.Application is the Application class, per
# the type library and help file cited above.
#
# It integrates completely seamlessly into the python
# object model.
#
# Hence, for methods such as GetNamespace, see
# the help file. I found the following article quite
# helpful as well. The examples are in visual basic, but
# the translation to python is straightforward.
#
# The Microsoft Outlook 97 Automation Server Programming Model
#  Last Updated: June 26, 1998 
# http://www.microsoft.com/OutlookDev/Articles/Outprog.htm
#

# Note this is a copy of the version in notation3.py:
def stringToN3(str):
	res = ""
	if len(str) > 20 and string.find(str, "\n") >=0:
		delim= '"""'
		forbidden = "\\\"\a\b\f\r\t\v"
	else:
		delim = '"'
		forbidden = "\\\"\a\b\f\r\t\v\n"
	for i in range(len(str)):
		ch = str[i]
		j = string.find(forbidden, ch)
		if j>=0: ch = "\\" + '\\\"abfrtvn'[j]
		elif (ch < " " or ch > "}")and ch != "\n": ch= 'x'+`ch`[1:-1] # Use python
		res = res + ch
	return delim + res + delim

def stripCR(str):
	res = ""
	for i in range(len(str)):
		ch = str[i]
		if ch != "\r": res = res + ch
	return res

# For MS Outlook, the convention seems to be CRLF.
# This adds the CRs to a unix-style multiline string just before the LF.
def addCR(str):
	res = ""
	for i in range(len(str)):
		ch = str[i]
		if ch == "\n": res = res + "\r"
		res = res + ch
	return res

def _toString(x):
	""" In N3 everything is represented as a string (at the moment), so we need
	to turn everything into a string without Python encoding.
	"""
	if type(x) is type(' '): return stringToN3(stripCR(x))
	if type(x) is type(6): return '"'+`x`+'"'
	y = `x`
	if y[:5]=="<time":  # Must be better way
		str = x.Format("%Y-%m-%dT%H:%M:%S%z")
		if str[:2] == "45": return ""   # Null date value - must be better way! @@
		return '"'  + str + '"'
	return `x`   # @@@ unhandled things

class outlookToN3(outlook.Application):

	def __init__(self):
		outlook.Application.__init__(self)
		self.internal = []
		self._nextId = 0
		self.details = []   # Set of interesting subfields for this operations
		
	def findContact(self, filter):
		_mapi = self.GetNamespace(MAPI)

#		_c = outlook.OlDefaultFolders.olFolderContacts
		_c = outlook.constants.olFolderContacts
#		contacts = _mapi.GetDefaultFolder(outlook.OlDefaultFolders.olFolderContacts)
		contacts = _mapi.GetDefaultFolder(outlook.constants.olFolderContacts)

		return contacts.Items.Find(filter)

	def getFolder(self, what, details):
		_mapi = self.GetNamespace(MAPI)
		_c = outlook.constants.olFolderCalendar
		self.details = details
		# Result is of type MAPIFolder
		cal = _mapi.GetDefaultFolder(what)
		print "\n# Folder %i:" % what
		self._getItem(cal)
		
		list = cal.Items
		n = len(list)
		if n>0 : print " util:item "
		for i in range(n):
			item = list[i+1] # GetFirst()
			self._getItem(item)
			if i<n-1: print ","
		print "."
			
	def _getItem(self, item, indent=0):
		try:
			gkeys = item._prop_map_get_.keys()
			pkeys = item._prop_map_put_.keys()        # don't in case it sets "changed" bit
#			pkeys = []
		except:
			print "[ a ms:weirdThing ] #", `self`
			return			
		print "\n", "    "*indent, 
		need_semicolon = 0

		key = "EntryID"
		try:
			id = item.__getattr__(key)
			print " <uuid:%s> " % id
		except:
			id = None
			print " [ "

		for k in range(len(gkeys)):
			key = gkeys[k]
			_w = (key in pkeys)		# Is this writable?

			if not _w : pass # print "              # Read only:", key
			try:
				x = item.__getattr__(key)
			except:
				print "# ", key, " cannot be read @@\n    ",
				break
			if x != "" and key not in BORING and key != "EntryID":
				str = _toString(x)
				if str != "" and str[:9] != "<win32com":
					if need_semicolon: print "; %s\n    " %tail, "    "*indent,
					need_semicolon = 1
					if str[:1]=="<":  # Internal structure of some sort
						if 0:
							atts = [] # In case this is an unknown type
							if `x`[:11] != "<PyIUnknown":
								atts = x._prop_map_get_.keys()
							if "EntryID" in atts:
								msid = x.__getattr__("EntryID") or "???"
							else:
								msid = "???"
								print "@@@@@@@@ No EntryID in", `atts`
							

						for ms, f in self.internal:
							if ms is x:
								frag = f
								already = 1
								break
						else:
							self._nextId = self._nextId + 1
							frag = "#_g" + `self._nextId`
							self.internal.append((x, frag)) 
							already = 0
								
						print "%-32s  %s" % (PREFIX+key, str),
						if (not already) and indent < 3 and key in self.details:
							print " = ",
							self._getItem(x, indent+1) # Recurse
					else: # Not a funny internal thingy
						print "%-32s  %s" % (PREFIX+key, str),
					tail = "# rw"
					if not _w : tail = "# r"
		if id : print " ."
		else: print " ] . "
		
	


def iso2vb(isotime):
	# YYYY-MM-DDTHH:MM:SS
	# raises ??? exception when parts are missing?
	year = isotime[:4]
	month = isotime[5:7]
	day = isotime[8:10] or '1' ## @# only month given
	hour = isotime[11:13]
	minute = isotime[14:16]
	second = isotime[17:19]
	ret = month + '/' + day + '/' + year
	if hour and minute:
		ret = ret + ' ' + hour + ':' + minute
		if second:
			ret = ret + ':' + second
	print "@@convdate: ", isotime, ret
	return ret


	
def nextrow(fp):
	# A simple state-machine implementation of Windows
	# tab-delimited file format with quoted fields.
	# I'm not sure if this really
	# does CRLF's right.
	# There are faster ways to do this, I'm sure...
	s = 'start'
	row = ()
	field = ""
	while 1:
		c = fp.read(1)
		if not c:
			if field or len(row):
				raise IOError, "bad end of file"
			return None
		if s == 'start':
			if c == "\n":
				row = row + (field,)
				return row
			elif c == "\t":
				row = row + (field,)
				field = ''
			elif c == '"':
				s = 'quoted'
			else:
				field = field + c
		elif s == 'quoted':
			if c == '"':
				s = 'start'
			elif c == "\\":
				s = 'escaped'
			else:
				field = field + c
		elif s == 'escaped':
			field = field + c
			s = 'quoted'
		else:
			raise RuntimeError, 'bad case'
			
		
if __name__ == '__main__': main()

