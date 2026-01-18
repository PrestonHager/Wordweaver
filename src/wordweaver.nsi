; wordweaver.nsi
;--------------------------------

; The name of the installer
Name "Wordweaver"

; The file to write
OutFile "dist\Wordweaver-install.exe"

; Request application privileges for Windows Vista and higher
RequestExecutionLevel admin

; Build Unicode installer
Unicode True

; The default installation directory
InstallDir $PROGRAMFILES\Wordweaver

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\Wordweaver" "Install_Dir"

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "Wordweaver (required)"

  SectionIn RO
  
  ; Set output path to the installation directory.
  SetOutPath $INSTDIR
  
  ; Put file there
  File "dist\Wordweaver.exe"
  
  ; Write the installation path into the registry
  WriteRegStr HKLM "SOFTWARE\Wordweaver" "Install_Dir" "$INSTDIR"
  
  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wordweaver" "DisplayName" "Wordweaver"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wordweaver" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wordweaver" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wordweaver" "NoRepair" 1
  WriteUninstaller "$INSTDIR\uninstall.exe"
  
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\Wordweaver"
  CreateShortcut "$SMPROGRAMS\Wordweaver\Uninstall.lnk" "$INSTDIR\uninstall.exe"
  CreateShortcut "$SMPROGRAMS\Wordweaver\Wordweaver.lnk" "$INSTDIR\Wordweaver.exe"

SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Wordweaver"
  DeleteRegKey HKLM "SOFTWARE\Wordweaver"

  ; Remove files and uninstaller
  Delete $INSTDIR\Wordweaver.nsi
  Delete $INSTDIR\uninstall.exe

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\Wordweaver\*.lnk"

  ; Remove directories
  RMDir "$SMPROGRAMS\Wordweaver"
  RMDir "$INSTDIR"

SectionEnd
