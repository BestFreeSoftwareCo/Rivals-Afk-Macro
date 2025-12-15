#NoTrayIcon

If $CmdLine[0] < 1 Then
    ConsoleWrite("ERR:missing_command")
    Exit 2
EndIf

Local $cmd = StringLower($CmdLine[1])

Switch $cmd
    Case "move"
        If $CmdLine[0] < 4 Then
            ConsoleWrite("ERR:move_args")
            Exit 2
        EndIf
        MouseMove(Number($CmdLine[2]), Number($CmdLine[3]), Number($CmdLine[4]))
        Exit 0

    Case "click"
        If $CmdLine[0] < 6 Then
            ConsoleWrite("ERR:click_args")
            Exit 2
        EndIf
        MouseClick($CmdLine[2], Number($CmdLine[3]), Number($CmdLine[4]), Number($CmdLine[5]), Number($CmdLine[6]))
        Exit 0

    Case "send"
        If $CmdLine[0] < 2 Then
            ConsoleWrite("ERR:send_args")
            Exit 2
        EndIf
        Send($CmdLine[2])
        Exit 0

    Case "getpos"
        Local $pos = MouseGetPos()
        ConsoleWrite($pos[0] & "," & $pos[1])
        Exit 0

    Case Else
        ConsoleWrite("ERR:unknown_command")
        Exit 2
EndSwitch
