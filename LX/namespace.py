"""A convenience for handling RDF-style namespaces

TODO: load names from web?
"""
__version__ = "$Revision: 1.2 $"
# $Id: namespace.py,v 1.2 2002-08-29 16:39:55 sandro Exp $

import LX

class Namespace:
    """
    


    """
    def __init__(self, uri, initialNames=[], strict=1, shortForm=None):
        """Provide the namespace URI (without the trailing #)

        If "strict", then names must be added (here or with add())
        before being used.   shortForm is the conventional short form,
        which need not be unique.
        """
        self.uri = uri
        self.strict = strict
        self.shortForm = shortForm
        for name in initialNames:
            self.add(name)

    def add(self, name):
        self.__dict__[name] = LX.URIRef(self.uri + "#" + name)

    def __getattr__(self, name):
        if self.strict:
            msg = ("No name %s declared for namespace %s (in strict mode)" %
                   name, self.uri)
            raise AttributeError, msg
        result = LX.URIRef(self.uri + "#" + name)
        self.__dict__[name] = result
        return result


# $Log: namespace.py,v $
# Revision 1.2  2002-08-29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 