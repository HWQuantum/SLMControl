import matplotlib.pyplot as plt
import numpy as np
import pickle
from scipy.optimize import minimize

with open("./2x2_correct_values", 'rb') as f:
    d = pickle.load(f)


def get_coincidences(o):
    '''Get coincidences from an element of the data
    '''
    return o[0][3][3]


keys = [k for k in d.keys() if k[0] == 'angle_a_b']
angles_a = sorted(list(set([k[1] for k in keys])))
angles_b = sorted(list(set([k[2] for k in keys])))

data = [[get_coincidences(d[('angle_a_b', a, b)]) for b in angles_b]
        for a in angles_a]


def closest_index(x, v):
    '''Gets the index of the value in v closes to x
    '''
    if x > 2 * np.pi:
        return min([(i, y) for i, y in enumerate(v)],
                   key=lambda a: abs(a[1] - x + (2 * np.pi)))[0]
    else:
        return min([(i, y) for i, y in enumerate(v)],
                   key=lambda a: abs(a[1] - x))[0]


def normalisation(a, b):
    '''Get the normalisation factor for angles a, b
    This is:
    C(A,B)+C(A+pi/2,B+pi/2)+C(A+pi/2,B)+C(A,B+pi/2)
    '''
    total = 0
    for x in [0, np.pi / 2]:
        for y in [0, np.pi / 2]:
            total += data[closest_index(a + x, angles_a)][closest_index(
                b + y, angles_b)]

    return total


def E(a, b):
    '''Get the normalisation factor for angles a, b
    This is:
    (C(A,B)+C(A+pi/2,B+pi/2)-C(A+pi/2,B)-C(A,B+pi/2))/normalisation
    '''
    total = 0
    for s_x, x in [(1, 0), (-1, np.pi / 2)]:
        for s_y, y in [(1, 0), (-1, np.pi / 2)]:
            total += s_x * s_y * data[closest_index(
                a + x, angles_a)][closest_index(b + y, angles_b)]

    return total / normalisation(a, b)


def S(a, ad):
    '''The bell parameter defined for a, b, a', b'
    '''
    return (E(a, a + np.pi / 8) - E(a, ad + np.pi / 8) + E(ad, a + np.pi / 8) +
            E(ad, ad + np.pi / 8))

s_vec = np.vectorize(S)

# for i, f in enumerate(data):
#     plt.plot(angles_b, f)
# plt.show()

new_data = [[
    r / normalisation(angles_a[i], angles_b[j]) for j, r in enumerate(p)
] for i, p in enumerate(data)]

# for f in new_data:
#     plt.plot(angles_b, f)
# plt.show()
x, y = np.mgrid[0:(2 * np.pi):50j, 0:(2 * np.pi):50j]
vals = s_vec(x, y)

plt.matshow(vals)
plt.show()
