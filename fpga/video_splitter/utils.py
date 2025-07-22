from dataclasses import dataclass

from amaranth import *
from amaranth.build import Resource, Subsignal, Pins, Platform
from amaranth.lib.cdc import AsyncFFSynchronizer
from amaranth.lib.wiring import Signature, In, Out, PureInterface, Component
from amaranth.lib.data import Struct
from amaranth_boards.resources import *

from video_splitter.parallel_video_receiver import ParallelVideoReceiver

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

class RGB888(Struct):
    r: 8
    g: 8
    b: 8

def ParallelVideoBusResource(
    name: str,
    number: int,
    dir: str,
    shape: int,
    data: str,
    h_sync: str | None,
    v_sync: str | None,
    de: str | None,
    pclk: str | None,
    conn=None,
    attrs=None
):
    ios = [Subsignal("data", Pins(data, dir=dir, conn=conn, assert_width=shape))]
    if h_sync is not None:
        ios.append(Subsignal("h_sync", Pins(h_sync, dir=dir, conn=conn, assert_width=1)))
    if v_sync is not None:
        ios.append(Subsignal("v_sync", Pins(v_sync, dir=dir, conn=conn, assert_width=1)))
    if de is not None:
        ios.append(Subsignal("de", Pins(de, dir=dir, conn=conn, assert_width=1)))
    if pclk is not None:
        ios.append(Subsignal("pclk", Pins(pclk, dir=dir, conn=conn, assert_width=1)))

    if attrs is not None:
        ios.append(attrs)

    return Resource.family(name, number, ios=ios, default_name="parallel_video_bus")

def SetSynchronizer(m: Module, out: Signal, in_domain: str, out_domain: str):
    """When `trigger` (the signal returned from the function) is asserted, assert `out`.

    Note that `out` is not automatically deasserted.
    Also, `trigger` is set low; it's expected to be overridden to high to trigger assertion of `out`.
    """

    trigger = Signal()
    m.d[in_domain] += trigger.eq(0)
    raw_out = Signal()
    m.submodules += AsyncFFSynchronizer(trigger, raw_out, o_domain=out_domain)
    with m.If(raw_out):
        m.d[out_domain] += out.eq(1)
    return trigger
