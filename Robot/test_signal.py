import matplotlib.pyplot as plt
from temp_signal import TSignal

for i in xrange(1):
    x = []
    y = []
    for j in xrange(1000):
        x.append(j)
        y.append(sig.next())

    plt.figure(1)
    plt.plot(x,y)

    plt.ylabel("Signal")
    plt.xlabel("Step")
    plt.ylim([-1.0,1.0])
    plt.show()

    sig.mutate()
