#!/usr/bin/python
"""

$Id: SqlDB.py,v 1.12 2003-01-14 18:51:48 eric Exp $

"""

#CONTEXT = 0
#PRED = 1  
#SUBJ = 2
#OBJ = 3
CONTEXT = 5
PRED = 0  
SUBJ = 1
OBJ = 2

PARTS =  PRED, SUBJ, OBJ
ALL4 = CONTEXT, PRED, SUBJ, OBJ

import string
import sys
import re
import imp
import MySQLdb
import TableRenderer
from TableRenderer import TableRenderer

SUBST_NONE = 0
SUBST_PRED = 1
SUBST_SUBJ = 2
SUBST_OBJ = 4

RE_symbol = re.compile("\?(?P<symbol>\w+)$")
RE_URI = re.compile("\<(?P<uri>[^\>]+)\>$")
RE_literal = re.compile("\"(?P<literal>\w+)\"$")

def Assure(list, index, value):
    for i in range(len(list), index+1):
        list.append(None)
    list[index] = value

def NTriplesAtom(s, rowBindings):
    if (s._URI()):
        subj = "<"+s._URI()+">"
    elif (s._literal()):
        subj = "<"+s._literal()+">"
    else:
        try:
            subj = '"'+rowBindings[s.symbol()]+'"'
        except TypeError, e:
            subj = '"'+str(rowBindings[s.symbol()])+'"'
        except KeyError, e:
            print s.toString()
            print s._literal()
            subj = '"'+"KeyError:"+str(e)+" "+s.symbol()+'"'
    return subj

def ShowStatement(statement):
    c, p, s, o = statement
    return '%s %s %s .' % (s, p, o)

class QueryPiece:
    "base class for query atoms"
    def __init__(self, datum):
        self.datum = datum

    def symbol(self):
        return None

    def _URI(self):
        return None

    def _literal(self):
        return None

    def _const(self):
        return None

    def getList(self):
        return None

class ConstantQueryPiece(QueryPiece):
    ""
    def _const(self):
        return self.datum
    def toString(self):
        return "\""+self.datum+"\""

class UriQueryPiece(ConstantQueryPiece):
    ""
    def _URI(self):
        return self.datum
    def toString(self):
        return "<"+self.datum+">"
    
class LiteralQueryPiece(ConstantQueryPiece):
    ""
    def _literal(self):
        return self.datum
    def toString(self):
        return "<"+self.datum+">"
    
class VariableQueryPiece(QueryPiece):
    ""
    def __init__(self, symbol, index, existential):
        QueryPiece.__init__(self, symbol)
        self.varIndex = index
        self.existential = existential
    def symbol(self):
        return self.datum
    def getVarIndex(self):
        return self.varIndex
    def toString(self):
        return "?"+self.datum+""

class SetQueryPiece(QueryPiece):
    ""
    def __init__(self, datum):
        QueryPiece.__init__(self, datum)
        self.disjunction = 0
        self.nope = 0
    def getList(self):
        return self.datum
    def isDisjunction(self):
        return None
    def isNot(self):
        return None
    def toString(self):
        ret = []
        for s in self.datum:
            row = []
            row.append("(")
            row.append(s[0].toString())
            row.append(" ")
            row.append(s[1].toString())
            row.append(" ")
            row.append(s[2].toString())
            row.append(")")
            ret.append(string.join(row, ""))
        return string.join(ret, "\n")

class ResultSet:
    ""
    def __init__(self):
        self.varIndex = {}
        self.indexVar = []
        self.results = []
    def myIntern(self, q, index, variables, existentials):
        try:
            existentials.index(q)
            symbol = q.fragid
            try:
                index = self.varIndex[symbol]
            except KeyError, e:
                index = self.varIndex[symbol] = len(self.indexVar)
                self.indexVar.append(symbol)
            return (VariableQueryPiece(symbol, index, 1))
        except ValueError, e:
            try:
                variables.index(q)
                symbol = q.fragid
                try:
                    index = self.varIndex[symbol]
                except KeyError, e:
                    index = self.varIndex[symbol] = len(self.indexVar)
                    self.indexVar.append(symbol)
                return (VariableQueryPiece(symbol, index, 0))
            except ValueError, e:
                try:
                    return (LiteralQueryPiece(q.string))
                except AttributeError, e:
                    try:
                        return (UriQueryPiece(q.uriref()))
                    except Exception, e:
                        raise RuntimeError, "what's a \""+q+"\"?"
        
    def buildQuerySetsFromCwm(self, sentences, variables, existentials):
        set = []
        for sentence in sentences:
            sentStruc = []
            set.append(sentStruc)
            sentStruc.append(self.myIntern(sentence.quad[1], 0, variables, existentials))
            sentStruc.append(self.myIntern(sentence.quad[2], 1, variables, existentials))
            sentStruc.append(self.myIntern(sentence.quad[3], 2, variables, existentials))
        return SetQueryPiece(set)
    def buildQuerySetsFromArray(self, sentences):
        # /me thinks that one may group by ^existentials
        set = []
        for sentence in sentences:
            sentStruc = []
            set.append(sentStruc)
            for word in sentence:
                m = RE_symbol.match(word)
                if (m):
                    symbol = m.group("symbol")
                    try:
                        index = self.varIndex[symbol]
                    except KeyError, e:
                        index = self.varIndex[symbol] = len(self.indexVar)
                        self.indexVar.append(symbol)
                    sentStruc.append(VariableQueryPiece(symbol, index, 0))
                else:
                    m = RE_URI.match(word)
                    if (m):
                        sentStruc.append(UriQueryPiece(m.group("uri")))
                    else:
                        m = RE_literal.match(word)
                        if (m):
                            sentStruc.append(LiteralQueryPiece(m.group("literal")))
                        else:
                            raise RuntimeError, "what's a \""+word+"\"?"
        return SetQueryPiece(set)
    def getVarIndex(self, symbol):
        return self.varIndex[symbol]
    def setNewResults(self, newResults):
        self.results = newResults
    def toString(self, flags):
        #df = lambda o: o
        #renderer = TableRenderer(flags, dataFilter=df)
        renderer = TableRenderer()
        renderer.addHeaders(self.indexVar)
        if (len(self.results) == 0):
            renderer.addData(['-no solutions-'])
        elif (len(self.results) == 1 and len(self.results[0]) == 0):
            renderer.addData(['-initialized-'])
        else:
            renderer.addData(self.results)
        return renderer.toString()

class RdfDBAlgae:
    ""
    
class SqlDBAlgae(RdfDBAlgae):
    def __init__(self, baseURI, tableDescModuleName, user, password, host, database, meta, pointsAt, duplicateFieldsInQuery=0, checkUnderConstraintsBeforeQuery=1, checkOverConstraintsOnEmptyResult=1):
        # Grab _AllTables from tableDescModuleName, analogous to
        #        import tableDescModuleName
        #        from tableDescModuleName import _AllTables
        self.user = user
        if (password):
            self.password = password
        else:
            self.password = ""
        self.host = host
        self.database = database
        self.connection = None
        self.duplicateFieldsInQuery = duplicateFieldsInQuery
        self.checkUnderConstraintsBeforeQuery = checkUnderConstraintsBeforeQuery
        self.checkOverConstraintsOnEmptyResult = checkOverConstraintsOnEmptyResult

        try:
            fp, path, stuff = imp.find_module(tableDescModuleName)
            tableDescModule = imp.load_module(tableDescModuleName, fp, path, stuff)
            if (fp): fp.close
            self.structure = tableDescModule._AllTables
        except ImportError, e:
            print tableDescModuleName, " not found\n"
            self.structure = None
        except TypeError, e:
            self.structure = None

        self.baseUri = baseURI
        self.predicateRE = re.compile(baseURI.uri+
                                      "(?P<table>\w+)\#(?P<field>[\w\d\%\=\&]+)$")

        if (self.structure == None):
            print "analyzing sql://%s/%s\n" % (host, database)
            self.structure = {}
            cursor = self._getCursor()
            cursor.execute("SHOW TABLES")
            while 1:
                tableName_ = cursor.fetchone()
                if not tableName_:
                    break
                self._buildTableDesc(tableName_[0], meta, pointsAt)

        # SQL query components:
        self.tableAliases = [];		# FROM foo AS bar
        self.selects = [];		# SELECT foo
        self.labels = [];		#            AS bar
        self.selectPunct = [];		# pretty printing
        self.wheres = [];		# WHERE foo=bar

        # Variable, table, column state:
        self.whereStack = [];		# Save WHERES for paren exprs.
        self.symbolBindings = {};	# Table alias for a given symbol.
        self.tableBindings = {};	# Next number for a table alias.
        self.objectBindings = [];	# External key targs in SELECT.
        self.scalarBindings = [];	# Literals in SELECT.
        self.fieldBindings = {};	# Which alias.fields are in SELECT.
        self.disjunctionBindings = {};	# Which OR clauses are in SELECT.
        self.scalarReferences = {};	# Where scalar variables were used.

        # Keeping track of [under]constraints
        self.constraintReaches = {};	# Transitive closure of all aliases
					# constrained with other aliases.
        self.constraintHints = {};	# Aliases constrained in some but not
					# all paths of an OR. Handy diagnostic.
        self.overConstraints = {};	# Redundent constraints between aliases.

    def _buildTableDesc(self, table, meta, pointsAt):
        self.structure[table] = { '-fields' : {},
                                  '-primaryKey' : [] }
        cursor = self._getCursor()
        cursor.execute("SHOW FIELDS FROM " + table)
        while 1:
            name_type_null_key_default_extra_ = cursor.fetchone()
            if not name_type_null_key_default_extra_:
                break
            name = name_type_null_key_default_extra_[0]
            self.structure[table]['-fields'][name] = {}
            target = meta.any(pred=pointsAt, subj=self.baseUri.store.internURI(self.baseUri.uri+table+"#"+name))
            if (target):
                self.structure[table]['-fields'][name]['-target'] = self.predicateRE.match(target.uriref()).groups()
                #print "%s#%s -> %s#%s" % (table, name,
                #                          self.structure[table]['-fields'][name]['-target'][0],
                #                          self.structure[table]['-fields'][name]['-target'][1])

        cursor = self._getCursor()
        cursor.execute("SHOW INDEX FROM " + table)
        while 1:
            tableName_nonUnique_keyName_seq_columnName_ = cursor.fetchone()
            if not tableName_nonUnique_keyName_seq_columnName_:
                break
            (tableName, nonUnique, keyName, seq, columnName, d,d,d,d,d) = tableName_nonUnique_keyName_seq_columnName_
            if (keyName == 'PRIMARY'):
                self.structure[table]['-primaryKey'].append(columnName)

    def _processRow(self, row, statements, implQuerySets, resultSet, messages, flags):
        #for iC in range(len(implQuerySets)):
        #    print implQuerySets[iC]

        for term in implQuerySets.getList():
	    self._walkQuery(term, row, flags)

        if (self.checkUnderConstraintsBeforeQuery):
            self._checkForUnderConstraint()

        self.selectPunct[-1] = ''

        query = self._buildQuery(implQuerySets)
        messages.append("query SQLselect \"\"\""+query+"\"\"\" .")
        cursor = self._getCursor()
        cursor.execute(query)

        #if (cursor.rows() == 0 and self.checkOverConstraintsOnEmptyResult):
        #    self._checkForOverConstraint;

        nextResults, nextStatements = self._buildResults(cursor, implQuerySets, row, statements)
        return nextResults, nextStatements

    def _getCursor(self):
        if (self.connection == None):
            self.connection = MySQLdb.connect(self.host, self.user, self.password, self.database)
        cursor = self.connection.cursor()
        return cursor

    def _walkQuery (self, term, row, flags):
        if (0):
            # Handle ORs here.
	    tmpWheres = self.wheres
        else:
            c = term	# @@@ NUKE c
            p = c[PRED]
            s = c[SUBJ]
            o = c[OBJ]
            sTable, field, oTable, targetField = self._lookupPredicate(p._URI())
            sAlias = None;
            oAlias = None;

            if (s._const()):
                uri = s._uri()
                if (uri):
                    sAlias = self._bindTableToConstant(sTable, s)
                else:
                    raise RuntimeError, "not implemented"
            else:
                sAlias = self._bindTableToVariable(sTable, s)

            if (o._const()):
                if (oTable):
                    oAlias = self._bindTableToConstant(oTable, o)
                    self._addWhere(sAlias+"."+field+"="+oAlias+"."+targetField, term)
                    self._adddReaches(sAlias, oAlias, term)
                else:
                    self._addWhere(sAlias+"."+field+"=\""+o._const()+"\"", term)
            else:
                if (oTable):
                    oAlias = self._bindTableToVariable(oTable, o)
                    self._addWhere(sAlias+"."+field+"="+oAlias+"."+targetField, term)
                    self._addReaches(sAlias, oAlias, term)
                else:
                    try:
                        scalarReference = self.scalarReferences[o.symbol()]
                        firstAlias, firstField = scalarReference
                        self._addWhere(sAlias+"."+field+"="+firstAlias+"."+firstField, term)
                        self._addReaches(sAlias, firstAlias, term)
                    except KeyError, e:
                        col = self._addSelect(sAlias+"."+field, o.symbol()+"_"+field, "\n")
                        self.scalarBindings.append([o, [col]])
                        self.scalarReferences[o.symbol()] = [sAlias, field]
                
    def _preferredID (self, table, alias, qp):
        pk = self.structure[table]['-primaryKey']
        try:
            pk.isdigit() # Lord, there's got to be a better way. @@@
            pk = [pk]
        except AttributeError, e:
            pk = pk
        cols = []
        fieldz = []
        for iField in range(len(pk)):
            field = pk[iField]
            if (iField == len(pk)-1):
                punct = "\n       "
            else:
                punct = ' '
            col = self._addSelect(alias+"."+field, qp.symbol()+"_"+field, punct)
            cols.append(col)
            fieldz.append(field)
        self.objectBindings.append([qp, cols, fieldz, table])
        #        self.selectPunct.pop()

    def _addSelect (self, name, label, punct):
        try:
            ret = self.fieldBindings[name]
            if (self.duplicateFieldsInQuery):
                raise KeyError, "force duplicate fields"
        except KeyError, e:
            self.selects.append(name)
            self.labels.append(label)
            self.selectPunct.append(punct)
            self.fieldBindings[name] = ret = len(self.selects)-1
        return ret

    def _bindTableToVariable (self, table, qp):
        try:
            self.symbolBindings[qp.symbol()]
        except KeyError, e:
            self.symbolBindings[qp.symbol()] = {}
        try:
            binding = self.symbolBindings[qp.symbol()][table]
        except KeyError, e:
            try:
                maxForTable = self.tableBindings[table]
            except KeyError, e:
                maxForTable = self.tableBindings[table] = 0
            binding = table+"_"+repr(maxForTable)
            self.symbolBindings[qp.symbol()][table] = binding
            self.tableBindings[table] = self.tableBindings[table] + 1

            self.tableAliases.append([table, binding])
            self._preferredID(table, binding, qp) # (A_0.u0, A_0.u1)
        return binding

    def _bindTableToConstant (self, table, qp):
        try:
            self.symbolBindings[qp._URI()]
        except KeyError, e:
            self.symbolBindings[qp._URI()] = {}
        try:
            binding = self.symbolBindings[qp._URI()][table]
        except KeyError, e:
            try:
                maxForTable = self.tableBindings[table]
            except KeyError, e:
                maxForTable = self.tableBindings[table] = 0
            binding = table+"_"+repr(maxForTable)
            self.symbolBindings[qp._URI()][table] = binding
            self.tableBindings[table] = self.tableBindings[table] + 1

            self.tableAliases.append([table, binding])
            for where in self._decomposeUniques(qp._URI(), binding, table):
                self._addWhere(where, qp)
        return binding

    def _lookupPredicate(self, predicate):
        m = self.predicateRE.match(predicate)
        table = m.group("table")
        field = m.group("field")
        try:
            fieldDesc = self.structure[table]['-fields'][field]
        except KeyError, e:
            fieldDesc = None
        try:
            target = fieldDesc['-target']
            return table, field, target[0], target[1]
        except KeyError, e:
            target = None
            return table, field, None, None

    def _uniquesFor(self, table):
        try:
            pk = self.structure[table]['-primaryKey']
            return pk;
        except KeyError, e:
            raise RuntimeError, "no primary key for table \"table\""

    def _composeUniques(self, values, table):
        segments = []
        pk = self.structure[table]['-primaryKey']
        try:
            pk.isdigit() # Lord, there's got to be a better way. @@@
            pk = [pk]
        except AttributeError, e:
            pk = pk
        for field in pk:
	    lvalue = self.CGI_escape(field)
            rvalue = self.CGI_escape(str(values[field]))
	    segments.append(lvalue+"="+rvalue)
        value = string.join(segments, '&')
        return self.baseUri.uri+table+"."+value;

    def _decomposeUniques(self, uri, tableAs, table):
        m = self.predicateRE.match(uri)
        table1 = m.group("table")
        field = m.group("field")
        if (table1 != table):
            raise RuntimeError, "\""+uri+"\" not based on "+self.baseUri.uri+table
        recordId = self.CGI_unescape(field)
        specifiers = strings.split(recordId, '&')
        constraints = [];
        for specifier in specifiers:
            field, value = split (specifier, '=')
            field = self.unescapeName(field)
            field = self.unescapeName(field)
            constraints.append(tableAs+"."+field+"=\""+value+"\"")
        return constraints

    def _buildQuery (self, implQuerySets):
        # assemble the query
        segments = [];
        segments.append('SELECT ')
	tmp = []
        for i in range(len(self.selects)):
            # Note, the " AS self.labels[$i]" is just gravy -- nice in logs.
            if (i == len(self.selects) - 1):
                comma = ''
            else:
                comma = ','
            if (self.labels[1] == None):
                asStr = ''
            else:
                asStr = " AS "+self.labels[i]
            tmp.append(self.selects[i]+asStr+comma+self.selectPunct[i])
	segments.append(string.join(tmp, ''))

        segments.append("\nFROM ")
        tmp = []
        for i in range(len(self.tableAliases)):
            tmp.append(self.tableAliases[i][0]+" AS "+self.tableAliases[i][1])
        segments.append(string.join (tmp, ', '))
        where = whereStr = self._makeWheres(implQuerySets.disjunction, implQuerySets.nope)
        if (where):
            segments.append("\nWHERE ")
            segments.append(whereStr)
        #    if ($flags->{-uniqueResults}) {
        #	push (@$segments, ' GROUP BY ');
        #	push (@$segments, CORE::join (',', @{self.labels}));
        #    } elsif (my $groupBy = $flags->{-groupBy}) {
        #	if (@$groupBy) {
        #	    push (@$segments, ' GROUP BY ');
        #	    push (@$segments, CORE::join (',', @$groupBy));
        #	}
        #    }
        return string.join(segments, '')

    def _buildResults (self, cursor, implQuerySets, row, statements):
        nextResults = []
        nextStatements = []
        uniqueStatementsCheat = {}
        while 1:
            answerRow = cursor.fetchone()
            if not answerRow:
                break
            col = 1
            nextResults.append(row[:])
            nextStatements.append(statements[:])

            # Grab objects from the results
            rowBindings = {}
            for binding in self.objectBindings:
                queryPiece, cols, fieldz, table = binding
                valueHash = {}
                for i in range(len(cols)):
                    col = cols[i]
                    field = fieldz[i]
                    valueHash[field] = answerRow[col]
                uri = self._composeUniques(valueHash, table)
                Assure(nextResults[-1], queryPiece.getVarIndex(), uri) # nextResults[-1][queryPiece.getVarIndex()] = uri
                rowBindings[queryPiece.symbol()] = uri
            # Grab literals from the results
            for binding in self.scalarBindings:
                queryPiece, cols = binding
                str = answerRow[cols[0]]
                Assure(nextResults[-1], queryPiece.getVarIndex(), str) # nextResults[-1][queryPiece.getVarIndex()] = uri
                rowBindings[queryPiece.symbol()] = str
            # Grab sub-expressions from the results
            for qpStr in self.disjunctionBindings.keys():
                binding = self.disjunctionBindings[qpStr]
                qp, cols = binding
                rowBindings[qp] = answerRow[cols[0]]

            # ... and the supporting statements.
            foo = self._bindingsToStatements(implQuerySets, rowBindings, uniqueStatementsCheat)
            for statement in foo:
                nextStatements[-1].append(statement)
	    #for s in nextStatements->[-1]
            #    $self->{-db}->applyClosureRules($self->{-db}{INTERFACES_implToAPI}, 
            #				    $s->getPredicate, $s->getSubject, $s->getObject, 
            #				    $s->getReifiedAs, $s->getReifiedIn, $s->getAttribution);
        return nextResults, nextStatements

    def _bindingsToStatements (self, term, rowBindings, uniqueStatementsCheat):
        if (term.__class__.__name__ == "SetQueryPiece"):
            ret = []
            if (term.nope == 0):
                for subTerm in term.getList():
                    if (term.disjunction):
                        binding = self.disjunctionBindings[subTerm]
                        qp, cols = binding
                        if (rowBindings[qp]):
                            foo = self._bindingsToStatements(subTerm, rowBindings, uniqueStatementsCheat)
                            for statement in foo:
                                ret.append(statement)
		    else:
		        foo = self._bindingsToStatements(subTerm, rowBindings, uniqueStatementsCheat)
                        for statement in foo:
                            ret.append(statement)
            return ret
        pred = NTriplesAtom(term[PRED], rowBindings)
        subj = NTriplesAtom(term[SUBJ], rowBindings)
        obj = NTriplesAtom(term[OBJ], rowBindings)

        try:
            statement = uniqueStatementsCheat[pred][subj][obj]
        except KeyError, e:
            statement = ['<db>', pred, subj, obj]
            try:
                byPred = uniqueStatementsCheat[pred]
                try:
                    bySubj = byPred[subj]
                except KeyError, e:
                    uniqueStatementsCheat[pred][subj] = {obj : statement}
            except KeyError, e:
                uniqueStatementsCheat[pred] = {subj : {obj : statement}}
        return [statement]

    def _addReaches (self, frm, to, term):
        # Entries are a list of paths (lists) that connect frm to to and visa
        # versa. The first path is the first way the tables were constrained.
        # Additional paths represent over-constraints.
        self._fromReachesToAndEverythingToReaches(frm, to, [term])
        for fromFrom in self.constraintReaches[frm].keys():
            if (fromFrom != to):
                self._fromReachesToAndEverythingToReaches(fromFrom, to, [self.constraintReaches[frm][fromFrom], term])

    def _fromReachesToAndEverythingToReaches (self, frm, to, path):
        try:
            self.constraintReaches[frm]
        except KeyError, e:
            self.constraintReaches[frm] = {}
        try:
            self.constraintReaches[to]
        except KeyError, e:
            self.constraintReaches[to] = {}
        try:
            self.overConstraints[frm][to].append(path)
        except KeyError, e:
            #	print "  [c]-[g]->[p]\n"
            try:
                for toTo in self.constraintReaches[to].keys():
                    toPath = [self.constraintReaches[to][toTo], path]
                    try:
                        self.overConstraints[frm][toTo].append(path)
                    except KeyError, e:
                        self.constraintReaches[frm][toTo] = toPath
                        self.constraintReaches[toTo][frm] = toPath
            except KeyError, e:
                self.constraintReaches[to] = {}
            self.constraintReaches[frm][to] = path
            self.constraintReaches[to][frm] = path

    def _showConstraints (self):
        ret = []
        for frm in self.constraintReaches.keys():
            for to in self.constraintReaches[frm].keys():
                ret.append(self._showConstraint(frm, to))
        return string.join(ret, "\n")

#    def _showConstraint (self, frm, to):
#        my pathStr = join (' - ', map {_->toString({-brief => 1})} @{self.constraintReaches[frm][to]})
#        return "frm:to: pathStr"

    def _mergeCommonConstraints (self, reachesSoFar, term, subTerm):
        for fromTable in self.constraintReaches.keys():
            try:
                reachesSoFar[fromTable]
            except KeyError, e:
                try:
                    self.constraintHints[fromTable]
                except KeyError, e:
                    self.constraintHints[fromTable] = {}
                    #			    push (@{self.constraintHints[fromTable]}, "for fromTable")
            for toTable in self.constraintReaches[fromTable].keys():
                try:
                    reachesSoFar[fromTable][toTable]
                except KeyError, e:
                    self.constraintHints[fromTable][toTable].append([term, subTerm])
                    self.constraintHints[toTable][fromTable].append([term, subTerm])
        for fromTable in eachesSoFa.keys():
            try:
                self.constraintReaches[fromTable]
            except KeyError, e:
                try:
                    self.constraintHints[fromTable]
                except KeyError, e:
                    self.constraintHints[fromTable] = {}
                    #			    push (@{self.constraintHints[fromTable]}, "for fromTable")
            for toTable in reachesSoFar[fromTable].keys():
                try:
                    self.constraintReaches[fromTable][toTable]
                except KeyError, e:
                    del reachesSoFar[fromTable][toTable]
                    del reachesSoFar[toTable][fromTable]
                    self.constraintHints[fromTable][toTable].append([term, subTerm])
                    self.constraintHints[toTable][fromTable].append([term, subTerm])

    def _checkForUnderConstraint (self):
        firstAlias = self.tableAliases[0][1]
        messages = []
        for iAliasSet in range(1, len(self.tableAliases)):
            table, alias = self.tableAliases[iAliasSet]
            try:
                self.constraintReaches[firstAlias][alias]
            except KeyError, e:
                messages.append("  %s not constrained against %s" % (firstAlias, alias))
                if (self.constraintReaches.has_key(firstAlias)):
                    for reaches in self.constraintReaches[firstAlias].keys():
                        messages.append("    %s reaches %s" % (firstAlias, reaches))
                else:
                    messages.append("    %s reaches NOTHING" % (firstAlias))
                if (self.constraintReaches.has_key(alias)):
                    for reaches in self.constraintReaches[alias].keys():
                        messages.append("    %s reaches %s" % (alias, reaches))
                else:
                    messages.append("    %s reaches NOTHING" % (alias))
                if (self.constraintHints.has_key(firstAlias) and self.constraintHints[firstAlias].has_key(alias)):
                    for terms in self.constraintHints[firstAlias][alias]:
                        constrainedByStr = terms[1].toString({-brief : 1})
                        constrainedInStr = terms[0].toString({-brief : 1})
                        messages.append("    partially constrained by 'constrainedByStr' in 'constrainedInStr'")
        if (len(messages) > 0):
            raise RuntimeError, "underconstraints exception:\n"+string.join(messages, "\n")

    def _checkForOverConstraint (self):
        messages = []
        done = {}
        for frm in self.overConstraints.keys():
            try:
                done[frm]
            except KeyError, e:
                break
            done[frm] = 1
            for to in self.overConstraints[frm].keys():
                try:
                    done[frm]
                except KeyError, e:
                    break
                if (to != frm):
                    messages.append("  frm over-constrained against to"._showPath(self.constraintReaches[frm][to]))
                    for path in self.overConstraints[frm][to]:
                        messages.append('    '._showPath(path))
        if (len(messages)):
            raise RuntimeError, "overconstraints exception:\n"+string.join(messages, "\n")

    def _showPath(path) : # static
        pathStrs = []
        for term in path:
            pathStrs.append(term.toString({-brief : 1}))
        return string.join(pathStrs, ' - ')

    def _addWhere (self, condition, term):
        self.wheres.append(condition)

    def _pushWheres (self):
        self.whereStack.append(self.wheres)
        self.wheres = []

    def _popWheres (self, disjunction, negation):
        innerWheres = self._makeWheres(disjunction, negation)
        self.wheres = self.whereStack.pop()
        if (innerWheres):
            self.wheres.push("("+innerWheres+")")

    def _makeWheres (self, disjunction, negation):
        if (len(self.wheres) < 1):
            return ''
        if (disjunction):
            junction = "\n   OR "
        else:
            junction = "\n  AND "
        ret = string.join(self.wheres, junction)
        if (negation):
            return "NOT (ret)"
        else:
            return ret

    def unescapeName(toEscape):
        a = toEscape
        re.sub("\_e", "=", z)
        a = re.sub("\_e", "\=", a)
        a = re.sub("\_a", "\&", a)
        a = re.sub("\_h", "\-", a)
        a = re.sub("\_d", "\.", a)
        a = re.sub("\_p", "\%", a)
        a = re.sub("\_u", "_", a)
        a = CGI_unescape(a)
        return a

    def CGI_escape(self, toEscape):
        a = toEscape
        a = re.sub("&", "\&amp\;", a)
        a = re.sub("\"", "\&quot\;", a)
        return a

    def CGI_unescape(toEscape):
        a = toEscape
        a = re.sub("\&amp\;", "&", a)
        a = re.sub("\&quot\;", "\"", a)
        return a

if __name__ == '__main__':
    s = [["<http://localhost/SqlDB/uris#uri>", "?urisRow", "<http://www.w3.org/Member/Overview.html>"], 
         ["<http://localhost/SqlDB/acls#access>", "?acl", "?access"], 
         ["<http://localhost/SqlDB/acls#acl>", "?acl", "?aacl"], 
         ["<http://localhost/SqlDB/acls#id>", "?acl", "?accessor"], 
         ["<http://localhost/SqlDB/idInclusions#groupId>", "?g1", "?accessor"], 
         ["<http://localhost/SqlDB/idInclusions#id>", "?g1", "?u1"], 
         ["<http://localhost/SqlDB/ids#value>", "?u1", "\"eric\""], 
         ["<http://localhost/SqlDB/uris#acl>", "?urisRow", "?aacl"]]
    rs = ResultSet()
    qp = rs.buildQuerySetsFromArray(s)
    a = SqlDBAlgae("http://localhost/SqlDB/", "AclSqlObjects")
    messages = []
    nextResults, nextStatements = a._processRow([], [], qp, rs, messages, {})
    rs.results = nextResults
    def df(datum):
        return re.sub("http://localhost/SqlDB#", "sql:", datum)
    print string.join(messages, "\n")
    print "query matrix \"\"\""+rs.toString({'dataFilter' : None})+"\"\"\" .\n"
    for solutions in nextStatements:
        print "query solution {"
        for statement in solutions:
            print ShowStatement(statement)
        print "} ."

blah = """
testing with `python2.2 ./cwm.py test/dbork/aclQuery.n3 -think`

aclQuery -- :acl acls:access :access .
sentences[1].quad -- (attrib,      s,   p,      o)
                     (0_work, access, acl, access)
p.uriref() -- 'file:/home/eric/WWW/2000/10/swap/test/dbork/aclQuery.n3#acl'
s.uriref() -- 'http://localhost/SqlDB/acls#access'
o.uriref() -- 'file:/home/eric/WWW/2000/10/swap/test/dbork/aclQuery.n3#access'
existentials[1] == sentences[1].quad[2] -- 1

n
s
b 576
c
s
b 2352
c
s

this one works:
    s = [["<http://localhost/SqlDB/uris#uri>", "?urisRow", "<http://www.w3.org/Member/Overview.html>"], 
         ["<http://localhost/SqlDB/uris#acl>", "?urisRow", "?aacl"], 
         ["<http://localhost/SqlDB/acls#acl>", "?acl", "?aacl"], 
         ["<http://localhost/SqlDB/acls#access>", "?acl", "?access"], 
         ["<http://localhost/SqlDB/ids#value>", "?u1", "\"eric\""], 
         ["<http://localhost/SqlDB/idInclusions#id>", "?g1", "?u1"], 
         ["<http://localhost/SqlDB/idInclusions#groupId>", "?g1", "?accessor"], 
         ["<http://localhost/SqlDB/acls#id>", "?acl", "?accessor"]]

"""

