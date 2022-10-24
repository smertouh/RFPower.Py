import logging
import sys
import time

import numpy
import tango
from tango import DispLevel, AttrWriteType, DevState
from tango.server import attribute, command

sys.path.append('../TangoUtils')
from TangoServerPrototype import TangoServerPrototype
from TangoUtils import Configuration
from config_logger import config_logger
from log_exception import log_exception
import datetime
import PyTango
from tango import DeviceProxy


t0 = time.time()
OFF_PASSWORD = 'dnbi'



class HV_RF_ConditioningServer(TangoServerPrototype):
    server_version = '0.1'
    server_name = 'Python HV_RF_Conditioning Tango Server'
    device_list = []

    U_ac_cur = attribute(label="U_ac_cur", dtype=float,
                            display_level=DispLevel.OPERATOR,
                            access=AttrWriteType.READ,
                            unit="kV", format="%f",
                            doc="Total source voltage")
    U_ac_step_no_BD = attribute(label="U_ac_step_no_BD", dtype=float,
                         display_level=DispLevel.OPERATOR,
                         access=AttrWriteType.READ_WRITE,
                         unit="%", format="%f",
                         doc="Total source voltage")
    U_ac_step_BD = attribute(label="U_ac_step_BD", dtype=float,
                                display_level=DispLevel.OPERATOR,
                                access=AttrWriteType.READ_WRITE,
                                unit="%", format="%f",
                                doc="Total source voltage")
    U_ac_target = attribute(label="U_ac_target", dtype=float,
                         display_level=DispLevel.OPERATOR,
                         access=AttrWriteType.READ_WRITE,
                         unit="kV", format="%f",
                         doc="Total source voltage")
    U_ac_conditioning_start = attribute(label="U_ac_conditioning_start", dtype=bool,
                            display_level=DispLevel.OPERATOR,
                            access=AttrWriteType.READ_WRITE,
                            unit="kV", format="%f",
                            doc="Total source voltage")





    def init_device(self):
        self.device_name = ''
        self.tango_test = tango.DeviceProxy("binp/auto/1")
        self.shot_number =0
        self.BD=self.tango_test.read_attribute("Protection").value



        HV_RF_ConditioningServer.device_list.append(self)
        # extraction
        self.device_Uex1=tango.DeviceProxy("ET7000_server/test/pet4_7026")
        self.device_Uex2=tango.DeviceProxy("ET7000_server/test/pet25_7026")
        #TangoAbstractSpinBox('ET7000_server/test/pet4_7026/ao00', self.doubleSpinBox_5),
        #TangoAbstractSpinBox('ET7000_server/test/pet25_7026/ao01', self.doubleSpinBox_8),
        # acceleration

        self.UacstepnoBD = 1
        self.UacstepBD = 0
        self.Uacconditioningstart = 0

        self.device_Uac1=tango.DeviceProxy('ET7000_server/test/pet9_7026')
        self.device_Uac2=tango.DeviceProxy('ET7000_server/test/pet7_7026')
        try:
            self.Uaccur=self.tango_test.read_attribute("U_tot").value
        except PyTango.DevFailed:
            self.Uaccur = 0
        self.Uactarget = self.Uaccur
        #TangoAbstractSpinBox('ET7000_server/test/pet9_7026/ao00', self.doubleSpinBox_9),
        #TangoAbstractSpinBox('ET7000_server/test/pet7_7026/ao00', self.doubleSpinBox_10),

        super().init_device()

    def read_U_ac_cur(self):
        self.Uaccur=self.tango_test.read_attribute("U_tot").value
        return self.Uaccur
    def read_U_ac_step_no_BD(self):
        return self.UacstepnoBD
    def read_U_ac_step_BD(self):
        return self.UacstepBD
    def read_U_ac_target(self):
        return self.Uactarget
    def read_U_ac_conditioning_start(self):
        return self.Uacconditioningstart

    def write_U_ac_step_no_BD(self,value):
        self.UacstepnoBD=value
        return self.UacstepnoBD
    def write_U_ac_step_BD(self,value):
        self.UacstepBD=value
        return self.UacstepBD
    def write_U_ac_target(self,value):
        self.Uactarget=value
        return self.Uactarget
    def write_U_ac_conditioning_start(self,value):
        self.Uacconditioningstart=value
        return self.Uacconditioningstart




def looping():
    global t0
    time.sleep(0.1)

    for dev in HV_RF_ConditioningServer.device_list:
        dev.shot_number -= 1
        time.sleep(0.001)
        try:
            if dev.shot_number==(dev.tango_test.read_attribute("Shot").value):
                pass
            else:
                dev.shot_number=(dev.tango_test.read_attribute("Shot").value)
                try:
                    dev.UacSt=dev.device_Uac2.read_attribute("ao00").value
                except PyTango.DevFailed:
                    dev.UacSt= 0

                try:
                    if dev.BD > 0 :
                        dev.device_Uac2.write_attribute("ao00", dev.UacSt + dev.UacstepBD)

                    elif dev.Uactarget> dev.Uaccur:
                        print(dev.UacSt + dev.UacstepnoBD)
                        dev.device_Uac2.ao00 = (dev.UacSt + dev.UacstepnoBD)
                    else:
                        #dev.Uacconditioningstart=0
                        pass
                except PyTango.DevFailed:
                    pass

                #print(dev.UacSt + dev.UacstepBD)
        except:
            dev.log_exception('Error in loop')


if __name__ == "__main__":
    HV_RF_ConditioningServer.run_server(event_loop=looping)
    # RFPowerTangoServer.run_server()
