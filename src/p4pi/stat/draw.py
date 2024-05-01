import os
import matplotlib as mpl
if os.environ.get('DISPLAY','') == '':
    print('no display found. Using non-interactive Agg backend')
    mpl.use('Agg')

from matplotlib import pyplot as plt

import math 
import numpy as np
import csv, sys
import matplotlib
from matplotlib.lines import Line2D

CONF = [{
        "label": "without ML inference",
        "line-style": "-",
        "line-color": "red",
        "csv-file-name-format": "latency-overhead-{0}-pkt-no-ml.csv"
    }, {
        "label": "with ML inference",
        "line-style": "-.",
        "line-color": "blue",
        "csv-file-name-format": "latency-overhead-{0}-pkt-with-ml.csv"
    }
]

pkt_size = [10000]

def load_data( file_name ):
    print( file_name )
    with open( file_name, 'r' ) as input_file:
        csv_reader = csv.reader(input_file)
        rows = [row for row in csv_reader]
        #exclude the first and the last rows (header and result)
        rows = rows[1:-1]
        result = [ int(row[3]) for row in rows ]
        return result;

result = {}

for i in CONF:
    i["data"] = []
    val = [];
    for pkt in pkt_size:
        data = load_data( i["csv-file-name-format"].format( pkt ) )
        val += data
        
    val = np.array( val )
    print( np.average( val ) )
    i["data"].append( val ) 


plt.rcParams['axes.xmargin'] = 0.2
plt.rcParams["figure.figsize"] = (8,5)
plt.tight_layout()



fig, ax = plt.subplots()

#plot_cdf(ax, data_a, label=l[0], color='r', linewidth=1)
#plot_cdf(ax, data_b, label=l[1], color='b', linewidth=1)

for i in CONF:
    ax.hist( i["data"], histtype='step', bins=2000, density=True, cumulative=True, label=i["label"], linewidth=2, color=i["line-color"], linestyle=i["line-style"])


ax.set_xlim(10000, 50000)
ax.set_ylim(0, 1)
ax.set_ylabel("Distribution (%)")
ax.set_xlabel( "RTT  ($\mu$s)", fontsize=14 )
ax.grid()

# modify the last x label
#a=ax.get_xticks().tolist()
#a = [int(v) for v in a]
#a[-1]= '{0} ($\mu$s)'.format( a[-1] )
#ax.set_xticklabels(a)
ax.set_yticklabels( [0, 20, 40, 60, 80, 100] )

#ax.legend()
# Create new legend handles but use the colors from the existing ones
handles, labels = ax.get_legend_handles_labels()
new_handles = [Line2D([], [], c=h.get_edgecolor(), linestyle=h.get_linestyle()) for h in handles]


plt.legend(handles=new_handles, labels=labels, loc="lower right",)
#plt.legend( labels=labels, loc="lower right",)

plt.savefig( "rtt-with-without-ml-cdf.pdf", dpi=30, format='pdf', bbox_inches='tight')
