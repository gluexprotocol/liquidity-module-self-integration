class Math:
	@staticmethod
	def reduced_ratio(n, d, max_value):
		new_n, new_d = n, d
		if new_n > max_value or new_d > max_value:
			new_n, new_d = Math.normalized_ratio(new_n, new_d, max_value)
		if new_n != new_d:
			return new_n, new_d
		return 1, 1
	
	@staticmethod
	def normalized_ratio(n, d, max_value):
		if n <= d:
			return Math.accurate_ratio(n, d, max_value)
		y, x = Math.accurate_ratio(d, n, max_value)
		return x, y

	@staticmethod
	def accurate_ratio(a, b, scale):
		max_val = 2**256 // scale
		if a > max_val:
			c = a // (max_val + 1) + 1
			a //= c
			b //= c
		if a != b:
			new_n = a * scale
			new_d = a + b
			if new_d >= a:
				x = Math.round_div(new_n, new_d)
				y = scale - x
				return x, y
			if new_n < b - (b - a) // 2:
				return 0, scale
			return 1, scale - 1
		return scale // 2, scale // 2
	
	@staticmethod
	def round_div(n, d):
		if d == 0:
			return 0
		return n // d + (n % d) // (d - d // 2)