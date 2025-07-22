from amaranth import *
from amaranth.build import Platform
from amaranth.lib.cdc import AsyncFFSynchronizer, PulseSynchronizer

from video_splitter.plat import ICESugarProPlatform, WorldCubeDriverValidationBoardPlatform
from video_splitter.panel_driver import SharedParallelBusMultiPanelDriver
from video_splitter.double_buffer import SwappableDoubleBufferMemory
from video_splitter.utils import ParallelVideoParams, RGB888, SetSynchronizer

# TODO: support ICE40?

class VideoSplitterTop(Elaboratable):
    def __init__(
        self,
        video_params: ParallelVideoParams,
        n_panels: int,
        video_in_pclk_max_freq: float,
        video_out_clk: Signal
    ):
        self.vp = video_params
        self.n_panels = n_panels
        self.video_in_pclk_max_freq = video_in_pclk_max_freq
        self.video_out_clk = video_out_clk

    def elaborate(self, platform: Platform | None):
        m = Module()

        video_in = platform.request("video_in")
        panels = platform.request("panels")
        panels_pclk = [platform.request("panels_pclk", i) for i in range(self.n_panels)]
        rgbled = platform.request("rgb_led")

        m.domains.video_in = cd_video_in = ClockDomain(local=True)
        m.d.comb += cd_video_in.clk.eq(video_in.pclk.i)
        platform.add_clock_constraint(video_in.pclk.i, self.video_in_pclk_max_freq)

        m.domains.video_out = cd_video_out = ClockDomain(local=True)
        m.d.comb += cd_video_out.clk.eq(self.video_out_clk)

        line_buffers = [DomainRenamer("video_in")(
            SwappableDoubleBufferMemory(
                shape=self.vp.color_depth,
                depth=self.vp.width,
                read_port_args={"domain": "video_out"},
                write_port_args={"domain": "video_in"}
            )
        ) for _ in range(self.n_panels)]
        line_buffers_swap = Signal()
        m.d.video_in += line_buffers_swap.eq(0)
        for i, buf in enumerate(line_buffers):
            m.submodules[f"line_buffer_{i}"] = buf
            m.d.comb += buf.swap.eq(line_buffers_swap)

        m.submodules.panel_driver = panel_driver = DomainRenamer("video_out")(
            SharedParallelBusMultiPanelDriver(
                self.n_panels, self.vp,
                [buf.read_b for buf in line_buffers],
                keep_clocking_when_paused=False
            )
        )
        m.d.comb += panels.data.o.eq(panel_driver.pixel_data)
        m.d.comb += panels.h_sync.o.eq(~panel_driver.video_buses[0].h_sync)
        m.d.comb += panels.v_sync.o.eq(~panel_driver.video_buses[0].v_sync)
        m.d.comb += panels.de.o.eq(panel_driver.video_buses[0].de)
        for i in range(self.n_panels):
            m.d.comb += panels_pclk[i].o.eq(panel_driver.video_buses[i].pclk)

        # CDC line & frame trigger
        line_trigger = Signal()
        m.d.video_in += line_trigger.eq(0)
        m.submodules.line_trigger_sync = AsyncFFSynchronizer(line_trigger, panel_driver.line_trigger,
                                                             o_domain="video_out")
        frame_trigger = Signal()
        m.d.video_in += frame_trigger.eq(0)
        m.submodules.frame_trigger_sync = AsyncFFSynchronizer(frame_trigger, panel_driver.frame_trigger,
                                                              o_domain="video_out")

        ## Main Logic

        x = Signal(range(self.vp.width))
        n_panel = Signal(range(self.n_panels))
        y = Signal(range(self.vp.height))

        last_h_sync = Signal()
        last_v_sync = Signal()
        last_de = Signal()
        m.d.video_in += last_h_sync.eq(video_in.h_sync.i)
        m.d.video_in += last_v_sync.eq(video_in.v_sync.i)
        m.d.video_in += last_de.eq(video_in.de.i)

        for n, buf in enumerate(line_buffers):
            m.d.video_in += buf.write_a.en.eq(0)

        with m.If(video_in.de.i):
            m.d.video_in += x.eq(x + 1)
            with m.If(x == (self.vp.width - 1)):
                m.d.video_in += x.eq(0)
                m.d.video_in += n_panel.eq(n_panel + 1)

            for n, buf in enumerate(line_buffers):
                with m.If(n_panel == n):
                    m.d.video_in += [
                        buf.write_a.addr.eq(x),
                        buf.write_a.data.eq(video_in.data.i),
                        buf.write_a.en.eq(1)
                    ]

        with m.If(~video_in.de.i & last_de):  # end of line
            m.d.video_in += y.eq(y + 1)
            # The line trigger CDC has some delay,
            # so asserting line_buffers_swap and line_trigger.trigger at the same time
            # shouldn't result in race conditions between them.
            m.d.video_in += line_buffers_swap.eq(1)
            m.d.video_in += line_trigger.eq(1)

        with m.If(video_in.h_sync.i & ~last_h_sync):  # h_sync rising edge
            m.d.video_in += x.eq(0)
            m.d.video_in += n_panel.eq(0)

        with m.If(video_in.v_sync.i & ~last_v_sync):  # v_sync rising edge
            m.d.video_in += y.eq(0)
            m.d.video_in += frame_trigger.eq(1)

        m.domains.sync = cd_sync = ClockDomain()  # unused
        m.d.comb += cd_sync.clk.eq(0)

        return m

def _build_1():
    # platform = ICESugarProPlatform()
    platform = WorldCubeDriverValidationBoardPlatform()

    m = Module()
    video_out_clk = Signal()
    # m.submodules.pll = Instance(  # 200MHz
    #     "EHXPLLL",
    #     a_ICP_CURRENT="12",
    #     a_LPF_RESISTOR="8",
    #     p_CLKI_DIV=1,
    #     p_CLKOP_ENABLE="ENABLED",
    #     p_CLKOP_DIV=3,
    #     p_CLKOP_CPHASE=1,
    #     p_CLKOP_FPHASE=0,
    #     p_FEEDBK_PATH="CLKOP",
    #     p_CLKFB_DIV=8,
    #     i_CLKI=platform.request("clk25").i,
    #     o_CLKOP=video_out_clk,
    #     i_CLKFB=video_out_clk
    # )
    # m.submodules.pll = Instance(  # 180MHz
    #     "EHXPLLL",
    #     a_ICP_CURRENT="12",
    #     a_LPF_RESISTOR="8",
    #     p_CLKI_DIV=5,
    #     p_CLKOP_ENABLE="ENABLED",
    #     p_CLKOP_DIV=3,
    #     p_CLKOP_CPHASE=1,
    #     p_CLKOP_FPHASE=0,
    #     p_FEEDBK_PATH="CLKOP",
    #     p_CLKFB_DIV=36,
    #     i_CLKI=platform.request("clk25").i,
    #     o_CLKOP=video_out_clk,
    #     i_CLKFB=video_out_clk
    # )
    m.submodules.pll = Instance(  # 100MHz
        "EHXPLLL",
        a_ICP_CURRENT="12",
        a_LPF_RESISTOR="8",
        p_CLKI_DIV=5,
        p_CLKOP_ENABLE="ENABLED",
        p_CLKOP_DIV=3,
        p_CLKOP_CPHASE=1,
        p_CLKOP_FPHASE=0,
        p_FEEDBK_PATH="CLKOP",
        p_CLKFB_DIV=24,
        i_CLKI=platform.request("clk25").i,
        o_CLKOP=video_out_clk,
        i_CLKFB=video_out_clk
    )
    m.submodules.top = VideoSplitterTop(
        video_params=ParallelVideoParams(
            RGB888,
            480, 480,
            2, 2, 2, 2,
            2, 2
        ),
        n_panels=6,
        video_in_pclk_max_freq=50e6,
        video_out_clk=video_out_clk
    )

    platform.build(m, verbose=True, do_program=False)

if __name__ == "__main__":
    _build_1()
