import os

from pomocnicze import funkcja_sciezka_z_polecenia

_PODEJRZANE_POLECENIA = [
    "cmd.exe", "powershell", "rundll32", "-enc", "-encodedcommand",
    "mshta", "regsvr32", "wscript", "cscript",
]


def _nazwa_losowa(nazwa):
    rdzen = "".join(znak for znak in nazwa if znak.isalpha())
    if len(rdzen) < 6:
        return False
    samogloski = sum(1 for znak in rdzen.lower() if znak in "aeiouy")
    cyfry = sum(1 for znak in nazwa if znak.isdigit())
    return samogloski / max(len(rdzen), 1) < 0.25 or cyfry >= 4


def funkcja_ocena(opis, konfiguracja):
    wynik = 0
    powody = []
    sciezka = opis.get("sciezka_exe") or ""
    niska = sciezka.lower()
    plik_oceny = opis.get("plik_oceny") or sciezka
    niska_oceny = plik_oceny.lower()
    linia = opis.get("linia_polecen") or ""
    niska_linia = linia.lower()
    podpis = opis.get("podpis", "")

    if podpis != "zaufany":
        for katalog in konfiguracja.get("katalogi_zapisywalne", []):
            if katalog.lower() in niska_oceny:
                wynik += 3
                powody.append("plik_w_katalogu_zapisywalnym")
                break

    if podpis in ("niepodpisany", "niezaufany"):
        wynik += 3
        powody.append("podpis_%s" % podpis)
    elif podpis in ("blad", "brak_pliku"):
        wynik += 1
        powody.append("podpis_nierozstrzygniety")

    for wzorzec in _PODEJRZANE_POLECENIA:
        if wzorzec in niska_linia:
            wynik += 4
            powody.append("podejrzane_polecenie")
            break

    nazwa_pliku = os.path.basename(niska)
    if nazwa_pliku == "svchost.exe" and "\\system32\\" not in niska:
        wynik += 5
        powody.append("svchost_poza_system32")

    if _nazwa_losowa(opis.get("nazwa", "")) or not (opis.get("opis") or "").strip():
        wynik += 1
        powody.append("nazwa_lub_brak_opisu")

    if opis.get("typ_startu") == "Auto" and opis.get("konto_systemowe"):
        wynik += 1
        powody.append("auto_start_konto_systemowe")

    if linia and not linia.strip().startswith('"') and " " in funkcja_sciezka_z_polecenia(linia):
        wynik += 1
        powody.append("sciezka_niecytowana")

    if opis.get("sterownik") and podpis != "zaufany":
        wynik += 2
        powody.append("sterownik_niepodpisany")

    return wynik, powody
