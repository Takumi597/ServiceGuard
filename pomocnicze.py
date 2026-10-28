import os
import hashlib


def funkcja_sciezka_z_polecenia(linia):
    linia = (linia or "").strip()
    if not linia:
        return ""
    if linia.startswith('"'):
        koniec = linia.find('"', 1)
        return linia[1:koniec] if koniec > 0 else linia[1:]
    niski = linia.lower()
    if ".exe" in niski:
        return linia[:niski.find(".exe") + 4]
    return linia.split(" ")[0]


def funkcja_skrot_pliku(sciezka):
    if not sciezka or not os.path.isfile(sciezka):
        return None
    try:
        suma = hashlib.sha256()
        with open(sciezka, "rb") as plik:
            for fragment in iter(lambda: plik.read(65536), b""):
                suma.update(fragment)
        return suma.hexdigest()
    except Exception:
        return None
