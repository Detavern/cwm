"""Call doctest on all our modules, or something.

"""

__version__ = "$Revision: 1.4 $"
# $Id: test.py,v 1.4 2003-01-29 18:54:02 sandro Exp $

import doctest
import LX
import LX.engine
import LX.language
import html

for x in [ "LX.expr", "LX.engine.otter", "LX.sniff", "html" ]:
    print "Module", "%-25s" %x,
    __import__(x)
    print "failed %3d of %3d tests." % eval("doctest.testmod(%s)" % x)
    
# $Log: test.py,v $
# Revision 1.4  2003-01-29 18:54:02  sandro
# added testing ../html module
#
# Revision 1.3  2003/01/10 21:33:36  sandro
# added sniff.py
#
# Revision 1.2  2003/01/08 17:51:22  sandro
# improved output format
#
# Revision 1.1  2003/01/08 17:48:27  sandro
# test harness for doctest across modules
#