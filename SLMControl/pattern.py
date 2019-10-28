import numpy as np
from numba import njit


@njit()
def point_in_slice(x, y, r, R, theta_1, theta_2):
    '''Check if the given point is inside the given pizza slice
    The pizza slice is defined by two angles (theta_1, theta_2),
    which the angle of the point must be inside.
    r gives a limit to the inside of the circle and
    R gives a limit to the outside of the circle
    '''
    theta = (np.arctan2(y, x)) % (np.pi * 2)
    mag = x**2 + y**2
    return (theta_1 <= theta) & (theta < theta_2) & (r**2 < mag) & (mag < R**2)


def pizza_pattern(X,
                  Y,
                  components,
                  circle_inner_radius=0,
                  circle_outer_radius=1,
                  slice_fraction=1,
                  circle_fraction=1):
    """Draw a pizza pattern over X and Y
    
    Keyword arguments:
    circle_inner_radius -- The inner radius that the circle making up the pizza has
    circle_outer_radius -- The outer radius of the circle
    clice_fraction -- The amount of space the individual slices of pizza actually take up
    circle_fraction -- The amount of a whole circle that is filled by the pizza

    returns a complex array with shape X.shape or Y.shape
    """
    dim = len(components)
    rotational_span = 2 * np.pi * circle_fraction
    slice_spacing_rads = rotational_span * (1 - slice_fraction) / (2 * dim)
    lower_angle = np.linspace(0, rotational_span - (rotational_span / dim),
                              dim) + slice_spacing_rads

    upper_angle = np.linspace(rotational_span / dim, rotational_span,
                              dim) - slice_spacing_rads

    field = np.zeros(X.shape, dtype=np.complex128)
    if dim > 1:
        for i, p in enumerate(components):
            field += p * point_in_slice(X, Y, circle_inner_radius,
                                        circle_outer_radius, lower_angle[i],
                                        upper_angle[i])
    else:
        field += components[0] * point_in_slice(
            X, Y, circle_inner_radius, circle_outer_radius, lower_angle[i],
            upper_angle[i])

    return field


def oam_pattern(X, Y, components):
    """Draw an exp(ilθ) pattern over X and Y
    
    returns a complex array with shape X.shape or Y.shape
    """
    dim = len(components)
    ang_mom_limit = (dim - 1) * (1 / 2)

    amplitude = np.abs(components)
    phase = np.angle(components)
    angular_momentum = np.linspace(-ang_mom_limit, ang_mom_limit, dim)
    theta = np.arctan2(Y, X)
    return np.sum([
        amplitude[i] * np.exp(1j * (l * theta + phase[i]))
        for i, l in enumerate(angular_momentum)
    ],
                  axis=0)


def draw_plot():
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 1)
    X, Y = np.mgrid[-1:1:512j, -1:1:512j]
    rot = 2*np.pi
    rotX, rotY = np.cos(rot) * X + np.sin(rot) * Y, -np.sin(rot) * X + np.cos(
        rot) * Y
    p = oam_pattern(rotX, rotY, [1, 1j, 1j, -1])
    ax.imshow(np.angle(p))
    plt.show()
