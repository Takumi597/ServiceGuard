import os
import sys
import json
import time
import queue
import threading

from srodowisko import wykrywanie
from zrodla import baseline, zdarzenia
from detekcja import podpis, reguly, korelacja
from reakcja import uslugi
from logowanie import log


def funkcja_katalog_danych():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def funkcja_sciezka_danych(wartosc, domyslna):
    sciezka = wartosc or domyslna
    if not os.path.isabs(sciezka):
        sciezka = os.path.join(funkcja_katalog_danych(), sciezka)
    return sciezka


def funkcja_wczytaj_json(sciezka, domyslne):
    try:
        with open(sciezka, "r", encoding="utf-8") as plik:
            return json.load(plik)
    except Exception:
        return domyslne


def funkcja_wyczysc_obsluzone(obsluzone, teraz):
    if len(obsluzone) <= 500:
        return
    prog = teraz - 3600
    for klucz in [nazwa for nazwa, czas in obsluzone.items() if czas < prog]:
        del obsluzone[klucz]


def funkcja_obsluz_sygnal(sygnal, konfiguracja, biala_lista, bufor, rejestrator, obsluzone, stan_baseline, blokada):
    nazwa = sygnal.get("nazwa", "")
    if not nazwa or nazwa.lower() in biala_lista:
        return
    teraz = time.time()
    funkcja_wyczysc_obsluzone(obsluzone, teraz)
    if teraz - obsluzone.get(nazwa, 0) < 10:
        return
    obsluzone[nazwa] = teraz

    opis = baseline.funkcja_opis_uslugi(nazwa)
    if opis is None:
        sciezka_rejestru = sygnal.get("sciezka_exe", "") or baseline.funkcja_imagepath_uslugi(nazwa)
        rozmiar_rejestru, mtime_rejestru = baseline.funkcja_metryka(sciezka_rejestru)
        opis = {
            "nazwa": nazwa,
            "sciezka_exe": sciezka_rejestru,
            "plik_oceny": sciezka_rejestru,
            "linia_polecen": sygnal.get("linia_polecen", ""),
            "typ_startu": "",
            "konto_systemowe": True,
            "opis": "",
            "sterownik": False,
            "wspoldzielony": False,
            "rozmiar": rozmiar_rejestru,
            "mtime": mtime_rejestru,
        }
    opis["podpis"] = podpis.funkcja_weryfikacja(opis.get("plik_oceny") or opis.get("sciezka_exe", ""))

    wynik, powody = reguly.funkcja_ocena(opis, konfiguracja)
    bonus, rodzic = bufor.funkcja_dopasuj(opis)
    if bonus:
        wynik += bonus
        powody.append("korelacja_proces")

    raport = {
        "usluga": nazwa,
        "sciezka": opis.get("sciezka_exe", ""),
        "plik_oceny": opis.get("plik_oceny", ""),
        "wynik": wynik,
        "powody": powody,
        "zrodlo": sygnal.get("zrodlo", ""),
        "podpis": opis.get("podpis", ""),
    }
    if rodzic:
        raport["proces_nadrzedny"] = rodzic

    with blokada:
        baseline.funkcja_zapis_do_baseline(stan_baseline, opis)

    if wynik >= konfiguracja.get("prog_podejrzenia", 5):
        if konfiguracja.get("tryb_dry_run", True):
            rejestrator.funkcja_zapis("wykrycie", "Wykryto podejrzana usluge. Tryb tylko do raportowania, usluga nie zostala zablokowana.", raport)
            return
        rejestrator.funkcja_zapis("wykrycie", "Wykryto podejrzana usluge.", raport)
        zatrzymano = uslugi.funkcja_zatrzymaj(nazwa)
        wylaczono = uslugi.funkcja_wylacz(nazwa)
        schowano = None
        if konfiguracja.get("kwarantanna", False):
            schowano = uslugi.funkcja_kwarantanna(opis.get("sciezka_exe", ""), konfiguracja.get("katalog_kwarantanny", "kwarantanna"))
        rejestrator.funkcja_zapis("reakcja", "Podejrzana usluga zostala zatrzymana i wylaczona.", {
            "usluga": nazwa,
            "zatrzymano": zatrzymano,
            "wylaczono": wylaczono,
            "kwarantanna": schowano,
        })
    elif wynik >= konfiguracja.get("prog_informacji", 2):
        rejestrator.funkcja_zapis("informacja", "Wykryto nowa lub zmieniona usluge.", raport)


def funkcja_polling(konfiguracja, kolejka, stop, stan_baseline, blokada, rejestrator):
    import pythoncom
    try:
        pythoncom.CoInitialize()
    except Exception:
        pass
    while not stop.is_set():
        try:
            with blokada:
                roznice = baseline.funkcja_roznice(stan_baseline)
            for usluga in roznice:
                kolejka.put({
                    "nazwa": usluga["nazwa"],
                    "sciezka_exe": usluga["sciezka_exe"],
                    "linia_polecen": usluga["linia_polecen"],
                    "zrodlo": "odpytywanie",
                })
        except Exception as blad:
            rejestrator.funkcja_zapis("blad", "Blad watku odpytywania.", {"opis": str(blad)})
        stop.wait(konfiguracja.get("interwal_pollingu", 30))
    try:
        pythoncom.CoUninitialize()
    except Exception:
        pass


def funkcja_main():
    katalog = funkcja_katalog_danych()
    konfiguracja = funkcja_wczytaj_json(os.path.join(katalog, "config.json"), {})
    biala_lista = set(str(pozycja).lower() for pozycja in funkcja_wczytaj_json(os.path.join(katalog, "whitelist.json"), []))

    konfiguracja["plik_baseline"] = funkcja_sciezka_danych(konfiguracja.get("plik_baseline"), "baseline.json")
    konfiguracja["plik_logu"] = funkcja_sciezka_danych(konfiguracja.get("plik_logu"), "serviceguard.log")
    konfiguracja["katalog_kwarantanny"] = funkcja_sciezka_danych(konfiguracja.get("katalog_kwarantanny"), "kwarantanna")

    rejestrator = log.rejestrator_zdarzen(konfiguracja)
    srodowisko = wykrywanie.funkcja_sprawdz_srodowisko()
    rejestrator.funkcja_zapis("start", "Monitor uslug zostal uruchomiony.", srodowisko)
    if not srodowisko.get("administrator"):
        rejestrator.funkcja_zapis("ostrzezenie", "Program nie ma uprawnien administratora. Zatrzymywanie i wylaczanie uslug bedzie niedostepne.", None)

    plik_baseline = konfiguracja.get("plik_baseline", "baseline.json")
    stan_baseline = baseline.funkcja_wczytaj_baseline(plik_baseline)
    if not stan_baseline:
        stan_baseline = baseline.funkcja_utworz_baseline(plik_baseline)
        rejestrator.funkcja_zapis("start", "Utworzono stan odniesienia listy uslug.", {"liczba": len(stan_baseline)})

    kolejka = queue.Queue()
    bufor = korelacja.bufor_procesow(konfiguracja.get("okno_korelacji_sekundy", 60))
    stop = threading.Event()
    blokada_baseline = threading.Lock()

    zdarzenia.funkcja_uruchom_nasluch(kolejka, bufor, srodowisko, stop)
    watek_polling = threading.Thread(
        target=funkcja_polling, args=(konfiguracja, kolejka, stop, stan_baseline, blokada_baseline, rejestrator), daemon=True)
    watek_polling.start()

    obsluzone = {}
    try:
        while True:
            try:
                sygnal = kolejka.get(timeout=1)
            except queue.Empty:
                continue
            try:
                funkcja_obsluz_sygnal(sygnal, konfiguracja, biala_lista, bufor, rejestrator, obsluzone, stan_baseline, blokada_baseline)
            except Exception as blad:
                rejestrator.funkcja_zapis("blad", "Wystapil blad podczas obslugi zdarzenia.", {"opis": str(blad)})
    except KeyboardInterrupt:
        stop.set()
        rejestrator.funkcja_zapis("stop", "Monitor uslug zostal zatrzymany.", None)


if __name__ == "__main__":
    funkcja_main()
