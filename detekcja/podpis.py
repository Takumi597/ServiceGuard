import os
import ctypes
from ctypes import wintypes

try:
    _wintrust = ctypes.WinDLL("wintrust.dll")
except Exception:
    _wintrust = None

try:
    _kernel = ctypes.WinDLL("kernel32.dll")
except Exception:
    _kernel = None

_GENERIC_READ = 0x80000000
_FILE_SHARE_READ = 0x00000001
_OPEN_EXISTING = 3
_NIEPRAWIDLOWY = 0xFFFFFFFFFFFFFFFF


class _identyfikator(ctypes.Structure):
    _fields_ = [
        ("a", wintypes.DWORD),
        ("b", wintypes.WORD),
        ("c", wintypes.WORD),
        ("d", ctypes.c_ubyte * 8),
    ]


class _plik(ctypes.Structure):
    _fields_ = [
        ("rozmiar", wintypes.DWORD),
        ("sciezka", wintypes.LPCWSTR),
        ("uchwyt", wintypes.HANDLE),
        ("temat", ctypes.c_void_p),
    ]


class _katalog(ctypes.Structure):
    _fields_ = [
        ("rozmiar", wintypes.DWORD),
        ("wersja", wintypes.DWORD),
        ("sciezka_katalogu", wintypes.LPCWSTR),
        ("znacznik", wintypes.LPCWSTR),
        ("sciezka_pliku", wintypes.LPCWSTR),
        ("uchwyt_pliku", wintypes.HANDLE),
        ("skrot", ctypes.POINTER(ctypes.c_ubyte)),
        ("rozmiar_skrotu", wintypes.DWORD),
        ("kontekst", ctypes.c_void_p),
        ("administrator", wintypes.HANDLE),
    ]


class _dane(ctypes.Structure):
    _fields_ = [
        ("rozmiar", wintypes.DWORD),
        ("polityka", ctypes.c_void_p),
        ("sip", ctypes.c_void_p),
        ("ui", wintypes.DWORD),
        ("odwolania", wintypes.DWORD),
        ("wybor", wintypes.DWORD),
        ("wskaznik", ctypes.c_void_p),
        ("akcja", wintypes.DWORD),
        ("stan", wintypes.HANDLE),
        ("url", wintypes.LPCWSTR),
        ("flagi", wintypes.DWORD),
        ("kontekst", wintypes.DWORD),
        ("ustawienia", ctypes.c_void_p),
    ]


class _opis_katalogu(ctypes.Structure):
    _fields_ = [
        ("rozmiar", wintypes.DWORD),
        ("plik", ctypes.c_wchar * 260),
    ]


def _guid_weryfikacji():
    return _identyfikator(
        0x00AAC56B, 0xCD44, 0x11D0,
        (ctypes.c_ubyte * 8)(0x8C, 0xC2, 0x00, 0xC0, 0x4F, 0xC2, 0x95, 0xEE),
    )


def _winverify(dane):
    _wintrust.WinVerifyTrust.restype = ctypes.c_long
    _wintrust.WinVerifyTrust.argtypes = [wintypes.HANDLE, ctypes.POINTER(_identyfikator), ctypes.c_void_p]
    akcja = _guid_weryfikacji()
    wynik = _wintrust.WinVerifyTrust(None, ctypes.byref(akcja), ctypes.byref(dane))
    dane.akcja = 2
    _wintrust.WinVerifyTrust(None, ctypes.byref(akcja), ctypes.byref(dane))
    return wynik & 0xFFFFFFFF


def _weryfikacja_osadzona(sciezka):
    info = _plik(ctypes.sizeof(_plik), sciezka, None, None)
    dane = _dane()
    dane.rozmiar = ctypes.sizeof(_dane)
    dane.ui = 2
    dane.wybor = 1
    dane.wskaznik = ctypes.cast(ctypes.byref(info), ctypes.c_void_p)
    dane.akcja = 1
    dane.flagi = 0x00000010
    try:
        kod = _winverify(dane)
    except Exception:
        return "blad"
    if kod == 0:
        return "zaufany"
    if kod in (0x800B0100, 0x800B0003):
        return "niepodpisany"
    return "niezaufany"


def _weryfikacja_katalogowa(sciezka):
    if _wintrust is None or _kernel is None:
        return False
    _kernel.CreateFileW.restype = wintypes.HANDLE
    _kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    uchwyt = _kernel.CreateFileW(sciezka, _GENERIC_READ, _FILE_SHARE_READ, None, _OPEN_EXISTING, 0, None)
    if not uchwyt or (uchwyt & 0xFFFFFFFFFFFFFFFF) == _NIEPRAWIDLOWY:
        return False
    administrator = wintypes.HANDLE()
    katalog = None
    try:
        _wintrust.CryptCATAdminAcquireContext.restype = wintypes.BOOL
        _wintrust.CryptCATAdminAcquireContext.argtypes = [ctypes.POINTER(wintypes.HANDLE), ctypes.c_void_p, wintypes.DWORD]
        if not _wintrust.CryptCATAdminAcquireContext(ctypes.byref(administrator), None, 0):
            return False
        _wintrust.CryptCATAdminCalcHashFromFileHandle.restype = wintypes.BOOL
        _wintrust.CryptCATAdminCalcHashFromFileHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(ctypes.c_ubyte), wintypes.DWORD]
        rozmiar = wintypes.DWORD(0)
        _wintrust.CryptCATAdminCalcHashFromFileHandle(uchwyt, ctypes.byref(rozmiar), None, 0)
        if rozmiar.value == 0:
            return False
        bufor = (ctypes.c_ubyte * rozmiar.value)()
        if not _wintrust.CryptCATAdminCalcHashFromFileHandle(uchwyt, ctypes.byref(rozmiar), bufor, 0):
            return False
        _wintrust.CryptCATAdminEnumCatalogFromHash.restype = wintypes.HANDLE
        _wintrust.CryptCATAdminEnumCatalogFromHash.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_ubyte), wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
        katalog = _wintrust.CryptCATAdminEnumCatalogFromHash(administrator, bufor, rozmiar.value, 0, None)
        if not katalog:
            return False
        _wintrust.CryptCATCatalogInfoFromContext.restype = wintypes.BOOL
        _wintrust.CryptCATCatalogInfoFromContext.argtypes = [wintypes.HANDLE, ctypes.POINTER(_opis_katalogu), wintypes.DWORD]
        opis = _opis_katalogu()
        opis.rozmiar = ctypes.sizeof(_opis_katalogu)
        if not _wintrust.CryptCATCatalogInfoFromContext(katalog, ctypes.byref(opis), 0):
            return False
        znacznik = "".join("%02X" % b for b in bufor)
        info = _katalog()
        info.rozmiar = ctypes.sizeof(_katalog)
        info.sciezka_katalogu = opis.plik
        info.znacznik = znacznik
        info.sciezka_pliku = sciezka
        info.uchwyt_pliku = uchwyt
        info.skrot = bufor
        info.rozmiar_skrotu = rozmiar.value
        info.administrator = administrator
        dane = _dane()
        dane.rozmiar = ctypes.sizeof(_dane)
        dane.ui = 2
        dane.wybor = 2
        dane.wskaznik = ctypes.cast(ctypes.byref(info), ctypes.c_void_p)
        dane.akcja = 1
        dane.flagi = 0x00000010
        try:
            kod = _winverify(dane)
        except Exception:
            return False
        return kod == 0
    except Exception:
        return False
    finally:
        try:
            if katalog:
                _wintrust.CryptCATAdminReleaseCatalogContext(administrator, katalog, 0)
            if administrator.value:
                _wintrust.CryptCATAdminReleaseContext(administrator, 0)
        except Exception:
            pass
        try:
            _kernel.CloseHandle(uchwyt)
        except Exception:
            pass


def funkcja_weryfikacja(sciezka):
    if not sciezka:
        return "nieznany"
    if not os.path.isfile(sciezka):
        return "brak_pliku"
    if _wintrust is None:
        return "blad"
    stan = _weryfikacja_osadzona(sciezka)
    if stan in ("niepodpisany", "niezaufany"):
        try:
            if _weryfikacja_katalogowa(sciezka):
                return "zaufany"
        except Exception:
            return stan
    return stan
