from .Vector3 import Vector3

class AABB:
    min: Vector3
    max: Vector3

    def __init__(self, _min: Vector3 = Vector3.Zero(), _max: Vector3 = Vector3.Zero()) -> 'AABB':
        self.min = _min
        self.max = _max
    
    def update(self, new):
        self.min = self.min.min(new)
        self.max = self.max.max(new)

    @staticmethod
    def FromPoint(self, point: Vector3, size: int = 8) -> 'AABB':
        hs = size / 2 # half size
        _min = point + Vector3(hs, -hs, -hs)
        _max = point + Vector3(-hs, hs, hs)
        return AABB(_min, _max)
    
    def IsTouching(self, box: 'AABB') -> bool:
        return (
            (self.min.x <= box.max.x and self.max.x >= box.min.x) and
            (self.min.x <= box.max.y and self.max.y >= box.min.y) and
            (self.min.x <= box.max.z and self.max.z >= box.min.z)
        )