Unicode true
!include "MUI2.nsh"
!include "x64.nsh"
!include "LogicLib.nsh"
!define PRODUCT "Virtual HSM Studio"
!define VERSION "0.4.0-beta.1"
Name "${PRODUCT} ${VERSION}"
OutFile "..\dist\installer\VirtualHsmStudio-${VERSION}-Setup.exe"
InstallDir "$LOCALAPPDATA\Programs\VirtualHsmStudio"
InstallDirRegKey HKCU "Software\VirtualHsmStudio\Installer" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
BrandingText "Virtual HSM Studio | POC Preview"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\VirtualHsmStudio.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Virtual HSM Studio"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "This POC requires 64-bit Windows."
    Abort
  ${EndIf}
FunctionEnd
Section "Application"
  SetShellVarContext current
  SetOutPath "$INSTDIR"
  File /r "..\dist\VirtualHsmStudio\*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\Virtual HSM Studio"
  CreateShortcut "$SMPROGRAMS\Virtual HSM Studio\Virtual HSM Studio.lnk" "$INSTDIR\VirtualHsmStudio.exe"
  WriteRegStr HKCU "Software\VirtualHsmStudio\Installer" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VirtualHsmStudio" "DisplayName" "${PRODUCT}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VirtualHsmStudio" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VirtualHsmStudio" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VirtualHsmStudio" "DisplayIcon" "$INSTDIR\VirtualHsmStudio.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VirtualHsmStudio" "Publisher" "Virtual HSM Studio"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VirtualHsmStudio" "InstallLocation" "$INSTDIR"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VirtualHsmStudio" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VirtualHsmStudio" "NoRepair" 1
SectionEnd
Section "Uninstall"
  SetShellVarContext current
  ; The generated manifest deletes only application files, never token data or unrelated files.
  !include "uninstall-files.nsh"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\Virtual HSM Studio\Virtual HSM Studio.lnk"
  RMDir "$SMPROGRAMS\Virtual HSM Studio"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\VirtualHsmStudio"
  DeleteRegKey HKCU "Software\VirtualHsmStudio\Installer"
SectionEnd
