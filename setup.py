#!/usr/bin/env python
# borrowing liberally from Eikeon's setup.py for rdflib
# an attempt at a setup.py installer for Cwm/SWAP
# version: $Id: setup.py,v 1.3 2004-07-16 17:44:31 syosi Exp $
# by Dan Brickley <danbri@w3.org>
#
# STATUS: not working yet
# 
# notes:
# http://esw.w3.org/t/view/ESW/CwmTips

# current output / error:
#	sudo ./setup.py install
#	swap dir: /usr/lib/python2.2/site-packages/swap
#	running install
#	running build
#	running build_py
#	error: package directory 'swap/swap/cwm' does not exist


from distutils.sysconfig import get_python_lib
from os import rename
from os.path import join, exists
from time import time

lib_dir = get_python_lib()
swap_dir = join(lib_dir, "swap")
print "swap dir: "+swap_dir


if exists(swap_dir):
    backup = "%s-%s" % (swap_dir, int(time()))
    print "Renaming previously installed rdflib to: \n  %s" % backup
    rename(swap_dir, backup)



# Install SWAP
from distutils.core import setup
#from swap import __version__
__version__='0.8.0'
setup(
    name = 'cwm',
    version = __version__,
    description = "Semantic Web Area for Play",
    author = "TimBL, Dan Connolly and contributors",
    author_email = "timbl@w3.org",
    maintainer = "Tim Berners-Lee",
    maintainer_email = "timbl@w3.org",
    url = "http://www.w3.org/2000/10/swap/",
    package_dir = {'swap': 'swap'},
    packages = ['swap'],
    scripts = ['cwm.py'],
   )
    # todo, figure out which other modules are in public APIs
    # --danbri



#,'swap.cwm','swap.RDFSink','swap.llyn'],
#		'swap.RDFSink',
#		'swap.llyn'],
#    packages = ['swap.cwm',
#		'swap.RDFSink',
#		'swap.llyn'],
#    package_dir = {'': 'swap'},
