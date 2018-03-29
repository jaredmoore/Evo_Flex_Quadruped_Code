'''
    Miscellaneous methods for performing vector math when working with ODE objects.
'''

from math import *

ANG_TO_RAD = pi/180.
RAD_TO_ANG = 180./pi

def sign(x):
    """Returns 1.0 if x is positive, -1.0 if x is negative or zero."""
    if x > 0.0: return 1.0
    else: return -1.0

def len3(v):
    """Returns the length of 3-vector v."""
    return sqrt(v[0]**2 + v[1]**2 + v[2]**2)

def neg3(v):
    """Returns the negation of 3-vector v."""
    return (-v[0], -v[1], -v[2])

def add3(a, b):
    """Returns the sum of 3-vectors a and b."""
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

def sub3(a, b):
    """Returns the difference between 3-vectors a and b."""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def mul3(v, s):
    """Returns 3-vector v multiplied by scalar s."""
    return (v[0] * s, v[1] * s, v[2] * s)

def div3(v, s):
    """Returns 3-vector v divided by scalar s."""
    return (v[0] / s, v[1] / s, v[2] / s)

def dist3(a, b):
    """Returns the distance between point 3-vectors a and b."""
    return len3(sub3(a, b))

def norm3(v):
    """Returns the unit length 3-vector parallel to 3-vector v."""
    l = len3(v)
    if (l > 0.0): return (v[0] / l, v[1] / l, v[2] / l)
    else: return (0.0, 0.0, 0.0)

def dot3(a, b):
    """Returns the dot product of 3-vectors a and b."""
    return (a[0] * b[0] + a[1] * b[1] + a[2] * b[2])

def cross(a, b):
    """Returns the cross product of 3-vectors a and b."""
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0])

def project3(v, d):
    """Returns projection of 3-vector v onto unit 3-vector d."""
    return mul3(v, dot3(norm3(v), d))

def acosdot3(a, b):
    """Returns the angle between unit 3-vectors a and b."""
    x = dot3(a, b)
    if x < -1.0: return pi
    elif x > 1.0: return 0.0
    else: return acos(x)

def rotate3(m, v):
    """Returns the rotation of 3-vector v by 3x3 (row major) matrix m."""
    return (v[0] * m[0] + v[1] * m[1] + v[2] * m[2],
        v[0] * m[3] + v[1] * m[4] + v[2] * m[5],
        v[0] * m[6] + v[1] * m[7] + v[2] * m[8])

def invert3x3(m):
    """Returns the inversion (transpose) of 3x3 rotation matrix m."""
    return (m[0], m[3], m[6], m[1], m[4], m[7], m[2], m[5], m[8])

def zaxis(m):
    """Returns the z-axis vector from 3x3 (row major) rotation matrix m."""
    return (m[2], m[5], m[8])

def calcRotMatrix(axis, angle):
    """
    Returns the row-major 3x3 rotation matrix defining a rotation around axis by
    angle.
    """
    cosTheta = cos(angle)
    sinTheta = sin(angle)
    t = 1.0 - cosTheta
    return (
        t * axis[0]**2 + cosTheta,
        t * axis[0] * axis[1] - sinTheta * axis[2],
        t * axis[0] * axis[2] + sinTheta * axis[1],
        t * axis[0] * axis[1] + sinTheta * axis[2],
        t * axis[1]**2 + cosTheta,
        t * axis[1] * axis[2] - sinTheta * axis[0],
        t * axis[0] * axis[2] - sinTheta * axis[1],
        t * axis[1] * axis[2] + sinTheta * axis[0],
        t * axis[2]**2 + cosTheta)

def makeOpenGLMatrix(r, p):
    """
    Returns an OpenGL compatible (column-major, 4x4 homogeneous) transformation
    matrix from ODE compatible (row-major, 3x3) rotation matrix r and position
    vector p.
    """
    return (
        r[0], r[3], r[6], 0.0,
        r[1], r[4], r[7], 0.0,
        r[2], r[5], r[8], 0.0,
        p[0], p[1], p[2], 1.0)

def form_rotation(rot_deg):
    """ Form the rotation matrix for ode to apply to a body.

    Arguments:
    @param rot_deg: list of rotations(roll,pitch,yaw) to apply to the body (x,y,z)
        also (gamma,beta,alpha)
    @type rot_deg: float
    """

    x = rot_deg[0] * ANG_TO_RAD
    y = rot_deg[1] * ANG_TO_RAD
    z = rot_deg[2] * ANG_TO_RAD

    r = [0 for i in range(9)]

    r[0] = cos(z)*cos(y)
    r[1] = sin(z)
    r[2] = -sin(y)
    r[3] = -sin(z)
    r[4] = cos(z)*cos(x)
    r[5] = sin(x)
    r[6] = sin(y)
    r[7] = -sin(x)
    r[8] = cos(y)*cos(x)

    alpha = rot_deg[2]*ANG_TO_RAD
    beta  = rot_deg[1]*ANG_TO_RAD
    gamma = rot_deg[0]*ANG_TO_RAD
    
    rot = [0 for i in range(9)]
    rot[0] = cos(alpha)*cos(beta)
    rot[1] = cos(alpha)*sin(gamma)-sin(alpha)*cos(gamma)
    rot[2] = cos(alpha)*sin(beta)*cos(gamma)+sin(alpha)*sin(gamma)
    rot[3] = sin(alpha)*cos(beta)
    rot[4] = sin(alpha)*sin(beta)*sin(gamma)+cos(alpha)*cos(gamma)
    rot[5] = sin(alpha)*sin(beta)*cos(gamma)-cos(alpha)*sin(gamma)
    rot[6] = -sin(beta)
    rot[7] = cos(beta)*sin(gamma)
    rot[8] = cos(beta)*cos(gamma)

    return r

def QMultiply0(qa,qb):
    """ Multiply two quaternions together.

    Derived from the ODE dQMultiply0 method.

    Args:
        qa: quaternion 1
        qb: quaternion 2
    Returns
        new quaternion based on qa*qb
    """
    qc = []
    qc.append(qa[0]*qb[0] - qa[1]*qb[1] - qa[2]*qb[2] - qa[3]*qb[3])
    qc.append(qa[0]*qb[1] + qa[1]*qb[0] + qa[2]*qb[3] - qa[3]*qb[2])
    qc.append(qa[0]*qb[2] + qa[2]*qb[0] + qa[3]*qb[1] - qa[1]*qb[3])
    qc.append(qa[0]*qb[3] + qa[3]*qb[0] + qa[1]*qb[2] - qa[2]*qb[1])
    return qc

def QFromR(rot):
    """ Create a quaternion from the given rotation matrix.

    Adapated from the ODE dQFromR method.

    Args:
        rot: rotation matrix to adapt to quaternion
    Returns:
        quaternion of the rotation matrix
    """
    q = [0 for i in xrange(4)]
    
    tr = rot[0*3 + 0] + rot[1*3 + 1] + rot[2*3 + 2]
    if tr >= 0:
        s = sqrt(tr+1.)
        q[0] = 0.5 * s
        s = 0.5 * (1./s)
        q[1] = (rot[2*3+1] - rot[1*3+2]) * s
        q[2] = (rot[0*3+2] - rot[2*3+0]) * s
        q[3] = (rot[1*3+0] - rot[0*3+1]) * s
    else:
        case = 0
        if rot[1*3+1] > rot[0*3+0]:
            if rot[2*3+2] > rot[1*3+1]:
                case = 2
            else:
                case = 1
        elif rot[2*3+2] > rot[0*3+0]:
            case = 2

        if case == 0:
            s = sqrt((rot[0*3+0] - (rot[1*3+1] + rot[2*3+2])) + 1.)
            q[1] = 0.5 * s
            s = 0.5 * (1./s)
            q[2] = (rot[0*3+1] + rot[1*3+0]) * s
            q[3] = (rot[2*3+0] + rot[0*3+2]) * s
            q[0] = (rot[2*3+1] - rot[1*3+2]) * s
        elif case == 1:
            s = sqrt((rot[1*3+1] - (rot[2*3+2] + rot[0*3+0])) + 1.)
            q[2] = 0.5 * s
            s = 0.5 * (1./s)
            q[3] = (rot[1*3+2] + rot[2*3+1]) * s
            q[1] = (rot[0*3+1] + rot[1*3+0]) * s
            q[0] = (rot[0*3+2] - rot[2*3+0]) * s
        elif case == 2:
            s = sqrt((rot[2*3+2] - (rot[0*3+0] + rot[1*3+1])) + 1.)
            q[3] = 0.5 * s
            s = 0.5 * (1./s)
            q[1] = (rot[2*3+0] + rot[0*3+2]) * s
            q[2] = (rot[1*3+2] + rot[2*3+1]) * s
            q[0] = (rot[1*3+0] - rot[0*3+1]) * s
    return q

def RFromQ(q):
    """ Create a rotation matrix from a quaternion.

    Adapted from the ODE dRFromQ method.

    Args:
        q: quaternion
    Returns:
        rotation matrix in 3x3 form.
    """
    qq1 = 2.*q[1]*q[1]
    qq2 = 2.*q[2]*q[2]
    qq3 = 2.*q[3]*q[3]
    rot = []
    rot.append(1. - qq2 - qq3)
    rot.append(2.*(q[1]*q[2] - q[0]*q[3]))
    rot.append(2.*(q[1]*q[3] + q[0]*q[2]))
    rot.append(2.*(q[1]*q[2] + q[0]*q[3]))
    rot.append(1. - qq1 - qq3)
    rot.append(2.*(q[2]*q[3] - q[0]*q[2]))
    rot.append(2.*(q[1]*q[3] - q[0]*q[2]))
    rot.append(2.*(q[2]*q[3] + q[0]*q[1]))
    rot.append(1. - qq1 - qq2)
    return rot

def GetRotationRad(rot_quat):
    """ Retrieve the rotation information for the main body of the robot.

        Solution adapted from: http://stackoverflow.com/a/1031235/480685

        Args:
            rot_quat: rotation quaternion of the body to get rotations for.
    """
    
    mnasa = [0.,0.,0.]
    
    q0 = rot_quat[0] # W
    q1 = rot_quat[1] # X
    q2 = rot_quat[2] # Y
    q3 = rot_quat[3] # Z
    
    w2 = q0*q0
    x2 = q1*q1
    y2 = q2*q2
    z2 = q3*q3
    unitLength = w2 + x2 + y2 + z2
    abcd = q0*q1 + q2*q3
    eps = 1e-7
    if (abcd > (0.5-eps)*unitLength):
        mnasa[2] = -2. * atan2(q2, q0)
        mnasa[1] = pi
        mnasa[0] = 0.
    elif (abcd < (-0.5+eps)*unitLength):
        mnasa[2] = 2. * atan2(q2, q0)
        mnasa[1] = -pi
        mnasa[0] = 0.
    else:
        adbc = q0*q3 - q1*q2
        acbd = q0*q2 - q1*q3
        mnasa[2] = -atan2(2.*adbc, 1. - 2.*(z2+x2))
        mnasa[1] = asin(2.*abcd/unitLength)
        mnasa[0] = atan2(2.*acbd, 1. - 2.*(y2+x2))
    
    #std::cout << mnasa.at(0)*RAD_TO_ANG << "\t" << mnasa.at(1)*RAD_TO_ANG << "\t" << mnasa.at(2)*RAD_TO_ANG << std::endl;
    
    return mnasa
