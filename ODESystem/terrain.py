"""
    Create a set of random terrain in an ODE world.
"""

from manager import ODEManager
import math

class Terrain(object):
    """ Create terrain for an ODE world. """

    def __init__(self, man):
        """ Initialize the terrain class. """
        self.man = man

    def add_checkered_boxes(self,height=1,width=1,grid_size=20):
        """ Add checkered boxes to the world. 
        
        Args:
            height: height of the boxes to generate
            width: width of the boxes to generate
            grid_size: size of the grid to generate boxes for.
        """
        k = 0
        off = 0
        for i in range(0-grid_size/2,grid_size/2):
            off = 0 if off == 1 else 1
            for j in range(0-grid_size/2,grid_size/2):
                if off:
                    if not((i >= -2 and i < 2) and (j >= -2 and j < 2)):
                        self.man.create_box(k,[width,height,width],[(i+width/2.),height/2.,j+width/2.],terrain=True)
                        k += 1
                    off = 0
                else:
                    off = 1

    def add_concentric_bumps(self, height=1., width=1., num_rings=4):
        """ Add a concentric pattern of rings around the starting location.

        Args:
            height: height of the obstacles
            width:  width of the rings
            num_rings: number of rings to create
        """
        bias = 2 # Initial ring placed bordering this.

        k = 0
        for j in range(num_rings):
            for i in range(bias):
                self.man.create_box(k,[width,height,1.],[(bias+width/2.),height/2.,i+1/2.],terrain=True)
                k += 1
                self.man.create_box(k,[width,height,1.],[(-bias-width/2.),height/2.,i+1./2.],terrain=True)
                k += 1
                self.man.create_box(k,[width,height,1.],[(bias+width/2.),height/2.,-i-1./2.],terrain=True)
                k += 1
                self.man.create_box(k,[width,height,1.],[(-bias-width/2.),height/2.,-i-1./2.],terrain=True)
                k += 1
                self.man.create_box(k,[1.,height,width],[i+1./2.,height/2.,bias+width/2.],terrain=True)
                k += 1
                self.man.create_box(k,[1.,height,width],[i+1./2.,height/2.,-bias-width/2.],terrain=True)
                k += 1
                self.man.create_box(k,[1.,height,width],[-i-1./2.,height/2.,bias+width/2.],terrain=True)
                k += 1
                self.man.create_box(k,[1.,height,width],[-i-1./2.,height/2.,-bias-width/2.],terrain=True)
                k += 1
            self.man.create_box(k,[width,height,width],[bias+width/2.,height/2.,bias+width/2.],terrain=True)
            k += 1
            self.man.create_box(k,[width,height,width],[-bias-width/2.,height/2.,bias+width/2.],terrain=True)
            k += 1
            self.man.create_box(k,[width,height,width],[-bias-width/2.,height/2.,-bias-width/2.],terrain=True)
            k += 1
            self.man.create_box(k,[width,height,width],[bias+width/2.,height/2.,-bias-width/2.],terrain=True)
            k += 1
            bias += 2
        
    def add_concentric_hill(self, height=1., width=1., num_rings=4):
        """ Add a concentrically increasing hill around the start location.

        Args:
            height: height of the obstacles
            width:  width of the rings
            num_rings: number of rings to create
        """
        bias = 2 # Initial ring placed bordering this.

        k = 0
        for j in range(num_rings):
            placement = 2+(bias-2)*width
            elev = height/2. + height*j
            for i in range(bias):
                self.man.create_box(k,[width,height,1.],[(placement+width/2.),elev,i+1/2.],terrain=True)
                k += 1
                self.man.create_box(k,[width,height,1.],[(-placement-width/2.),elev,i+1./2.],terrain=True)
                k += 1
                self.man.create_box(k,[width,height,1.],[(placement+width/2.),elev,-i-1./2.],terrain=True)
                k += 1
                self.man.create_box(k,[width,height,1.],[(-placement-width/2.),elev,-i-1./2.],terrain=True)
                k += 1
                self.man.create_box(k,[1.,height,width],[i+1./2.,elev,placement+width/2.],terrain=True)
                k += 1
                self.man.create_box(k,[1.,height,width],[i+1./2.,elev,-placement-width/2.],terrain=True)
                k += 1
                self.man.create_box(k,[1.,height,width],[-i-1./2.,elev,placement+width/2.],terrain=True)
                k += 1
                self.man.create_box(k,[1.,height,width],[-i-1./2.,elev,-placement-width/2.],terrain=True)
                k += 1
            self.man.create_box(k,[width,height,width],[placement+width/2.,elev,placement+width/2.],terrain=True)
            k += 1
            self.man.create_box(k,[width,height,width],[-placement-width/2.,elev,placement+width/2.],terrain=True)
            k += 1
            self.man.create_box(k,[width,height,width],[-placement-width/2.,elev,-placement-width/2.],terrain=True)
            k += 1
            self.man.create_box(k,[width,height,width],[placement+width/2.,elev,-placement-width/2.],terrain=True)
            k += 1
            bias += 1 
            
