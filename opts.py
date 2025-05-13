


UNITS = ['2theta [degrees]',
         '2theta [radians]',
         'q space [1/nm]',
         'q space [1/A]',
         'd-spacing [nm]',
         'd-spacing [A]',
         ]

PLOTOPTIONS = {'xaxis': '2Theta',
               'xlabel': '2Theta (degrees)',
                'yaxis': 'Intensity',
                'ylabel': 'Intensity (a.u.)',
                'title': 'XRD Pattern',
                'peak_shape': 'lorentzian',
                'peak_width': 0.01,
                'npoints': 5000,
                'xrange': (0, 20),
                'yrange': (-2, 2),
                'offset': 1e-3,
                'autoscale': False,

                }

CROSSHAIR_OPTIONS = {'color': 'm',
                    }



PENS = ['r', 'g', 'c', 'y', 'm', 'b', 'k']