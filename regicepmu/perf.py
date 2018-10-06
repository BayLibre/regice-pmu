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

"""
    This is a module to get performance from device using PMU.
    PerfEvent have to be implemented per architecture, to convert PMU counter
    value to performance value such as CPU load.
"""

class PerfEvent:
    """
        A class to read and process PMU counters

        This provides many methods to use the PMU and exploit its counters.
        Basically, this can enable the PMU and its counters, read them,
        and compute human readable performance values such as CPU load.
    """
    def __init__(self, pmu, perf_type, name):
        self.type = perf_type
        self.name = name
        self.unit = None
        self.yrange = []
        self.delay = 0
        self.pmu = pmu
        if not perf_type in pmu.perf_events:
            pmu.perf_events[perf_type] = {}
        pmu.perf_events[perf_type][name] = self

    def _enable(self):
        pass

    def _disable(self):
        pass

    def enable(self):
        """
            Enable the counters and the PMU required to compute
            the perf event.
        """
        self._enable()
        self.pmu.enable(refcount=True)

    def disable(self):
        """
            Disable the counters and the PMU if there no other event enabled.
        """
        self.pmu.disable(refcount=True)
        self._disable()


    def reset(self):
        """
            Reset the value of the counter used for the event or the PMU.
            A reset may fail if there are other events enabled.
        """
        # FIXME: raise exception
        pass

    def get_value(self):
        """
            Compute the value of the event, using PMU counters.
            :return: The value of event.
        """
        raise NotImplementedError

    def has_range(self):
        """
            Return True if a range for the event value has been defined.

            :return: True if the event has a range
        """
        return self.yrange

    def get_range(self):
        """
            Return the range of event value

            :return: A tuple of min and max value the of event could have
        """
        if not self.has_range():
            return None, None
        return self.yrange[0], self.yrange[1]

    def get_name(self):
        """
            Return the name of the event

            :return: the name of the event
        """
        return self.name

    def get_unit(self):
        """
            Return the name of unit of the event

            :return: the name of the unit, usually in short form or an empty
                     string if there is no unit
        """
        if self.unit:
            return self.unit
        return ''

class CPULoad(PerfEvent):
    def __init__(self, pmu, cpu_id):
        if cpu_id is not None:
            name = "CPU {} load".format(cpu_id)
        else:
            name = "CPU load"
        super(CPULoad, self).__init__(pmu, Perf.CPU_LOAD, name)
        self.yrange = [0, 100]
        self.unit = '%'

class MemoryLoad(PerfEvent):
    def __init__(self, pmu):
        super(MemoryLoad, self).__init__(pmu, Perf.MEMORY_LOAD, "Memory load")
        self.yrange = [0, 100]
        self.unit = '%'

class Perf:
    """
        A class to manage perf events
    """
    CPU_LOAD = 1
    MEMORY_LOAD = 2
    def __init__(self, device):
        self.events = {}
        self.device = device
        for pmu_name in self.device.pmus:
            pmu = self.device.pmus[pmu_name]
            for event_type in pmu.perf_events:
                if event_type not in self.events:
                    self.events[event_type] = {}
                self.events[event_type].update(pmu.perf_events[event_type])

    def get_events(self, event_type=None):
        """
            Return a list of events

            This returns the list of all registered events,
            or the list of event for the specified event type.

            :param event_type: The type of event to return
            :return: A list of events
        """
        events = []
        if event_type is not None:
            events += self.events[event_type].values()
        else:
            for _event_type in self.events:
                events += self.events[_event_type].values()
        return events

    def get_events_name(self, event_type=None):
        """
            Return a list of events' name

            This returns the list of name of all registered events or
            or those of specified event type.

            :param event_type: The type of event to return
            :return: A list of events' name
        """
        events = self.get_events(event_type)
        return [event.name for event in events]

    def get(self, event_type, event_name):
        """
            Get an event

            :param param_type: The type of the event to get
            :param event_name: The name of the event to get
            :return: An PerfEvent object
        """
        if not event_type and not event_name:
            return None

        events = self.get_events(event_type)
        for event in events:
            if event.name == event_name:
                return event

        return None

    def get_value(self, event_type, event_name):
        """
            Get the value from an event

            :param param_type: The type of the event to get
            :param event_name: The name of the event to get
            :return: the value read from the event
        """
        event = self.get(event_type, event_name)
        if not event:
            raise ValueError
        return event.get_value()
