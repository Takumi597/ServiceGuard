import ctypes


def funkcja_czy_administrator():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _test_kanal(nazwa):
    try:
        import win32evtlog
        import win32event
        sygnal = win32event.CreateEvent(None, 0, 0, None)
        win32evtlog.EvtSubscribe(nazwa, win32evtlog.EvtSubscribeToFutureEvents, SignalEvent=sygnal)
        return True
    except Exception:
        return False


def _test_wmi():
    try:
        import win32com.client
        win32com.client.GetObject("winmgmts:\\\\.\\root\\cimv2")
        return True
    except Exception:
        return False


def funkcja_sprawdz_srodowisko():
    return {
        "administrator": funkcja_czy_administrator(),
        "kanal_system": _test_kanal("System"),
        "kanal_security": _test_kanal("Security"),
        "kanal_sysmon": _test_kanal("Microsoft-Windows-Sysmon/Operational"),
        "wmi": _test_wmi(),
    }
