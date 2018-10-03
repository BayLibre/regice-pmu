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
    A module to manage the PMU.

    This provides PMU and PMUCounte base class, used to manage the counters
    and the PMU. Many methods must be implemented in architecture files.
"""

class PMUCounter:
    """
        A class to manage one PMU counter

        PMU usually have many counters.
        Depending on the PMU features, counters may be enabled or disabled
        individually.
        This provides many methods to read and manage one PMU counter.
        :param pmu: A PMU object (e.g the owner of the counter)
        :param register: A RegiceObject object to use to read the register
    """

    def __init__(self, pmu, register):
        pmu.counters[register.name] = self
        self.register = register

    def read(self):
        """
            Read the current value of counter

            :return: The current value of counter
        """
        return int(self.register)

    def enable(self):
        """
            Enable the counter and the PMU

            This enables the counter if can be individually managed.
            This could be left unimplemented if the counter can't
            be individually enabled.
        """
        pass

    def disable(self):
        """
            Disable the counter and the PMU

            This disables the counter if can be individually managed.
            This could be left unimplemented if the counter can't
            be individually managed.
        """
        pass

    def __str__(self):
        """
            Return the name of the PMU counter.

            By default, this uses the register name as counter name.

            :return: The name of the counter
        """
        return self.register.name

class PMU:
    """
        A class to manage the PMU

        This provides many methods to manage a PMU.
        :param device: A Device object (e.g the owner of the PMU)
        :param name: The name of the PMU, also used as PMU id
    """
    def __init__(self, device, name):
        if not hasattr(device, 'pmus'):
            device.pmus = {}
        device.pmus[name] = self
        self.name = name
        self.device = device
        self.counters = {}
        self.events = {}
        self.perf_events = {}
        self.refcount = 0

    @staticmethod
    def get_pmus(device):
        """
            Return a dictionary of device's PMUs

            :param device: A Device object (e.g the owner of the PMU)
            :return: A dictionary of PMU object
        """
        if hasattr(device, 'pmus'):
            return device.pmus
        return {}

    def _enable(self):
        raise NotImplementedError

    def _disable(self):
        raise NotImplementedError

    def enable(self, refcount=False):
        """
            Enable the PMU

            :param refcount: If False, always enable the PMU, else enable
                             the PMU if it is not enabled
        """
        if refcount:
            self.refcount += 1
        if self.refcount == 1 or refcount is False:
            self._enable()

    def disable(self, refcount=False):
        """
            Disable the PMU

            :param refcount: If False, always disable the PMU, else disable
                             the PMU if it is enabled, and not used anymore
        """
        if refcount:
            self.refcount -= 1
        if self.refcount == 0:
            self._disable()

    def pause(self):
        """
            Pause the PMU

            This stops the PMU in order to read the counters.
        """
        raise NotImplementedError

    def resume(self):
        """
            Resume the PMU

            This resumes the PMU, e.g must be done after counters
            have been read.
        """
        raise NotImplementedError

    def reset(self):
        """
            Reset the PMU

            This reset the PMU, e.g reset all the counters.
        """
        raise NotImplementedError

    def get_counters(self):
        """
            Return the PMU's counters

            :return: the counters
        """
        return self.counters

    def read(self, counter_name):
        """
            Read the value from a counter

            :param counter_name: The name of counter to read from
            :return: The value of counter
        """
        return self.counters[counter_name].read()

    def get_events(self):
        return self.events

    def enable_event(self, event_id):
        pass

    def disable_event(self, event_id):
        pass
