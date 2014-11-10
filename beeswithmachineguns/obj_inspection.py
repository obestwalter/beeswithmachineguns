import inspect
import logging
import os
from types import FunctionType, MethodType

log = logging.getLogger(__name__)


SPECIAL_ATTR_NAMES = [
    "str", "repr", "dict", "doc", "class", "delattr", "format",
    "getattribute", "hash", "init", "module", "new", "reduce", "reduce_ex",
    "setattr", "sizeof", "subclasshook", "weakref"]

SIMPLE_OBJECTS = [basestring, list, tuple, dict, set, int, float]


def obj_attr(obj, hideString='', filterMethods=True, filterPrivate=True,
             sanitize=False, excludeAttrs=None, indent=0, objName=""):
    try:
        if any(isinstance(obj, t) for t in SIMPLE_OBJECTS):
            return ("[simple obj_attr] %s (%s): %s" %
                       (objName or "(anon)", type(obj).__name__, str(obj)))

        return _obj_attr(
            obj, hideString, filterMethods, filterPrivate,
            sanitize, excludeAttrs, indent, objName)

    except Exception:
        msg = "problems calling obj_attr"
        log.error(msg, exc_info=True)
        return msg


def _obj_attr(obj, hideString='', filterMethods=True, filterPrivate=True,
              sanitize=False, excludeAttrs=None, indent=0, objName=""):
    """show attributes of any object - generic representation of objects"""
    excludeAttrs = excludeAttrs or []
    names = dir(obj)
    for specialObjectName in SPECIAL_ATTR_NAMES:
        n = "__%s__" % (specialObjectName)
        if n in names:
            names.remove(n)
    if hideString:
        names = [n for n in names if hideString not in n]
    if filterPrivate:
        names = [n for n in names if not n.startswith('_')]
    out = []
    for name in sorted([d for d in names if d not in excludeAttrs]):
        try:
            attr = getattr(obj, name)
            attrType = type(attr)
            if attr is obj:
                continue  # recursion avoidance

            if filterMethods and (attrType in [FunctionType, MethodType]):
                continue

            if attrType in (FunctionType, MethodType):
                try:
                    value = attr.__doc__.split("\n")[0]
                except:
                    value = "<<func>>"
            else:
                value = str(attr).replace("\n", "\n|  ")
            out.append((name, attrType.__name__, value))
        except AssertionError as e:
            out.append(("[A] %s" % (name), e.__class__.__name__, e.message))

        except Exception as e:
            out.append(
                ("[E] %s" % (name), e.__class__.__name__, e.message[:80]))
    out = out or [(objName, str(type(obj)), repr(obj))]
    boundTo = "'%s' " % (objName) if objName else ""
    header = "|# %s%s (0x%X) #|" % (boundTo, type(obj).__name__, (id(obj)))
    numDashes = 40 - len(header) / 2
    out = (
        ["\n," + "-" * (numDashes - 1) + header + "-" * numDashes] +
        [_prepare_content(content) for content in out] +
        ["'" + "-" * 80])
    if sanitize:
        out = [o.replace('<', '(').replace('>', ')') for o in out]
    if indent:
        out = ["%s%s" % (" " * indent, o) for o in out]
    return os.linesep.join(out) + "\n  "
    #return _os.linesep.join(out) + "\ncaller: %s" % (caller(10))


def _prepare_content(contentTuple):
    """add line breaks within an attribute line"""
    name, typeName, value = contentTuple
    pattern = "| %-30s %15s: %%s" % (name, typeName.rpartition(".")[-1])
    if not isinstance(value, basestring):
        value = str(value)
    if str(value).strip().startswith("| "):
        return pattern % (value)

    windowSize = 80
    lines = [pattern % value[:windowSize]]
    curPos = windowSize
    while True:
        curString = value[curPos:curPos + windowSize]
        if not curString:
            break

        lines.append("\n|    %s" % (curString))
        curPos += windowSize
    return "".join(lines)


def caller(depth=1):
    """return the caller of the calling function. """

    def get_caller_path(depth):
        callers = [inspect.stack()[1 + depth][3]
                   for depth in range(depth, 0, -1)]
        return ".".join(callers)

    for depth in range(depth, 0, -1):
        try:
            return get_caller_path(depth)

        except Exception:
            if depth == 1:
                log.error("caller failed", exc_info=True)
    return "unknown caller"
