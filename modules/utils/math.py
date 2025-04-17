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
    
    @staticmethod
    def div(x: int, y: int) -> int:
        if y == 0:
            raise Exception ('ds-math-div-zero')
        
        z: int = x // y
        return z

    @staticmethod
    def muldiv(x: int, y: int, z: int) -> int:
        return SafeMath.div(SafeMath.mul(x, y), z)
