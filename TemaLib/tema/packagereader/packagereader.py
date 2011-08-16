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

import sys
from tema.eini.mddparser import Parser as mddParser
import tema.data.datareader as datareader

usage = """
Usage: packagereader <mddFilePath> <id> <params>

  <mddFilePath>		path to the mdd file of the package
  <id>			identifier of the information being sought
  <params>		additional id-specific parameters

Recognized ids:

  name			Prints the name of the domain.
  products		Lists the products within the domain.
  concurrentunits	Lists the concurrent units belonging to the given product.
  components		Lists the model components belonging to the given product and concurrent unit.
  devices		Lists the devices belonging to the given product.
  datatables		Lists the data tables within the domain.
  datarequirement	Lists the data table requirements for the given concurrent unit and component.
  locales		Lists the locales available for the given product.
  logicalname		Prints the logical name of the given data table.
  datacomment		Prints the comment of the given data table.
  actions		Lists the action words and state verifications belonging to the given product, concurrent unit and component.
  interestingactions	Lists the interesting action words and state verifications belonging to the given product, concurrent unit and component.
  comment		Prints the comment attached to the given product, concurrent unit, component and action.

Examples:

  packagereader domain.mdd name
  packagereader domain.mdd products
  packagereader domain.mdd concurrentunits product1
  packagereader domain.mdd components product1 concurrentunit1
  packagereader domain.mdd devices product1
  packagereader domain.mdd datatables
  packagereader domain.mdd datarequirement concurrentunit1 component1
  packagereader domain.mdd locales product1
  packagereader domain.mdd logicalname datatable1
  packagereader domain.mdd datacomment datatable1
  packagereader domain.mdd actions product1 concurrentunit1 component1
  packagereader domain.mdd interestingactions product1 concurrentunit1 component1
  packagereader domain.mdd comment product1 concurrentunit1 component1 action1
"""

class Reader:
	class Error(Exception):
		pass

	__suffixes = {"Model Designer Model":"mdm", "Model Designer Data Table":"td", "Model Designer Localization Table":"csv", "Basic Data Table":"td", "Basic Localization Table":"csv"}

	def __init__(self, mddFilePath):
		try:
			f = file(mddFilePath)
		except IOError:
			raise Reader.Error("Cannot open file '%s'." % mddFilePath)
		try:
			self.__mdd = mddParser().parse(f)
		finally:
			f.close()

		i = mddFilePath.rfind('/')
		if i != -1:
			self.__directory = mddFilePath[:i+1]
		else:
			self.__directory = ""

	def getValue(self, id, params = []):
		try:
			function = eval('self._Reader__get_' + id)
		except Exception, e:
			raise Reader.Error("Unknown id '%s'." % id)
	
		return function(params)

	def __get_name(self, params):
		if len(params) > 0:
			raise Reader.Error("Name query does not accept additional parameters.")

		return self.__mdd[mddParser.DOMAIN][mddParser.D_I_NAME][mddParser.D_F_VALUE]
		products = [p[mddParser.E_F_NAME] for pId, p in self.__mdd[mddParser.PRODUCTS].iteritems() if self.__isActiveP(pId)]
		return self.__list2str(products)

	def __get_products(self, params):
		if len(params) > 0:
			raise Reader.Error("Product listing does not accept additional parameters.")

		products = [p[mddParser.E_F_NAME] for pId, p in self.__mdd[mddParser.PRODUCTS].iteritems() if self.__isActiveP(pId)]
		return self.__list2str(products)

	def __get_concurrentunits(self, params):
		if len(params) < 1:
			raise Reader.Error("Concurrent unit listing requires as an additional parameter the name of a product.")
		elif len(params) > 1:
			raise Reader.Error("Concurrent unit listing does not accept more than one additional parameter.")

		for i,p in self.__mdd[mddParser.PRODUCTS].iteritems():
			if p[mddParser.E_F_NAME] == params[0]:
				productId = i
				break
		else:
			raise Reader.Error("Unknown product '%s'." % params[0])

		concurrentunits = [cu[mddParser.E_F_NAME] \
                                   for cuId, cu in self.__mdd[mddParser.CONCURRENTUNITS].iteritems() \
                                   if productId in cu[mddParser.CU_F_PRODUCTS] and self.__isActiveCu(cuId, productId)]
		return self.__list2str(concurrentunits)

	def __get_components(self, params):
		if len(params) < 2:
			raise Reader.Error("Component listing requires as additional parameters the names of a product and a concurrent unit.")
		elif len(params) > 2:
			raise Reader.Error("Component listing does not accept more than two additional parameters.")

		for i,p in self.__mdd[mddParser.PRODUCTS].iteritems():
			if p[mddParser.E_F_NAME] == params[0]:
				productId = i
				break
		else:
			raise Reader.Error("Unknown product '%s'." % params[0])

		for i,cu in self.__mdd[mddParser.CONCURRENTUNITS].iteritems():
			if cu[mddParser.E_F_NAME] == params[1]:
				concurrentunitId = i
				break
		else:
			raise Reader.Error("Unknown concurrent unit '%s'." % params[1])

		components = [am[mddParser.E_F_NAME] \
                              for amId, am in self.__mdd[mddParser.ACTIONMACHINES].iteritems() \
                              if am[mddParser.AM_F_CONCURRENTUNIT] == concurrentunitId and self.__isActiveAm(amId, productId)]
		return self.__list2str(components)

	def __get_devices(self, params):
		if len(params) < 1:
			raise Reader.Error("Device listing requires as an additional parameter the name of a product.")
		elif len(params) > 1:
			raise Reader.Error("Device listing does not accept more than one additional parameter.")

		for i,p in self.__mdd[mddParser.PRODUCTS].iteritems():
			if p[mddParser.E_F_NAME] == params[0]:
				productId = i
				break
		else:
			raise Reader.Error("Unknown product '%s'." % params[0])

		devices = [d[mddParser.E_F_NAME] \
                           for dId, d in self.__mdd[mddParser.SYSTEMSUNDERTEST].iteritems() \
                           if d[mddParser.ST_F_PRODUCT] == productId and self.__isActiveD(dId)]
		return self.__list2str(devices)

	def __get_datatables(self, params):
		if len(params) > 0:
			raise Reader.Error("Data table listing does not accept additional parameters.")

		datatables = [dt[mddParser.E_F_NAME] for dtId, dt in self.__mdd[mddParser.DATATABLES].iteritems() if self.__isActiveDt(dtId)]
		return self.__list2str(datatables)

	def __get_datarequirement(self, params):
		if len(params) < 2:
			raise Reader.Error("Data requirement listing requires as additional parameters the names of a concurrent unit and a component.")
		elif len(params) > 2:
			raise Reader.Error("Data requirement listing does not accept more than two additional parameters.")

		for i,cu in self.__mdd[mddParser.CONCURRENTUNITS].iteritems():
			if cu[mddParser.E_F_NAME] == params[0]:
				concurrentunitId = i
				break
		else:
			raise Reader.Error("Unknown concurrent unit '%s'." % params[0])

		for am in self.__mdd[mddParser.ACTIONMACHINES].itervalues():
			if am[mddParser.E_F_NAME] == params[1] and am[mddParser.AM_F_CONCURRENTUNIT] == concurrentunitId:
				actionmachine = am
				break
		else:
			raise Reader.Error("Unknown component '%s'." % params[1])

		datarequirement = actionmachine[mddParser.AM_F_DATAREQUIREMENT]
		if datarequirement == None:
			datarequirement = []

		return self.__list2str(datarequirement)

	def __get_locales(self, params):
		if len(params) < 1:
			raise Reader.Error("Locale listing requires as an additional parameter the name of a product.")
		elif len(params) > 1:
			raise Reader.Error("Locale listing does not accept more than one additional parameter.")

		for p in self.__mdd[mddParser.PRODUCTS].itervalues():
			if p[mddParser.E_F_NAME] == params[0]:
				product = p
				break
		else:
			raise Reader.Error("Unknown product '%s'." % params[0])

		if product[mddParser.E_F_MODEL] != None:
			path = self.__directory + self.__id2filename(params[0]) + '.' + Reader.__suffixes[product[mddParser.E_F_MODEL]]
			try:
				f = file(path)
			except IOError:
				raise Reader.Error("Cannot open file '%s'." % path)
			try:
				line = f.readline()
			finally:
				f.close()

			locales = line.strip().split(';')[1:]
			return self.__list2str(locales)

		else:
			return ""

	def __get_logicalname(self, params):
		if len(params) < 1:
			raise Reader.Error("Logical name query requires as an additional parameter the name of a data table.")
		elif len(params) > 1:
			raise Reader.Error("Logical name query does not accept more than one additional parameter.")

		for dt in self.__mdd[mddParser.DATATABLES].itervalues():
			if dt[mddParser.E_F_NAME] == params[0]:
				datatable = dt
				break
		else:
			raise Reader.Error("Unknown data table '%s'." % params[0])

		path = self.__directory + self.__id2filename(params[0]) + '.' + Reader.__suffixes[datatable[mddParser.E_F_MODEL]]
		try:
			f = file(path)
		except IOError:
			raise Reader.Error("Cannot open file '%s'." % path)
		try:
			line = f.readline()
		finally:
			f.close()

#		return line.split(':',1)[0].split('(',1)[0].strip()
		return datareader.getDataInfo(line)[0]

	def __get_datacomment(self, params):
		if len(params) < 1:
			raise Reader.Error("Data comment query requires as an additional parameter the name of a data table.")
		elif len(params) > 1:
			raise Reader.Error("Data comment query does not accept more than one additional parameter.")

		for dt in self.__mdd[mddParser.DATATABLES].itervalues():
			if dt[mddParser.E_F_NAME] == params[0]:
				datatable = dt
				break
		else:
			raise Reader.Error("Unknown data table '%s'." % params[0])

		path = self.__directory + self.__id2filename(params[0]) + '.' + Reader.__suffixes[datatable[mddParser.E_F_MODEL]]
		try:
			f = file(path)
		except IOError:
			raise Reader.Error("Cannot open file '%s'." % path)
		try:
			line = f.readline()
		finally:
			f.close()

#		i = 0
#		while i < len(line):
#			for separator in ('"""', '"', "'"):
#				if line[i:i+len(separator)] == separator:
#					j = i + len(separator)
#					while j < len(line):
#						if line[j] == '\\':
#							j = j+1
#						elif line[j:j+len(separator)] == separator:
#							i = j + len(separator) - 1
#							break
#						j = j+1
#					else:
#						raise Reader.Error("Cannot parse file '%s'." % path)
#					break
#
#			else:
#				if line[i] == '#':
#					return line[i+1:].strip()
#
#			i = i+1
#
#		return ""

		return datareader.getDataInfo(line)[1]

	def __get_actions(self, params, interestingonly=False):
		if len(params) < 3:
			raise Reader.Error("Action listing requires as additional parameters the names of a product, a concurrent unit and a component.")
		elif len(params) > 3:
			raise Reader.Error("Action listing does not accept more than three additional parameters.")

		for i,p in self.__mdd[mddParser.PRODUCTS].iteritems():
			if p[mddParser.E_F_NAME] == params[0]:
				productId = i
				break
		else:
			raise Reader.Error("Unknown product '%s'." % params[0])

		for i,cu in self.__mdd[mddParser.CONCURRENTUNITS].iteritems():
			if cu[mddParser.E_F_NAME] == params[1]:
				concurrentunitId = i
				break
		else:
			raise Reader.Error("Unknown concurrent unit '%s'." % params[1])

		for i,am in self.__mdd[mddParser.ACTIONMACHINES].iteritems():
			if am[mddParser.E_F_NAME] == params[2] and am[mddParser.AM_F_CONCURRENTUNIT] == concurrentunitId:
				actionmachineId = i
				actionmachine = am
				break
		else:
			raise Reader.Error("Unknown component '%s'." % params[2])

		suffix = Reader.__suffixes[actionmachine[mddParser.E_F_MODEL]]
		exec("from tema.model." + suffix + "model import Model")
		path = self.__directory + self.__id2filename(params[1] + ' - ' + params[2]) + '.' + suffix
		try:
			f = file(path)
		except IOError:
			raise Reader.Error("Cannot open file '%s'." % path)
		try:
			actionModel = Model()
			actionModel.loadFromFile(f)
		finally:
			f.close()

		for rm in self.__mdd[mddParser.REFINEMENTMACHINES].itervalues():
			if rm[mddParser.KM_F_ACTIONMACHINE] == actionmachineId and rm[mddParser.KM_F_PRODUCT] == productId:
				refinementmachine = rm
				break
		else:
			return self.__list2str([])

		suffix = Reader.__suffixes[refinementmachine[mddParser.E_F_MODEL]]
		exec("from tema.model." + suffix + "model import Model")
		path = self.__directory + self.__id2filename(params[0]) + '/' + self.__id2filename(params[1] + ' - ' + params[2]) + '-rm.' + suffix
		try:
			f = file(path)
		except IOError:
			raise Reader.Error("Cannot open file '%s'." % path)
		try:
			refinementModel = Model()
			refinementModel.loadFromFile(f)
		finally:
			f.close()

		try:
			actions = [a for a in actionModel.getActions() if not interestingonly or a.isInteresting()]
		except AttributeError:
			actions = actionModel.getActions()
		actions = [str(a) for a in actions if str(a).startswith("aw")]

		try:
			attributes = actionModel.getStatePropList()
			try:
				attributes = [a for a in attributes if not interestingonly or a.isInteresting()]
			except AttributeError:
				pass
		except AttributeError:
			attributes = []
		attributes = [str(a) for a in attributes if str(a).startswith("sv")]

		rmActions = set([str(a) for a in refinementModel.getActions()])
		allActions = [a for a in actions + attributes if 'start_' + a in rmActions and ('end_' + a in rmActions or '~end_' + a in rmActions)]

		return self.__list2str(allActions)

	def __get_interestingactions(self, params):
		return self.__get_actions(params, True)

	def __get_comment(self, params):
		if len(params) < 4:
			raise Reader.Error("Action listing requires as additional parameters the names of a product, a concurrent unit, a component and an action.")
		elif len(params) > 4:
			raise Reader.Error("Action listing does not accept more than four additional parameters.")

		for i,p in self.__mdd[mddParser.PRODUCTS].iteritems():
			if p[mddParser.E_F_NAME] == params[0]:
				productId = i
				break
		else:
			raise Reader.Error("Unknown product '%s'." % params[0])

		for i,cu in self.__mdd[mddParser.CONCURRENTUNITS].iteritems():
			if cu[mddParser.E_F_NAME] == params[1]:
				concurrentunitId = i
				break
		else:
			raise Reader.Error("Unknown concurrent unit '%s'." % params[1])

		for i,am in self.__mdd[mddParser.ACTIONMACHINES].iteritems():
			if am[mddParser.E_F_NAME] == params[2] and am[mddParser.AM_F_CONCURRENTUNIT] == concurrentunitId:
				actionmachineId = i
				actionmachine = am
				break
		else:
			raise Reader.Error("Unknown component '%s'." % params[2])

		suffix = Reader.__suffixes[actionmachine[mddParser.E_F_MODEL]]
		exec("from tema.model." + suffix + "model import Model")
		path = self.__directory + self.__id2filename(params[1] + ' - ' + params[2]) + '.' + suffix
		try:
			f = file(path)
		except IOError:
			raise Reader.Error("Cannot open file '%s'." % path)
		try:
			model = Model()
			model.loadFromFile(f)
		finally:
			f.close()

		for a in model.getActions():
			if str(a) == params[3]:
				try:
					comment = a.getComment()
				except AttributeError:
					comment = ""

				return comment.replace('\\n', '\n')

		for a in model.getStatePropList():
			if str(a) == params[3]:
				try:
					comment = a.getComment()
				except AttributeError:
					comment = ""

				return comment.replace('\\n', '\n')

		raise Reader.Error("Unknown action '%s'." % params[3])

	def __hasRefinementmachine(self, actionmachineId, productId):
		for rm in self.__mdd[mddParser.REFINEMENTMACHINES].itervalues():
			if rm[mddParser.KM_F_ACTIONMACHINE] == actionmachineId and rm[mddParser.KM_F_PRODUCT] == productId:
				return True
		else:
			return False

	def __isActiveP(self, pId):
		for cuId, cu in self.__mdd[mddParser.CONCURRENTUNITS].iteritems():
			if pId in cu[mddParser.CU_F_PRODUCTS] and self.__isActiveCu(cuId, pId):
				return True

		return False

	def __isActiveCu(self, cuId, pId):
		for amId, am in self.__mdd[mddParser.ACTIONMACHINES].iteritems():
			if am[mddParser.AM_F_CONCURRENTUNIT] == cuId and self.__isActiveAm(amId, pId):
				return True

		return False

	def __isActiveAm(self, amId, pId):
		if self.__mdd[mddParser.ACTIONMACHINES][amId][mddParser.E_F_MODEL] != None:
			for rmId, rm in self.__mdd[mddParser.REFINEMENTMACHINES].iteritems():
				if rm[mddParser.KM_F_ACTIONMACHINE] == amId and rm[mddParser.KM_F_PRODUCT] == pId and self.__isActiveRm(rmId):
					return True

		return False

	def __isActiveRm(self, rmId):
		return self.__mdd[mddParser.REFINEMENTMACHINES][rmId][mddParser.E_F_MODEL] != None

	def __isActiveD(self, dId):
		return self.__mdd[mddParser.SYSTEMSUNDERTEST][dId][mddParser.E_F_MODEL] != None

	def __isActiveDt(self, dtId):
		return self.__mdd[mddParser.DATATABLES][dtId][mddParser.E_F_MODEL] != None

	def __id2filename(self, id):
		return ''.join([self.__escapeChar(ch) for ch in id])                               
	
	def __escapeChar(self, ch):
		if self.__isPlainChar(ch):
			return ch
		else:
			hx = hex(ord(ch))[2:]
			if len(hx) == 2:  
				return '%' + hx
			else:
				return '%0' + hx
	
	def __isPlainChar(self, ch):
		return '0' <= ch <= '9' or 'a' <= ch <= 'z' or 'A' <= ch <= 'Z' or ch in '_-'

	def __list2str(self, list):
		if len(list) > 0:
			list.sort()
			return reduce(lambda x,y: x + '\n' + y, list)
		else:
			return ""

if __name__ == '__main__':
	if len(sys.argv) >= 3:
		mddFilePath = sys.argv[1]
		id = sys.argv[2]
		params = sys.argv[3:]
		try:
			print Reader(mddFilePath).getValue(id, params)
		except Exception, e:
			print "\nError: " + str(e) + "\n\n\n" + usage
	else:
		print usage
