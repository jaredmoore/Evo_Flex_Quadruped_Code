""" 
    Class to generate a signal based on internal values.  Can be used to generate
    a temporal signal, or as Tony suggested, to translate a sensor reading into some
    sort of periodic signal.
"""
import math
import random

class TSignal(object):
    """ Produce a signal based on internal values. """

    def __init__(self,params=0):
        """ Initializer.

        Args:
            params: list of the parameters associated with a signal, for basis or validation
        """
        if(params):
            self.amp_1 = params[0] 
            self.amp_2 = params[1]
            self.frq_1 = params[2]
            self.frq_2 = params[3]
            self.ph_1 = params[4]
            self.ph_2 = params[5]
        else:
            self.amp_1 = float("{0:.4f}".format(random.random()))
            self.amp_2 = float("{0:.4f}".format(random.random()))
            self.frq_1 = float("{0:.4f}".format(random.random()*2.*math.pi))
            self.frq_2 = float("{0:.4f}".format(random.random()*2.*math.pi))
            self.ph_1 = float("{0:.4f}".format(random.random()*2.*math.pi))
            self.ph_2 = float("{0:.4f}".format(random.random()*2.*math.pi))

        self.num_params = 6

        self.throttle = False
        self.throttle_num = 0
        self.reset_signal() 

    def __str__(self):
        """ To String representation of the signal. """
        return "TSignal: "+str(self.amp_1)+","+str(self.amp_2)+","+str(self.frq_1)+","+str(self.frq_2)+","+str(self.ph_1)+","+str(self.ph_2)

    def copy(self):
        """ Copy self. """
        return TSignal(params=self.serialize())

    def serialize(self):
        """ Return a list of the parameters. """
        return [self.amp_1,self.amp_2,self.frq_1,self.frq_2,self.ph_1,self.ph_2]

    def next(self):
        """ Get the next value in the signal. """
        if self.throttle:
            self.throttle_num += 1
            if self.throttle_num < 10:
                return (self._get_value()/10.)*self.throttle_num
            else:
                self.throttle = False
                self.throttle_num = 0
        self.tick += self.ts
        return self._get_value() 

    def _get_value(self):
        """ Get the value of the signal at current timestep """

        return self._get_value_at(self.tick) 

    def _get_value_at(self,val):
        """ Get the value of the signal at the provided spot.

        Args:
            val: value to use to get signal.
        Returns:
            value at position
        """
        return (self.amp_1*math.sin(self.frq_1*val+self.ph_1)+
                self.amp_2*math.cos(self.frq_2*val+self.ph_2))/(self.amp_1+self.amp_2+0.000001)

    def mutate(self):
        """ Mutate one of the parameters of the signal using a gaussian distribution. """
        mut_loc = random.randint(0,5)

        if mut_loc == 0:
            self.amp_1 = float("{0:.4f}".format(self.amp_1 + random.uniform(-.5,.5)))
            if self.amp_1 < 0:
                self.amp_1 = 0
            elif self.amp_1 > 1:
                self.amp_1 = 1
        elif mut_loc == 1:
            self.amp_2 = float("{0:.4f}".format(self.amp_2 + random.uniform(-.5,.5)))
            if self.amp_2 < 0:
                self.amp_2 = 0
            elif self.amp_2 > 1:
                self.amp_2 = 1
        elif mut_loc == 2:
            self.frq_1 = float("{0:.4f}".format(self.frq_1 + random.uniform(-math.pi,math.pi)))
            if self.frq_1 < 0:
                self.frq_1 = 0
            elif self.frq_1 > 2.*math.pi:
                self.frq_1 = float("{0:.4f}".format(2.*math.pi))
        elif mut_loc == 3:
            self.frq_2 = float("{0:.4f}".format(self.frq_2 + random.uniform(-math.pi,math.pi)))
            if self.frq_2 < 0:
                self.frq_2 = 0
            elif self.frq_2 > 2.*math.pi:
                self.frq_2 = float("{0:.4f}".format(2.*math.pi))
        elif mut_loc == 4:
            self.ph_1 = float("{0:.4f}".format(self.ph_1 + random.uniform(-math.pi,math.pi)))
            if self.ph_1 < 0:
                self.ph_1 = 0
            elif self.ph_1 > 2.*math.pi:
                self.ph_1 = float("{0:.4f}".format(2.*math.pi))
        elif mut_loc == 5:
            self.ph_2 = float("{0:.4f}".format(self.ph_2 + random.uniform(-math.pi,math.pi)))
            if self.ph_2 < 0:
                self.ph_2 = 0
            elif self.ph_2 > 2.*math.pi:
                self.ph_2 = float("{0:.4f}".format(2.*math.pi))
        self.reset_signal()

    def crossover(self,sec_signal):
        """ Crossover two individual signals.

        Args:
            sec_signal: other signal to crossover from.
        """
        x_pts = random.sample([0,1,2,3,4,5],2)
        if x_pts[1] < x_pts[0]:
            tmp = x_pts[1]
            x_pts[1] = x_pts[0]
            x_pts[0] = x_pts[1]
    
        params = []
        one_params = self.serialize()
        two_params = sec_signal.serialize()

        # Decide on outer or inner crossover.
        if random.randint(0,1) == 0:
            for i in xrange(self.num_params):
                if i < x_pts[0] or i > x_pts[1]:
                    params.append(one_params[i])
                else:
                    params.append(two_params[i])
        else:
            for i in xrange(self.num_params):
                if i < x_pts[0] or i > x_pts[1]:
                    params.append(two_params[i])
                else:
                    params.append(one_params[i])
        return TSignal(params=params)

    def reset_signal(self):
        """ Reset the signal to start from 0. """
        # Prepare the signal by moving towards 0 for a common starting state.
        
        # Keep track of the closest value to zero for throttle up.
        closest_ts = 0
        closest_val = 10
        counter = 0

        self.tick = 0
        self.ts = 0.01
        threshold = 0.02
        val = self._get_value() 
        while((val > threshold or val < -threshold) and counter < 500):
            self.tick += self.ts
            val = self._get_value()
            if math.fabs(val) < closest_val:
                closest_ts = self.tick
                closest_val = math.fabs(val)
            counter += 1
        if counter == 500:
            self.tick = closest_ts
            self.throttle = True
        else:
            self.tick -= self.ts
            self.throttle = False
        self.throttle_num = 0

