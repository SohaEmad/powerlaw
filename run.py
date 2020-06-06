from matplotlib.pyplot import figure
from numpy import genfromtxt

import powerlaw
from matplotlib.pyplot import figure
from numpy import genfromtxt

import powerlaw

print(powerlaw.__version__)

# %pylab inline

import pylab
pylab.rcParams['xtick.major.pad']='8'
pylab.rcParams['ytick.major.pad']='8'
#pylab.rcParams['font.sans-serif']='Arial'

from matplotlib import rc
rc('font', family='sans-serif')
rc('font', size=10.0)
rc('text', usetex=False)


from matplotlib.font_manager import FontProperties

panel_label_font = FontProperties().copy()
panel_label_font.set_weight("bold")
panel_label_font.set_size(12.0)
panel_label_font.set_family("sans-serif")

data = genfromtxt('testing/reference_data/blackouts.txt') # data can be list or numpy array
results = powerlaw.Fit(data)
print(results.power_law.alpha)
print(results.power_law.xmin)
R, p = results.distribution_compare('power_law', 'lognormal')
# plot(data)



# from os import listdir
# files = listdir('.')
# if 'blackouts.txt' not in files:
#     import urllib.request
#     urllib.request.urlretrieve('https://raw.github.com/jeffalstott/powerlaw/master/manuscript/blackouts.txt')
# if 'words.txt' not in files:
#     import urllib
#     urllib.request.urlretrieve('https://raw.github.com/jeffalstott/powerlaw/master/manuscript/words.txt', 'words.txt')
# if 'worm.txt' not in files:
#     import urllib
#     urllib.request.urlretrieve('https://raw.github.com/jeffalstott/powerlaw/master/manuscript/worm.txt', 'worm.txt')

from numpy import genfromtxt
blackouts = genfromtxt('testing/reference_data/blackouts.txt')#/10**3
words = genfromtxt('testing/reference_data/words.txt')
# worm = genfromtxt('reference_data/worm.txt')
# worm = worm[worm>0]

def plot_basics(data, data_inst, fig, units):
    from powerlaw import plot_pdf, Fit, pdf
    annotate_coord = (-.4, .95)
    ax1 = fig.add_subplot(n_graphs, n_data, data_inst)
    x, y = pdf(data, linear_bins=True)
    ind = y > 0
    y = y[ind]
    x = x[:-1]
    x = x[ind]
    ax1.scatter(x, y, color='r', s=.5)
    plot_pdf(data[data > 0], ax=ax1, color='b', linewidth=2)
    from pylab import setp
    setp(ax1.get_xticklabels(), visible=False)

    if data_inst == 1:
        ax1.annotate("A", annotate_coord, xycoords="axes fraction", fontproperties=panel_label_font)

    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    ax1in = inset_axes(ax1, width="30%", height="30%", loc=3)
    # ax1in.hist(data, normed=True, color='b')
    ax1in.set_xticks([])
    ax1in.set_yticks([])

    ax2 = fig.add_subplot(n_graphs, n_data, n_data + data_inst, sharex=ax1)
    plot_pdf(data, ax=ax2, color='b', linewidth=2)
    fit = Fit(data, xmin=1, discrete=True)
    fit.power_law.plot_pdf(ax=ax2, linestyle=':', color='g')
    p = fit.power_law.pdf()

    ax2.set_xlim(ax1.get_xlim())

    fit = Fit(data, discrete=True)
    fit.power_law.plot_pdf(ax=ax2, linestyle='--', color='g')
    from pylab import setp
    setp(ax2.get_xticklabels(), visible=False)

    if data_inst == 1:
        ax2.annotate("B", annotate_coord, xycoords="axes fraction", fontproperties=panel_label_font)
        ax2.set_ylabel(u"p(X)")  # (10^n)")

    ax3 = fig.add_subplot(n_graphs, n_data, n_data * 2 + data_inst)  # , sharex=ax1)#, sharey=ax2)
    fit.power_law.plot_pdf(ax=ax3, linestyle='--', color='g')
    fit.exponential.plot_pdf(ax=ax3, linestyle='--', color='r')
    fit.plot_pdf(ax=ax3, color='b', linewidth=2)

    ax3.set_ylim(ax2.get_ylim())
    ax3.set_xlim(ax1.get_xlim())

    if data_inst == 1:
        ax3.annotate("C", annotate_coord, xycoords="axes fraction", fontproperties=panel_label_font)

    ax3.set_xlabel(units)

n_data = 3
n_graphs = 4
f = figure(figsize=(8,11))

# data = words
# data_inst = 1
# units = 'Word Frequency'
# plot_basics(data, data_inst, f, units)

# data_inst = 2
#data = city
#units = 'City Population'
# data = worm
# units = 'Neuron Connections'
# plot_basics(data, data_inst, f, units)

data = blackouts
data_inst = 3
units = 'Population Affected\nby Blackouts'
plot_basics(data, data_inst, f, units)

f.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=.3, hspace=.2)
figname = 'dataOut'
f.savefig(figname+'.eps', bbox_inches='tight')
#f.savefig(figname+'.tiff', bbox_inches='tight', dpi=300)