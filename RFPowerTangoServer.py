import logging
import time

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
                            doc="Thetrode anode power")

    power_limit = attribute(label="anode_power_limit", dtype=float,
                            display_level=DispLevel.OPERATOR,
                            access=AttrWriteType.READ_WRITE,
                            unit="kW", format="%f",
                            doc="Thetrode anode power limit")

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
            self.timer = tango.DeviceProxy(self.config.get('timer', 'binp/nbi/timer'))
            self.adc = tango.DeviceProxy(self.config.get('adc', 'binp/nbi/adc'))
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

    def calculate_anode_power(self):
        return 1.0


def looping():
    global t0
    time.sleep(0.1)
    for dev in RFPowerTangoServer.device_list:
        time.sleep(0.001)
        try:
            p = dev.calculate_anode_power()
            if p > dev.power_limit_vaue:
                dev.logger.error('Anode power limit exceeded')
                dev.stop_opertion()
        except:
            log_exception(dev, '%s Error in loop' % dev.device_name)


if __name__ == "__main__":
    RFPowerTangoServer.run_server(event_loop=looping)
