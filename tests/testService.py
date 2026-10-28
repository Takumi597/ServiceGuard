import sys
import win32serviceutil
import win32service
import win32event
import servicemanager


class usluga_testowa(win32serviceutil.ServiceFramework):
    _svc_name_ = "TestServiceRun"
    _svc_display_name_ = "Usluga testowa ServiceGuard"

    def __init__(self, argumenty):
        win32serviceutil.ServiceFramework.__init__(self, argumenty)
        self._zdarzenie = win32event.CreateEvent(None, 0, 0, None)
        self._pracuj = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self._pracuj = False
        win32event.SetEvent(self._zdarzenie)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        while self._pracuj:
            win32event.WaitForSingleObject(self._zdarzenie, 5000)


def funkcja_glowna():
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(usluga_testowa)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(usluga_testowa)


if __name__ == "__main__":
    funkcja_glowna()
