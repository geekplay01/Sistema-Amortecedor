' PERFECT Shock Data - abre o sistema sem a janela do cmd (etapa 24).
' Com o ambiente pronto (.venv e dependencias conferidas), roda o iniciar.bat escondido; senao (1a vez, dependencia nova), mostra a janela da instalacao.
' Se der erro escondido, o iniciar.bat se reabre visivel com a mensagem. Para fechar o sistema: Configuracoes > Sistema > «Fechar o sistema».
Set sh = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
pasta = fs.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = pasta
pronto = fs.FileExists(pasta & "\.venv\Scripts\pythonw.exe") And fs.FileExists(pasta & "\.venv\req.ok")
If pronto Then
  sh.Run "cmd /c """"" & pasta & "\iniciar.bat"" oculto""", 0, False
Else
  sh.Run "cmd /c """"" & pasta & "\iniciar.bat""""", 1, False
End If
