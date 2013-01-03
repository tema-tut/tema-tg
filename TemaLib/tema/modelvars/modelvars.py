import sys



class ModelVarException(Exception):
	def __init__(self, row, msg):
		self.row = row
		self.msg = msg

	def __str__(self):
		return "error in model variable definition on line\n\t" + row + "\n" + msg

class VarSyntaxException(ModelVarException):
	pass

class ValTypeException(ModelVarException):
	pass

class ValCountException(ModelVarException):
	pass

class DuplicateVarException(ModelVarException):
	pass

def error(msg):
	sys.stderr.write(msg + '\n')
	sys.exit(1)



def parse_vars(raw_var_defs):
	def is_seq(val):
		return isinstance(val, list) or isinstance(val, tuple)

	def is_prim(val):
		return isinstance(val, str) or isinstance(val, int) or (val == None)

	rows = []
	for raw_row in raw_var_defs.split('\n'):
		i = raw_row.find('#')
		if i == -1:
			row = raw_row.strip()
		else:
			row = raw_row[:i].strip()

		if row != "":
			rows.append(row)

	values_all = {}
	values_comb = {}

	for row in rows:
		vars, vals = row.split(':', 1)
		vars = [var.strip() for var in vars.split(',')]
		for var in vars:
			if var == "":
				raise VarSyntaxException(row, "empty variable name")
			for c in var:
				if not (c.isalnum() or c == '_'):
					raise VarSyntaxException(row, "illegal character '" + c + "' in variable name")

		if vals.strip() == "":
			vals = ()
		else:
			try:
				vals = eval(vals)
			except:
				raise VarSyntaxException(row, "cannot evaluate value sequence")

		if not is_seq(vals):
			vals = ((vals,),)

		else:
			for val in vals:
				if is_seq(val):
					break
			else:
				if len(vars) == 1:
					vals = [(val,) for val in vals]
				else:
					vals = (vals,)

		for val in vals:
			if (not is_seq(val)) or (len(val) != len(vars)):
				raise ValCountException(row, "subvalue count doesn\'t match variable count")

			for subval in val:
				if not is_prim(subval):
					raise ValTypeException(row, "only string and integer values and None are allowed")

		for i in range(len(vars)):
			val_set = values_all.get(str(vars[i]), None)
			if val_set == None:
				val_set = set()
				values_all[str(vars[i])] = val_set

			for val in vals:
				if val[i] != None:
					val_set.add(val[i])

		vars_sorted = [var for var in vars]
		vars_sorted.sort()
		for i in range(len(vars_sorted) - 1):
			if vars_sorted[i] == vars_sorted[i+1]:
				raise DuplicateVarException(row, "variable may not occur multiple times in one definition")
		vars_sorted = tuple(vars_sorted)

		sorting = len(vars)*[None]
		for i in range(len(vars)):
			for j in range(len(vars_sorted)):
				if vars[i] == vars_sorted[j]:
					sorting[j] = i
					break

		val_set = values_comb.get(vars_sorted)
		if val_set == None:
			val_set = set()
			values_comb[vars_sorted] = val_set

		for val in vals:
			val_sorted = len(val)*[None]
			for i in range(len(sorting)):
				val_sorted[i] = val[sorting[i]]
			val_set.add(tuple(val_sorted))

	return values_all, values_comb



def get_values(values_all, values_comb, vars):
	vars = tuple(vars)

	values_set = set([()])
	for var in vars:
		next_values_set = set()
		for var_val in values_all.get(var, []):
			for prev_val in values_set:
				next_values_set.add(prev_val + (var_val,))
		values_set = next_values_set

	var_subsets = set()
	next_subsets = set([vars])
	while next_subsets != set([()]):
		var_subsets |= next_subsets
		prev_subsets = next_subsets
		next_subsets = set()
		for subset in prev_subsets:
			for i in range(len(subset)):
				next_subsets.add(subset[:i] + subset[i+1:])

	var_indices = {}
	for i in range(len(vars)):
		var_indices[vars[i]] = i

	for var_subset in var_subsets:
		combinations = values_comb.get(var_subset, None)
		if combinations != None:
			new_values = set()

			for values in values_set:
				var_vals = ()
				for var in var_subset:
					var_vals += (values[var_indices[var]],)

				if var_vals in combinations:
					new_values.add(values)

			values_set = new_values

	return values_set
