"""
    Helper class for the Manager to perform automatic placement of ODE objects.
"""

from vector_ops import *
import ode

class Placement(object):
    """ ODE Object Placement Class """
    Identity_R = [[1,0,0,0],[0,1,0,0],[0,0,1,0]]
    #def __init__(self,man):
    #    """ Initializer for the class.  Link with the Manager """
    #    self.man = man

    @staticmethod
    def place_capsule(obj1,obj2,rot=0.):
        """ Place obj2 at the negative end of obj1 """

        # Set the rotation of the second body to match that of the first.
        quat1 = obj1.getQuaternion()
        obj2.setQuaternion(quat1)
        if rot:
            obj2.setRotation(form_rotation(rot))

        # Get the position of the point on the parent that we wish to join the second body on.
        obj_pos = obj1.getRelPointPos((0.,obj1.length/2.,0.))
        obj2_pos = obj2.getRelPointPos((0.,-obj2.length/2.,0.))

        print(obj_pos[0],obj_pos[2],obj_pos[1])
        print(obj2_pos[0],obj2_pos[2],obj2_pos[1])

        new_pos = add3(obj_pos,neg3(obj2_pos))

        obj2.setPosition((new_pos[0],new_pos[2],new_pos[1]))

        print(new_pos[0],new_pos[2],new_pos[1])

        return [obj_pos[0],obj_pos[2],obj_pos[1]]

    @staticmethod
    def place_capsule_trans(obj1,obj2,rot=0.):
        """ Place obj2 at the positive end of obj1.

        Args:
            obj1: base object to place
            obj2: object to move to the end of obj1
            rot: optional rotation to apply to obj2
        Returns:
            position to place a joint between the two objects.
        """
        # Set the rotation of the second body to match that of the first.
        quat1 = obj1.getQuaternion()
        quat2 = obj2.getQuaternion()
        obj2.setQuaternion(QMultiply0(quat1,quat2))
        obj2.setQuaternion(quat1)
        if rot:
            quat2 = QFromR(form_rotation([rot[0],0,0]))
            obj2.setQuaternion(QMultiply0(quat1, quat2))
            quat1 = obj2.getQuaternion()
            quat2 = QFromR(form_rotation([0,rot[1],0]))
            obj2.setQuaternion(QMultiply0(quat1, quat2))
            quat1 = obj2.getQuaternion()
            quat2 = QFromR(form_rotation([0,0,rot[2]]))
            obj2.setQuaternion(QMultiply0(quat1, quat2))
        # Get the position of the point on the parent that we wish to join the second body on.
        obj_pos = obj1.getRelPointPos((0.,0,-obj1.length/2.))
        obj2_pos = obj2.getRelPointPos((0.,0.,obj2.length/2.))

        new_pos = sub3(obj_pos,obj2_pos)

        obj2.setPosition(new_pos)

        obj2_pos = obj2.getPosition()

        return [obj_pos[0],obj_pos[1],obj_pos[2]]

    @staticmethod
    def place_capsule_at_trans(obj1,pos=[0,0,0],rot=0.):
        """ Place obj1 so that it's negative end is at the specified position. 

        Args:
            obj1: object to place 
            pos: position to put the negative end at
            rot: optional rotation to apply to obj2
        """
        # Set the rotation of the second body to match that of the first.
        quat1 = obj1.getQuaternion()
        if rot:
            quat2 = QFromR(form_rotation([rot[0],0,0]))
            obj1.setQuaternion(QMultiply0(quat1, quat2))
            quat1 = obj1.getQuaternion()
            quat2 = QFromR(form_rotation([0,rot[1],0]))
            obj1.setQuaternion(QMultiply0(quat1, quat2))
            quat1 = obj1.getQuaternion()
            quat2 = QFromR(form_rotation([0,0,rot[2]]))
            obj1.setQuaternion(QMultiply0(quat1, quat2))
        # Get the position of the point on the parent that we wish to join the second body on.
        obj_pos = obj1.getRelPointPos((0.,0,obj1.length/2.))

        new_pos = sub3(pos,obj_pos)

        obj1.setPosition(new_pos)
