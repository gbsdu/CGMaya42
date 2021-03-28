import os
import platform
import ctypes


dir = 'D:/projects'
if platform.system() == 'Windows':
    drive = dir.split(':')[0]
    folder = drive + ':\\'
    free_bytes = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None,
                                               ctypes.pointer(free_bytes))
    storageSize = free_bytes.value / 1024 / 1024 / 1024
else:
    st = os.statvfs(dir)
    storageSize = st.f_bavail * st.f_frsize / 1024 / 1024
print str(storageSize) + 'MB'