from dogpile.cache.region import make_region
from dogpile.cache.util import sha1_mangle_key
import inspect
import unicodedata

try:
    from pyramid.request import Request
    from pyramid.security import authenticated_userid
    PYRAMID_AVAILABLE = True
except ImportError as e:
    PYRAMID_AVAILABLE = False


__all__ = ['to_ascii', 'to_str', 'cache_key_generator', 'cache', 'configure_cache',
           'includeme', 'create_cache']


def to_ascii(ze_text):
    if not isinstance(ze_text, unicode):
        ze_text = unicode(ze_text)
    return unicodedata.normalize('NFKD', ze_text).encode('ascii', 'ignore')


def to_str(val, transform=to_ascii):
    if PYRAMID_AVAILABLE and isinstance(val, Request):
        user = authenticated_userid(val)
        s = transform(val.path) + transform(val.query_string)
        if user:
            s += ":" + user
        return s
    return transform(val)


def cache_key_generator(namespace, fn, to_str=to_str):
    """Cache key generation function that accepts keyword args"""
    if namespace is None:
        namespace = '%s:%s' % (fn.__module__, fn.__name__)
    else:
        namespace = '%s:%s|%s' % (fn.__module__, fn.__name__, namespace)

    args = inspect.getargspec(fn)
    has_self = args[0] and args[0][0] in ('self', 'cls')

    def generate_key(*args, **kw):
        args = list(args)
        if kw:
            for k in sorted(kw):
                args.append('{}={}'.format(k, to_str(kw[k])))
        if has_self:
            inst = args[0]
            if hasattr(inst, 'cache_hash'):
                hsh = inst.cache_hash()
                args.insert(0, hsh)
            else:
                args = args[1:]

        # Some key manglers don't like non-ascii inputs, normalize
        key = namespace + "|" + " ".join(map(to_str, args))
        return key
    return generate_key


DEFAULT_PREFIX = 'warchiefx.qtile.caching.'


DEFAULTS = {
    'backend': 'dogpile.cache.memory',
    'expiration_time': 3600,
}


cache = make_region(key_mangler=sha1_mangle_key,
                    function_key_generator=cache_key_generator).configure_from_config(
                        {DEFAULT_PREFIX + k: v for k, v in DEFAULTS.items()}, DEFAULT_PREFIX)


def create_cache():
    cache_inst = make_region(key_mangler=sha1_mangle_key, function_key_generator=cache_key_generator)
    return cache_inst


def configure_cache(settings, prefix=DEFAULT_PREFIX, cache_inst=None):
    conf = {}
    conf.update({prefix + k: v for k, v in DEFAULTS.items()})
    conf.update(settings)

    if cache_inst:
        cache = cache_inst
    else:
        global cache
        cache = create_cache()
    cache.configure_from_config(conf, prefix)
    return cache


def includeme(config):
    global cache
    settings = dict(config.get_settings())
    # See: http://dogpilecache.readthedocs.org/en/latest/usage.html

    cache = create_cache()
    configure_cache(settings)
