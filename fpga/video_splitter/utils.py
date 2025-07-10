from dataclasses import dataclass

from amaranth import *
from amaranth.lib.wiring import Signature, In, Out, PureInterface
from amaranth.lib.data import Struct

@dataclass(frozen=True)
class ParallelVideoParams:
    color_format: type[Struct] | int
    width: int
    height: int

    h_front_porch: int
    h_back_porch: int
    v_front_porch: int
    v_back_porch: int

    h_sync_length: int
    v_sync_length: int

    @property
    def color_depth(self):
        return self.color_format if isinstance(self.color_format, int) else self.color_format.as_shape().size

class ParallelVideoBus(Signature):
    def __init__(self, color_format: type[Struct]):
        self.color_format = color_format
        super().__init__({
            "pclk": Out(1),
            "data": Out(self.color_format),
            "h_sync": Out(1),
            "v_sync": Out(1),
            "de": Out(1)
        })

    def create(self, *, path=None, src_loc_at=0):
        return ParallelVideoBusInterface(self, path=path, src_loc_at=1 + src_loc_at)

class ParallelVideoBusInterface(PureInterface):
    pclk: Signal
    data: Signal
    h_sync: Signal
    v_sync: Signal
    de: Signal
    pass

class RGB888(Struct):
    r: 8
    g: 8
    b: 8
