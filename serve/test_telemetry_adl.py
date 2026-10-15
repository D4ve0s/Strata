"""The Monitor's AMD-on-Windows readings (ADL2 PMLog) degrade safely and map to the gpu_* keys the web UI uses.

No GPU or download is required for the safety half: on a box without atiadlxx.dll every reader must report
"unavailable" (ok() False, read() {}) and never raise, so the server keeps running.  On a box that does have the
driver (the R9700 / RX 9070 XT the Monitor is meant for), the same reader must fill gpu_util / gpu_temp /
gpu_mem_used / gpu_power, and each card's own PCIe link (PMLog's negotiated BUS_SPEED / BUS_LANES) so a
motherboard's PCI bifurcation shows the real width per slot."""
import os
import unittest

from serve.telemetry import _AmdWin, amd_card_count, free_vram_mib, gpu_reader


class AdlDegrades(unittest.TestCase):
    """Nothing in the Windows AMD path may raise: an absent driver, a blocked call, or an unreadable sensor all
    leave the reader off, and the server still runs."""

    def test_reader_never_raises(self):
        for index in (0, 1, 5):
            r = gpu_reader(index, amd=True)
            self.assertTrue(hasattr(r, "ok") and hasattr(r, "read"))
            self.assertIsInstance(r.read(), dict)
            self.assertIsInstance(r.name(), str)

    def test_free_vram_never_raises(self):
        for index in (0, 1):
            free = free_vram_mib(index, amd=True)
            self.assertTrue(free is None or isinstance(free, int))

    def test_card_count_never_raises(self):
        n = amd_card_count()
        self.assertTrue(n is None or isinstance(n, int))

    def test_unavailable_off(self):
        if _AmdWin(0).lib is None:  # no atiadlxx.dll here: the reader must be fully off
            r = _AmdWin(0)
            self.assertFalse(r.ok())
            self.assertEqual(r.read(), {})
            self.assertEqual(amd_card_count(), 0)


class AdlReadings(unittest.TestCase):
    """On a machine that has the driver, the reader fills the gpu_* keys the Monitor tab renders."""

    def test_readings_when_driver_present(self):
        r = _AmdWin(0)
        if not r.ok():
            return  # no AMD driver on this box; the degrade test above covers it
        out = r.read()
        self.assertIn("util", out)
        self.assertIn("mem_used", out)
        self.assertIn("mem_total", out)
        self.assertGreaterEqual(out["mem_used"], 0)
        self.assertLessEqual(out["mem_used"], out["mem_total"])
        if out.get("temp") is not None:
            self.assertTrue(0 < out["temp"] < 120)  # degrees C, not millidegrees
        if out.get("power") is not None:
            self.assertTrue(0 < out["power"] < 1000)  # watts (BOARD_POWER factor 1.0), not milliwatts
        # PCIe is the per-card negotiated link, not a device-wide max
        for k in ("pcie_gen_max", "pcie_width"):
            self.assertTrue(out.get(k) is None or isinstance(out[k], int))

    def test_every_card_enumerates(self):
        """The Monitor shows a tile per card, so every present discrete card (index < card_count) must read."""
        n = amd_card_count()
        if n < 1:
            return
        for i in range(n):
            self.assertTrue(_AmdWin(i).ok())


if __name__ == "__main__":
    unittest.main()
