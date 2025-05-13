import numpy as np

def gaussian(x:np.ndarray, x0:float=0, sig:float=0.01, amp:float=1) -> np.ndarray:
    """
    Gaussian function.
    Args:
        x (np.ndarray): Input array.
        x0 (float): Center of the Gaussian.
        sig (float): Standard deviation (width) of the Gaussian.
        amp (float): Amplitude of the Gaussian.
    Returns:
        np.ndarray: Gaussian function evaluated at x.
    """
    return (amp / (np.sqrt(2.0 * np.pi) * sig) * np.exp(-np.power((x - x0) / sig, 2.0) / 2))

def lorentzian(x: np.ndarray, x0: float = 0, sig: float = 0.01, amp: float = 1) -> np.ndarray:
    """
    Lorentzian function.
    Args:
        x (np.ndarray): Input array.
        x0 (float): Center of the Lorentzian.
        sig (float): Width (half-width at half-maximum) of the Lorentzian.
        amp (float): Amplitude of the Lorentzian.
    Returns:
        np.ndarray: Lorentzian function evaluated at x.
    """
    return (amp / (np.pi * sig) * (sig**2 / ((x - x0)**2 + sig**2)))

def voigt(x: float, x0: float = 0, sig: float = 0.01, amp: float = 1) -> float:
    """
    Compute the Voigt profile, which is a convolution of a Gaussian and a Lorentzian profile.

    Parameters:
        x (float): The input value at which the Voigt profile is evaluated.
        x0 (float, optional): The center of the profile. Defaults to 0.
        sig (float, optional): The standard deviation of the Gaussian component. Defaults to 0.01.
        amp (float, optional): The amplitude of the profile. Defaults to 1.

    Returns:
        float: The value of the Voigt profile at the given input `x`.
    """
    return (amp / (np.sqrt(2.0 * np.pi) * sig) * np.exp(-np.power((x - x0) / sig, 2.0) / 2)) + \
            (amp / (np.pi * sig) * (sig**2 / ((x - x0)**2 + sig**2)))

def pearson(x: float, x0: float = 0, sig: float = 0.01, amp: float = 1) -> float:
    """
    Compute the Pearson distribution function.

    The Pearson distribution is a type of probability density function 
    often used in statistical modeling and data analysis.

    Parameters:
        x (float): The input value at which to evaluate the function.
        x0 (float, optional): The center of the distribution. Defaults to 0.
        sig (float, optional): The scale parameter (standard deviation). Defaults to 0.01.
        amp (float, optional): The amplitude or scaling factor. Defaults to 1.

    Returns:
        float: The computed value of the Pearson distribution at the given input.
    """
    return (amp / (np.pi * sig) * (sig**2 / ((x - x0)**2 + sig**2)))**(1/2)


def combine_peaks(x:np.ndarray,
                    peak_func:str='voigt',
                    x0:list=None,
                    amp:list=None,
                    sig:float=0.01,
                    offset:float=1e-3,
                    ) -> np.ndarray:
    y = np.full_like(x, offset)
    if peak_func == 'gaussian':
        peak_func = gaussian
    elif peak_func == 'lorentzian':
        peak_func = lorentzian
    elif peak_func == 'voigt':
        peak_func = voigt
    elif peak_func == 'pearson':
        peak_func = pearson
    else:
        raise ValueError("Invalid peak function. Choose 'gaussian', 'lorentzian', 'voigt' or 'pearson'.")
    for cx0,camp in zip(x0, amp):
        y += peak_func(x, x0=cx0, sig=sig, amp=camp)
    return y


def th2d2tw(theta:np.ndarray) -> np.ndarray:
    """
    Convert 2Theta to 2*Theta in radians.
    
    Args:
        theta (np.ndarray): Input array of 2Theta values in degrees.
        
    Returns:
        np.ndarray: Converted array of 2*Theta values in radians.
    """
    return np.radians(theta) * 2