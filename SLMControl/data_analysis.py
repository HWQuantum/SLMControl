import matplotlib.pyplot as plt
import numpy as np
import pickle
from scipy.optimize import minimize, curve_fit


def plot_data(filename, axis):
    with open(filename, 'rb') as f:
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
    data = [data[-i] for i in range(len(data))]
    # indices for a
    i_a = [0, 1, 2, 3]
    # indices for b
    i_b = [13, 38, 63, 88]
    # E(A, B) = (C(A, B) + C(A+pi, B+pi) - C(A+pi, B) - C(A, B+pi))/
    # (sum of above with no minuses)
    E1 = ((data[0][13] + data[2][63] - data[2][13] - data[0][63]) /
          (data[0][13] + data[2][63] + data[2][13] + data[0][63]))
    E2 = ((data[0][38] + data[2][88] - data[2][38] - data[0][88]) /
          (data[0][38] + data[2][88] + data[2][38] + data[0][88]))
    E3 = ((data[1][13] + data[3][63] - data[3][13] - data[1][63]) /
          (data[1][13] + data[3][63] + data[3][13] + data[1][63]))
    E4 = ((data[1][38] + data[3][88] - data[3][38] - data[1][88]) /
          (data[1][38] + data[3][88] + data[3][38] + data[1][88]))
    print(E1, E2, E3, E4)
    s = abs(E1) + abs(E2) + abs(E3) + abs(E4)
    print(s)
    print((data[0][13] + data[2][63] - data[2][13] - data[0][63]) /
          (data[0][13] + data[2][63] + data[2][13] + data[0][63])  #E(A, B)
          )
    print(
        (data[0][38] + data[2][88] - data[2][38] - data[0][88]) /
        (data[0][38] + data[2][88] + data[2][38] + data[0][88]))  # - E(A, Bd)

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
        return (E(a, a + np.pi / 8) - E(a, ad + np.pi / 8) +
                E(ad, a + np.pi / 8) + E(ad, ad + np.pi / 8))

    s_vec = np.vectorize(S)

    # for i, f in enumerate(data):
    #     plt.plot(angles_b, f)
    # plt.show()

    # / normalisation(angles_a[i], angles_b[j])
    normalisation_2 = []
    for i in range(len(data[0])):
        p = 0
        for j in range(4):
            p += data[j][i]
        normalisation_2.append(p)

    new_data = [[r / normalisation_2[j] for j, r in enumerate(p)]
                for i, p in enumerate(data)]

    fitted_sins = []

    for f in data[:4]:
        axis.plot(angles_b, f)
        fit = curve_fit(lambda x, a, b, c, d: a * np.sin(b * x + c) + d,
                        angles_b,
                        f,
                        p0=[700, 0, 0, 0])[0]
        # def new_sin(x):
        #     return fit[0]*np.sin(fit[1]*x+fit[2])+fit[3]
        print(fit)
        fitted_sins.append((lambda fit: lambda x: fit[0] * np.sin(fit[
            1] * x + fit[2]) + fit[3])(fit))

    return fitted_sins


fig, axs = plt.subplots(1, 1)
sins = plot_data("./2x2_bell_waaay_better", axs)
# plt.show()


def normalisation(a, b):
    '''Get the normalisation factor for angles a, b
    This is:
    C(A,B)+C(A+pi/2,B+pi/2)+C(A+pi/2,B)+C(A,B+pi/2)
    a should be an index of [0, 1, 2, 3]
    '''
    total = 0
    for x in [0, 1]:
        for y in [0, np.pi / 2]:
            total += sins[(a + x) % 4](b + y)
    return total


def E(a, b):
    '''Get the normalisation factor for angles a, b
    This is:
    (C(A,B)+C(A+pi/2,B+pi/2)-C(A+pi/2,B)-C(A,B+pi/2))/normalisation
    a should be in [0, 1, 2, 3]
    '''
    total = 0
    for x, y, s in [(0, 0, 1), (0, np.pi, -1), (2, 0, -1), (2, np.pi, 1)]:
        total += s * sins[(a + x) % 4](b + y)

    return total / normalisation(a, b)


def S(a, ad, b, bd):
    '''The bell parameter defined for a, b, a', b'
    a and ad should be in [0, 1, 2, 3]
    '''
    return (E(a, b) - E(a, bd) + E(ad, b) + E(ad, bd))


s_vec = np.vectorize(S)


def curry_s(a, ad):
    return lambda p: -s_vec(a, ad, p[0], p[1])


# fig, axs = plt.subplots(4, 4)
# maxs = []

# for a, ax_a in enumerate(axs):
#     for ad, ax in enumerate(ax_a):
#         # maxs.append(
#         #     minimize(curry_s(a, ad), [0, 0],
#         #              bounds=[(0, 2 * np.pi)] * 2)['fun'])
#         x, y = np.mgrid[0:(2 * np.pi):20j, 0:(2 * np.pi):20j]
#         ax.imshow(s_vec(a, ad, x, y))
# plt.show()

# for s in sins:
#     x = np.linspace(0, 2 * np.pi, 100)
#     plt.plot(x, s(x))
# plt.legend(['s1', 's2', 's3', 's4'])
# plt.show()
vb = np.pi / 4
vbd = 3 * np.pi / 4

E1 = (sins[0](vb) + sins[2](vb + np.pi) - sins[2](vb) -
      sins[0](vb + np.pi)) / (sins[0](vb) + sins[2](vb + np.pi) + sins[2](vb) +
                              sins[0](vb + np.pi))

E2 = ((sins[0](vbd) + sins[2](vbd + np.pi) - sins[2](vbd) -
       sins[0](vbd + np.pi)) / (sins[0](vbd) + sins[2](vbd + np.pi) +
                                sins[2](vbd) + sins[0](vbd + np.pi)))

E3 = (sins[1](vb) + sins[3](vb + np.pi) - sins[3](vb) -
      sins[1](vb + np.pi)) / (sins[1](vb) + sins[3](vb + np.pi) + sins[3](vb) +
                              sins[1](vb + np.pi))

E4 = ((sins[1](vbd) + sins[3](vbd + np.pi) - sins[3](vbd) -
       sins[1](vbd + np.pi)) / (sins[1](vbd) + sins[3](vbd + np.pi) +
                                sins[3](vbd) + sins[1](vbd + np.pi)))

print(E1, E2, E3, E4)
print(E1 - E2 + E3 + E4)
