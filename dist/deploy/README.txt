ServiceGuard - monitor uslug systemu Windows


Do czego sluzy

ServiceGuard obserwuje uslugi systemu Windows. Wykrywa uslugi nowo dodane oraz
podejrzane, a w trybie aktywnym zatrzymuje je i wylacza. Program dziala takze
wtedy, gdy nie ma Sysmona albo gdy audyt jest wylaczony. Korzysta wowczas
z mniejszej liczby zrodel, ale nie przestaje dzialac.


Wymagania

Windows 11 oraz uprawnienia administratora, ktore sa konieczne do zatrzymywania
uslug. Wersja uruchamiana ze zrodel potrzebuje Pythona i biblioteki pywin32.
Wersja w pliku exe nie wymaga niczego dodatkowego.


Jak uruchomic

1. Kliknij ServiceGuard.exe prawym przyciskiem myszy i wybierz "Uruchom jako
   administrator". Jesli uruchamiasz ze zrodel, w oknie administratora wpisz
   polecenie: python main.py
2. Przy pierwszym uruchomieniu program zapisuje stan odniesienia listy uslug.
3. Zdarzenia sa zapisywane do pliku serviceguard.log w tym samym folderze,
   w ktorym znajduje sie program.


Tryb pracy

Domyslnie program dziala w trybie tylko do raportowania. Wykrywa i zapisuje,
ale nie zatrzymuje uslug. Aby wlaczyc blokowanie, otworz plik config.json,
zmien wartosc tryb_dry_run na false i uruchom program ponownie.


Pliki konfiguracyjne

config.json przechowuje progi, odstep sprawdzania i tryb pracy.

whitelist.json to lista nazw uslug, ktorych program nigdy nie zatrzymuje.
Aby dodac wlasna usluge, wpisz jej krotka nazwe na koncu listy, w cudzyslowie,
z przecinkiem po poprzedniej pozycji, i uruchom program ponownie. Krotka nazwa
to wartosc z kolumny Name w wyniku polecenia Get-Service.


Wazne uwagi

Program nalezy uruchamiac z uprawnieniami administratora. Bez nich nie zatrzyma
uslugi i zapisze o tym ostrzezenie przy starcie.

Tryb blokowania ma nieodwracalne skutki dla pracy systemu. Testuj go najpierw
w maszynie wirtualnej z zapisanym punktem przywracania.

Pelny zakres zrodel wymaga wlaczenia audytu zdarzen oraz instalacji Sysmona.
Bez nich program dziala, lecz wykrywa mniej przypadkow.

Plik exe nie jest podpisany cyfrowo, dlatego system moze go oznaczyc. W razie
potrzeby dodaj dla niego wyjatek w zabezpieczeniach.


Opcjonalna konfiguracja systemu

Audyt instalacji uslug (zdarzenie 4697), w oknie administratora:
auditpol /set /subcategory:"Security System Extension" /success:enable /failure:enable

Instalacja Sysmona z dolaczona konfiguracja:
sysmon64 -accepteula -i sysmon-config.xml


Budowa wersji exe

W folderze programu uruchom plik build.bat. Powstanie folder dist\deploy
z plikiem ServiceGuard.exe oraz plikami config.json, whitelist.json
i sysmon-config.xml. Caly folder deploy przenosisz na docelowy komputer.
Na tym komputerze Python nie jest juz potrzebny.
