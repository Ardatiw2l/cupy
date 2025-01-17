import math
import cmath
import cupy
from cupy.linalg import _util


def khatri_rao(a, b):
    r"""
    Khatri-rao product

    A column-wise Kronecker product of two matrices

    Parameters
    ----------
    a : (n, k) array_like
        Input array
    b : (m, k) array_like
        Input array

    Returns
    -------
    c:  (n*m, k) ndarray
        Khatri-rao product of `a` and `b`.

    See Also
    --------
    .. seealso:: :func:`scipy.linalg.khatri_rao`

    """

    _util._assert_2d(a)
    _util._assert_2d(b)

    if a.shape[1] != b.shape[1]:
        raise ValueError("The number of columns for both arrays "
                         "should be equal.")

    c = a[..., :, cupy.newaxis, :] * b[..., cupy.newaxis, :, :]
    return c.reshape((-1,) + c.shape[2:])


# ### expm ###
b = [64764752532480000.,
     32382376266240000.,
     7771770303897600.,
     1187353796428800.,
     129060195264000.,
     10559470521600.,
     670442572800.,
     33522128640.,
     1323241920.,
     40840800.,
     960960.,
     16380.,
     182.,
     1.,]

th13 = 5.37


def expm(a):
    """Compute the matrix exponential.

    Parameters
    ----------
    a : ndarray, 2D

    Returns
    -------
    matrix exponential of `a`

    Notes
    -----
    Uses (a simplified) version of Algorithm 2.3 of [1]_:
    a [13 / 13] Pade approximant with scaling and squaring.

    Simplifications:

        * we always use a [13/13] approximate
        * no matrix balancing

    References
    ----------
    .. [1] N. Higham, SIAM J. MATRIX ANAL. APPL. Vol. 26(4), p. 1179 (2005)
       https://doi.org/10.1137/04061101X

    """
    if a.size == 0:
        return cupy.zeros((0, 0), dtype=a.dtype)

    n = a.shape[0]

    # try reducing the norm
    mu = cupy.diag(a).sum() / n
    A = a - cupy.eye(n)*mu

    # scale factor
    nrmA = cupy.linalg.norm(A, ord=1).item()

    scale = nrmA > th13
    s = int(math.ceil(math.log2(float(nrmA) / th13))) + 1 if scale else 1

    A /= 2**s

    # compute [13/13] Pade approximant
    A2 = A @ A
    A4 = A2 @ A2
    A6 = A2 @ A4

    E = cupy.eye(A.shape[0])

    u1, u2, v1, v2 = _expm_inner(E, A, A2, A4, A6, cupy.asarray(b))
    u = A @ (A6 @ u1 + u2)
    v = A6 @ v1 + v2

    r13 = cupy.linalg.solve(-u + v, u + v)

    # squaring
    x = r13
    for _ in range(s):
        x = x @ x

    # undo preprocessing
    x *= cmath.exp(mu) if cupy.iscomplexobj(mu) else math.exp(mu)

    return x


@cupy.fuse
def _expm_inner(E, A, A2, A4, A6, b):
    u1 = b[13]*A6 + b[11]*A4 + b[9]*A2
    u2 = b[7]*A6 + b[5]*A4 + b[3]*A2 + b[1]*E

    v1 = b[12]*A6 + b[10]*A4 + b[8]*A
    v2 = b[6]*A6 + b[4]*A4 + b[2]*A2 + b[0]*E
    return u1, u2, v1, v2


def cosm(a):  
    """
    Compute the matrix cosine.

    This routine uses expm to compute the matrix exponentials.

    Parameters
    ----------
    A : (N, N) array_like
        Input array

    Returns
    -------
    cosm : (N, N) ndarray
        Matrix cosine of A
    """
    if cupy.iscomplexobj(a):
        return 0.5*(expm(1j*a) + expm(-1j*a))
    else:
        return expm(1j*a).real

def sinm(a):  
    """
    Compute the matrix sine.

    This routine uses expm to compute the matrix exponentials.

    Parameters
    ----------
    A : (N, N) array_like
        Input array

    Returns
    -------
    cosm : (N, N) ndarray
        Matrix sine of A
    """
    if cupy.iscomplexobj(a):
        return -0.5*(expm(1j*a) - expm(-1j*a))
    else:
        return expm(1j*a).imag