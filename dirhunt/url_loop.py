from dirhunt.url import Url

MATCHS_LOOP_NUM = 3


def is_url_loop(url, ignore_end=True):
    # No necesito other, puedo hacerlo sólo con url. Recorrer directorios desde el último.
    # Si el penúltimo directorio es igual al último, es una repetición, aplicar a las 2
    # próximas posiciones
    url = url if isinstance(url, Url) else Url(url)
    directories = list(filter(bool, url.directories))
    directories.reverse()
    for i in range(1, (len(directories) // MATCHS_LOOP_NUM) + 1):
        groups = [tuple(directories[j:j+i]) for j in range(0, len(directories), i)]
        if len(set(groups)) == 1 and len(groups) >= MATCHS_LOOP_NUM:
            return True
    if ignore_end:
        return is_url_loop(url.parent(), False)
    return False
