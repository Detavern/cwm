"""
Main LX package import point.

We import most modules here, so users can just use LX.Foo instead of
LX.foo.Foo.  That means we have to be more careful about naming
conflicts, but it also gives us more freedom to move code between
files without affecting the API.
"""
__version__ = "$Revision: 1.3 $"
# $Id: __init__.py,v 1.3 2002-08-29 21:02:13 sandro Exp $

# To allow "from LX import *", though I'm not sure when/why one would
# want that.
__all__ = ["operator", "language", "formula", "term", "kb"] 

# Let people use LX.Formula instead of LX.formula.Formula, etc, while
# having these parts in separate files
from LX.operator import *
from LX.term import *
from LX.formula import *
from LX.kb import *
from LX.describer import *

from LX.namespace import *
rdfns  = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns",
                   ["type", "nil", "first", "rest"])
lxns   = Namespace("http://www.w3.org/2002/08/LX/RDF/v2", strict=0)



# $Log: __init__.py,v $
# Revision 1.3  2002-08-29 21:02:13  sandro
# passes many more tests, esp handling of variables
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

  