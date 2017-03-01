"""
Author: Dr. John T. Hwang <hwangjt@umich.edu>
"""
import cPickle as pickle
import hashlib


def _caching_load(filename, checksum):
    """
    Load the saved SM state if the checksum in the file matches the given one.

    Arguments
    ---------
    filename : str
        Name of the file to try to read in.
    checksum : str
        Hexadecimal string checksum to be compared to that found in the file, if any.

    Returns
    -------
    bool
        Whether the load was successful.
    object or None
        The loaded data if successful; otherwise, None.
    """
    try:
        save_pkl = pickle.load(open(filename, 'r'))

        if checksum == save_pkl['checksum']:
            return True, save_pkl['data']
        else:
            return False, None
    except:
        return False, None

def _caching_save(filename, checksum, data):
    """
    Save the given data and the given checksum to a file with the given filename.

    Arguments
    ---------
    filename : str
        Name of the file to save to.
    checksum : str
        Hexadecimal string checksum to be included in the file.
    """
    save_dict = {
        'checksum': checksum,
        'data': data,
    }
    pickle.dump(save_dict, open(filename, 'w'))

def _caching_checksum(obj):
    """
    Compute the hex string checksum of the given object.

    Arguments
    ---------
    obj : object
        Object to compute the checksum for.

    Returns
    -------
    str
        Hexadecimal string checksum that was computed.
    """
    self_pkl = pickle.dumps(obj)
    checksum = hashlib.md5(self_pkl).hexdigest()
    return checksum

def _caching_checksum_sm(sm):
    """
    Compute the hex string checksum of the SM instance, ignoring the printer attribute.

    Arguments
    ---------
    sm : SM
        The surrogate model object. We will temporarily remove the printer attribute
        when computing the checksum since it stores recorded times which will be
        inconsistent from run to run.

    Returns
    -------
    str
        Hexadecimal string checksum that was computed.
    """
    tmp = sm.printer

    sm.printer = None
    checksum = _caching_checksum((sm.sm_options, sm.training_pts))
    sm.printer = tmp
    return checksum
