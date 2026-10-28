import xml.etree.ElementTree as ET

_PRZESTRZEN = "{http://schemas.microsoft.com/win/2004/08/events/event}"


def funkcja_parsuj(tekst):
    try:
        korzen = ET.fromstring(tekst)
    except Exception:
        return {"id": 0, "dane": {}, "pozycyjne": []}
    system = korzen.find(_PRZESTRZEN + "System")
    identyfikator = 0
    if system is not None:
        wezel = system.find(_PRZESTRZEN + "EventID")
        if wezel is not None and wezel.text:
            try:
                identyfikator = int(wezel.text)
            except Exception:
                identyfikator = 0
    dane = {}
    pozycyjne = []
    sekcja = korzen.find(_PRZESTRZEN + "EventData")
    if sekcja is not None:
        for element in sekcja.findall(_PRZESTRZEN + "Data"):
            tresc = element.text or ""
            pozycyjne.append(tresc)
            klucz = element.get("Name")
            if klucz:
                dane[klucz] = tresc
    return {"id": identyfikator, "dane": dane, "pozycyjne": pozycyjne}


def funkcja_subskrybuj(kanal, zapytanie, oddzwonienie, stop):
    import win32evtlog
    import win32event
    try:
        sygnal = win32event.CreateEvent(None, 1, 0, None)
        subskrypcja = win32evtlog.EvtSubscribe(
            kanal,
            win32evtlog.EvtSubscribeToFutureEvents,
            SignalEvent=sygnal,
            Query=zapytanie,
        )
    except Exception:
        return
    while not stop.is_set():
        pobrano = False
        while True:
            try:
                grupa = win32evtlog.EvtNext(subskrypcja, 20)
            except Exception:
                grupa = []
            if not grupa:
                break
            pobrano = True
            for zdarzenie in grupa:
                try:
                    tekst = win32evtlog.EvtRender(zdarzenie, win32evtlog.EvtRenderEventXml)
                    oddzwonienie(funkcja_parsuj(tekst))
                except Exception:
                    continue
        if not pobrano:
            stop.wait(1)
