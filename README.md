Yara rule for Xworm:
rule Windows_Trojan_XWorm_1 : malware { 
    meta:
        description = "Detects XWorm orders in memory"
        researcher = "Alexis Bonnefoi"
        source = "External"
        creation_date = "21/01/2025"
        os = "Windows"
        category = "Trojan"
        product = "p2a, mfd"
        threat_name = "Windows.Trojan.AsyncRat"
        samples = "1891b9ab0f06ecb635d7a7ea6a5799aa437b28bf322a263bc44d6889b5e9949d"
    strings:
        $s1 = "Err HWID" ascii wide
        $s2 = "HostsMSG" ascii wide
        $s3 = "pong" ascii wide
        $s4 = "Urlopen" ascii wide
        $s5 = "Urlhide" ascii wide
        $s6 = "PCShutdown" ascii wide
        $s7 = "PCRestart" ascii wide
        $s8 = "PCLogoff" ascii wide
        $s9 = "RunShell" ascii wide
        $s10 = "startDDos" ascii wide
        $s11 = "stopDDos" ascii wide
        $s12 = "startReport" ascii wide
        $s13 = "stopReport" ascii wide
        $s14 = "Xchat" ascii wide
        $s15 = "shosts" ascii wide
        $s16 = "HostsMSG" ascii wide
        $s17 = "Modified successfully!" ascii wide
        $s18 = "HostsErr" ascii wide
        $s19 = "ngrok+" ascii wide
        $s20 = "sendPlugin" ascii wide
        $s21 = "savePlugin" ascii wide
        $s22 = "OfflineGet" ascii wide
        $s23 = "OfflineKeylogger Not Enabled" ascii wide
        $s24 = "RunOptions" ascii wide
        $s25 = "UACFunc" ascii wide
        $s26 = "Plugin Error!" ascii wide
        $s27 = "PING!" ascii wide
        $s28 = "rec" ascii wide
        $s29 = "CLOSE" ascii wide
        $s30 = "StartDDos" ascii wide
        $s31 = "StopDDos" ascii wide
        $s32 = "StartReport" ascii wide
        $s33 = "StopReport" ascii wide
        $s34 = "RemovePlugins" ascii wide
        $s35 = "#CAP" ascii wide
        $s36 = "RunRecovery" ascii wide
        $s37 = "RunOptions" ascii wide
        $s38 = "injRun" ascii wide
        $s39 = "UACFunc" ascii wide
    condition:
        uint16(0) == 0x5A4D and 20 of them
}
