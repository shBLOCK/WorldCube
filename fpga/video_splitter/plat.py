import os
import subprocess

import dotenv
from amaranth.vendor import LatticeECP5Platform
from amaranth.build import *
from amaranth_boards.resources import *

dotenv.load_dotenv(".env")

class ICESugarProPlatform(LatticeECP5Platform):
    device = "LFE5U-25F"
    package = "BG256"
    speed = "6"
    default_clk = "clk25"

    resources = [
        Resource("clk25", 0, Pins("P6", dir="i"), Clock(25e6), Attrs(IO_TYPE="LVCMOS33")),
        RGBLEDResource(0, r="B11", g="A11", b="A12")
    ]
    connectors = [
        Connector("P", 2, "")
    ]

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
