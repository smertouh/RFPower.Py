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


t0 = time.time()
OFF_PASSWORD = 'dnbi'

def read_values(vec):
    result=[]
    try:
        now = datetime.datetime.now()
        s = now.strftime("%Y\%Y-%m\%Y-%m-%d\%Y-%m-%d.log")
        for v in vec:
            with open("d:\\data\\"+s) as f:

                mess=f.readlines()[-1].split(";")
                for mes in mess:
                    if v in mes:
                        if "True" in mes:
                            result.append(1)
                        elif "False"in mes:
                            result.append(0)
                        else:
                            result.append(float(mes.split("=")[1].rsplit(" ",1)[0]))
    except:
        for v in vec:
            result.append(0)
    return result

def calcPRF(val):
    try:
        ua=val[7]
        ic=val[8]
        iscr=val[9]
        ug1=val[10]
        if ug1<77:
            t=1.0e-6
        else:
            t=numpy.arccos(-77.0/ug1)
        a0=(numpy.sin(t) - t * numpy.cos(t))
        a1=(t - numpy.sin(t) * numpy.cos(t))
        i1=(ic - iscr) * a1 / a0
        PRF=i1*ua/2
    except:
        PRF=0
    return PRF

class ReadLogServer(TangoServerPrototype):
    server_version = '0.2'
    server_name = 'Python ReadLogServer Tango Server'
    device_list = []

    U_tot = attribute(label="U_total", dtype=float,
                            display_level=DispLevel.OPERATOR,
                            access=AttrWriteType.READ,
                            unit="kV", format="%f",
                            doc="Total source voltage")

    U_ex = attribute(label="U_extraction", dtype=float,
                            display_level=DispLevel.OPERATOR,
                            access=AttrWriteType.READ,
                            unit="kV", format="%f",
                            doc="Extraction voltage")

    I_b = attribute(label="I_beam", dtype=float,
                               display_level=DispLevel.OPERATOR,
                               access=AttrWriteType.READ,
                               unit="A", format="%f",
                               doc="Beam current at IOS exit")

    I_e = attribute(label="I_electron", dtype=float,
                             display_level=DispLevel.OPERATOR,
                             access=AttrWriteType.READ,
                             unit="A", format="%f",
                             doc="Costreaming electron current")

    P_RF = attribute(label="RF_power", dtype=float,
                            display_level=DispLevel.OPERATOR,
                            access=AttrWriteType.READ,
                            unit="kW", format="%f",
                            doc="Tetrode RF power")

    Lauda = attribute(label="T_Lauda", dtype=float,
                            display_level=DispLevel.OPERATOR,
                            access=AttrWriteType.READ,
                            unit=" C", format="%f",
                            doc="Return temperature of Lauda")

    Protection = attribute(label="Protection", dtype=float,
                      display_level=DispLevel.OPERATOR,
                      access=AttrWriteType.READ,
                      unit=" BD", format="%1.0f",
                      doc="Return number of BD")
    Shot = attribute(label="Shot_number", dtype=int,
                           display_level=DispLevel.OPERATOR,
                           access=AttrWriteType.READ,
                           unit=" shot", format="%6.0f",
                           doc="Returns shot number")



    def init_device(self):
        self.Utot = 0.0
        self.Uex = 0.0
        self.Ib = 0.0
        self.Ie = 0.0
        self.PRF = 0.0
        self.TLauda = 0.0
        self.device_name = ''
        self.BD_protection=0
        self.shot_number=0.0

        super().init_device()
        ReadLogServer.device_list.append(self)


    def read_U_tot(self):
        return self.Utot
    def read_U_ex(self):
        return self.Uex
    def read_I_b(self):
        return self.Ib
    def read_I_e(self):
        return self.Ie
    def read_P_RF(self):
        return self.PRF
    def read_Lauda(self):
        return self.TLauda
    def read_Protection(self):
        return self.BD_protection
    def read_Shot(self):
        return self.shot_number




def looping():
    global t0
    time.sleep(3)
    for dev in ReadLogServer.device_list:
        time.sleep(0.001)
        try:
            pass
        except:
            dev.log_exception('Error in loop')

    #print(s)
    val=(read_values(["RF_UA1","Iac_2","Iex","Uex","Utot","IAG","Ret","RF_UA1","Cath1_C","S_C1(A)","RF_UG1","U110kV","U15kV","I110kV","I15kV","Shot"]))
    
    
    dev.Ib = val[1]-val[5]
    dev.Ie = val[2]-dev.Ib
    dev.Uex = val[3]
    dev.Utot = val[4]
    dev.TLauda = val[6]
    dev.PRF = calcPRF(val)
    dev.BD_protection = int(val[11] + val[12] + val[13] + val[14])
    dev.shot_number = val[15]
if __name__ == "__main__":
    ReadLogServer.run_server(event_loop=looping)
    # RFPowerTangoServer.run_server()
