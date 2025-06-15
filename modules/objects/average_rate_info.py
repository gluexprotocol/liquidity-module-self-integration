class AverageRateInfo(object):
	MAX_UINT112 = 2**112 - 1

	def __init__(self, encoded=None, t=None, n=None, d=None):
		# t = current time
		if t is None:
			self.t = self._decodeAverageRateT(encoded)
		else:
			self.t = t
		# n = token1
		if n is None:
			self.n = self._decodeAverageRateN(encoded)
		else:
			self.n = n
		# d = token2
		if d is None:
			self.d = self._decodeAverageRateD(encoded)
		else:
			self.d = d

	def _decodeAverageRateT(self, encoded):
		return encoded >> 224
	
	def _decodeAverageRateN(self, encoded):
		return (encoded >> 112) & self.MAX_UINT112
	
	def _decodeAverageRateD(self, encoded):
		return encoded & self.MAX_UINT112
	
	def encode(self):
		return (self.t << 224) | (self.n << 112) | self.d