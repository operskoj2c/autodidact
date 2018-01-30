from __future__ import absolute_import
import numpy as onp
from . import numpy_wrapper as anp
from .numpy_boxes import ArrayBox
from autograd.tracer import primitive
from autograd.core import defvjp

# ----- Binary ufuncs -----

defvjp(anp.add,         lambda g, ans, x, y : unbroadcast(x, g),
                        lambda g, ans, x, y : unbroadcast(y, g))
defvjp(anp.multiply,    lambda g, ans, x, y : unbroadcast(x, y * g),
                        lambda g, ans, x, y : unbroadcast(y, x * g))
defvjp(anp.subtract,    lambda g, ans, x, y : unbroadcast(x, g),
                        lambda g, ans, x, y : unbroadcast(y, -g))
defvjp(anp.divide,      lambda g, ans, x, y : unbroadcast(x,   g / y),
                        lambda g, ans, x, y : unbroadcast(y, - g * x / y**2))
defvjp(anp.power,
    lambda g, ans, x, y: unbroadcast(x, g * y * x ** anp.where(y, y - 1, 1.)),
    lambda g, ans, x, y: unbroadcast(y, g * anp.log(replace_zero(x, 1.)) * x ** y))

def replace_zero(x, val):
    return anp.where(x, x, val)

def unbroadcast(target, g, broadcast_idx=0):
    while anp.ndim(g) > anp.ndim(target):
        g = anp.sum(g, axis=broadcast_idx)
    for axis, size in enumerate(anp.shape(target)):
        if size == 1:
            g = anp.sum(g, axis=axis, keepdims=True)
    if anp.iscomplexobj(g) and not anp.iscomplex(target):
        g = anp.real(g)
    return g

# ----- Simple grads -----

defvjp(anp.negative, lambda g, ans, x: -g)
defvjp(anp.exp,    lambda g, ans, x: ans * g)
defvjp(anp.log,    lambda g, ans, x: g / x)
defvjp(anp.tanh,   lambda g, ans, x: g / anp.cosh(x) **2)
defvjp(anp.sinh,   lambda g, ans, x: g * anp.cosh(x))
defvjp(anp.cosh,   lambda g, ans, x: g * anp.sinh(x))

defvjp(anp.where, None,
       lambda ans, c, x=None, y=None : lambda g: anp.where(c, g, anp.zeros(g.shape)),
       lambda ans, c, x=None, y=None : lambda g: anp.where(c, anp.zeros(g.shape), g))

# ----- Dot grads -----

# These definitions only work for arrays of rank 0, 1, or 2.

def _dot_vjp_0(g, ans, lhs, rhs):
  if anp.ndim(lhs) == 0:
    return unbroadcast(lhs, rhs * g)
  if anp.ndim(lhs) == 1 and anp.ndim(rhs) == 1:
    return g * rhs
  if anp.ndim(lhs) == 2 and anp.ndim(rhs) == 1:
    return g[:, None] * rhs
  if anp.ndim(lhs) == 1 and anp.ndim(rhs) == 2:
    return anp.dot(rhs, g)
  return anp.dot(g, rhs.T)

def _dot_vjp_1(g, ans, lhs, rhs):
  if anp.ndim(rhs) == 0:
    return unbroadcast(rhs, lhs * g)
  if anp.ndim(lhs) == 1 and anp.ndim(rhs) == 1:
    return g * lhs
  if anp.ndim(lhs) == 2 and anp.ndim(rhs) == 1:
    return anp.dot(g, lhs)
  if anp.ndim(lhs) == 1 and anp.ndim(rhs) == 2:
    return lhs[:, None] * g
  return anp.dot(lhs.T, g)

defvjp(anp.dot, _dot_vjp_0, _dot_vjp_1)
