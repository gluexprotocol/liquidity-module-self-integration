class SafeMath():

    @staticmethod
    def add(x: int, y: int) -> int:
        z: int = x + y
        if z < x:
            raise Exception ('ds-math-add-overflow')

        return z


    @staticmethod
    def sub(x: int, y: int) -> int:
        z: int = x - y
        if z > x:
            raise Exception ('ds-math-sub-underflow')

        return z


    @staticmethod
    def mul(x: int, y: int) -> int:
        if y == 0:
            return 0

        z: int = x * y
        if (z // y != x ):
            raise Exception ('dds-math-mul-overflow')

        return z

class Math():

  @staticmethod
  def sqrt(x: int):
    y: int = x

    z: int = 181

    if (y >= 0x10000000000000000000000000000000000):
      y >>= 128
      z <<= 64


    if (y >= 0x1000000000000000000):
      y >>= 64
      z <<= 32


    if (y >= 0x10000000000):
      y >>= 32
      z <<= 16


    if (y >= 0x1000000):
      y >>= 16
      z <<= 8


    z = (z * (y + 65536)) >> 18
    z = (x // z + z) >> 1
    z = (x // z + z) >> 1
    z = (x // z + z) >> 1
    z = (x // z + z) >> 1
    z = (x // z + z) >> 1
    z = (x // z + z) >> 1
    z = (x // z + z) >> 1

    return int(z - 1 if (x // z < z) else z)