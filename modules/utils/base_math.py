from decimal import Decimal, getcontext

# Setting the precision for decimal operations
getcontext().prec = 30

WAD = Decimal('1e18')
halfWAD = WAD / 2

RAY = Decimal('1e27')
halfRAY = RAY / 2

WAD_RAY_RATIO = Decimal('1e9')

def ray():
    return RAY

def wad():
    return WAD

def halfRay():
    return halfRAY

def halfWad():
    return halfWAD

def wadMul(a, b):
    return (halfWAD + (a * b)) / WAD

def wadDiv(a, b):
    halfB = Decimal(b / 2)
    return (halfB + (a * WAD)) / b

def rayMul(a, b):
    a = Decimal(a)
    b = Decimal(b)
    return (halfRAY + (a * b)) / RAY

def rayDiv(a, b):
    a = Decimal(a)
    b = Decimal(b)
    halfB = b / 2
    return (halfB + (a * RAY)) / b

def rayToWad(a):
    halfRatio = WAD_RAY_RATIO / 2
    return (halfRatio + a) / WAD_RAY_RATIO

def wadToRay(a):
    return a * WAD_RAY_RATIO

def rayPow(x, n):
    z = x if n % 2 != 0 else RAY
    n = n // 2
    while n != 0:
        x = rayMul(x, x)
        if n % 2 != 0:
            z = rayMul(z, x)
        n = n // 2
    return z