import os
import re
import json

import pomocnicze

_WZORZEC_SESJI = re.compile(r"_[0-9a-fA-F]{4,}$")
_MAPA_STARTU = {0: "Boot", 1: "System", 2: "Auto", 3: "Manual", 4: "Disabled"}


def funkcja_nazwa_bazowa(nazwa):
    return _WZORZEC_SESJI.sub("", nazwa or "")


def _rozwin_imagepath(wartosc):
    sciezka = pomocnicze.funkcja_sciezka_z_polecenia(os.path.expandvars(wartosc))
    niska = sciezka.lower()
    korzen = os.environ.get("SystemRoot", "C:\\Windows")
    if niska.startswith("\\??\\"):
        sciezka = sciezka[4:]
    elif niska.startswith("\\systemroot\\"):
        sciezka = os.path.join(korzen, sciezka[len("\\systemroot\\"):])
    elif not os.path.splitdrive(sciezka)[0] and not sciezka.startswith("\\"):
        sciezka = os.path.join(korzen, sciezka)
    return sciezka


def funkcja_metryka(sciezka):
    if not sciezka or not os.path.isfile(sciezka):
        return (0, 0)
    try:
        dane = os.stat(sciezka)
        return (dane.st_size, int(dane.st_mtime))
    except Exception:
        return (0, 0)


def funkcja_biblioteka_uslugi(nazwa):
    try:
        import winreg
    except Exception:
        return ""
    galezie = [
        "SYSTEM\\CurrentControlSet\\Services\\%s\\Parameters" % nazwa,
        "SYSTEM\\CurrentControlSet\\Services\\%s" % nazwa,
    ]
    for galaz in galezie:
        try:
            klucz = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, galaz)
        except Exception:
            continue
        try:
            wartosc, _ = winreg.QueryValueEx(klucz, "ServiceDll")
            winreg.CloseKey(klucz)
            if wartosc:
                return os.path.expandvars(wartosc.strip('"'))
        except Exception:
            try:
                winreg.CloseKey(klucz)
            except Exception:
                pass
    return ""


def funkcja_imagepath_uslugi(nazwa):
    try:
        import winreg
    except Exception:
        return ""
    try:
        klucz = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services\\%s" % nazwa)
    except Exception:
        return ""
    wartosc = ""
    try:
        wartosc, _ = winreg.QueryValueEx(klucz, "ImagePath")
    except Exception:
        wartosc = ""
    try:
        winreg.CloseKey(klucz)
    except Exception:
        pass
    if not wartosc:
        return ""
    return _rozwin_imagepath(wartosc)


def funkcja_rejestr_uslugi():
    try:
        import winreg
    except Exception:
        return []
    try:
        korzen = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SYSTEM\\CurrentControlSet\\Services")
    except Exception:
        return []
    wynik = []
    indeks = 0
    while True:
        try:
            nazwa = winreg.EnumKey(korzen, indeks)
        except OSError:
            break
        indeks += 1
        try:
            klucz = winreg.OpenKey(korzen, nazwa)
        except Exception:
            continue
        linia = ""
        start = ""
        try:
            try:
                wartosc, _ = winreg.QueryValueEx(klucz, "ImagePath")
                linia = wartosc or ""
            except Exception:
                linia = ""
            try:
                numer, _ = winreg.QueryValueEx(klucz, "Start")
                start = _MAPA_STARTU.get(numer, "")
            except Exception:
                start = ""
        finally:
            try:
                winreg.CloseKey(klucz)
            except Exception:
                pass
        sciezka = _rozwin_imagepath(linia) if linia else ""
        rozmiar, mtime = funkcja_metryka(sciezka)
        wynik.append({
            "nazwa": nazwa,
            "linia_polecen": linia,
            "sciezka_exe": sciezka,
            "typ_startu": start,
            "rozmiar": rozmiar,
            "mtime": mtime,
        })
    try:
        winreg.CloseKey(korzen)
    except Exception:
        pass
    return wynik


def funkcja_na_opis(pozycja):
    linia = pozycja.PathName or ""
    sciezka = _rozwin_imagepath(linia) if linia else ""
    konto = (pozycja.StartName or "").lower()
    systemowe = konto in ("localsystem", "", "nt authority\\system") or konto.startswith("nt authority")
    rozmiar, mtime = funkcja_metryka(sciezka)
    return {
        "nazwa": pozycja.Name or "",
        "linia_polecen": linia,
        "sciezka_exe": sciezka,
        "plik_oceny": sciezka,
        "typ_startu": pozycja.StartMode or "",
        "konto_systemowe": systemowe,
        "opis": pozycja.Description or "",
        "sterownik": "Driver" in (pozycja.ServiceType or ""),
        "wspoldzielony": "Share" in (pozycja.ServiceType or ""),
        "rozmiar": rozmiar,
        "mtime": mtime,
    }


def funkcja_pobierz_uslugi():
    import win32com.client
    polaczenie = win32com.client.GetObject("winmgmts:\\\\.\\root\\cimv2")
    zapytanie = polaczenie.ExecQuery(
        "SELECT Name,PathName,StartMode,StartName,State,Description,ServiceType FROM Win32_Service"
    )
    uslugi = []
    for pozycja in zapytanie:
        uslugi.append(funkcja_na_opis(pozycja))
    return uslugi


def funkcja_opis_uslugi(nazwa):
    try:
        import win32com.client
        polaczenie = win32com.client.GetObject("winmgmts:\\\\.\\root\\cimv2")
        bezpieczna = nazwa.replace("'", "").replace('"', "")
        zapytanie = polaczenie.ExecQuery(
            "SELECT Name,PathName,StartMode,StartName,State,Description,ServiceType FROM Win32_Service WHERE Name='%s'" % bezpieczna
        )
        for pozycja in zapytanie:
            opis = funkcja_na_opis(pozycja)
            if opis.get("wspoldzielony") or os.path.basename((opis.get("sciezka_exe") or "").lower()) == "svchost.exe":
                biblioteka = funkcja_biblioteka_uslugi(opis["nazwa"])
                if biblioteka:
                    opis["plik_oceny"] = biblioteka
            return opis
    except Exception:
        return None
    return None


def funkcja_utworz_baseline(sciezka_pliku):
    uslugi = funkcja_rejestr_uslugi()
    mapa = {}
    for usluga in uslugi:
        mapa[funkcja_nazwa_bazowa(usluga["nazwa"])] = {
            "sciezka_exe": usluga["sciezka_exe"],
            "rozmiar": usluga["rozmiar"],
            "mtime": usluga["mtime"],
            "typ_startu": usluga["typ_startu"],
        }
    katalog = os.path.dirname(sciezka_pliku)
    if katalog and not os.path.isdir(katalog):
        os.makedirs(katalog)
    with open(sciezka_pliku, "w", encoding="utf-8") as plik:
        json.dump(mapa, plik, ensure_ascii=False, indent=2)
    return mapa


def funkcja_wczytaj_baseline(sciezka_pliku):
    if not os.path.exists(sciezka_pliku):
        return {}
    try:
        with open(sciezka_pliku, "r", encoding="utf-8") as plik:
            return json.load(plik)
    except Exception:
        return {}


def funkcja_zapis_do_baseline(stan_baseline, opis):
    stan_baseline[funkcja_nazwa_bazowa(opis["nazwa"])] = {
        "sciezka_exe": opis.get("sciezka_exe", ""),
        "rozmiar": opis.get("rozmiar", 0),
        "mtime": opis.get("mtime", 0),
        "typ_startu": opis.get("typ_startu", ""),
    }


def funkcja_roznice(stan_baseline):
    nowe = []
    for usluga in funkcja_rejestr_uslugi():
        zapis = stan_baseline.get(funkcja_nazwa_bazowa(usluga["nazwa"]))
        if (zapis is None
                or (zapis.get("sciezka_exe") or "").lower() != (usluga["sciezka_exe"] or "").lower()
                or zapis.get("rozmiar") != usluga["rozmiar"]
                or zapis.get("mtime") != usluga["mtime"]):
            nowe.append(usluga)
    return nowe
