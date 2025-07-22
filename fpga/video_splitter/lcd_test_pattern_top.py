from amaranth import *
from amaranth.lib.memory import Memory, WritePort
from amaranth.build import Platform

from video_splitter.panel_driver import SharedParallelBusMultiPanelDriver
from video_splitter.utils import ParallelVideoParams, RGB888

class LCDTestPatternTop(Elaboratable):
    def elaborate(self, platform: Platform | None):
        m = Module()
        N_PANELS = 6
        vp = ParallelVideoParams(
            RGB888, 480, 480,
            4, 2, 4, 2,
            2, 2
        )
        line_buffers = [Memory(shape=RGB888, depth=vp.width, init=[]) for _ in range(N_PANELS)]
        for i, buf in enumerate(line_buffers):
            m.submodules[f"line_buffer_{i}"] = buf

        m.domains.sync = cd_sync = ClockDomain("sync")

        # CLK = 66.6666e6
        # pll = Instance( # 66.6M
        #     "EHXPLLL",
        #     a_ICP_CURRENT="12",
        #     a_LPF_RESISTOR="8",
        #     p_CLKI_DIV=3,
        #     p_CLKOP_ENABLE="ENABLED",
        #     p_CLKOP_DIV=18,
        #     p_CLKOP_CPHASE=9,
        #     p_CLKOP_FPHASE=0,
        #     p_FEEDBK_PATH="CLKOP",
        #     p_CLKFB_DIV=8,
        #     i_CLKI=platform.request("clk25").i,
        #     o_CLKOP=cd_sync.clk,
        #     i_CLKFB=cd_sync.clk
        # )
        # CLK = 100e6
        # pll = Instance( # 100M
        #     "EHXPLLL",
        #     a_ICP_CURRENT="12",
        #     a_LPF_RESISTOR="8",
        #     p_CLKI_DIV=1,
        #     p_CLKOP_ENABLE="ENABLED",
        #     p_CLKOP_DIV=3,
        #     p_CLKOP_CPHASE=1,
        #     p_CLKOP_FPHASE=0,
        #     p_FEEDBK_PATH="CLKOP",
        #     p_CLKFB_DIV=4,
        #     i_CLKI=platform.request("clk25").i,
        #     o_CLKOP=cd_sync.clk,
        #     i_CLKFB=cd_sync.clk
        # )
        # CLK = 200e6
        # pll = Instance( # 200M
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
        #     o_CLKOP=cd_sync.clk,
        #     i_CLKFB=cd_sync.clk
        # )
        CLK = 180e6
        pll = Instance(  # 180MHz
            "EHXPLLL",
            a_ICP_CURRENT="12",
            a_LPF_RESISTOR="8",
            p_CLKI_DIV=5,
            p_CLKOP_ENABLE="ENABLED",
            p_CLKOP_DIV=3,
            p_CLKOP_CPHASE=1,
            p_CLKOP_FPHASE=0,
            p_FEEDBK_PATH="CLKOP",
            p_CLKFB_DIV=36,
            i_CLKI=platform.request("clk25").i,
            o_CLKOP=cd_sync.clk,
            i_CLKFB=cd_sync.clk
        )
        m.submodules["pll"] = pll

        driver = SharedParallelBusMultiPanelDriver(
            N_PANELS, vp,
            [buf.read_port() for buf in line_buffers],
            keep_clocking_when_paused=True
        )
        m.submodules["driver"] = driver

        rgbled = platform.request("rgb_led")
        panels = platform.request("panels")
        panels_pclk = [platform.request("panels_pclk", i) for i in range(N_PANELS)]

        # Connect panels
        m.d.comb += panels.data.o.eq(driver.pixel_data)
        m.d.comb += panels.h_sync.o.eq(~driver.video_buses[0].h_sync)
        m.d.comb += panels.v_sync.o.eq(~driver.video_buses[0].v_sync)
        m.d.comb += panels.de.o.eq(driver.video_buses[0].de)
        for i in range(N_PANELS):
            m.d.comb += panels_pclk[i].o.eq(driver.video_buses[i].pclk)

        sync1_div = Signal(1)
        m.d.sync += sync1_div.eq(~sync1_div)
        m.domains.sync1 = cd_sync1 = ClockDomain()
        m.d.comb += ClockSignal("sync1").eq(sync1_div)
        platform.add_clock_constraint(sync1_div, 100e6)

        # Frame control
        F_FPS = 60
        F_V_FRONT_PORCH = 3
        F_V_BACK_PORCH = 20
        F_TOTAL_LINES = F_V_FRONT_PORCH + vp.height + F_V_BACK_PORCH
        F_LINE_CLOCKS = int(CLK / 2 / (F_FPS * F_TOTAL_LINES)) # how many clocks per line
        x = Signal(range(F_LINE_CLOCKS))
        y = Signal(range(F_TOTAL_LINES))
        m.d.sync1 += x.eq(x + 1)
        with m.If(x >= (F_LINE_CLOCKS - 1)):
            m.d.sync1 += x.eq(0)
            m.d.sync1 += y.eq(y + 1)
            with m.If(y >= (F_TOTAL_LINES - 1)):
                m.d.sync1 += y.eq(0)
        m.d.comb += driver.line_trigger.eq(x >= (F_LINE_CLOCKS - 10))
        m.d.comb += driver.frame_trigger.eq(y == (F_TOTAL_LINES - 1))

        # Render pattern
        for panel in range(N_PANELS):
            write_port = line_buffers[panel].write_port()
            m.d.sync1 += write_port.en.eq(0)
            with m.If(x < vp.width):
                m.d.sync1 += write_port.en.eq(1)
                m.d.sync1 += write_port.addr.eq(x)
                color = Signal(RGB888)
                m.d.sync1 += color.r.eq(x[:8])
                m.d.sync1 += color.g.eq(y[:8])
                m.d.sync1 += color.b.eq(int(255 * (panel / (N_PANELS - 1))))
                color_raw = Signal(24)
                m.d.comb += color_raw[:8].eq(color.b)
                m.d.comb += color_raw[8:16].eq(color.g)
                m.d.comb += color_raw[16:24].eq(color.r)
                m.d.sync1 += write_port.data.eq(color_raw)

        return m

if __name__ == "__main__":
    from video_splitter.plat import ICESugarProPlatform

    ICESugarProPlatform().build(LCDTestPatternTop(), verbose=True, do_program=True)
