import time
import threading

_WZORCE = [
    "sc.exe", "sc create", "sc  create", "sc config", "new-service",
    "reg add", "\\services\\", "binpath",
]


def _zawiera_token(tekst, token):
    if not token or len(token) < 4:
        return False
    poczatek = 0
    while True:
        pozycja = tekst.find(token, poczatek)
        if pozycja < 0:
            return False
        przed = tekst[pozycja - 1] if pozycja > 0 else " "
        koniec = pozycja + len(token)
        po = tekst[koniec] if koniec < len(tekst) else " "
        if not przed.isalnum() and not po.isalnum():
            return True
        poczatek = pozycja + 1


class bufor_procesow:
    def __init__(self, okno):
        self._okno = okno
        self._dane = []
        self._blokada = threading.Lock()

    def _czysc(self):
        prog = time.time() - self._okno
        self._dane = [pozycja for pozycja in self._dane if pozycja[0] >= prog]

    def funkcja_dodaj(self, linia, obraz, rodzic):
        niska = (linia or "").lower()
        niski_obraz = (obraz or "").lower()
        if not any(wzorzec in niska for wzorzec in _WZORCE) and "sc.exe" not in niski_obraz:
            return
        with self._blokada:
            self._dane.append((time.time(), niska, obraz or "", rodzic or ""))
            self._czysc()

    def funkcja_dopasuj(self, opis):
        nazwa = (opis.get("nazwa") or "").lower()
        sciezka = (opis.get("sciezka_exe") or "").lower()
        with self._blokada:
            self._czysc()
            for _, linia, _, rodzic in reversed(self._dane):
                if _zawiera_token(linia, nazwa) or (sciezka and len(sciezka) >= 4 and sciezka in linia):
                    return 2, rodzic
        return 0, ""
