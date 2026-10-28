import os
import tempfile
import subprocess


def funkcja_glowna():
    katalog = tempfile.gettempdir()
    sciezka = os.path.join(katalog, "usluga_testowa.bat")
    with open(sciezka, "w", encoding="utf-8") as plik:
        plik.write("@echo off\r\nping -n 30 127.0.0.1 >nul\r\n")
    polecenie = 'sc.exe create ServiceGuardTest binPath= "cmd.exe /c %s" start= demand' % sciezka
    print("Tworzenie uslugi testowej poleceniem:")
    print(polecenie)
    subprocess.run(polecenie, shell=True)
    print("Aby uruchomic usluge: sc.exe start ServiceGuardTest")
    print("Aby zatrzymac usluge: sc.exe stop ServiceGuardTest")
    print("Aby usunac usluge: sc.exe delete ServiceGuardTest")


if __name__ == "__main__":
    funkcja_glowna()
