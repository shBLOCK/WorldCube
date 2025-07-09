from amaranth import *
from amaranth.build import Platform
from amaranth.lib import wiring
from amaranth.lib.wiring import Component, In
from amaranth.lib.memory import Memory, ReadPort, WritePort

class SwappableDoubleBufferMemory(Component):
    """Simple swappable double buffer (memory)."""

    swap: Signal
    read_a: ReadPort
    read_b: ReadPort
    write_a: WritePort
    write_b: WritePort

    def __init__(self, shape, depth: int):
        self.shape = shape
        self.depth = depth

        self.memories = Array([Memory(shape=shape, depth=depth, init=[]) for _ in range(2)])
        self._read_ports = Array([mem.read_port() for mem in self.memories])
        self._write_ports = Array([mem.write_port() for mem in self.memories])

        self._state = Signal(reset=0)

        super().__init__({
            "swap": In(1),
            "read_a": In(self._read_ports[0].signature),
            "read_b": In(self._read_ports[1].signature),
            "write_a": In(self._write_ports[0].signature),
            "write_b": In(self._write_ports[1].signature)
        })

    def elaborate(self, platform: Platform | None):
        m = Module()
        m.submodules.memory_a = self.memories[0]
        m.submodules.memory_b = self.memories[1]

        with m.If(self.swap):
            m.d.sync += self._state.eq(~self._state)

        with m.If(self._state):
            wiring.connect(m, self.read_a, self._read_ports[1])
            wiring.connect(m, self.read_b, self._read_ports[0])
            wiring.connect(m, self.write_a, self._write_ports[1])
            wiring.connect(m, self.write_b, self._write_ports[0])
        with m.Else():
            wiring.connect(m, self.read_a, self._read_ports[0])
            wiring.connect(m, self.read_b, self._read_ports[1])
            wiring.connect(m, self.write_a, self._write_ports[0])
            wiring.connect(m, self.write_b, self._write_ports[1])

        return m

def _main():
    from amaranth.sim import Simulator, SimulatorContext

    sdb = SwappableDoubleBufferMemory(8, 10)

    # noinspection PyProtectedMember
    async def tb(ctx: SimulatorContext):
        await ctx.tick()
        assert ctx.get(sdb._state) == 0
        await ctx.tick()
        assert ctx.get(sdb._state) == 0
        ctx.set(sdb.swap, True)
        await ctx.delay(0)
        assert ctx.get(sdb._state) == 0
        await ctx.tick()
        assert ctx.get(sdb._state) == 1
        ctx.set(sdb.swap, False)

        d = 123
        ctx.set(sdb.write_a.data, d)
        ctx.set(sdb.write_a.addr, 0)
        ctx.set(sdb.write_a.en, True)
        await ctx.tick()
        ctx.set(sdb.write_a.en, False)

        ctx.set(sdb.read_a.addr, 0)
        ctx.set(sdb.read_a.en, True)
        ctx.set(sdb.read_b.addr, 0)
        ctx.set(sdb.read_b.en, True)
        await ctx.tick()
        assert ctx.get(sdb.read_a.data) == d
        assert ctx.get(sdb.read_b.data) == 0

        ctx.set(sdb.swap, True)
        await ctx.tick()
        ctx.set(sdb.swap, False)
        await ctx.tick()
        assert ctx.get(sdb.read_a.data) == 0
        assert ctx.get(sdb.read_b.data) == d

        await ctx.tick()

    sim = Simulator(sdb)
    sim.add_clock(1e-6)
    sim.add_testbench(tb)
    file = "sim/SwappableDoubleBufferMemory"
    with sim.write_vcd(
        f"{file}.vcd",
        f"{file}.gtkw",
        traces=[sdb.swap, sdb._state, sdb.memories[0].data[0], sdb.memories[1].data[0], sdb.write_a]
    ):
        sim.run()

    import subprocess
    subprocess.run(["../bin/surfer.exe", f"{file}.vcd", "-s", f"{file}.surf.ron"])

if __name__ == "__main__":
    _main()
