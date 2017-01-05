import stellarTwins as st
from extreme_deconvolution import extreme_deconvolution as ed
import astropy.units as units
import numpy as np
import pdb
import matplotlib.pyplot as plt
import time
from sklearn.model_selection import train_test_split

from xdgmm import XDGMM
from sklearn.learning_curve import validation_curve
from sklearn.model_selection import ShuffleSplit
import demo_plots


def XD(data_1, err_1, data_2, err_2, ngauss=2, mean_guess=np.array([[0.5, 6.], [1., 4.]]), w=0.0):

    amp_guess = np.zeros(ngauss) + 1.
    ndim = 2
    X = np.vstack([data_1, data_2]).T
    Xerr = np.zeros(X.shape + X.shape[-1:])
    diag = np.arange(X.shape[-1])
    Xerr[:,diag,diag] = np.vstack([err_1**2., err_2**2.]).T

    cov_guess = np.zeros(((ngauss,) + X.shape[-1:] + X.shape[-1:]))
    cov_guess[:,diag,diag] = 1.0 #np.random.rand(ndim, ngauss)
    #pdb.set_trace()
    ed(X, Xerr, amp_guess, mean_guess, cov_guess, w=w)

    return amp_guess, mean_guess, cov_guess

if __name__ == '__main__':
    b_v_lim = [0.25, 1.5]
    g_r_lim = None #[0, 1.5]

    r_i_lim = None #[-0.25, 0.75]
    M_v_lim = None #[10, 2]

    teff_lim = [7, 4] #kKd
    log_g_lim = [6, 3]
    feh_lim = [-1.5, 1]

    maxlogg = 20
    minlogg = 1
    mintemp = 100
    SNthreshold = 4
    filename = 'cutMatchedArrays.' + str(minlogg) + '_' + str(maxlogg) + '_' + str(mintemp) + '_' + str(SNthreshold) + '.npz'

    try:
        cutMatchedArrays = np.load(filename)
        tgasCutMatched = cutMatchedArrays['tgasCutMatched']
        apassCutMatched = cutMatchedArrays['apassCutMatched']
        raveCutMatched = cutMatchedArrays['raveCutMatched']
        twoMassCutMatched = cutMatchedArrays['twoMassCutMatched']
        wiseCutMatched = cutMatchedArrays['wiseCutMatched']
        distCutMatched = cutMatchedArrays['distCutMatched']
    except IOError:
        tgasCutMatched, apassCutMatched, raveCutMatched, twoMassCutMatched, wiseCutMatched, distCutMatched = st.observationsCutMatched(maxlogg=maxlogg, minlogg=minlogg, mintemp=mintemp, SNthreshold=SNthreshold, filename=filename)
    print 'Number of Matched stars is: ', len(tgasCutMatched)

    B_RedCoeff = 3.626
    V_RedCoeff = 2.742
    g_RedCoeff = 3.303
    r_RedCoeff = 2.285
    i_RedCoeff = 1.698
    bayesDust = st.dust(tgasCutMatched['l']*units.deg, tgasCutMatched['b']*units.deg, np.median(distCutMatched, axis=1)*units.pc)
    #M_V = apassCutMatched['vmag'] - V_RedCoeff*bayesDust - meanMuMatched
    g_r = apassCutMatched['gmag'] - g_RedCoeff*bayesDust - (apassCutMatched['rmag'] - r_RedCoeff*bayesDust)
    r_i = apassCutMatched['rmag'] - r_RedCoeff*bayesDust - (apassCutMatched['imag'] - i_RedCoeff*bayesDust)

    B_V = apassCutMatched['bmag'] - B_RedCoeff*bayesDust - (apassCutMatched['vmag'] - V_RedCoeff*bayesDust)
    B_V_err = np.sqrt(apassCutMatched['e_bmag']**2. + apassCutMatched['e_vmag']**2.)

    temp = raveCutMatched['TEFF']/1000.
    temp_err = raveCutMatched['E_TEFF']/1000.

    absMagKinda = tgasCutMatched['parallax']*1e-3*10.**(0.2*tgasCutMatched['phot_g_mean_mag'])
    absMagKinda_err = np.sqrt(tgasCutMatched['parallax_error']**2. + 0.3**2.)*1e-3*10.**(0.2*tgasCutMatched['phot_g_mean_mag'])
    #print absMagKinda_err
    #plt.scatter(B_V, absMagKinda, alpha=0.1, lw=0)
    #plt.show()
    data1 = [B_V, B_V]
    data2 = [temp, absMagKinda]
    err1 = [B_V_err, B_V_err]
    err2 = [temp_err, absMagKinda_err]
    xlabel = ['B-V', 'B-V']
    ylabel = ['Teff [kK]', r'$\varpi 10^{0.2*m_G}$']
    ngauss = 32
     #[np.array([[0.5, 6.], [1., 4.]]), np.array([[0.5, 1.], [1., 2.]])]

    fig, axes = plt.subplots(1, figsize=(7,7))
    #fig, axes = plt.subplots(1, 2, figsize=(12,5))
    for j, ax in enumerate(axes):
        X = np.vstack([data1, data2]).T
        Xerr = np.zeros(X.shape, X.shape[-1:])
        diag = np.arange(X.shape[-1])
        Xerr[:, diag, diag] = np.vstack([err1**2., err2**2.]).T
        xdgmm = XDGMM(method='Bovy')
        param_range(np.array([1, 2, 4, 8, 16]))
        shuffle_split = ShuffleSplit(n_splits=len(X), test_size=0.3)
        train_scores, test_scores = validation_curve(xdgmm, X=X, y=Xerr, param_name='n_components', param_range=param_range, n_jobs=3, cv=shuffle_split, verbose=1)
        np.savez('xdgmm_scores.npz', train_scores=train_scores, test_scores=test_scores)
        train_scores_mean = np.mean(train_scores, axis=1)
        train_scores_std  = np.std(train_scores, axis=1)
        test_scores_mean = np.mean(test_scores, axis=1)
        test_scores_std = np.std(test_scores, axis=1)
        plot_val_curve(param_range, train_scores_mean, train_scores_std, test_scores_mean, test_scores_std)
        import pdb;pdb.set_trace()


        mean_guess = np.random.rand(ngauss,2)*10.
        X_train, X_test, y_train, y_test, xerr_train, xerr_test, yerr_train, yerr_test = train_test_split(data1[j], data2[j], err1[j], err2[j], test_size=0.4, random_state=0)

        start = time.time()
        amp, mean, cov = XD(data1[j], err1[j], data2[j], err2[j], ngauss=ngauss, mean_guess=mean_guess, w=0.001)
        end = time.time()
        #print np.shape(amp), np.shape(mean), np.shape(cov)
        print 'Time to run XD: ', end - start
        print 'Amplitudes are :', amp
        print 'Means are: ', mean
        print 'Covariances are: ', cov

        ax.scatter(data1[j], data2[j], alpha=0.1, lw=0)
        ax.errorbar(data1[j], data2[j], xerr=err1[j], yerr=err2[j], fmt="none", ecolor='black', zorder=0, lw=0.5, mew=0, alpha=0.1)
        for scale, alpha in zip([1, 2], [1.0, 0.5]):
            for i in range(ngauss):
                st.draw_ellipse(mean[i][0:2], cov[i][0:2], scales=[scale], ax=ax,
                     ec='k', fc="None", alpha=alpha*amp[i]/np.max(amp), zorder=99, lw=2)
        ax.set_xlabel(xlabel[j])
        ax.set_ylabel(ylabel[j])
    ax.set_title('eXtreme Deconvolution')
    fig.savefig('testXD_' + str(ngauss) + '.png')
    plt.tight_layout()
    plt.show()
