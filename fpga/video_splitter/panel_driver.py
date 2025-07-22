from amaranth import *
from amaranth.build import Platform
from amaranth.lib.memory import ReadPort, Memory
from amaranth.lib.wiring import Component, In, Out

from video_splitter.utils import ParallelVideoParams, ParallelVideoBus, ParallelVideoBusInterface

#TODO: this doesn't work with <=2 panels
class SharedParallelBusMultiPanelDriver(Component):
    """Drive multiple panels that use the parallel bus (e.g. RGB888) at the same time, sharing their data and timing lines.

    The clock of each panel is driven at a different phase from the others.
    This makes it possible to transfer the required data rate on the shared lines while not violating the panels' clock speed requirements.
    (Assuming the timing requirements for the data and timing lines are less restrictive than clock, which is the case for most panel drivers.)

    Clock frequency has to be (parallel_bus_pclk * n_panels * 2)
    """

    line_trigger: Signal
    frame_trigger: Signal
    pixel_data: Signal

    def __init__(
        self,
        n_panels: int,
        video_params: ParallelVideoParams,
        line_read_ports: list[ReadPort],
        line_read_offsets: list[int] | None = None,
        keep_clocking_when_paused: bool = False
    ):
        self.n_panels = n_panels
        self.vp = video_params
        self.line_read_ports = line_read_ports
        self.line_read_offsets = line_read_offsets if line_read_offsets is not None else ([0] * self.n_panels)
        self.keep_clocking_when_paused = keep_clocking_when_paused

        super().__init__({
            "line_trigger": In(1),
            "frame_trigger": In(1),
            "pixel_data": Out(self.vp.color_format),  # the shared pixel data output
            **{
                f"video_bus_{i}": Out(ParallelVideoBus(self.vp.color_format)) for i in range(self.n_panels)
            }
        })
        self.video_buses: tuple[ParallelVideoBusInterface, ...] = tuple(
            getattr(self, f"video_bus_{i}") for i in range(self.n_panels))

    _x: Signal
    _y: Signal
    _phase: Signal

    def elaborate(self, platform: Platform | None):
        m = Module()

        TOTAL_WIDTH = self.vp.h_front_porch + self.vp.width + self.vp.h_back_porch
        TOTAL_HEIGHT = self.vp.v_front_porch + self.vp.height + self.vp.v_back_porch
        # >max values indicates "waiting for trigger"
        self._x = Signal(range(TOTAL_WIDTH + 1), reset=TOTAL_WIDTH)
        self._y = Signal(range(TOTAL_HEIGHT + 1), reset=TOTAL_HEIGHT)
        self._phase = Signal(range(self.n_panels * 2), reset=(self.n_panels * 2 - 1))

        # Is in visible region
        is_pixel_area = Signal()
        x_is_pixel_area = Signal()
        y_is_pixel_area = Signal()
        m.d.comb += x_is_pixel_area.eq(
            (self._x >= self.vp.h_front_porch)
            & (self._x < (self.vp.h_front_porch + self.vp.width))
        )
        m.d.comb += y_is_pixel_area.eq(
            (self._y >= self.vp.v_front_porch)
            & (self._y < (self.vp.v_front_porch + self.vp.height))
        )
        m.d.comb += is_pixel_area.eq(x_is_pixel_area & y_is_pixel_area)

        # Line & frame trigger set/reset latch
        line_trigger_sr = Signal()
        frame_trigger_sr = Signal()
        with m.If(self.line_trigger):
            m.d.sync += line_trigger_sr.eq(1)
        with m.If(self.frame_trigger):
            m.d.sync += frame_trigger_sr.eq(1)

        # Increment logic
        is_phase_wrapping = Signal()
        m.d.sync += self._phase.eq(self._phase + 1)
        m.d.comb += is_phase_wrapping.eq(self._phase == (self.n_panels * 2 - 1))
        with m.If(is_phase_wrapping): # phase wrap
            m.d.sync += self._phase.eq(0)
            with m.If(~self._x.all()):
                m.d.sync += self._x.eq(self._x + 1)
            with m.If(self._x >= (TOTAL_WIDTH - 1)): # x wrap
                with m.If(line_trigger_sr | ~y_is_pixel_area):
                    m.d.sync += line_trigger_sr.eq(0)
                    m.d.sync += self._x.eq(0)
                    with m.If(~self._y.all()):
                        m.d.sync += self._y.eq(self._y + 1)
                    with m.If(self._y >= (TOTAL_HEIGHT - 1)): # y wrap
                        with m.If(frame_trigger_sr):
                            m.d.sync += frame_trigger_sr.eq(0)
                            m.d.sync += self._y.eq(0)

        # Is in valid area (not in valid area indicates "waiting for line/frame trigger")
        is_valid_area = Signal()
        m.d.comb += is_valid_area.eq((self._x < TOTAL_WIDTH) & (self._y < TOTAL_HEIGHT))

        # Sync & control signals
        h_sync = Signal()
        m.d.sync += h_sync.eq(self._x < self.vp.h_sync_length)
        v_sync = Signal()
        m.d.sync += v_sync.eq(self._y < self.vp.v_sync_length)
        de = Signal()
        m.d.sync += de.eq(is_pixel_area)

        # Phase related
        target_panel = Signal(range(self.n_panels))
        m.d.comb += target_panel.eq(self._phase // 2)
        target_panel_sync = Signal(range(self.n_panels))
        m.d.sync += target_panel_sync.eq(target_panel)
        is_odd_phase = Signal()
        m.d.comb += is_odd_phase.eq(self._phase % 2)

        for n in range(self.n_panels):
            video_bus: ParallelVideoBusInterface = self.video_buses[n]
            read_port = self.line_read_ports[n]

            # PCLK pulse generator
            pclk_timer = Signal(range(self.n_panels), reset=0, name=f"pclk_timer_{n}")
            with m.If(pclk_timer.bool()):
                m.d.sync += pclk_timer.eq(pclk_timer - 1)
            m.d.comb += video_bus.pclk.eq(pclk_timer.bool())

            # Note: setup data & control lines on even phases, trigger PCLK on odd phases

            # Read line buffer
            # (read next pixel's value on phase wrap so that the pixel data arrive in time for the next pixel)
            m.d.sync += read_port.en.eq(0)
            m.d.comb += read_port.addr.eq(self._x - self.vp.h_front_porch)
            with m.If(is_phase_wrapping):
                with m.If(
                    (self._x >= (self.vp.h_front_porch - 1))
                    & (self._x < (self.vp.h_front_porch + self.vp.width - 1))
                    & y_is_pixel_area
                ):  # the next "pixel" is in pixel area
                    m.d.sync += read_port.en.eq(1)

            # Set pixel data
            with m.If(target_panel_sync == n):
                m.d.comb += self.pixel_data.eq(read_port.data)

            # PCLK trigger
            with m.If(target_panel == n):
                with m.If(is_odd_phase if self.keep_clocking_when_paused else (is_odd_phase & is_valid_area)):
                    m.d.sync += pclk_timer.eq(self.n_panels)

            # Connect video bus
            m.d.comb += video_bus.h_sync.eq(h_sync)
            m.d.comb += video_bus.v_sync.eq(v_sync)
            m.d.comb += video_bus.de.eq(de)

        return m

def _main():
    import string
    from amaranth.sim import Simulator, SimulatorContext

    m = Module()
    vp = ParallelVideoParams(
        8,
        width=8, height=3,
        h_front_porch=2, h_back_porch=2,
        v_front_porch=2, v_back_porch=2,
        h_sync_length=2, v_sync_length=2
    )
    line_buffer_data = list([int(f"{string.ascii_uppercase[n]}{i}", base=16) for i in range(vp.width)] for n in range(3))
    line_buffers = [Memory(shape=8, depth=vp.width, init=line_buffer_data[i]) for i in range(3)]
    for i, lb in enumerate(line_buffers):
        m.submodules[f"line_buffer_{i}"] = lb

    drv = SharedParallelBusMultiPanelDriver(
        n_panels=3,
        video_params=vp,
        line_read_ports=[lb.read_port() for lb in line_buffers],
        line_read_offsets=[0, 0, 0],
        keep_clocking_when_paused=False
    )
    m.submodules += drv

    async def tb(ctx: SimulatorContext):
        ctx.set(drv.frame_trigger, True)
        ctx.set(drv.line_trigger, True)
        await ctx.tick().repeat(6*12*7*3)

    sim = Simulator(m)
    sim.add_clock(1 / 100e6)
    sim.add_testbench(tb)
    file = "sim/SharedParallelBusMultiPanelDriver"
    with sim.write_vcd(f"{file}.vcd", traces=[]):
        sim.run()

    import subprocess
    subprocess.run(["../bin/surfer.exe", f"{file}.vcd", "-s", f"{file}.surf.ron"])

if __name__ == "__main__":
    _main()
