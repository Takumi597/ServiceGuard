import threading

from zrodla import kanal
from pomocnicze import funkcja_sciezka_z_polecenia


def _watek(cel):
    return threading.Thread(target=cel, daemon=True)


def _sygnal(nazwa, polecenie, zrodlo):
    return {
        "nazwa": nazwa,
        "sciezka_exe": funkcja_sciezka_z_polecenia(polecenie) if polecenie else "",
        "linia_polecen": polecenie or "",
        "zrodlo": zrodlo,
    }


def _nazwa_z_rejestru(cel):
    niski = (cel or "").replace("/", "\\")
    marker = "\\services\\"
    pozycja = niski.lower().find(marker)
    if pozycja < 0:
        return ""
    reszta = niski[pozycja + len(marker):]
    czesci = [czesc for czesc in reszta.split("\\") if czesc]
    if not czesci:
        return ""
    if len(czesci) == 1:
        return czesci[0]
    if czesci[1].lower() in ("imagepath", "start", "type", "servicedll"):
        return czesci[0]
    return ""


def funkcja_uruchom_nasluch(kolejka, bufor, srodowisko, stop):
    watki = []

    if srodowisko.get("kanal_system"):
        def _system(zdarzenie):
            dane = zdarzenie["dane"]
            pozycyjne = zdarzenie.get("pozycyjne", [])
            if zdarzenie["id"] == 7045:
                nazwa = dane.get("ServiceName", "")
                if nazwa:
                    kolejka.put(_sygnal(nazwa, dane.get("ImagePath", ""), "system_7045"))
            elif zdarzenie["id"] == 7040:
                nazwa = dane.get("ServiceName", "")
                if not nazwa and len(pozycyjne) >= 4:
                    nazwa = pozycyjne[3]
                if nazwa:
                    kolejka.put(_sygnal(nazwa, "", "system_7040"))
        watki.append(_watek(lambda: kanal.funkcja_subskrybuj(
            "System", "*[System[(EventID=7045 or EventID=7040)]]", _system, stop)))

    if srodowisko.get("kanal_security"):
        def _security(zdarzenie):
            dane = zdarzenie["dane"]
            if zdarzenie["id"] == 4697:
                nazwa = dane.get("ServiceName", "")
                if nazwa:
                    kolejka.put(_sygnal(nazwa, dane.get("ServiceFileName", ""), "security_4697"))
        watki.append(_watek(lambda: kanal.funkcja_subskrybuj(
            "Security", "*[System[(EventID=4697)]]", _security, stop)))

    if srodowisko.get("kanal_sysmon"):
        def _sysmon(zdarzenie):
            dane = zdarzenie["dane"]
            if zdarzenie["id"] == 1:
                bufor.funkcja_dodaj(dane.get("CommandLine", ""), dane.get("Image", ""), dane.get("ParentImage", ""))
            elif zdarzenie["id"] in (12, 13, 14):
                nazwa = _nazwa_z_rejestru(dane.get("TargetObject", ""))
                if nazwa:
                    kolejka.put(_sygnal(nazwa, dane.get("Details", ""), "sysmon_rejestr"))
        watki.append(_watek(lambda: kanal.funkcja_subskrybuj(
            "Microsoft-Windows-Sysmon/Operational",
            "*[System[(EventID=1 or EventID=12 or EventID=13 or EventID=14)]]", _sysmon, stop)))
    elif srodowisko.get("kanal_security"):
        def _procesy(zdarzenie):
            dane = zdarzenie["dane"]
            if zdarzenie["id"] == 4688:
                bufor.funkcja_dodaj(dane.get("CommandLine", ""), dane.get("NewProcessName", ""), dane.get("ParentProcessName", ""))
        watki.append(_watek(lambda: kanal.funkcja_subskrybuj(
            "Security", "*[System[(EventID=4688)]]", _procesy, stop)))

    for watek in watki:
        watek.start()
    return watki
