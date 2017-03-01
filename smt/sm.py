"""
Author: Dr. Mohamed Amine Bouhlel <mbouhlel@umich.edu>
        Dr. John T. Hwang         <hwangjt@umich.edu>

Metamodels - a base class for metamodel methods
"""
#TODO: Extend to multifidelity problems by adding training_pts = {'approx': {}}

from __future__ import division

import numpy as np

from smt.utils.printer import Printer


class SM(object):
    '''
    Base class for all model methods.
    '''

    def __init__(self, sm_options=None, printf_options=None):
        '''
        Constructor.

        Arguments
        ---------
        sm_options : dict
            Model-related options, in _default_options in the inheriting class

        printf_options : dict
            Output printing options
        '''
        #Initialization
        self._set_default_options()
        if sm_options is not None:
            self.sm_options.update(sm_options)
        if printf_options is not None:
            self.printf_options.update(printf_options)

        self.training_pts = {'exact': {}}

        self.printer = Printer()

    def compute_rms_error(self, xe=None, ye=None, kx=None):
        '''
        Returns the RMS error of the training points or the given points.

        Arguments
        ---------
        xe : np.ndarray[ne, dim] or None
            Input values. If None, the input values at the training points are used instead.
        ye : np.ndarray[ne, 1] or None
            Output / deriv. values. If None, the training pt. outputs / derivs. are used.
        kx : int or None
            If None, we are checking the output values.
            If int, we are checking the derivs. w.r.t. the kx^{th} input variable (0-based).
        '''
        if xe is not None and ye is not None:
            ye2 = self.predict(xe, kx)
            return np.linalg.norm(ye2 - ye) / np.linalg.norm(ye)
        elif xe is None and ye is None:
            num = 0.
            den = 0.
            if kx is None:
                kx2 = 0
            else:
                kx2 += 1
            if kx2 not in self.training_pts['exact']:
                raise ValueError('There is no training point data available for kx %s' % kx2)
            xt, yt = self.training_pts['exact'][kx2]
            yt2 = self.predict(xt, kx)
            num += np.linalg.norm(yt2 - yt) ** 2
            den += np.linalg.norm(yt) ** 2
            return num ** 0.5 / den ** 0.5

    def add_training_pts(self, typ, xt, yt, kx=None):
        '''
        Adds nt training/sample data points

        Arguments
        ---------
        typ : str
            'exact'  if this data are considered as a high-fidelty data
            'approx' if this data are considered as a low-fidelity data (TODO)
        xt : np.ndarray [nt, dim]
            Training point input variable values
        yt : np.ndarray [nt, 1]
            Training point output variable values or derivatives (a vector)
        kx : int or None
            None if this data set represents output variable values
            int  if this data set represents derivatives
                 where it is differentiated w.r.t. the kx^{th}
                 input variable (kx is 0-based)
        '''
        yt = yt.reshape((xt.shape[0],1))
        #Output or derivative variables
        if kx is None:
            kx = 0
            self.dim = xt.shape[1]
            self.nt = xt.shape[0]
        else:
            kx = kx + 1

        #Construct the input data
        pts = self.training_pts[typ]
        if kx in pts:
            pts[kx][0] = np.vstack([pts[kx][0], xt])
            pts[kx][1] = np.vstack([pts[kx][1], yt])
        else:
            pts[kx] = [np.array(xt), np.array(yt)]

    def train(self):
        '''
        Train the model
        '''
        n_exact = self.training_pts['exact'][0][0].shape[0]

        self.printer.active = self.printf_options['global']
        self.printer._line_break()
        self.printer._center(self.sm_options['name'])

        self.printer.active = self.printf_options['global'] and self.printf_options['problem']
        self.printer._title('Problem size')
        self.printer('   %-25s : %i' % ('# training pts.', n_exact))
        self.printer()

        self.printer.active = self.printf_options['global'] and self.printf_options['time_train']
        if self.sm_options['name'] == 'MixExp':
            # Mixture of experts model
            self.printer._title('Training of the Mixture of experts')
        else:
            self.printer._title('Training')

        # Train the model using the specified model-method
        with self.printer._timed_context('Training'):
            self.fit()

    def predict(self, x, kx=None):
        '''
        Evaluates the model at a set of unknown points

        Arguments
        ---------
        x : np.ndarray [n_evals, dim]
            Evaluation point input variable values
        kx : int or None
            None if evaluation of the interpolant is desired.
            int  if evaluation of derivatives of the interpolant is desired
                 with respect to the kx^{th} input variable (kx is 0-based).

        Returns
        -------
        y : np.ndarray
            Evaluation point output variable values
        '''
        n_evals = x.shape[0]

        self.printer.active = self.printf_options['global'] and self.printf_options['time_eval']

        if self.sm_options['name'] == 'MixExp':
            # Mixture of experts model
            self.printer._title('Evaluation of the Mixture of experts')
        else:
            self.printer._title('Evaluation')
        self.printer('   %-12s : %i' % ('# eval pts.', n_evals))
        self.printer()

        #Output or derivative variables
        if kx is None:
            kx = 0
        else:
            kx = kx + 1

        #Evaluate the unknown points using the specified model-method
        with self.printer._timed_context('Predicting', key='prediction'):
            y = self.evaluate(x, kx)

        time_pt = self.printer._time('prediction') / n_evals
        self.printer()
        self.printer('Prediction time/pt. (sec) : %10.7f' %  time_pt)
        self.printer()

        return y.reshape(n_evals,1)
