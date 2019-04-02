from __future__ import print_function
from P13pt.mascril.measurement import MeasurementBase
from P13pt.mascril.parameter import Sweep, String, Folder, Boolean
from P13pt.drivers.bilt import Bilt, BiltVoltageSource, BiltVoltMeter

import time
import numpy as np
import os

class Measurement(MeasurementBase):
    params = {
        'Vdss': Sweep([0.0]),
        'Vg1s': Sweep([0.0]),
        'Vg2s': Sweep([0.0]),
        'commongate': Boolean(False),
        'Rg1': 100e3,
        'Rg2': 100e3,
        'Rds': 22e3,
        'stabilise_time': 0.05,
        'comment': String(''),
        'data_dir': Folder(r'D:\MeasurementJANIS\Holger\KTW H5 2x3\2017-11-09 LHe')
    }

    observables = ['Vg1', 'Vg1m', 'Ileak1', 'Vg2', 'Vg2m', 'Ileak2', 'Vds', 'Vdsm', 'Rs']

    alarms = [
        ['np.abs(Ileak1) > 1e-8', MeasurementBase.ALARM_CALLCOPS],
        ['np.abs(Ileak2) > 1e-8', MeasurementBase.ALARM_CALLCOPS],
        ['np.abs(Vg1-Vg2)', MeasurementBase.ALARM_SHOWVALUE]        # useful if we just want to know how much voltage
                                                                    # is applied between the two gates
    ]

    def measure(self, data_dir, comment, Vdss, Vg1s, Vg2s, commongate, Rg1, Rg2, Rds, stabilise_time, **kwargs):
        print("===================================")
        print("Starting acquisition script...")

        # initialise instruments
        try:
            print("Setting up DC sources and voltmeters...")
            bilt = Bilt('TCPIP0::192.168.0.2::5025::SOCKET')
            self.sourceVds = sourceVds = BiltVoltageSource(bilt, "I1", initialise=False)
            self.sourceVg1 = sourceVg1 = BiltVoltageSource(bilt, "I2", initialise=False)
            self.sourceVg2 = sourceVg2 = BiltVoltageSource(bilt, "I3", initialise=False)
            self.meterVds = meterVds = BiltVoltMeter(bilt, "I5;C1", "2", "Vdsm")
            self.meterVg1 = meterVg1 = BiltVoltMeter(bilt, "I5;C2", "2", "Vg1m")
            self.meterVg2 = meterVg2 = BiltVoltMeter(bilt, "I5;C3", "2", "Vg2m")
            print("DC sources and voltmeters are set up.")
        except:
            print("There has been an error setting up DC sources and voltmeters.")
            raise

        timestamp = time.strftime('%Y-%m-%d_%Hh%Mm%Ss')

        # prepare saving data
        filename = timestamp + '_' + (comment if comment else '') + '.txt'
        self.prepare_saving(os.path.join(data_dir, filename))

        # loops
        for Vds in Vdss:
            sourceVds.set_voltage(Vds)
            for Vg2 in Vg2s:
                if not commongate:
                    sourceVg2.set_voltage(Vg2)
                for Vg1 in Vg1s:
                    if self.flags['quit_requested']:
                        return locals()
    
                    sourceVg1.set_voltage(Vg1)
                    if commongate:
                        Vg2 = Vg1
                        sourceVg2.set_voltage(Vg1)
    
                    # stabilise
                    time.sleep(stabilise_time)
    
                    # measure
                    Vdsm = meterVds.get_voltage()
                    Vg1m = meterVg1.get_voltage()
                    Vg2m = meterVg2.get_voltage()
    
                    # do calculations
                    Ileak1 = (Vg1-Vg1m)/Rg1
                    Ileak2 = (Vg2-Vg2m)/Rg2
                    Rs = Rds*Vdsm/(Vds-Vdsm)
    
                    # save data
                    self.save_row(locals())

        print("Acquisition done.")
        
        return locals()

    def tidy_up(self):
        self.end_saving()

        print("Driving all voltages back to zero...")

        self.sourceVds.set_voltage(0.)
        self.sourceVg1.set_voltage(0.)
        self.sourceVg2.set_voltage(0.)


if __name__ == "__main__":
    m = Measurement()
    m.run()