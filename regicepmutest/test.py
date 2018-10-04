#!/usr/bin/env python
# -*- coding: utf-8 -*-

# MIT License
#
# Copyright (c) 2018 BayLibre
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import unittest

from libregice.regiceclienttest import RegiceClientTest
from libregice.device import Device
from regicetest import open_svd_file
from svd import SVDText

from regicepmu.perf import *
from regicepmu.pmu import *

class TestPMUCounter(PMUCounter):
    def __init__(self, pmu, register):
        super(TestPMUCounter, self).__init__(pmu, register, support_event=True)
        self.en = False

    def _enable(self):
        self.en = True

    def _disable(self):
        self.en = False

    def _enabled(self):
        return self.en

    def _set_event(self, event_id):
        pass

class TestPMU(PMU):
    def __init__(self, device, name):
        super(TestPMU, self).__init__(device, name)
        self.en = False
        self.paused = False
        PMUCounter(self, device.TEST1.TESTA)
        PMUCounter(self, device.TEST1.TESTB)

    def _enable(self):
        self.en = True

    def _disable(self):
        self.en = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def reset(self):
        self.device.TEST1.TESTA.write(0)
        self.device.TEST1.TESTB.write(0)

class TestPerfEvent(PerfEvent):
    def get_value(self):
        return self.pmu.device.TEST1.TESTA / self.pmu.device.TEST1.TESTB

class PMUCounterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        file = open_svd_file('test.svd')
        svd = SVDText(file.read())
        svd.parse()
        self.client = RegiceClientTest()
        self.dev = Device(svd, self.client)
        self.memory = self.client.memory

    @classmethod
    def setUp(self):
        self.client.memory_restore()
        pmu = TestPMU(self.dev, 'test')
        self.counter = TestPMUCounter(pmu, self.dev.TEST1.TESTA)
        self.counter.support_event = False
        self.dev.TEST1.TESTA.write(0)

    def test_enable(self):
        self.counter.enable()
        self.assertTrue(self.counter.en)

    def test_disable(self):
        self.counter.disable()
        self.assertFalse(self.counter.en)

    def test_read(self):
        value = self.counter.read()
        self.assertEqual(value, 0)

        self.dev.TEST1.TESTA.write(3)
        value = self.counter.read()
        self.assertEqual(value, 3)

    def test_str(self):
        self.assertEqual(str(self.counter), 'TESTA')

class PMUTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        file = open_svd_file('test.svd')
        svd = SVDText(file.read())
        svd.parse()
        self.client = RegiceClientTest()
        self.dev = Device(svd, self.client)
        self.memory = self.client.memory

    @classmethod
    def setUp(self):
        self.client.memory_restore()
        self.pmu = TestPMU(self.dev, 'test')
        self.not_implemented_pmu = PMU(self.dev, 'not_implemented_pmu')

    def test_enable(self):
        self.pmu.enable()
        self.assertTrue(self.pmu.en)

        with self.assertRaises(NotImplementedError):
            self.not_implemented_pmu.enable()

    def test_disable(self):
        self.pmu.disable()
        self.assertFalse(self.pmu.en)

        with self.assertRaises(NotImplementedError):
            self.not_implemented_pmu.disable()

    def test_pause(self):
        self.pmu.pause()
        self.assertTrue(self.pmu.paused)

        with self.assertRaises(NotImplementedError):
            self.not_implemented_pmu.pause()

    def test_resume(self):
        self.pmu.resume()
        self.assertFalse(self.pmu.paused)

        with self.assertRaises(NotImplementedError):
            self.not_implemented_pmu.resume()

    def test_reset(self):
        self.assertNotEqual(int(self.dev.TEST1.TESTA), 0)
        self.assertNotEqual(int(self.dev.TEST1.TESTB), 0)

        self.pmu.reset()
        self.assertEqual(int(self.dev.TEST1.TESTA), 0)
        self.assertEqual(int(self.dev.TEST1.TESTB), 0)

        with self.assertRaises(NotImplementedError):
            self.not_implemented_pmu.reset()

    def test_get_counters(self):
        counters = self.pmu.get_counters()
        self.assertEqual(counters, self.pmu.counters)

    def test_read(self):
        TESTA = self.pmu.read('TESTA')
        self.assertEqual(TESTA, 0x100003)

        TESTB = self.pmu.read('TESTB')
        self.assertEqual(TESTB, 0x10000)

    def test_enable_event(self):
        self.pmu.events = {0: ['test', 'test']}
        TestPMUCounter(self.pmu, self.pmu.device.TEST1.TESTA)
        TestPMUCounter(self.pmu, self.pmu.device.TEST1.TESTB)

        cnt = self.pmu.enable_event(0)
        self.assertEqual(cnt, self.pmu.get_counters()['TESTA'])

        cnt = self.pmu.enable_event(0)
        self.assertEqual(cnt, self.pmu.get_counters()['TESTB'])

        with self.assertRaises(Exception):
            cnt = self.pmu.enable_event(0)

    def test_disable_event(self):
        self.pmu.events = {0: ['test', 'test']}
        TestPMUCounter(self.pmu, self.pmu.device.TEST1.TESTA)
        TestPMUCounter(self.pmu, self.pmu.device.TEST1.TESTB)

        cnt = self.pmu.enable_event(0)
        self.assertEqual(cnt, self.pmu.get_counters()['TESTA'])

        self.pmu.disable_event(cnt)
        self.assertFalse(cnt.allocated)

class PMUEventTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        file = open_svd_file('test.svd')
        svd = SVDText(file.read())
        svd.parse()
        self.client = RegiceClientTest()
        self.dev = Device(svd, self.client)
        self.memory = self.client.memory

    @classmethod
    def setUp(self):
        self.client.memory_restore()
        self.pmu = TestPMU(self.dev, 'test')
        self.perf_event1 = TestPerfEvent(self.pmu, Perf.CPU_LOAD, 'test1')
        self.perf_event2 = PerfEvent(self.pmu, Perf.MEMORY_LOAD, 'test2')

    def test_enable_disable(self):
        self.perf_event1.enable()
        self.assertTrue(self.pmu.en)
        self.perf_event1.disable()

        self.perf_event1.enable()
        self.perf_event2.enable()
        self.assertTrue(self.pmu.en)
        self.perf_event2.disable()
        self.assertTrue(self.pmu.en)
        self.perf_event1.disable()
        self.assertFalse(self.pmu.en)

    def test_get_value(self):
        value = self.perf_event1.get_value()
        with self.assertRaises(NotImplementedError):
            self.perf_event2.get_value()

    def test_has_range(self):
        self.assertFalse(self.perf_event1.has_range())
        self.perf_event1.yrange = [0, 10]
        self.assertTrue(self.perf_event1.has_range())
        self.perf_event1.yrange = []

    def test_has_range(self):
        self.assertEqual(self.perf_event1.get_range(), (None, None))
        self.perf_event1.yrange = [0, 10]
        self.assertEqual(self.perf_event1.get_range(), (0, 10))
        self.perf_event1.yrange = []

    def test_get_name(self):
        self.assertEqual(self.perf_event1.get_name(), 'test1')

    def test_get_unit(self):
        self.assertEqual(self.perf_event1.get_unit(), '')
        self.perf_event1.unit = 's'
        self.assertEqual(self.perf_event1.get_unit(), 's')
        self.perf_event1.unit = ''

class PerfTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        file = open_svd_file('test.svd')
        svd = SVDText(file.read())
        svd.parse()
        self.client = RegiceClientTest()
        self.dev = Device(svd, self.client)
        self.memory = self.client.memory

    @classmethod
    def setUp(self):
        self.client.memory_restore()
        self.pmu = TestPMU(self.dev, 'test')
        self.perf_event1 = TestPerfEvent(self.pmu, Perf.CPU_LOAD, 'test1')
        self.perf_event2 = PerfEvent(self.pmu, Perf.MEMORY_LOAD, 'test2')
        self.pmu_no_perf = TestPMU(self.dev, 'test2')
        self.perf = Perf(self.dev)

    def test_get_events(self):
        events = self.perf.get_events()
        self.assertEqual(events, [self.perf_event1, self.perf_event2])

        events = self.perf.get_events(Perf.CPU_LOAD)
        self.assertEqual(events, [self.perf_event1])

        self.dev.pmus = {'test': self.pmu_no_perf}
        perf = Perf(self.dev)
        events = perf.get_events()
        self.assertEqual(events, [])

    def test_get_events_name(self):
        names = self.perf.get_events_name()
        self.assertEqual(names, [self.perf_event1.name, self.perf_event2.name])

        names = self.perf.get_events_name(Perf.CPU_LOAD)
        self.assertEqual(names, [self.perf_event1.name])

        self.dev.pmus = {'test': self.pmu_no_perf}
        perf = Perf(self.dev)
        names = perf.get_events_name()
        self.assertEqual(names, [])

    def test_get(self):
        event = self.perf.get(None, None)
        self.assertEqual(event, None)

        event = self.perf.get(Perf.CPU_LOAD, None)
        self.assertEqual(event, None)

        event = self.perf.get(None, 'test1')
        self.assertEqual(event, self.perf_event1)

        event = self.perf.get(Perf.CPU_LOAD, 'test1')
        self.assertEqual(event, self.perf_event1)

    def test_get_value(self):
        with self.assertRaises(ValueError):
            self.perf.get_value(None, None)

        device = self.pmu.device
        value = self.perf.get_value(None, 'test1')
        expected_value = device.TEST1.TESTA / device.TEST1.TESTB
        self.assertEqual(value, expected_value)

def run_tests(module):
    return unittest.main(module=module, exit=False).result

if __name__ == '__main__':
    unittest.main()
