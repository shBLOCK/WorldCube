import os
import subprocess

import dotenv
from amaranth.vendor import LatticeECP5Platform, LatticeICE40Platform
from amaranth.build import *
from amaranth_boards.resources import *

from video_splitter.utils import ParallelVideoBusResource

dotenv.load_dotenv(".env")

class ICESugarProPlatform(LatticeECP5Platform):
    device = "LFE5U-25F"
    package = "BG256"
    speed = "6"
    default_clk = "clk25"

    resources = [
        Resource("clk25", 0, Pins("P6", dir="i"), Clock(25e6), Attrs(IO_TYPE="LVCMOS33")),
        RGBLEDResource(0, r="B11", g="A11", b="A12"),

        ParallelVideoBusResource(
            "panels", 0, "o", 24,
            data="B1 C1 D1 F2 G2 L2 M2 N3 P2 R2 K1 M1 N1 P1 R1 T2 T3 T4 R6 P7 R3 R4 R5 T6",
            h_sync="C2",
            v_sync="B2",
            de="A2",
            pclk=None,
            attrs=Attrs(IO_TYPE="LVCMOS33")
        ),
        *[Resource("panels_pclk", i, Pins(p, dir="o"), Attrs(IO_TYPE="LVCMOS33"))
          for i, p in enumerate("A3 A4 A5 A6 A7 A8".split(" "))],

        ParallelVideoBusResource(
            "video_in", 0, "i", 24,
            data="C9 D10 C10 D11 F13 F14 G13 G14 H13 H14 J13 J14 K13 K14 L13 L14 M13 M12 P14 N13 P13 N12 P12 P11",
            h_sync="C7",
            v_sync="C8",
            de="C5",
            pclk="D9",
            attrs=Attrs(IO_TYPE="LVCMOS33")
        )
    ]

    connectors = []

    @property
    def required_tools(self):
        return super().required_tools + [
            "openFPGALoader"
        ]

    def toolchain_prepare(self, fragment, name, **kwargs):
        overrides = dict(ecppack_opts="--compress")
        overrides.update(kwargs)
        return super().toolchain_prepare(fragment, name, **overrides)

    def toolchain_program(self, products, name):
        env_bat = os.environ.get("AMARANTH_ENV_TRELLIS")
        assert env_bat is not None
        with products.extract("{}.bit".format(name)) as bitstream_filename:
            subprocess.check_call(
                f'cmd /c "call "{env_bat}" && openFPGALoader -c cmsisdap --vid=0x1d50 --pid=0x602b -m "{bitstream_filename}""'
            )

class WorldCubeDriverValidationBoardPlatform(LatticeECP5Platform):
    device = "LFE5U-25F"
    package = "BG256"
    speed = "6"
    default_clk = "clk25"

    resources = [
        Resource("clk25", 0, Pins("P6", dir="i"), Clock(25e6), Attrs(IO_TYPE="LVCMOS33")),
        RGBLEDResource(0, r="B11", g="A11", b="A12"),

        ParallelVideoBusResource(
            "panels", 0, "o", 24,
            data="R8 R7 P7 T6 R6 R5 T4 R4 T3 R3 T2 R2 R1 P2 P1 N3 N1 M2 M1 L2 L1 K2 K1 J2",
            h_sync="E2",
            v_sync="E1",
            de="D3",
            pclk=None,
            attrs=Attrs(IO_TYPE="LVCMOS33")
        ),
        *[Resource("panels_pclk", i, Pins(p, dir="o"), Attrs(IO_TYPE="LVCMOS33"))
          for i, p in enumerate("J1 H2 G2 G1 F2 F1".split(" "))],

        ParallelVideoBusResource(
            "video_in", 0, "i", 24,
            data="H3 G3 G4 F3 F4 E3 E4 C3 D4 C4 D5 C5 D6 C6 D7 C7 D8 C8 D9 C9 D10 C10 D11 C11",
            h_sync="K4",
            v_sync="J3",
            de="K3",
            pclk="J4",
            attrs=Attrs(IO_TYPE="LVCMOS33")
        )
    ]

    connectors = []

    @property
    def required_tools(self):
        return super().required_tools + [
            "openFPGALoader"
        ]

    def toolchain_prepare(self, fragment, name, **kwargs):
        overrides = dict(ecppack_opts="--compress")
        overrides.update(kwargs)
        return super().toolchain_prepare(fragment, name, **overrides)

    def toolchain_program(self, products, name):
        env_bat = os.environ.get("AMARANTH_ENV_TRELLIS")
        assert env_bat is not None
        with products.extract("{}.bit".format(name)) as bitstream_filename:
            subprocess.check_call(
                f'cmd /c "call "{env_bat}" && openFPGALoader -c cmsisdap --vid=0x1d50 --pid=0x602b -m "{bitstream_filename}""'
            )

if __name__ == "__main__":
    from amaranth_boards.test.blinky import *

    ICESugarProPlatform().build(Blinky(), verbose=True, do_program=True)
