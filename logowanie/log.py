import os
import json
import time


class rejestrator_zdarzen:
    def __init__(self, konfiguracja):
        self._sciezka = konfiguracja.get("plik_logu", "serviceguard.log")
        self._zdarzenia_windows = True
        katalog = os.path.dirname(self._sciezka)
        if katalog and not os.path.isdir(katalog):
            try:
                os.makedirs(katalog)
            except Exception:
                pass

    def funkcja_zapis(self, kategoria, tresc, dane=None):
        wpis = {
            "czas": time.strftime("%Y-%m-%d %H:%M:%S"),
            "kategoria": kategoria,
            "tresc": tresc,
        }
        if dane is not None:
            wpis["dane"] = dane
        linia = json.dumps(wpis, ensure_ascii=False)
        try:
            with open(self._sciezka, "a", encoding="utf-8") as plik:
                plik.write(linia + "\n")
        except Exception:
            pass
        print(linia)
        if kategoria in ("wykrycie", "reakcja"):
            self._funkcja_dziennik_windows(tresc)

    def _funkcja_dziennik_windows(self, tresc):
        if not self._zdarzenia_windows:
            return
        try:
            import win32evtlogutil
            import win32evtlog
            win32evtlogutil.ReportEvent(
                "ServiceGuard", 1000,
                eventType=win32evtlog.EVENTLOG_WARNING_TYPE,
                strings=[tresc],
            )
        except Exception:
            self._zdarzenia_windows = False
