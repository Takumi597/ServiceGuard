import os
import time
import shutil

import pomocnicze


def funkcja_zatrzymaj(nazwa):
    try:
        import win32serviceutil
        win32serviceutil.StopService(nazwa)
        return True
    except Exception:
        return False


def funkcja_wylacz(nazwa):
    try:
        import win32service
        menedzer = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ALL_ACCESS)
        uchwyt = win32service.OpenService(menedzer, nazwa, win32service.SERVICE_ALL_ACCESS)
        win32service.ChangeServiceConfig(
            uchwyt,
            win32service.SERVICE_NO_CHANGE,
            win32service.SERVICE_DISABLED,
            win32service.SERVICE_NO_CHANGE,
            None, None, 0, None, None, None, None,
        )
        win32service.CloseServiceHandle(uchwyt)
        win32service.CloseServiceHandle(menedzer)
        return True
    except Exception:
        return False


def funkcja_kwarantanna(sciezka, katalog):
    if not sciezka or not os.path.isfile(sciezka):
        return None
    try:
        if not os.path.isdir(katalog):
            os.makedirs(katalog)
        skrot = pomocnicze.funkcja_skrot_pliku(sciezka)
        cel = os.path.join(katalog, "%d_%s" % (int(time.time()), os.path.basename(sciezka)))
        shutil.move(sciezka, cel)
        return {"cel": cel, "skrot": skrot}
    except Exception:
        return None
