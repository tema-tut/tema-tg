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

import tema.eini.einiparser as einiparser

class Parser(einiparser.Parser):
	DOMAIN				= "domain"
	PRODUCTFAMILIES			= "productfamilies"
	PRODUCTS			= "products"
	CONCURRENTUNITS			= "concurrentunits"
	ACTIONMACHINES			= "actionmachines"
	REFINEMENTMACHINES		= "refinementmachines"
	LAUNCHMACHINES			= "launchmachines"
	INITIALIZATIONMACHINES		= "initializationmachines"
	SYSTEMSUNDERTEST		= "systemsundertest"
	DATATABLES			= "datatables"

	D_I_NAME			= "name"
	D_I_PF_ALIAS			= "pf_alias"
	D_I_P_ALIAS			= "p_alias"
	D_I_CU_ALIAS			= "cu_alias"
	D_I_ST_ALIAS			= "st_alias"
	D_F_VALUE			= "value"

	E_F_NAME			= "name"
	E_F_MODEL			= "model"
	E_F_LINK			= "link"

	P_F_PRODUCTFAMILY		= "productfamily"

	CU_F_PRODUCTS			= "products"

	AM_F_CONCURRENTUNIT		= "concurrentunit"
	AM_F_DEPENDENCIES		= "dependencies"
	AM_F_DATAREQUIREMENT		= "requireddata"

	KM_F_ACTIONMACHINE		= "actionmachine"
	KM_F_PRODUCT			= "product"

	ST_F_PRODUCT			= "product"



	__ERROR_N_ENTITY		= "Entity '%s' must be defined."
	__ERROR_N_INSTANCE		= "Instance '%s' must be defined for the entity '%s'."
	__ERROR_A			= "Field '%s' must be defined for the entity '%s'."
	__ERROR_T_STR			= "Field '%s' of the entity '%s' may not be a list."
	__ERROR_T_LIST			= "Field '%s' of the entity '%s' must be a list."
	__ERROR_V_EMPTY			= "Value of the field '%s' of the instance '%s' of the entity '%s' may not be empty."
	__ERROR_V_REF			= "Value of the field '%s' of the instance '%s' of the entity '%s' must refer " \
                                          "to an instance of the entity '%s'."
	__ERROR_V_REFS			= "Value of the field '%s' of the instance '%s' of the entity '%s' must refer " \
                                          "to instances of the entity '%s'."
	__ERROR_V_REF_CONTEXT		= "Value of the field '%s' of the instance '%s' of the entity '%s' must refer " \
                                          "to an ancestor instance of the entity '%s'."
	__ERROR_V_UNIQUE_CONTEXT	= "Values of the field '%s' of the instances of the entity '%s' must be unique " \
                                          "within the context of '%s'."
	__ERROR_V_UNIQUE		= "Values of the field '%s' of the instances of the entity '%s' must be unique."
	__ERROR_V_UNIQUES		= "Combined values of the fields '%s' and '%s' of the instances of the entity " \
                                          "'%s' must be unique."
	__ERROR_V_DEPEND_NONE		= "Instance '%s' of the entity '%s' has field '%s' and therefore must have field " \
                                          "'%s'."
	__ERROR_V_CONFLICT		= "Instances '%s' and '%s' of the entity '%s' must have the same value in field " \
                                          "'%s'."
	__ERROR_V_RING			= "Fields '%s' of the entity '%s' must form a ring."



	def parse(self, fileobj):
		result=einiparser.Parser.parse(self, fileobj)

		if Parser.DOMAIN not in result:
			raise NameError(__ERROR_N_ENTITY % DOMAIN)
		self.__handleDomain(result[Parser.DOMAIN])

		if Parser.PRODUCTFAMILIES not in result:
			productfamilies = einiparser.Entity()
			productfamilies.fields()[Parser.E_F_NAME] = str
			result[Parser.PRODUCTFAMILIES] = productfamilies
		self.__handleProductFamilies(result[Parser.PRODUCTFAMILIES])

		if Parser.PRODUCTS not in result:
			products = einiparser.Entity()
			products.fields()[Parser.E_F_NAME] = str
			products.fields()[Parser.P_F_PRODUCTFAMILY] = str
			result[Parser.PRODUCTS] = products
		self.__handleProducts(result[Parser.PRODUCTS], result[Parser.PRODUCTFAMILIES])

		if Parser.CONCURRENTUNITS not in result:
			concurrentunits = einiparser.Entity()
			concurrentunits.fields()[Parser.E_F_NAME] = str
			concurrentunits.fields()[Parser.CU_F_PRODUCTS] = list
			result[Parser.CONCURRENTUNITS] = concurrentunits
		self.__handleConcurrentUnits(result[Parser.CONCURRENTUNITS], result[Parser.PRODUCTS])

		if Parser.ACTIONMACHINES not in result:
			actionmachines = einiparser.Entity()
			actionmachines.fields()[Parser.E_F_NAME] = str
			actionmachines.fields()[Parser.AM_F_CONCURRENTUNIT] = str
			actionmachines.fields()[Parser.AM_F_DEPENDENCIES] = list
			result[Parser.ACTIONMACHINES] = actionmachines
		self.__handleActionMachines(result[Parser.ACTIONMACHINES], result[Parser.CONCURRENTUNITS])

		if Parser.REFINEMENTMACHINES not in result:
			refinementmachines = einiparser.Entity()
			refinementmachines.fields()[Parser.KM_F_ACTIONMACHINE] = str
			refinementmachines.fields()[Parser.KM_F_PRODUCT] = str
			result[Parser.REFINEMENTMACHINES] = refinementmachines
		self.__handleRefinementMachines(result[Parser.REFINEMENTMACHINES], result[Parser.ACTIONMACHINES], \
                                                result[Parser.CONCURRENTUNITS], result[Parser.PRODUCTS])

		if Parser.LAUNCHMACHINES not in result:
			launchmachines = einiparser.Entity()
			launchmachines.fields()[Parser.KM_F_ACTIONMACHINE] = str
			launchmachines.fields()[Parser.KM_F_PRODUCT] = str
			result[Parser.LAUNCHMACHINES] = launchmachines
		self.__handleLaunchMachines(result[Parser.LAUNCHMACHINES], result[Parser.ACTIONMACHINES], \
                                            result[Parser.CONCURRENTUNITS], result[Parser.PRODUCTS])

		if Parser.INITIALIZATIONMACHINES not in result:
			initializationmachines = einiparser.Entity()
			initializationmachines.fields()[Parser.KM_F_ACTIONMACHINE] = str
			initializationmachines.fields()[Parser.KM_F_PRODUCT] = str
			result[Parser.INITIALIZATIONMACHINES] = initializationmachines
		self.__handleInitializationMachines(result[Parser.INITIALIZATIONMACHINES], \
                                                    result[Parser.ACTIONMACHINES], result[Parser.CONCURRENTUNITS], \
                                                    result[Parser.PRODUCTS])

		if Parser.SYSTEMSUNDERTEST not in result:
			systemsundertest = einiparser.Entity()
			systemsundertest.fields()[Parser.E_F_NAME] = str
			systemsundertest.fields()[Parser.ST_F_PRODUCT] = str
			result[Parser.SYSTEMSUNDERTEST] = systemsundertest
		self.__handleSystemsUnderTest(result[Parser.SYSTEMSUNDERTEST], result[Parser.PRODUCTS])

		if Parser.DATATABLES not in result:
			datatables = einiparser.Entity()
			datatables.fields()[Parser.E_F_NAME] = str
			result[Parser.DATATABLES] = datatables
		self.__handleDataTables(result[Parser.DATATABLES])

		return result



	def __handleDomain(self, domain):
		if Parser.D_F_VALUE not in domain.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.D_F_VALUE, Parser.DOMAIN))

		if domain.fields()[Parser.D_F_VALUE] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.D_F_VALUE, Parser.DOMAIN))

		if Parser.D_I_NAME not in domain:
			raise NameError(Parser.__ERROR_N_INSTANCE % (Parser.D_I_NAME, Parser.DOMAIN))
		if Parser.D_I_PF_ALIAS not in domain:
			domain[Parser.D_I_PF_ALIAS] = {Parser.D_F_VALUE: None}
		if Parser.D_I_P_ALIAS not in domain:
			domain[Parser.D_I_P_ALIAS] = {Parser.D_F_VALUE: None}
		if Parser.D_I_CU_ALIAS not in domain:
			domain[Parser.D_I_CU_ALIAS] = {Parser.D_F_VALUE: None}
		if Parser.D_I_ST_ALIAS not in domain:
			domain[Parser.D_I_ST_ALIAS] = {Parser.D_F_VALUE: None}

		if len(domain[Parser.D_I_NAME][Parser.D_F_VALUE]) == 0:
			raise ValueError(Parser.__ERROR_V_EMPTY % (Parser.D_F_VALUE, Parser.D_I_NAME, Parser.DOMAIN))
		if domain[Parser.D_I_PF_ALIAS][Parser.D_F_VALUE] != None:
			if len(domain[Parser.D_I_PF_ALIAS][Parser.D_F_VALUE]) == 0:
				raise ValueError(Parser.__ERROR_V_EMPTY % \
                                                 (Parser.D_F_VALUE, Parser.D_I_PF_ALIAS, Parser.DOMAIN))
		if domain[Parser.D_I_P_ALIAS][Parser.D_F_VALUE] != None:
			if len(domain[Parser.D_I_P_ALIAS][Parser.D_F_VALUE]) == 0:
				raise ValueError(Parser.__ERROR_V_EMPTY % \
                                                 (Parser.D_F_VALUE, Parser.D_I_P_ALIAS, Parser.DOMAIN))
		if domain[Parser.D_I_CU_ALIAS][Parser.D_F_VALUE] != None:
			if len(domain[Parser.D_I_CU_ALIAS][Parser.D_F_VALUE]) == 0:
				raise ValueError(Parser.__ERROR_V_EMPTY % \
                                                 (Parser.D_F_VALUE, Parser.D_I_CU_ALIAS, Parser.DOMAIN))
		if domain[Parser.D_I_ST_ALIAS][Parser.D_F_VALUE] != None:
			if len(domain[Parser.D_I_ST_ALIAS][Parser.D_F_VALUE]) == 0:
				raise ValueError(Parser.__ERROR_V_EMPTY % \
                                                 (Parser.D_F_VALUE, Parser.D_I_ST_ALIAS, Parser.DOMAIN))



	def __handleProductFamilies(self, productfamilies):
		self.__checkName(productfamilies, Parser.PRODUCTFAMILIES)

		if len(dict().fromkeys([v[Parser.E_F_NAME].lower() for v in productfamilies.itervalues()])) < \
                   len(productfamilies):
			raise ValueError(Parser.__ERROR_V_UNIQUE % (Parser.E_F_NAME, Parser.PRODUCTFAMILIES))



	def __handleProducts(self, products, productfamilies):
		self.__checkName(products, Parser.PRODUCTS)

		if Parser.P_F_PRODUCTFAMILY not in products.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.P_F_PRODUCTFAMILY, Parser.PRODUCTS))

		if products.fields()[Parser.P_F_PRODUCTFAMILY] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.P_F_PRODUCTFAMILY, Parser.PRODUCTS))

		names = {}
		for k, v in products.iteritems():
			if v[Parser.P_F_PRODUCTFAMILY] not in productfamilies:
				raise ValueError(Parser.__ERROR_V_REF % \
                                                 (Parser.P_F_PRODUCTFAMILY, k, Parser.PRODUCTS, \
                                                  Parser.PRODUCTFAMILIES))

			if v[Parser.E_F_NAME].lower() in names:
				raise ValueError(Parser.__ERROR_V_UNIQUE % (Parser.E_F_NAME, Parser.PRODUCTS))
			names[v[Parser.E_F_NAME].lower()] = None



	def __handleConcurrentUnits(self, concurrentunits, products):
		self.__checkName(concurrentunits, Parser.CONCURRENTUNITS)

		if Parser.CU_F_PRODUCTS not in concurrentunits.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.CU_F_PRODUCTS, Parser.CONCURRENTUNITS))

		if concurrentunits.fields()[Parser.CU_F_PRODUCTS] != list:
			raise TypeError(Parser.__ERROR_T_LIST % (Parser.CU_F_PRODUCTS, Parser.CONCURRENTUNITS))

		names = {}
		name_ids = {}
		for k, v in concurrentunits.iteritems():
			if len(v[Parser.CU_F_PRODUCTS]) == 0:
				raise ValueError(Parser.__ERROR_V_EMPTY % \
                                                 (Parser.CU_F_PRODUCTS, k, Parser.CONCURRENTUNITS))

			for i in v[Parser.CU_F_PRODUCTS]:
				if i not in products:
					raise ValueError(Parser.__ERROR_V_REFS % \
                                                         (Parser.CU_F_PRODUCTS, k, Parser.CONCURRENTUNITS, \
                                                          Parser.PRODUCTS))

			if v[Parser.E_F_NAME].lower() in names:
				raise ValueError(Parser.__ERROR_V_UNIQUE % (Parser.E_F_NAME, Parser.CONCURRENTUNITS))
			names[v[Parser.E_F_NAME].lower()] = None



	def __handleActionMachines(self, actionmachines, concurrentunits):
		self.__checkName(actionmachines, Parser.ACTIONMACHINES)
		self.__checkModel(actionmachines, Parser.ACTIONMACHINES)

		if Parser.AM_F_CONCURRENTUNIT not in actionmachines.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.AM_F_CONCURRENTUNIT, Parser.ACTIONMACHINES))
		if Parser.AM_F_DEPENDENCIES not in actionmachines.fields():
			actionmachines.fields()[Parser.AM_F_DEPENDENCIES] = list
			for v in actionmachines.itervalues():
				v[Parser.AM_F_DEPENDENCIES] = None
		if Parser.AM_F_DATAREQUIREMENT not in actionmachines.fields():
			actionmachines.fields()[Parser.AM_F_DATAREQUIREMENT] = list
			for v in actionmachines.itervalues():
				v[Parser.AM_F_DATAREQUIREMENT] = None

		if actionmachines.fields()[Parser.AM_F_CONCURRENTUNIT] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.AM_F_CONCURRENTUNIT, Parser.ACTIONMACHINES))
		if actionmachines.fields()[Parser.AM_F_DEPENDENCIES] != list:
			raise TypeError(Parser.__ERROR_T_LIST % (Parser.AM_F_DEPENDENCIES, Parser.ACTIONMACHINES))
		if actionmachines.fields()[Parser.AM_F_DATAREQUIREMENT] != list:
			raise TypeError(Parser.__ERROR_T_LIST % (Parser.AM_F_DATAREQUIREMENT, Parser.ACTIONMACHINES))

		names = {}
		for k, v in actionmachines.iteritems():
			if v[Parser.AM_F_CONCURRENTUNIT] not in concurrentunits:
				raise ValueError(Parser.__ERROR_V_REF % \
                                                 (Parser.AM_F_CONCURRENTUNIT, k, Parser.ACTIONMACHINES, \
                                                  Parser.CONCURRENTUNITS))

			if v[Parser.AM_F_CONCURRENTUNIT] in names:
				if v[Parser.E_F_NAME].lower() in names[v[Parser.AM_F_CONCURRENTUNIT]]:
					raise ValueError(Parser.__ERROR_V_UNIQUE_CONTEXT % \
                                                         (Parser.E_F_NAME, Parser.ACTIONMACHINES, \
                                                          Parser.CONCURRENTUNITS))
			else:
				names[v[Parser.AM_F_CONCURRENTUNIT]] = {}
			names[v[Parser.AM_F_CONCURRENTUNIT]][v[Parser.E_F_NAME].lower()] = None



	def __handleRefinementMachines(self, refinementmachines, actionmachines, concurrentunits, products):
		self.__handleKeywordMachines(refinementmachines, actionmachines, concurrentunits, products, \
                                             Parser.REFINEMENTMACHINES)



	def __handleLaunchMachines(self, launchmachines, actionmachines, concurrentunits, products):
		self.__handleKeywordMachines(launchmachines, actionmachines, concurrentunits, products, \
                                             Parser.REFINEMENTMACHINES)



	def __handleInitializationMachines(self, initializationmachines, actionmachines, concurrentunits, products):
		self.__handleKeywordMachines(initializationmachines, actionmachines, concurrentunits, products, \
                                             Parser.REFINEMENTMACHINES)



	def __handleSystemsUnderTest(self, systemsundertest, products):
		self.__checkName(systemsundertest, Parser.SYSTEMSUNDERTEST)
		self.__checkModel(systemsundertest, Parser.SYSTEMSUNDERTEST)

		if Parser.ST_F_PRODUCT not in systemsundertest.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.ST_F_PRODUCT, Parser.SYSTEMSUNDERTEST))

		if systemsundertest.fields()[Parser.ST_F_PRODUCT] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.ST_F_PRODUCT, Parser.SYSTEMSUNDERTEST))

		names = {}
		for k, v in systemsundertest.iteritems():
			if v[Parser.ST_F_PRODUCT] not in products:
				raise ValueError(Parser.__ERROR_V_REF % \
                                                 (Parser.ST_F_PRODUCT, k, Parser.SYSTEMSUNDERTEST, Parser.PRODUCTS))

			if v[Parser.ST_F_PRODUCT] in names:
				if v[Parser.E_F_NAME].lower() in names[v[Parser.ST_F_PRODUCT]]:
					raise ValueError(Parser.__ERROR_V_UNIQUE_CONTEXT % \
                                                         (Parser.E_F_NAME, Parser.SYSTEMSUNDERTEST, Parser.PRODUCTS))
			else:
				names[v[Parser.ST_F_PRODUCT]] = {}
			names[v[Parser.ST_F_PRODUCT]][v[Parser.E_F_NAME].lower()] = None



	def __handleDataTables(self, datatables):
		self.__checkName(datatables, Parser.DATATABLES)
		self.__checkModel(datatables, Parser.DATATABLES)

		if len(dict().fromkeys([v[Parser.E_F_NAME].lower() for v in datatables.itervalues()])) < len(datatables):
			raise ValueError(Parser.__ERROR_V_UNIQUE % (Parser.E_F_NAME, Parser.DATATABLES))

		

	def __handleKeywordMachines(self, keywordmachines, actionmachines, concurrentunits, products, entityName):
		self.__checkModel(keywordmachines, entityName)

		if Parser.KM_F_ACTIONMACHINE not in keywordmachines.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.KM_F_ACTIONMACHINE, entityName))
		if Parser.KM_F_PRODUCT not in keywordmachines.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.KM_F_PRODUCT, entityName))

		if keywordmachines.fields()[Parser.KM_F_ACTIONMACHINE] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.KM_F_ACTIONMACHINE, entityName))
		if keywordmachines.fields()[Parser.KM_F_PRODUCT] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.KM_F_PRODUCT, entityName))

		keys = {}
		for k, v in keywordmachines.iteritems():
			if v[Parser.KM_F_ACTIONMACHINE] not in actionmachines:
				raise ValueError(Parser.__ERROR_V_REF % \
                                                 (Parser.KM_F_ACTIONMACHINE, k, entityName, Parser.ACTIONMACHINES))
			if v[Parser.KM_F_PRODUCT] not in concurrentunits[actionmachines[v[Parser.KM_F_ACTIONMACHINE]] \
                                                                                         [Parser.AM_F_CONCURRENTUNIT]] \
                                                                          [Parser.CU_F_PRODUCTS]:
				raise ValueError(Parser.__ERROR_V_REF_CONTEXT % \
                                                 (Parser.KM_F_PRODUCT, k, entityName, Parser.PRODUCTS))
			if (v[Parser.KM_F_ACTIONMACHINE], v[Parser.KM_F_PRODUCT]) in keys:
				raise ValueError(Parser.__ERROR_V_UNIQUES % (Parser.KM_F_ACTIONMACHINE, \
                                                                             Parser.KM_F_PRODUCT, entityName))
			keys[(v[Parser.KM_F_ACTIONMACHINE], v[Parser.KM_F_PRODUCT])] = None



	def __checkName(self, entity, entityName):
		if Parser.E_F_NAME not in entity.fields():
			raise AttributeError(Parser.__ERROR_A % (Parser.E_F_NAME, entityName))

		if entity.fields()[Parser.E_F_NAME] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.E_F_NAME, entityName))

		for k, v in entity.iteritems():
			if len(v[Parser.E_F_NAME]) == 0:
				raise ValueError(Parser.__ERROR_V_EMPTY % (Parser.E_F_NAME, k, entityName))



	def __checkModel(self, entity, entityName):
		if Parser.E_F_MODEL not in entity.fields():
			entity.fields()[Parser.E_F_MODEL] = str
			for v in entity.itervalues():
				v[Parser.E_F_MODEL] = None
		if Parser.E_F_LINK not in entity.fields():
			entity.fields()[Parser.E_F_LINK] = str
			for v in entity.itervalues():
				v[Parser.E_F_LINK] = None

		if entity.fields()[Parser.E_F_MODEL] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.E_F_MODEL, entityName))
		if entity.fields()[Parser.E_F_LINK] != str:
			raise TypeError(Parser.__ERROR_T_STR % (Parser.E_F_LINK, entityName))

		handledLinks = {}
		for k, v in entity.iteritems():
			if v[Parser.E_F_MODEL] != None and len(v[Parser.E_F_MODEL]) == 0:
				raise ValueError(Parser.__ERROR_V_EMPTY % (Parser.E_F_MODEL, k, entityName))

			link = v[Parser.E_F_LINK]
			if link != None:
				if v[Parser.E_F_MODEL] == None:
					raise ValueError(Parser.__ERROR_V_DEPEND_NONE % (k, entityName, Parser.E_F_LINK, \
                                                                                         Parser.E_F_MODEL))

				if k not in handledLinks:
					while link != k:
						if link == None or link in handledLinks:
							raise ValueError(Parser.__ERROR_V_RING % (Parser.E_F_LINK, \
                                                                                                  entityName))
						if link not in entity:
							raise ValueError(Parser.__ERROR_V_REF % (link, k, entityName, \
                                                                                                 entityName))
						if entity[link][Parser.E_F_MODEL] != v[Parser.E_F_MODEL]:
							raise ValueError(Parser.__ERROR_V_CONFLICT % (k, link, entityName, \
                                                                                                      Parser.E_F_MODEL))
						handledLinks[link] = None
						link = entity[link][Parser.E_F_LINK]
				handledLinks[k] = None
