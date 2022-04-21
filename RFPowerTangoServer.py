import logging
import time

import numpy
import tango
from tango import DispLevel, AttrWriteType, DevState
from tango.server import attribute

from TangoServerPrototype import TangoServerPrototype
from TangoUtils import Configuration
from config_logger import config_logger
from log_exception import log_exception

t0 = time.time()


class RFPowerTangoServer(TangoServerPrototype):
    server_version = '0.0'
    server_name = 'Python RF Power Control Tango Server'
    device_list = []

    anode_power = attribute(label="anode_power", dtype=float,
                            display_level=DispLevel.OPERATOR,
                            access=AttrWriteType.READ,
                            unit="kW", format="%f",
                            doc="Tetrode anode power")

    power_limit = attribute(label="anode_power_limit", dtype=float,
                            display_level=DispLevel.OPERATOR,
                            access=AttrWriteType.READ_WRITE,
                            unit="kW", format="%f",
                            doc="Tetrode anode power limit")

    def init_device(self):
        self.power = 0.0
        self.power_limit_value = 50.0
        self.device_name = ''
        self.timer = None
        self.adc = None
        super().init_device()
        self.power_limit_value = self.config.get('power_limit', 50.0)
        self.power_limit.set_write_value(self.power_limit_value)
        self.configure_tango_logging()

    def set_config(self):
        super().set_config()
        try:
            self.device_name = self.get_name()
            self.set_state(DevState.INIT)
            self.set_status('Initialization')
            self.timer = tango.DeviceProxy(self.config.get('timer', 'binp/nbi/timing'))
            self.adc = tango.DeviceProxy(self.config.get('adc', 'binp/nbi/adc0'))
            self.dac = tango.DeviceProxy(self.config.get('dac', 'binp/nbi/dac0'))

            self.ia = self.get_scale(self.adc, 'APS_C')
            self.ea = self.get_scale(self.adc, 'An_V')
            self.ua = self.get_scale(self.adc, 'RF_UA1')
            self.ic = self.get_scale(self.adc, 'Cath_C')
            self.iscr = self.get_scale(self.adc, 'S_C1(A)')
            self.ug1 = self.get_scale(self.adc, 'RF_UG1')

            self.logger.info('%s has been initialized' % self.device_name)
            self.set_state(DevState.RUNNING)
            self.set_status('Initialized successfully')
        except Exception as ex:
            log_exception(self, 'Exception initiating %s', self.device_name)
            self.set_state(DevState.FAULT)
            self.set_status('Error initializing')
            return False
        return True

    def read_anode_power(self):
        return self.power

    def read_power_limit(self):
        return self.power_limit_value

    def write_power_limit(self, value):
        self.power_limit_value = value
        self.config['power_limit'] = value

    def get_scale(self, dp, name):
        config = dp.get_attribute_config_ex(name)[0]
        try:
            coeff = float(config.display_unit)
        except:
            coeff = 1.0
        return coeff

    def calculate_anode_power(self):
        try:
            ia = self.adc.read_attribute('APS_C').value * self.ia
            ea = self.adc.read_attribute('An_V').value * self.ea
            ua = self.adc.read_attribute('RF_UA1').value * self.ua
            ic = self.adc.read_attribute('Cath_C').value * self.ic
            iscr = self.adc.read_attribute('S_C1(A)').value * self.iscr
            ug1 = self.adc.read_attribute('RF_UG1').value * self.ug1
            try:
                t = numpy.arccos(-77.0/ug1)
                # a0 = (numpy.sin(t) - t * numpy.cos(t)) / (numpy.pi * (1 - numpy.cos(t)))
                a0 = (numpy.sin(t) - t * numpy.cos(t))
                # a1 = (t - numpy.sin(t) * numpy.cos(t)) / (numpy.pi * (1 - numpy.cos(t)))
                a1 = (t - numpy.sin(t) * numpy.cos(t))
                i1 = (ic - iscr) * a1 / a0
                prf = i1 * ua / 2.0
                ptot = ea * ia
                pa = ptot - prf
                return pa
            except:
                log_exception('Can not calculate power')
                return 0.0



        except:
            log_exception(self, '%s Error calculating power' % self.device_name)
        return 1.0

    def pulse_off(self):
        for k in range(12):
            try:
                self.timer.write_attribute('channel_enable' + str(k), False)
            except:
                log_exception('Pulse off error')
            self.logger.info('Pulse off')


def looping():
    global t0
    time.sleep(0.1)
    for dev in RFPowerTangoServer.device_list:
        time.sleep(0.001)
        try:
            p = dev.calculate_anode_power()
            if p > dev.power_limit_vaue:
                dev.logger.error('Anode power limit exceeded')
                dev.pulse_off()
        except:
            log_exception(dev, '%s Error in loop' % dev.device_name)


if __name__ == "__main__":
    RFPowerTangoServer.run_server(event_loop=looping)
