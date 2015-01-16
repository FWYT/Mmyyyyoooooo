import imp
import sys
import myo
import math
import time
import numpy
from myo.lowlevel import pose_t, stream_emg
sys.path.append('../')
myo.init()

from myo.six import print_

def convert_to_rpy(qternion):
    x = qternion[0]
    y = qternion[1]
    z = qternion[2]
    w = qternion[3]

    roll1=math.atan2(2.0*(w*x + y*z),1.0 - 2.0*(x**2+y**2))
    pitch1=math.asin(max(-1.0,min(1.0, 2.0*(w*y-z*x))))
    yaw1=math.atan2(2.0*(w*z + x*y),1.0 - 2.0*(y**2 + z**2))

    roll1=math.degrees(roll1)
    pitch1=math.degrees(pitch1)
    yaw1=math.degrees(yaw1)
    output=[roll1,pitch1,yaw1]
    return output

def assign_pose_number(pose):
    global pose_number
    if (pose == 'rest'):
        pose_number = 0
        pose_name = 'rest'

    elif (pose=='fingers_spread'):
        pose_number = 1
        pose_name ='fingers_spread'

    elif (pose=='thumb_to_pinky'):
        pose_number = 2
        pose_name ='thumb_to_pinky'

    elif (pose=='fist'):
        pose_number = 3
        pose_name = 'fist'

    elif (pose=='wave_in'):
        pose_number = 4
        pose_name = 'wave_in'

    elif (pose=='wave_out'):
        pose_number = 5
        pose_name = 'wave_out'

    return pose_number


class Listener(myo.DeviceListener):
    #return False from any method to stop the Hub

    def __init__(self):
        self.enable = 0
        self.odr=0
        self.counter2=0
        self.rcfull=[None]*100
        self.rsfull=[None]*100
        self.pcfull=[None]*100
        self.psfull=[None]*100
        self.ycfull=[None]*100
        self.ysfull=[None]*100
        self.rollb=0
        self.pitchb=0
        self.yawb=0
        self.state=-1
        self.fistcount=0
        self.Odata = []
        self.Adata = []
        self.Edata = []


    def on_connect(self, myo, timestamp):
        print_("Connected to Myo")
        myo.vibrate('short')
        myo.request_rssi()
        myo.set_stream_emg(stream_emg.enabled)
        print_("Enabling EMG")

    def on_rssi(self, myo, timestamp, rssi):
        print_("RSSI:", rssi)

    def on_event(self, event):
        r""" Called before any of the event callbacks. """

    def on_event_finished(self, event):
        r""" Called after the respective event callbacks have been
        invoked. This method is *always* triggered, even if one of
        the callbacks requested the stop of the Hub. """

    def on_pair(self, myo, timestamp):
        print_('on_pair')

    def on_disconnect(self, myo, timestamp):
        print_('on_disconnect')

    def on_pose(self, myo, timestamp, pose):
        self.nowpose=pose
        print_('on_pose', pose)
##        if pose == pose_t.double_tap:
##            print_("Enabling EMG")
##            myo.set_stream_emg(stream_emg.enabled)
##        elif pose == pose_t.fingers_spread:
##            myo.set_stream_emg(stream_emg.disabled)
        if pose == "fist":
            self.fistcount=self.fistcount+1
            if self.fistcount==1:
                self.state=0
                print("Entering state 0")



    def on_orientation_data(self, myo, timestamp, orientation):
        self.odr=orientation
        if self.state>-1:
            if self.counter2<100:
                output=convert_to_rpy(self.odr)
                roll1=output[0]
                pitch1=output[1]
                yaw1=output[2]

                self.rcfull[self.counter2] = math.cos(math.radians(roll1))
                self.rsfull[self.counter2] = math.sin(math.radians(roll1))
                self.pcfull[self.counter2] = math.cos(math.radians(pitch1))
                self.psfull[self.counter2] = math.sin(math.radians(pitch1))
                self.ycfull[self.counter2] = math.cos(math.radians(yaw1))
                self.ysfull[self.counter2] = math.sin(math.radians(yaw1))
                
                if self.state!=1:
                    print ("orientation")
                    print_(roll1,pitch1,yaw1)
                    if (self.state == 2):
                        rollc = math.cos(math.radians(roll1))
                        rolls = math.sin(math.radians(roll1))
                        pitchc = math.cos(math.radians(pitch1))
                        pitchs = math.sin(math.radians(pitch1))
                        yawc = math.cos(math.radians(yaw1))
                        yaws = math.sin(math.radians(yaw1))

                        rollbc = math.cos(math.radians(self.rollb))
                        rollbs = math.sin(math.radians(self.rollb))
                        pitchbc = math.cos(math.radians(self.pitchb))
                        pitchbs = math.sin(math.radians(self.pitchb))
                        yawbc = math.cos(math.radians(self.yawb))
                        yawbs = math.sin(math.radians(self.yawb))

                        rollf = math.degrees(math.atan2(rolls-rollbs,rollc-rollbc))
                        pitchf = math.degrees(math.atan2(pitchs-pitchbs,pitchc-pitchbc))
                        yawf = math.degrees(math.atan2(yaws-yawbs,yawc-yawbc))

                        self.Odata.append([rollf, pitchf, yawf])
                                        



                
            self.counter2=self.counter2+1


        if self.counter2 == 100:
            rc = numpy.mean(self.rcfull)
            pc = numpy.mean(self.pcfull)
            yc = numpy.mean(self.ycfull)
            rs = numpy.mean(self.rsfull)
            ps = numpy.mean(self.psfull)
            ys = numpy.mean(self.ysfull)

            if self.state==0:  # calibration-
                print ("Calibration")
                self.rollb = math.degrees(math.atan2(rs,rc))
                self.pitchb = math.degrees(math.atan2(ps,pc))
                self.yawb = math.degrees(math.atan2(ys,yc))
                baseline=[self.rollb,self.pitchb,self.yawb]
                print("baseline", baseline)
                print("Calibration Complete! You have 2 seconds to change your gesture and then record a new one for 2")
                self.counter2=0
                self.state=1
                self.start_time = time.time()
                print("Entering state 1")

            elif self.state == 1:

                for i in range(1,2000):
                    for j in range(1,10000):
                        a=i
                self.counter2=0
                self.state = 2
                print("Entering state 2")

            elif self.state == 2:  # data collection

                
                pose_number=assign_pose_number(self.nowpose)
                new_number=5#input("Please enter the gesture number for the last gesture: ")
                print ("Accel", self.Adata, len(self.Adata))
                print ("Orient", self.Odata, len(self.Odata))
                print ("EMG", self.Edata, len(self.Edata))
                if (len(self.Edata) == 400):
                    fo = open("trainingdata200.csv","ab")
                    iOA = 0
                    run = 0
                                           

##                    for point in self.Odata:
##                        fo.write('%s, %f,%f, %f, %f\n' % (point[0], point[1], point[2], point[3], new_number))
##
##                    for point in self.Adata:
##                        fo.write("%s, %f, %f, %f, %f\n" %(point[0], point[1][0], point[1][1], point[1][2], new_number))
                
                    for point in self.Edata:
                        fo.write('%f,%f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f\n' % (self.Odata[iOA][0], self.Odata[iOA][1], self.Odata[iOA][2], self.Adata[iOA][0], self.Adata[iOA][1],
                                                                                                        self.Adata[iOA][2], point[0], point[1], point[2], point[3], point[4],point[5], point[6],point[7], new_number))
##                        fo.write("%s, %f, %f, %f, %f\n" %(self.Adata[iOA][0], self.Adata[iOA][1], self.Adata[iOA][2], new_number))
##                        fo.write("%s, %f, %f, %f, %f, %f, %f, %f, %f, %f\n" %(point[0], point[1], point[2], point[3], point[4],point[5], point[6],point[7], new_number))
                        run+=1
                        if (run == 4):
                            run=0
                            iOA+=1
                    
                    fo.close()

                    f50 = open("trainingdata50.csv","ab")
                    EI = 3
                    for i in xrange(100):
                        f50.write('%f,%f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f\n' % (self.Odata[i][0], self.Odata[i][1], self.Odata[i][2], self.Adata[i][0], self.Adata[i][1],
                                                                                                  self.Adata[i][2], self.Edata[EI][0], self.Edata[EI][1], self.Edata[EI][2], self.Edata[EI][3],
                                                                                                  self.Edata[EI][4],self.Edata[EI][5], self.Edata[EI][6],self.Edata[EI][7], new_number))
                        EI+=4
                    f50.close()
                    print("Saved!")
                else:
                    print ("Not Saved.")
                self.counter2=0
                cont = raw_input("Press c to record another")
                if (cont == "c"):
                    self.Odata = []
                    self.Adata = []
                    self.Edata = []
                    self.state = 2
                else:
                    self.state=-1


            #print_(orientation)


    def on_accelerometor_data(self, myo, timestamp, acceleration):
        self.acc = acceleration
        if (self.state > -1):
            if (self.state != 1):
                print("acceleration")
                print (acceleration)
                if (self.state == 2):
                    self.Adata.append(acceleration)
        
    def on_gyroscope_data(self, myo, timestamp, gyroscope):
        pass

    def on_unlock(self, myo, timestamp):
        pass

    def on_lock(self, myo, timestamp):
        pass

    def on_sync(self, myo, timestamp):
        pass

    def on_unsync(self, myo, timestamp):
        pass

    def on_emg(self, myo, timestamp, emg):
        self.emg = emg
        if (self.state > -1):
            if (self.state !=1):
                print ("emg")
                print (emg)
                if (self.state ==2):
                    self.Edata.append(emg)
    
def main():
    hub = myo.Hub()
    hub.set_locking_policy(myo.locking_policy.none)
    hub.run(10000000, Listener())

    # Listen to keyboard interrupts and stop the
    # hub in that case.
    try:
        while hub.running:
            myo.time.sleep(0.2)
    except KeyboardInterrupt:
        print_("Quitting ...")
        hub.stop(True)

if __name__ == '__main__':
    main()

