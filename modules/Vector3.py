from math import cos, pi, pow, sin, sqrt

class Vector3:
    def __init__(self, a: float = float(0.0), b: float = float(0.0), c: float = float(0.0)):
        self.x = float(a) + 0
        self.y = float(b) + 0
        self.z = float(c) + 0

    def __add__(self, rhs):
        if isinstance(rhs, self.__class__):
            return Vector3(self.x + rhs.x, self.y + rhs.y, self.z + rhs.z)
        else:
            return Vector3(self.x + rhs, self.y + rhs, self.z + rhs)

    def __sub__(self, rhs):
        if isinstance(rhs, self.__class__):
            return Vector3(self.x - rhs.x, self.y - rhs.y, self.z - rhs.z)
        else:
            return Vector3(self.x - rhs, self.y - rhs, self.z - rhs)

    def __mul__(self, rhs):
        if isinstance(rhs, self.__class__):
            return Vector3(self.x * rhs.x, self.y * rhs.y, self.z * rhs.z)
        else:
            return Vector3(self.x * rhs, self.y * rhs, self.z * rhs)

    def __truediv__(self, rhs):
        if isinstance(rhs, self.__class__):
            return Vector3(self.x / rhs.x, self.y / rhs.y, self.z / rhs.z)
        else:
            return Vector3(self.x / rhs, self.y / rhs, self.z / rhs)

    def __eq__(self, rhs):
        if isinstance(rhs, self.__class__):
            return (self - rhs).len() <= 0.01
        return False

    def __pow__(self, p):
        return Vector3(self.x ** p, self.y ** p, self.z ** p)

    def __str__(self):
        res = self.round(3)
        return f"{res.x} {res.y} {res.z}"
    
    def __repr__(self):
        return f"<Vector3 \{self.x} {self.y} {self.z}\>"

    def abs(self):
        return Vector3(abs(self.x), abs(self.y), abs(self.z))

    def dot(self, rhs):
        return (self.x * rhs.x) + (self.y * rhs.y) + (self.z * rhs.z)

    def sqrLen(self):
        return self.dot(self)

    def len(self):
        return sqrt(self.sqrLen())

    def normalize(self):
        return self / self.len()

    def cross(self, rhs):
        return Vector3(
            self.y * rhs.z - self.z * rhs.y,
            self.z * rhs.x - self.x * rhs.z,
            self.x * rhs.y - self.y * rhs.x
        )

    def distance(self, rhs):
        return sqrt(pow(self.x - rhs.x, 2) + pow(self.y - rhs.y, 2) + pow(self.z - rhs.z, 2))

    def lerp(self, rhs, alpha):
        return Vector3(
            self.x + ((rhs.x - self.x) * alpha),
            self.y + ((rhs.y - self.y) * alpha),
            self.z + ((rhs.z - self.z) * alpha)
        )

    def round(self, digits=0):
        return Vector3(
            round(self.x, digits), round(self.y, digits), round(self.z, digits)
        )

    def isLegal(self, sides):
        for side in sides:
            facing = (self - side.center()).normalize()
            if facing.dot(side.normal().normalize()) < -0.001:
                return False
        return True

    def rotateX(self, rad):
        Cos = cos(rad)
        Sin = sin(rad)
        return Vector3(self.x, self.y * Cos - self.z * Sin, self.z * Cos + self.y * Sin)
    
    def rotateY(self, rad):
        Cos = cos(rad)
        Sin = sin(rad)
        return Vector3(self.x * Cos - self.z * Sin, self.y, self.z * Cos + self.x * Sin)

    def rotateZ(self, rad):
        Cos = cos(rad)
        Sin = sin(rad)
        return Vector3(self.x * Cos - self.y * Sin, self.y * Cos + self.x * Sin, self.z)

    def rotate(self, rot: 'Vector3'):
        return self.rotateX(rot.x).rotateY(rot.y).rotateZ(rot.z)

    def max(self, rhs: 'Vector3'):
        if max((self.x, self.y, self.z), (rhs.x, rhs.y, rhs.z)) == (self.x, self.y, self.z):
            return self
        else:
            return rhs

    def min(self, rhs: 'Vector3'):
        if min((self.x, self.y, self.z), (rhs.x, rhs.y, rhs.z)) == (self.x, self.y, self.z):
            return self
        else:
            return rhs

def Vector3FromStr(string: str):
    string = string.replace("[","").replace("]","").replace("{","").replace("}","").strip()
    tok = string.split(" ")
    return Vector3(tok[0], tok[1], tok[2])
