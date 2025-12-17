#NoTrayIcon
Opt("MouseCoordMode", 1)
Opt("SendKeyDelay", 0)
Opt("SendKeyDownDelay", 0)

While 1
    Local $chunk = ConsoleRead()
    If @error Then
        ExitLoop
    EndIf

    If $chunk <> "" Then
        $chunk = StringReplace($chunk, @CR, "")
        Local $lines = StringSplit($chunk, @LF, 1)

        For $i = 1 To $lines[0]
            Local $line = StringStripWS($lines[$i], 3)
            If $line = "" Then
                ContinueLoop
            EndIf

            Local $parts = StringSplit($line, "|", 1)
            If $parts[0] < 1 Then
                ConsoleWrite("ERR|PARSE" & @LF)
                ContinueLoop
            EndIf

            Local $cmd = StringUpper($parts[1])

            Switch $cmd
                Case "PING"
                    ConsoleWrite("OK" & @LF)

                Case "MOVE"
                    If $parts[0] < 4 Then
                        ConsoleWrite("ERR|ARGS" & @LF)
                        ContinueLoop
                    EndIf

                    MouseMove(Number($parts[2]), Number($parts[3]), Number($parts[4]))
                    ConsoleWrite("OK" & @LF)

                Case "CLICK"
                    If $parts[0] < 3 Then
                        ConsoleWrite("ERR|ARGS" & @LF)
                        ContinueLoop
                    EndIf

                    Local $x = Number($parts[2])
                    Local $y = Number($parts[3])
                    Local $button = "left"
                    Local $clicks = 1
                    Local $speed = 0

                    If $parts[0] >= 4 Then
                        $button = $parts[4]
                    EndIf
                    If $parts[0] >= 5 Then
                        $clicks = Number($parts[5])
                    EndIf
                    If $parts[0] >= 6 Then
                        $speed = Number($parts[6])
                    EndIf

                    MouseClick($button, $x, $y, $clicks, $speed)
                    ConsoleWrite("OK" & @LF)

                Case "KEY"
                    If $parts[0] < 2 Then
                        ConsoleWrite("ERR|ARGS" & @LF)
                        ContinueLoop
                    EndIf

                    Send($parts[2], 0)
                    ConsoleWrite("OK" & @LF)

                Case "EXIT"
                    ConsoleWrite("OK" & @LF)
                    ExitLoop

                Case Else
                    ConsoleWrite("ERR|UNKNOWN" & @LF)
            EndSwitch
        Next
    EndIf

    Sleep(5)
WEnd
