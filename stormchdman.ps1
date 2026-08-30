#requires -version 5.1
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.IO.Compression.FileSystem
Add-Type -AssemblyName System.Xml

# Runtime imports for window dragging
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool ReleaseCapture();
    [DllImport("user32.dll")]
    public static extern int SendMessage(IntPtr hWnd, int Msg, int wParam, int lParam);
    public const int WM_NCLBUTTONDOWN = 0xA1;
    public const int HT_CAPTION = 0x2;
}
"@

# --- LANGUAGE DICTIONARY ---
$script:currentLang = "RU"
$LanguageData = @{
    "Title"                 = @{ RU = "STORM CHDMan"; EN = "STORM CHDMan" }
    "BtnDownloadDATs"       = @{ RU = "Скачать DAT-файлы"; EN = "Download DAT Files" }
    "BtnDeleteDATs"         = @{ RU = "Удалить DAT-файлы"; EN = "Delete DAT Files" }
    "BtnClearCache"         = @{ RU = "Очистить кэш серийников"; EN = "Clear Serial Cache" }
    
    # Кнопки Input удалены полностью
    "BtnBrowseFolder"       = @{ RU = "Обзор папки"; EN = "Browse Folder" }
    "BtnClear"              = @{ RU = "Очистить"; EN = "Clear" }
    "BtnBrowse"             = @{ RU = "Обзор"; EN = "Browse" }
    "BtnPause"              = @{ RU = "Пауза"; EN = "Pause" }
    "BtnResume"             = @{ RU = "Возобновить"; EN = "Resume" }
    "BtnCancel"             = @{ RU = "Отмена"; EN = "Cancel" }
    "BtnExecute"            = @{ RU = "Выполнить"; EN = "Execute" }
    "BtnClose"              = @{ RU = "Закрыть"; EN = "Close" }
    
    "LblOutput"             = @{ RU = "Выходная папка:"; EN = "Output Folder:" }
    "LblCores"              = @{ RU = "Кол-во ядер:"; EN = "CPU Cores:" }
    "LblCompression"        = @{ RU = "Сжатие:"; EN = "Compression:" }
    "LblCDHunk"             = @{ RU = "Размер блока CD:"; EN = "CD Hunk Size:" }
    "LblDVDHunk"            = @{ RU = "Размер блока DVD:"; EN = "DVD Hunk Size:" }
    "LblCreatedBy"          = @{ RU = "Создано: ReiKatari"; EN = "Created by: ReiKatari" }
    "LblVersion"            = @{ RU = "Версия: 2.3.2"; EN = "Version: 2.3.2" }
    
    "ChkForce"              = @{ RU = "Принудительная перезапись"; EN = "Force Overwrite" }
    "ChkRecognition"        = @{ RU = "Распознавание платформ"; EN = "Platform Recognition" }
    "ChkAetherSX2"          = @{ RU = "AetherSX2/NetherSX2"; EN = "AetherSX2/NetherSX2" }
    "ChkTextNotif"          = @{ RU = "Текстовое уведомление"; EN = "Text Notification" }
    "ChkSoundNotif"         = @{ RU = "Звуковое уведомление"; EN = "Sound Notification" }
    
    "ColFile"               = @{ RU = "Файл (можно переименовать)"; EN = "File (Renamable)" }
    "ColCount"              = @{ RU = "Файлов"; EN = "Count" }
    "ColPlatform"           = @{ RU = "Платформа"; EN = "Platform" }
    "ColFormat"             = @{ RU = "Формат"; EN = "Format" }
    "ColStatus"             = @{ RU = "Статус"; EN = "Status" }
    "ColSizeStart"          = @{ RU = "Начальный размер"; EN = "Initial Size" }
    "ColSizeEnd"            = @{ RU = "Конечный размер"; EN = "Final Size" }
    "ColRatio"              = @{ RU = "Сжатие"; EN = "Ratio" }
    "ColSHA1"               = @{ RU = "SHA1"; EN = "SHA1" }
    "ColSerial"             = @{ RU = "Серийный номер"; EN = "Serial Number" }
    
    "StatusAdded"           = @{ RU = "Добавлено"; EN = "Added" }
    "StatusWorking"         = @{ RU = "В работе"; EN = "Working" }
    "StatusDone"            = @{ RU = "Готово"; EN = "Done" }
    "StatusError"           = @{ RU = "Ошибка"; EN = "Error" }
    "StatusCancelled"       = @{ RU = "Отменено"; EN = "Cancelled" }
    
    "MenuDeleteRow"         = @{ RU = "Удалить строку"; EN = "Delete Row" }
    "MenuOpenSource"        = @{ RU = "Открыть папку с исходным файлом"; EN = "Open Source Folder" }
    "MenuOpenDest"          = @{ RU = "Открыть папку с итоговым файлом"; EN = "Open Output Folder" }
    "MenuCopySerial"        = @{ RU = "Копировать серийный номер"; EN = "Copy Serial Number" }
    
    "MsgErrorCHDMan"        = @{ RU = "Ошибка: chdman.exe не найден в корневой папке."; EN = "Error: chdman.exe not found in root folder." }
    "MsgCritError"          = @{ RU = "Критическая ошибка"; EN = "Critical Error" }
    "MsgDatsDownloaded"     = @{ RU = "Скачивание завершено"; EN = "Download Complete" }
    "MsgCacheCleared"       = @{ RU = "Кэш серийных номеров очищен"; EN = "Serial cache cleared" }
    "MsgCacheEmpty"         = @{ RU = "Кэш серийных номеров уже пуст"; EN = "Serial cache is already empty" }
    "MsgFolderDeleted"      = @{ RU = "Папка DATs удалена"; EN = "DATs folder deleted" }
    "MsgNoFiles"            = @{ RU = "Не найдено подходящих файлов"; EN = "No suitable files found" }
    "MsgListCleared"        = @{ RU = "Список файлов очищен"; EN = "File list cleared" }
    "MsgRowsDeleted"        = @{ RU = "Удалены выбранные строки"; EN = "Selected rows deleted" }
    "MsgFolderNotFound"     = @{ RU = "Папка не найдена"; EN = "Folder not found" }
    "MsgPathNotFound"       = @{ RU = "Путь к файлу не найден"; EN = "File path not found" }
    "MsgFileNotProcessed"   = @{ RU = "Файл еще не обработан. Статус"; EN = "File not processed yet. Status" }
    "MsgSerialCopied"       = @{ RU = "Серийный номер скопирован"; EN = "Serial number copied" }
    "MsgSerialNotFound"     = @{ RU = "Серийный номер не найден для этой игры"; EN = "Serial number not found for this game" }
    "MsgCancelProcess"      = @{ RU = "Отменить обработку?"; EN = "Cancel processing?" }
    "MsgConfirmation"       = @{ RU = "Подтверждение"; EN = "Confirmation" }
    "MsgProcessCancelled"   = @{ RU = "Обработка отменена пользователем"; EN = "Processing cancelled by user" }
    "MsgNoFilesSelected"    = @{ RU = "Файлы не выбраны! Перетащите файлы в таблицу."; EN = "No files selected! Drag & drop files into the grid." }
    "MsgProcessingComplete" = @{ RU = "Обработка завершена!"; EN = "Processing Complete!" }
    "MsgProcessedCount"     = @{ RU = "Обработано"; EN = "Processed" }
    "MsgProcessResumed"     = @{ RU = "Обработка возобновлена"; EN = "Processing resumed" }
    "MsgProcessPaused"      = @{ RU = "Обработка приостановлена"; EN = "Processing paused" }
    "MsgStartProcessing"    = @{ RU = "=== Начало обработки ==="; EN = "=== Processing Started ===" }
    "MsgEndProcessing"      = @{ RU = "=== Обработка завершена ==="; EN = "=== Processing Finished ===" }
    "MsgTotalGames"         = @{ RU = "Всего игр"; EN = "Total games" }
    
    "LogDebugStart"         = @{ RU = "  DEBUG START: Get-SerialFromImage вызвана для"; EN = "  DEBUG START: Get-SerialFromImage called for" }
    "LogCacheHit"           = @{ RU = "  DEBUG: Взято из кэша"; EN = "  DEBUG: Retrieved from cache" }
    "LogCacheMiss"          = @{ RU = "  DEBUG: Кэш не содержит этот файл, начинаем извлечение"; EN = "  DEBUG: Cache miss, starting extraction" }
    "LogExt"                = @{ RU = "  DEBUG: Расширение файла:"; EN = "  DEBUG: File extension:" }
    "LogBinFound"           = @{ RU = "  DEBUG: Найдено BIN файлов:"; EN = "  DEBUG: BIN files found:" }
    "LogFirstBin"           = @{ RU = "  DEBUG: Первый BIN файл:"; EN = "  DEBUG: First BIN file:" }
    "LogNoBin"              = @{ RU = "  DEBUG: BIN файлы не найдены!"; EN = "  DEBUG: BIN files not found!" }
    "LogPlatformCache"      = @{ RU = "  DEBUG: Платформа из кэша:"; EN = "  DEBUG: Platform from cache:" }
    "LogPlatformNotFound"   = @{ RU = "  DEBUG: Платформа НЕ найдена в recognizedPlatforms!"; EN = "  DEBUG: Platform NOT found in recognizedPlatforms!" }
    "LogPlatformIs"         = @{ RU = "  DEBUG: Платформа ="; EN = "  DEBUG: Platform =" }
    "LogProcessing"         = @{ RU = "  DEBUG: Обработка"; EN = "  DEBUG: Processing" }
    "LogBytesRead"          = @{ RU = "  DEBUG: Прочитано байт:"; EN = "  DEBUG: Bytes read:" }
    "LogSig"                = @{ RU = "  DEBUG: Сигнатура:"; EN = "  DEBUG: Signature:" }
    "LogSerialFound"        = @{ RU = "  DEBUG: Найден серийник"; EN = "  DEBUG: Serial found" }
    "LogRegexFail"          = @{ RU = "  DEBUG: Regex не сработал для"; EN = "  DEBUG: Regex failed for" }
    "LogSigFail"            = @{ RU = "  DEBUG: Сигнатура SEGA не найдена!"; EN = "  DEBUG: SEGA signature not found!" }
    "LogNotSupported"       = @{ RU = "  DEBUG: не поддерживается"; EN = "  DEBUG: not supported" }
    "Log7ZipFound"          = @{ RU = "  DEBUG: 7-Zip найден, пробуем извлечь SYSTEM.CNF"; EN = "  DEBUG: 7-Zip found, attempting to extract SYSTEM.CNF" }
    "LogSysCnfFound"        = @{ RU = "  DEBUG: SYSTEM.CNF найден"; EN = "  DEBUG: SYSTEM.CNF found" }
    "LogSysCnfNotFound"     = @{ RU = "  DEBUG: SYSTEM.CNF не найден"; EN = "  DEBUG: SYSTEM.CNF not found" }
    "Log7ZipError"          = @{ RU = "  DEBUG: 7-Zip Ошибка:"; EN = "  DEBUG: 7-Zip Error:" }
    "LogFallbackRead"       = @{ RU = "  DEBUG: Пробуем прямое чтение образа..."; EN = "  DEBUG: Attempting direct image read..." }
    "LogSerialDirect"       = @{ RU = "  DEBUG: Найден серийник прямым чтением:"; EN = "  DEBUG: Serial found via direct read:" }
    "LogDirectFail"         = @{ RU = "  DEBUG: Прямое чтение не дало результатов"; EN = "  DEBUG: Direct read yielded no results" }
    "LogGeneralError"       = @{ RU = "  DEBUG: Общая ошибка:"; EN = "  DEBUG: General Error:" }
    "LogFinalSerial"        = @{ RU = "  DEBUG END: Итоговый серийник:"; EN = "  DEBUG END: Final Serial:" }
    "LogCacheLoaded"        = @{ RU = "Кэш серийных номеров загружен:"; EN = "Serial cache loaded:" }
    "LogHashLoaded"         = @{ RU = "Кэш хэшей загружен:"; EN = "Hash cache loaded:" }
    "LogHashCreated"        = @{ RU = "Кэш хэшей не найден, создан новый"; EN = "Hash cache not found, created new" }
    "LogPlatformRec"        = @{ RU = "Платформа распознана:"; EN = "Platform recognized:" }
    "LogSkipped"            = @{ RU = "Пропущен (уже добавлен):"; EN = "Skipped (already added):" }
    "LogWarnData"           = @{ RU = "Предупреждение: Файлы данных не найдены для"; EN = "Warning: Data files not found for" }
    "LogAdded"              = @{ RU = "Добавлен:"; EN = "Added:" }
    "LogFormatDef"          = @{ RU = "  Определен формат:"; EN = "  Format defined:" }
    "LogSize"               = @{ RU = "размер:"; EN = "size:" }
    "LogSerial"             = @{ RU = "  Серийный номер:"; EN = "  Serial number:" }
    "LogTotalTable"         = @{ RU = "=== Всего файлов в таблице:"; EN = "=== Total files in table:" }
    "LogStartDl"            = @{ RU = "=== Начало скачивания DAT-файлов ==="; EN = "=== Starting DAT files download ===" }
    "LogDownloaded"         = @{ RU = "Скачан:"; EN = "Downloaded:" }
    "LogErrDl"              = @{ RU = "Ошибка при скачивании"; EN = "Error downloading" }
    "LogDlComplete"         = @{ RU = "Скачивание завершено"; EN = "Download finished" }
    "LogCalcHash"           = @{ RU = "Вычисление SHA1..."; EN = "Calculating SHA1..." }
    "LogExtracting"         = @{ RU = "Извлечение данных для анализа..."; EN = "Extracting data for analysis..." }
    "LogRenamed"            = @{ RU = "Файл переименован:"; EN = "File renamed:" }
    "LogFileNotFound"       = @{ RU = "Ошибка: Файл не найден:"; EN = "Error: File not found:" }
    "LogNoLinkedFiles"      = @{ RU = "Ошибка: Не найдены связанные файлы для"; EN = "Error: Linked files not found for" }
    "LogProcessingItem"     = @{ RU = "Обработка:"; EN = "Processing:" }
    "LogCommand"            = @{ RU = "  Команда:"; EN = "  Command:" }
    "LogSourceFile"         = @{ RU = "  Исходный файл:"; EN = "  Source file:" }
    "LogStartProcess"       = @{ RU = "  Запуск процесса..."; EN = "  Starting process..." }
    "LogProcessRunning"     = @{ RU = "  Процесс выполняется... (прошло:"; EN = "  Process running... (elapsed:" }
    "LogSec"                = @{ RU = "сек)"; EN = "sec)" }
    "LogSuccess"            = @{ RU = "  ✓ Успешно обработано:"; EN = "  ✓ Successfully processed:" }
    "LogOriginalSize"       = @{ RU = "  Исходный размер:"; EN = "  Original size:" }
    "LogFinalSize"          = @{ RU = "  Конечный размер:"; EN = "  Final size:" }
    "LogCompRatio"          = @{ RU = "  Сжатие:"; EN = "  Compression:" }
    "LogTime"               = @{ RU = "  Время обработки:"; EN = "  Processing time:" }
    "LogErrorProcess"       = @{ RU = "  ✗ Ошибка обработки"; EN = "  ✗ Processing error" }
    "LogExitCode"           = @{ RU = "(Код выхода:"; EN = "(Exit code:" }
    "LogOutput"             = @{ RU = "  Вывод:"; EN = "  Output:" }
    "LogErrors"             = @{ RU = "  Ошибки:"; EN = "  Errors:" }
    "LogException"          = @{ RU = "  ✗ Исключение при обработке:"; EN = "  ✗ Exception during processing:" }
    "LogReady"              = @{ RU = "Готов к работе. Перетащите игры в таблицу."; EN = "Ready. Drag and drop games into the table." }
    "LogStarted"            = @{ RU = "=== STORM_CHDMan v2.3.2 запущен ==="; EN = "=== STORM_CHDMan v2.3.2 started ===" }
    
    "DlgSelectFile"         = @{ RU = "Дисковые файлы"; EN = "Disc Files" }
    "DlgAllFiles"           = @{ RU = "Все файлы"; EN = "All Files" }
    
    "StDownload"            = @{ RU = "Скачивание:"; EN = "Downloading:" }
    "StFrom"                = @{ RU = "из"; EN = "of" }
    "StComplete"            = @{ RU = "Завершено"; EN = "Complete" }
}

function T {
    param ([string]$Key)
    if ($LanguageData.ContainsKey($Key)) {
        return $LanguageData[$Key][$script:currentLang]
    }
    return $Key
}

$recognizedPlatforms = @{}
$script:isPaused = $false
$script:isCancelled = $false
$script:activeJobs = @()
$script:hashCache = @{}
$script:filePathsMap = @{}
$script:activeProcesses = @()
$script:customFileNames = @{}
$script:addedFolders = @()
$script:serialCache = @{}

function New-Guid {
    return [guid]::NewGuid().ToString()
}

function Get-ReadableSize {
    param ([uint64]$Size)
    if ($Size -ge 1GB) { "{0:N2} GB" -f ($Size / 1GB) }
    elseif ($Size -ge 1MB) { "{0:N2} MB" -f ($Size / 1MB) }
    else { "{0:N0} KB" -f ($Size / 1KB) }
}

function Sanitize-FileName {
    param ([string]$FileName)
    $invalidChars = [System.IO.Path]::GetInvalidFileNameChars() -join ''
    $sanitized = $FileName -replace "[$([RegEx]::Escape($invalidChars))]", '_'
    return $sanitized
}

function Get-7ZipPath {
    $possiblePaths = @(
        "${env:ProgramFiles}\7-Zip\7z.exe",
        "${env:ProgramFiles(x86)}\7-Zip\7z.exe",
        (Join-Path $PSScriptRoot "7z.exe")
    )
    foreach ($path in $possiblePaths) {
        if (Test-Path -LiteralPath $path) {
            return $path
        }
    }
    return $null
}

function Get-SerialFromImage {
    param ([string]$FilePath)
    
    $txtLog.AppendText("$(T 'LogDebugStart') '$FilePath'`r`n")
    
    
    if ($script:serialCache.ContainsKey($FilePath)) {
        $cachedSerial = $script:serialCache[$FilePath]
        if ($cachedSerial -and $cachedSerial -ne "" -and $cachedSerial -ne (T "MsgSerialNotFound")) {
            $txtLog.AppendText("$(T 'LogCacheHit')`r`n")
            return $cachedSerial
        }
        $txtLog.AppendText("  DEBUG: Кэш содержит '$cachedSerial', повторный поиск...`r`n")
    }
    
    $txtLog.AppendText("$(T 'LogCacheMiss')`r`n")
    
    $serial = ""
    $actualFilePath = $FilePath
    
    try {
        $extension = [System.IO.Path]::GetExtension($FilePath).ToLower()
        $txtLog.AppendText("$(T 'LogExt') '$extension'`r`n")
        
        # Для CUE/GDI получаем первый BIN файл
        if ($extension -eq ".cue" -or $extension -eq ".gdi") {
            $binFiles = @(Get-BinFilesFromCueOrGdi $FilePath)
            $txtLog.AppendText("$(T 'LogBinFound') $($binFiles.Count)`r`n")
            if ($binFiles -and $binFiles.Count -gt 0) {
                $actualFilePath = $binFiles[0]
                $extension = ".bin"
                $txtLog.AppendText("$(T 'LogFirstBin') '$actualFilePath'`r`n")
            }
            else {
                $txtLog.AppendText("$(T 'LogNoBin')`r`n")
                $script:serialCache[$FilePath] = (T "MsgSerialNotFound")
                return (T "MsgSerialNotFound")
            }
        }
        
        # Определяем платформу
        $platform = ""
        if ($recognizedPlatforms.ContainsKey($FilePath)) {
            $platform = $recognizedPlatforms[$FilePath]
            $txtLog.AppendText("$(T 'LogPlatformCache') '$platform'`r`n")
        }
        else {
            $txtLog.AppendText("$(T 'LogPlatformNotFound')`r`n")
        }
        
        $txtLog.AppendText("$(T 'LogPlatformIs') '$platform'`r`n")
        
        # === SEGA SATURN ===
        if ($platform -match "Saturn") {
            $txtLog.AppendText("$(T 'LogProcessing') Sega Saturn...`r`n")
            try {
                $fileStream = [System.IO.File]::OpenRead($actualFilePath)
                # Читаем первые 32KB, чтобы захватить начало данных даже с заголовками
                $buffer = New-Object byte[] 32768
                $fileStream.Position = 0
                $bytesRead = $fileStream.Read($buffer, 0, 32768)
                
                # Пробуем разные смещения для поиска заголовка "SEGA SEGASATURN"
                # Обычно это Offset 0 (ISO) или 16 (BIN MODE1 2352)
                $offsets = @(0, 16)
                
                foreach ($offset in $offsets) {
                    if ($bytesRead -ge ($offset + 256)) {
                        # Ищем сигнатуру "SEGA SEGASATURN" (16 байт) или хотя бы "SEGA"
                        $signature = [System.Text.Encoding]::ASCII.GetString($buffer, $offset, 16)
                        
                        if ($signature -match "SEGA") {
                            $txtLog.AppendText("  DEBUG: Found Saturn signature at offset $offset`r`n")
                            # Product ID обычно по смещению +0x20 (32) от начала заголовка
                            $prodOffset = $offset + 32
                            $productBytes = $buffer[$prodOffset..($prodOffset + 9)]
                            $productNumber = [System.Text.Encoding]::ASCII.GetString($productBytes).Trim()
                            
                            $txtLog.AppendText("  DEBUG: Candidate product string: '$productNumber'`r`n")

                            if ($productNumber -match '([A-Z0-9]{1,3}-\d{4,5}[A-Z0-9]?)') {
                                $serial = $matches[1]
                                break
                            }
                            elseif ($productNumber -match '([A-Z]{1,2}\d{4,5}[A-Z]?)') {
                                $temp = $matches[1]
                                if ($temp -match '^([A-Z]{1,2})(\d{4,5}[A-Z]?)$') {
                                    $serial = "$($matches[1])-$($matches[2])"
                                    break
                                }
                            }
                        }
                    }
                }
                
                $fileStream.Close()
                $fileStream.Dispose()
            }
            catch {
                $txtLog.AppendText("$(T 'LogGeneralError') Saturn: $_`r`n")
            }
        }
        
        # === SEGA CD (MEGA-CD) ===
        elseif ($platform -match "Mega.CD" -or $platform -match "Sega CD") {
            $txtLog.AppendText("$(T 'LogProcessing') Sega CD / Mega CD...`r`n")
            try {
                $fileStream = [System.IO.File]::OpenRead($actualFilePath)
                $buffer = New-Object byte[] 32768
                $fileStream.Position = 0
                $bytesRead = $fileStream.Read($buffer, 0, 32768)
                
                # Пробуем разные смещения. SYSTEM ID "SEGADISCSYSTEM" должен быть в начале.
                $offsets = @(0, 16)

                foreach ($offset in $offsets) {
                    if ($bytesRead -ge ($offset + 0x200)) {
                        # Пытаемся найти сигнатуру (обычно первые 14 байт)
                        $signature = [System.Text.Encoding]::ASCII.GetString($buffer, $offset, 14)
                        
                        if ($signature -match "SEGA") {
                            $txtLog.AppendText("  DEBUG: Found SegaCD signature at offset $offset`r`n")
                            
                            # Product ID по смещению 0x183 (или 0x180) от начала блока
                            # Обычно 0x183 в заголовке
                            $prodOffset = $offset + 0x180
                            $productBytes = $buffer[$prodOffset..($prodOffset + 15)]
                            $productCode = [System.Text.Encoding]::ASCII.GetString($productBytes).Trim()
                             
                            $txtLog.AppendText("  DEBUG: Candidate product string (1): '$productCode'`r`n")

                            if ($productCode -match '([A-Z]{1,3}-\d{4,6})') {
                                $serial = $matches[1]
                                break
                            }
                            elseif ($productCode -match '(\d{3}-\d{4})') {
                                $serial = $matches[1]
                                break
                            }
                            
                            # Пробуем +3 байта (старый вариант)
                            $prodOffset2 = $offset + 0x183
                            $productBytes2 = $buffer[$prodOffset2..($prodOffset2 + 15)]
                            $productCode2 = [System.Text.Encoding]::ASCII.GetString($productBytes2).Trim()
                            
                            $txtLog.AppendText("  DEBUG: Candidate product string (2): '$productCode2'`r`n")
                            
                            if ($productCode2 -match '([A-Z]{1,3}-\d{4,6})') {
                                $serial = $matches[1]
                                break
                            }
                        }
                    }
                }
                
                $fileStream.Close()
                $fileStream.Dispose()
            }
            catch {
                $txtLog.AppendText("$(T 'LogGeneralError') SegaCD: $_`r`n")
            }
        }
        
        # === 3DO ===
        elseif ($platform -match "3DO") {
            $serial = (T "LogNotSupported").Replace("  DEBUG: ", "")
        }
        
        # === PLAYSTATION 1/2 ===
        elseif ($platform -match "PlayStation" -or $platform -match "Sony") {
            $txtLog.AppendText("$(T 'LogProcessing') PlayStation...`r`n")
            $sevenZip = Get-7ZipPath
            
            if ($sevenZip -and ($extension -eq ".iso" -or $extension -eq ".bin")) {
                $txtLog.AppendText("$(T 'Log7ZipFound')`r`n")
                try {
                    $tempDir = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.IO.Path]::GetRandomFileName())
                    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
                    
                    $psi = New-Object System.Diagnostics.ProcessStartInfo
                    $psi.FileName = $sevenZip
                    $psi.Arguments = "e `"$actualFilePath`" -o`"$tempDir`" SYSTEM.CNF -y -r"
                    $psi.UseShellExecute = $false
                    $psi.CreateNoWindow = $true
                    $psi.RedirectStandardOutput = $true
                    $psi.RedirectStandardError = $true
                    
                    $process = [System.Diagnostics.Process]::Start($psi)
                    $process.WaitForExit(5000)
                    
                    $systemCnfPath = Join-Path $tempDir "SYSTEM.CNF"
                    
                    if (Test-Path -LiteralPath $systemCnfPath) {
                        $content = Get-Content -LiteralPath $systemCnfPath -Raw -Encoding ASCII
                        $txtLog.AppendText("$(T 'LogSysCnfFound')`r`n")
                        
                        if ($content -match 'BOOT\s*=\s*cdrom[0-9]*:\\?([A-Z]{4})[_\.](\d{3})\.?(\d{2})') {
                            $serial = "$($matches[1])-$($matches[2])$($matches[3])"
                        }
                        elseif ($content -match '([A-Z]{4})[_\.](\d{3})\.?(\d{2})') {
                            $serial = "$($matches[1])-$($matches[2])$($matches[3])"
                        }
                    }
                    
                    Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
                }
                catch {
                    $txtLog.AppendText("$(T 'Log7ZipError') $_`r`n")
                }
            }
            
            # Fallback: прямое чтение
            if (-not $serial -and ($extension -eq ".iso" -or $extension -eq ".bin")) {
                $txtLog.AppendText("$(T 'LogFallbackRead')`r`n")
                try {
                    $fileStream = [System.IO.File]::OpenRead($actualFilePath)
                    $sectorSize = 2352  # MODE2/2352
                    $dataOffset = 24    # Смещение данных
                    $buffer = New-Object byte[] $sectorSize
                    $searchLimit = [Math]::Min($fileStream.Length, 50MB)
                    $position = 0
                    
                    while ($position -lt $searchLimit -and -not $serial) {
                        # Отзывчивость интерфейса
                        [System.Windows.Forms.Application]::DoEvents()
                        
                        $fileStream.Position = $position
                        $bytesRead = $fileStream.Read($buffer, 0, $buffer.Length)
                        
                        if ($bytesRead -eq 0) { break }
                        
                        # Читаем данные с учётом смещения для MODE2/2352
                        $readOffset = if ($bytesRead -ge $sectorSize) { $dataOffset } else { 0 }
                        $readLength = if ($bytesRead -ge $sectorSize) { 2048 } else { $bytesRead }
                        $text = [System.Text.Encoding]::ASCII.GetString($buffer, $readOffset, $readLength)
                        
                        # Ищем PSX серийники: BOOT = cdrom:\SLUS_008.24;1
                        if ($text -match 'BOOT\s*=\s*cdrom[0-9]*:[\\\/]?([A-Z]{4})[_\.\-](\d{3})[\.\-](\d{2})') {
                            $serial = "$($matches[1])-$($matches[2])$($matches[3])"
                            $txtLog.AppendText("$(T 'LogSerialDirect') $serial (BOOT match)`r`n")
                            break
                        }
                        # Поиск PSX серийников: SLUS_008.24, SCUS-942.01
                        elseif ($text -match '(S[CL][EUP][SAP])[_\.\-](\d{3})[\.\-](\d{2})') {
                            $serial = "$($matches[1])-$($matches[2])$($matches[3])"
                            $txtLog.AppendText("$(T 'LogSerialDirect') $serial (Raw match)`r`n")
                            break
                        }
                        
                        # DEBUG: Если нашли похожее на серийник, но regex не сработал - пишем в лог
                        if ($text -match '(SLUS|SCUS|SLES|SCES|SLPM|SIPS|ESPM)') {
                            $txtLog.AppendText("  DEBUG: Найден кандидат (raw): " + $matches[0] + " в позиции $position`r`n")
                            # Попытка вычитать контекст
                            $contextStart = [Math]::Max(0, $text.IndexOf($matches[0]) - 10)
                            $contextLen = [Math]::Min($text.Length - $contextStart, 50)
                            $sub = $text.Substring($contextStart, $contextLen) -replace "`r", " " -replace "`n", " "
                            $txtLog.AppendText("  DEBUG: Контекст: ...$sub...`r`n")
                        }
                        
                        $position += $sectorSize
                    }
                    
                    $fileStream.Close()
                    $fileStream.Dispose()
                }
                catch {
                    $txtLog.AppendText("$(T 'LogGeneralError') PlayStation direct read: $_`r`n")
                }
            }
        }
    }
    catch {
        $txtLog.AppendText("$(T 'LogGeneralError') $_`r`n")
    }
    
    # === УНИВЕРСАЛЬНЫЙ FALLBACK для CUE/BIN без платформы ===
    if ((-not $serial -or $serial -eq "") -and $actualFilePath -match "\.bin$") {
        $txtLog.AppendText("  DEBUG: Универсальный поиск PSX серийника...`r`n")
        try {
            $fileStream = [System.IO.File]::OpenRead($actualFilePath)
            $sectorSize = 2352
            $dataOffset = 24
            $buffer = New-Object byte[] $sectorSize
            $searchLimit = [Math]::Min($fileStream.Length, 100MB)
            $position = 0
            
            while ($position -lt $searchLimit -and (-not $serial -or $serial -eq "")) {
                # Отзывчивость интерфейса
                [System.Windows.Forms.Application]::DoEvents()
                
                $fileStream.Position = $position
                $bytesRead = $fileStream.Read($buffer, 0, $sectorSize)
                
                if ($bytesRead -eq 0) { break }
                
                $readOffset = if ($bytesRead -ge $sectorSize) { $dataOffset } else { 0 }
                $readLength = if ($bytesRead -ge $sectorSize) { 2048 } else { $bytesRead }
                $text = [System.Text.Encoding]::ASCII.GetString($buffer, $readOffset, $readLength)
                
                # Ищем паттерны PSX серийников в SYSTEM.CNF
                if ($text -match 'BOOT\s*=\s*cdrom[0-9]*:\\?([A-Z]{4})[_\.](\d{3})\.?(\d{2})') {
                    $serial = "$($matches[1])-$($matches[2])$($matches[3])"
                    $txtLog.AppendText("  DEBUG: Найден PSX серийник: $serial`r`n")
                    break
                }
                
                $position += $sectorSize
            }
            
            $fileStream.Close()
            $fileStream.Dispose()
        }
        catch {
            $txtLog.AppendText("$(T 'LogGeneralError') Universal PSX scan: $_`r`n")
        }
    }
    
    if (-not $serial) {
        $serial = (T "MsgSerialNotFound")
    }
    
    $txtLog.AppendText("$(T 'LogFinalSerial') '$serial'`r`n")
    
    if (-not $serial -or $serial -eq "") {
        $serial = (T "MsgSerialNotFound")
        # Кэшируем "Не найден", чтобы при повторном поиске умный кэш мог решить, искать заново или нет
        $script:serialCache[$FilePath] = $serial
    }
    else {
        $script:serialCache[$FilePath] = $serial
        $txtLog.AppendText("  DEBUG: Серийник успешно найден: $serial`r`n")
    }
    
    return $serial
}

function Save-SerialCache {
    $script:serialCache | ConvertTo-Json -Depth 10 | Out-File -FilePath (Join-Path $PSScriptRoot "serials.json") -Encoding UTF8 -Force
}

function Load-SerialCache {
    $serialFile = Join-Path $PSScriptRoot "serials.json"
    if (Test-Path $serialFile) {
        try {
            $jsonContent = Get-Content $serialFile -Encoding UTF8 -Raw | ConvertFrom-Json
            $script:serialCache = @{}
            foreach ($property in $jsonContent.PSObject.Properties) {
                $script:serialCache[$property.Name] = $property.Value
            }
            $txtLog.AppendText("$(T 'LogCacheLoaded') $($script:serialCache.Count)`r`n")
        }
        catch {
            $txtLog.AppendText("Error loading serial cache: $_`r`n")
            $script:serialCache = @{}
        }
    }
    else {
        $script:serialCache = @{}
    }
}

function Kill-AllCHDManProcesses {
    try {
        $chdmanProcesses = Get-Process | Where-Object { $_.ProcessName -eq "chdman" }
        foreach ($proc in $chdmanProcesses) {
            try {
                $proc.Kill()
                $proc.WaitForExit(2000)
            }
            catch { }
        }
    }
    catch { }
}

function Save-Settings {
    $columnWidths = @{}
    for ($i = 0; $i -lt $dataGridView.Columns.Count; $i++) {
        $columnWidths["Column$i"] = $dataGridView.Columns[$i].Width
    }
    
    $settings = @{
        Language          = $cmbLanguage.SelectedItem 
        Theme             = $diskTheme.SelectedItem
        Cores             = $diskCores.SelectedItem
        Compression       = $diskCompression.SelectedItem
        CDHunk            = $diskCDHunk.SelectedItem
        DVDHunk           = $diskDVDHunk.SelectedItem
        Force             = $chkForce.Checked
        Recognition       = $chkRecognition.Checked
        AetherSX2         = $chkAetherSX2.Checked
        TextNotification  = $chkTextNotification.Checked
        SoundNotification = $chkSoundNotification.Checked
        OutputFolder      = $txtOutput.Text
        FormWidth         = $form.Width
        FormHeight        = $form.Height
        FormX             = $form.Location.X
        FormY             = $form.Location.Y
        ColumnWidths      = $columnWidths
    }
    $settings | ConvertTo-Json -Depth 10 | Out-File -FilePath (Join-Path $PSScriptRoot "settings.json") -Encoding UTF8 -Force
}

function Load-Settings {
    $settingsFile = Join-Path $PSScriptRoot "settings.json"
    try {
        if (Test-Path $settingsFile) {
            $settings = Get-Content $settingsFile -Encoding UTF8 | ConvertFrom-Json
            if ($settings.Language -and $cmbLanguage.Items -contains $settings.Language) { 
                $cmbLanguage.SelectedItem = $settings.Language
                $script:currentLang = if ($settings.Language -eq "Русский") { "RU" } else { "EN" }
            }
            if ($diskTheme.Items -contains $settings.Theme) { $diskTheme.SelectedItem = $settings.Theme }
            if ($diskCores.Items -contains $settings.Cores) { $diskCores.SelectedItem = $settings.Cores }
            if ($diskCompression.Items -contains $settings.Compression) { $diskCompression.SelectedItem = $settings.Compression }
            if ($diskCDHunk -and $diskCDHunk.Items -contains $settings.CDHunk) { $diskCDHunk.SelectedItem = $settings.CDHunk }
            if ($diskDVDHunk.Items -contains $settings.DVDHunk) { $diskDVDHunk.SelectedItem = $settings.DVDHunk }
            $chkForce.Checked = $settings.Force
            $chkRecognition.Checked = $settings.Recognition
            $chkAetherSX2.Checked = $settings.AetherSX2
            $chkTextNotification.Checked = $settings.TextNotification
            $chkSoundNotification.Checked = $settings.SoundNotification
            if ($settings.OutputFolder) { $txtOutput.Text = $settings.OutputFolder }
            if ($settings.FormWidth -and $settings.FormHeight) {
                $form.Size = New-Object System.Drawing.Size($settings.FormWidth, $settings.FormHeight)
            }
            if ($null -ne $settings.FormX -and $null -ne $settings.FormY) {
                $form.StartPosition = "Manual"
                $form.Location = New-Object System.Drawing.Point($settings.FormX, $settings.FormY)
            }
            if ($settings.ColumnWidths) {
                for ($i = 0; $i -lt $dataGridView.Columns.Count; $i++) {
                    if ($settings.ColumnWidths."Column$i") {
                        $dataGridView.Columns[$i].Width = $settings.ColumnWidths."Column$i"
                    }
                }
            }
        }
    }
    catch {
        $txtLog.AppendText("Error loading settings: $_`r`n")
    }
}

function Load-HashCache {
    $hashFile = Join-Path $PSScriptRoot "hashes.json"
    if (Test-Path $hashFile) {
        try {
            $jsonContent = Get-Content $hashFile -Encoding UTF8 -Raw | ConvertFrom-Json
            $script:hashCache = @{}
            foreach ($property in $jsonContent.PSObject.Properties) {
                $script:hashCache[$property.Name] = $property.Value
            }
            $txtLog.AppendText("$(T 'LogHashLoaded') $($script:hashCache.Count)`r`n")
        }
        catch {
            $txtLog.AppendText("Error loading hash cache: $_`r`n")
            $script:hashCache = @{}
        }
    }
    else {
        $script:hashCache = @{}
        $txtLog.AppendText("$(T 'LogHashCreated')`r`n")
    }
}

function Save-HashCache {
    try {
        $cleanCache = @{}
        foreach ($key in $script:hashCache.Keys) {
            $cleanCache[$key] = $script:hashCache[$key].ToString()
        }
        $cleanCache | ConvertTo-Json -Depth 10 | Out-File -FilePath (Join-Path $PSScriptRoot "hashes.json") -Encoding UTF8 -Force
    }
    catch { }
}
function Get-BinFilesFromCueOrGdi {
    param ([string]$FilePath)
    $fileDir = Split-Path $FilePath -Parent
    $fileContent = Get-Content -LiteralPath $FilePath -ErrorAction SilentlyContinue
    if (-not $fileContent) {
        return @()
    }
    $binFiles = @()
    if ($FilePath -match "\.cue$|\.mds$|\.ccd$|\.toc$") {
        foreach ($line in $fileContent) {
            # Ищем строки вида FILE "filename.bin" BINARY
            if ($line -match 'FILE\s+"(.+?)"') {
                $binFileName = $matches[1]
                $binFile = Join-Path $fileDir $binFileName
                if (Test-Path -LiteralPath $binFile) {
                    $binFiles += $binFile
                }
            }
        }
    }
    elseif ($FilePath -match "\.gdi$") {
        foreach ($line in $fileContent) {
            if ($line -match '^\s*\d+\s+\d+\s+\d+\s+\d+\s+"?(.+?)"?\s+\d+\s*$') {
                $binFileName = $matches[1].Trim('"')
                $binFile = Join-Path $fileDir $binFileName
                if (Test-Path -LiteralPath $binFile) {
                    $binFiles += $binFile
                }
            }
        }
    }
    return $binFiles
}

function Get-FirstDataTrack {
    param ([string]$FilePath)
    
    $fileDir = Split-Path $FilePath -Parent
    $fileContent = Get-Content -LiteralPath $FilePath -ErrorAction SilentlyContinue
    
    if (-not $fileContent) {
        return $null
    }
    
    if ($FilePath -match "\.cue$") {
        # Приоритет: ищем первый трек, помеченный как BINARY
        foreach ($line in $fileContent) {
            if ($line -match 'FILE\s+"([^"]+)"\s+BINARY') {
                $binFileName = $matches[1]
                $binFile = Join-Path $fileDir $binFileName
                if (Test-Path -LiteralPath $binFile) {
                    return $binFile
                }
            }
        }
        
        # Если не нашли явно, берем первый попавшийся файл
        $binFiles = @(Get-BinFilesFromCueOrGdi $FilePath)
        if ($binFiles -and $binFiles.Count -gt 0) {
            return $binFiles[0]
        }
    }
    
    elseif ($FilePath -match "\.gdi$") {
        $binFiles = @(Get-BinFilesFromCueOrGdi $FilePath)
        if ($binFiles -and $binFiles.Count -gt 0) {
            return $binFiles[0]
        }
    }
    
    return $null
}

function Get-PlatformFromDAT {
    param ([string]$FilePath)
    if (-not $chkRecognition.Checked) { 
        return ""
    }
    if ($recognizedPlatforms.ContainsKey($FilePath)) {
        return $recognizedPlatforms[$FilePath]
    }
    
    $datsFolder = Join-Path $PSScriptRoot "DATs"
    if (-not (Test-Path -LiteralPath $datsFolder)) { 
        $txtLog.AppendText("$(T 'LogWarnData') DATs`r`n")
        return ""
    }
    
    $hashes = @()
    # Логика хэширования: для CUE/GDI берем хэш БИНАРНЫХ файлов, а не самого текстового файла
    if ($FilePath -match "\.cue$|\.gdi$|\.mds$|\.ccd$|\.toc$") {
        $binFiles = @(Get-BinFilesFromCueOrGdi $FilePath)
        if (-not $binFiles) {
            return ""
        }
        # Считаем хэш только первого бинарника для скорости (как правило достаточно для Redump)
        # Или всех, если нужно точное совпадение (здесь берем все для надежности поиска в DAT)
        foreach ($binFile in $binFiles) {
            try {
                if ($script:hashCache.ContainsKey($binFile)) {
                    $hash = $script:hashCache[$binFile]
                }
                else {
                    $hash = Get-SHA1-Responsive $binFile
                    $script:hashCache[$binFile] = $hash
                    Save-HashCache
                }
                $hashes += $hash
            }
            catch {
                $txtLog.AppendText("$(T 'LogGeneralError') SHA1 ${binFile}: $_`r`n")
            }
        }
    }
    elseif ($FilePath -match "\.iso$|\.nrg$|\.chd$|\.mdf$|\.img$") {
        try {
            if ($script:hashCache.ContainsKey($FilePath)) {
                $hash = $script:hashCache[$FilePath]
            }
            else {
                $hash = Get-SHA1-Responsive $FilePath
                $script:hashCache[$FilePath] = $hash
                Save-HashCache
            }
            $hashes += $hash
        }
        catch {
            $txtLog.AppendText("$(T 'LogGeneralError') SHA1 ${FilePath}: $_`r`n")
        }
    }
    
    $priorityDatFiles = @("psx.dat", "ps2.dat")
    $datFiles = Get-ChildItem -LiteralPath $datsFolder -Filter "*.dat" -File -ErrorAction SilentlyContinue
    $priorityDats = $datFiles | Where-Object { $priorityDatFiles -contains $_.Name }
    $otherDats = $datFiles | Where-Object { $priorityDatFiles -notcontains $_.Name } | Sort-Object Name
    $datFiles = $priorityDats + $otherDats
    
    foreach ($datFile in $datFiles) {
        try {
            # Оптимизация: читаем как текст и ищем хэш перед загрузкой XML (быстрее)
            $content = Get-Content $datFile.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            $foundInDat = $false
            foreach ($h in $hashes) {
                if ($content -match $h) {
                    $foundInDat = $true
                    break
                }
            }
            
            if ($foundInDat) {
                $datName = [System.IO.Path]::GetFileNameWithoutExtension($datFile.Name)
                $platform = $datName -replace " - Datfile.*", ""
                # Исключаем DOS игры, которые часто совпадают по CUE
                if ($FilePath -match "\.cue$" -and $platform -eq "IBM - PC compatible") {
                    continue
                }
                 
                $recognizedPlatforms[$FilePath] = $platform
                $txtLog.AppendText("$(T 'LogPlatformRec') $platform - $(Split-Path $FilePath -Leaf)`r`n")
                return $platform
            }
        }
        catch {
            $txtLog.AppendText("$(T 'LogGeneralError') DAT ${datFile}: $_`r`n")
        }
    }
    $recognizedPlatforms[$FilePath] = ""
    return ""
}

function Get-GameFolderName {
    param ([string]$FilePath)
    $parentFolder = Split-Path $FilePath -Parent
    if ($parentFolder -eq $PSScriptRoot -or $parentFolder -eq "") {
        return [System.IO.Path]::GetFileNameWithoutExtension($FilePath)
    }
    return [System.IO.Path]::GetFileName($parentFolder)
}

function Get-FormatCategory {
    param ([string]$Platform, [uint64]$FileSize, [string]$Extension)
    
    if ($Extension -eq ".chd") {
        if ($FileSize -lt 800MB) { return "CHD CD-ROM" } else { return "CHD DVD-ROM" }
    }
    if ($Platform -eq "Sega - Dreamcast") { return "CD-ROM" }
    if ($Platform -eq "Sony - PlayStation 2" -and $chkAetherSX2.Checked) {
        if ($FileSize -lt 800MB) { return "CD-ROM" } else { return "DVD-ROM" }
    }
    if ($FileSize -lt 800MB) { return "CD-ROM" } else { return "DVD-ROM" }
}

function Get-SHA1-Responsive {
    param ([string]$FilePath)
    
    $sha1 = [System.Security.Cryptography.SHA1]::Create()
    $stream = [System.IO.File]::OpenRead($FilePath)
    $buffer = New-Object byte[] 1048576 # 1MB buffer
    $position = 0
    $totalLength = $stream.Length
    
    # Update Status
    $oldStatus = $lblProcessStatus.Text
    $lblProcessStatus.Text = "$(T 'LogCalcHash') $(Split-Path $FilePath -Leaf)"
    $lblProcessStatus.Visible = $true
    
    # Init Progress (reusing process bar temporarily or creating a visual effect)
    $progressProcess.Style = "Marquee"
    $progressProcess.Visible = $true
    
    try {
        do {
            $bytesRead = $stream.Read($buffer, 0, $buffer.Length)
            if ($bytesRead -gt 0) {
                $res = $sha1.TransformBlock($buffer, 0, $bytesRead, $buffer, 0)
            }
            $position += $bytesRead
            
            # Keep UI responsive
            [System.Windows.Forms.Application]::DoEvents()
            
        } while ($bytesRead -gt 0)
        
        $sha1.TransformFinalBlock($buffer, 0, 0) | Out-Null
        $hashBytes = $sha1.Hash
        $hashString = [BitConverter]::ToString($hashBytes).Replace("-", "").ToLower()
        return $hashString
    }
    catch {
        return "Error"
    }
    finally {
        $stream.Close()
        $stream.Dispose()
        $sha1.Dispose()
        
        # Restore Status
        $lblProcessStatus.Text = $oldStatus
        $progressProcess.Style = "Continuous"
    }
}

function Get-CHD-Info {
    param ([string]$FilePath)
    
    $chdInfo = @{ SHA1 = ""; Serial = "" }
    
    # 1. Get SHA1 from 'chdman info'
    # NOTE: chdman info shows 'SHA1' which is usually the compressed file hash in older versions, 
    # or 'Data SHA1' in newer. We try to find the most relevant one.
    # However, for accuracy with Redump DATs (which track BIN SHA1), 'Data SHA1' is what we need if available.
    
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $chdmanExe
    $psi.Arguments = "info -i `"$FilePath`""
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.CreateNoWindow = $true
    
    $process = [System.Diagnostics.Process]::Start($psi)
    $output = $process.StandardOutput.ReadToEnd()
    $process.WaitForExit()
    
    # Parse SHA1
    if ($output -match "Data SHA1:\s*([a-fA-F0-9]{40})") {
        $chdInfo.SHA1 = $matches[1].ToLower()
    }
    elseif ($output -match "SHA1:\s*([a-fA-F0-9]{40})") {
        $chdInfo.SHA1 = $matches[1].ToLower()
    }
    
    # 2. Get Serial by extracting first 2MB
    # We use a temp file
    $tempFile = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "storm_temp.bin")
    
    $lblProcessStatus.Text = "$(T 'LogExtracting') $(Split-Path $FilePath -Leaf)"
    $lblProcessStatus.Visible = $true
    [System.Windows.Forms.Application]::DoEvents()
    
    try {
        if (Test-Path $tempFile) { Remove-Item $tempFile -Force }
        
        $psiExtract = New-Object System.Diagnostics.ProcessStartInfo
        $psiExtract.FileName = $chdmanExe
        # Extract first 2MB (2097152 bytes)
        $psiExtract.Arguments = "extractraw -i `"$FilePath`" -o `"$tempFile`" -isb 0 -ib 2097152 -f"
        $psiExtract.UseShellExecute = $false
        $psiExtract.CreateNoWindow = $true
        
        $procExtract = [System.Diagnostics.Process]::Start($psiExtract)
        $procExtract.WaitForExit()
        
        if (Test-Path $tempFile) {
            $chdInfo.Serial = Get-SerialFromImage $tempFile
            Remove-Item $tempFile -Force
        }
    }
    catch {
        $txtLog.AppendText("  DEBUG: CHD Extract Error: $_`r`n")
    }
    finally {
        $lblProcessStatus.Visible = $false
    }
    
    return $chdInfo
}

# --- ОБНОВЛЕННАЯ ФУНКЦИЯ UPDATE-GRID (DRAG & DROP) ---
function Update-Grid {
    param ([array]$InputFiles, [bool]$ClearGrid = $true)
    
    if (-not $InputFiles) { return }
    
    $allFiles = @()
    $individualFileMap = @{}

    # Рекурсивный поиск файлов в перетаскиваемых папках
    # Рекурсивный поиск файлов с поддержкой DoEvents
    foreach ($item in $InputFiles) {
        if (-not (Test-Path -LiteralPath $item)) { continue }
        
        if (Test-Path -LiteralPath $item -PathType Container) {
            # Итеративный обход вместо блокирующего Get-ChildItem -Recurse
            $stack = New-Object System.Collections.Generic.Stack[string]
            $stack.Push($item)
             
            while ($stack.Count -gt 0) {
                $currentDir = $stack.Pop()
                [System.Windows.Forms.Application]::DoEvents()
                 
                try {
                    # Файлы
                    $filesInDir = [System.IO.Directory]::GetFiles($currentDir) 
                    foreach ($f in $filesInDir) {
                        if ($f -match "\.(iso|cue|gdi|mds|mdf|nrg|chd|ccd|img|toc)$") {
                            $allFiles += $f
                        }
                    }
                     
                    # Подпапки
                    $subDirs = [System.IO.Directory]::GetDirectories($currentDir)
                    foreach ($d in $subDirs) {
                        $stack.Push($d)
                    }
                }
                catch {
                    $txtLog.AppendText("$(T 'LogGeneralError') Access '$currentDir': $_`r`n")
                }
            }
        }
        elseif ($item -match "\.(iso|cue|gdi|mds|mdf|nrg|chd|ccd|img|toc)$") {
            $allFiles += $item
            $individualFileMap[$item] = $true
        }
    }
    
    if ($allFiles.Count -eq 0) { 
        $txtLog.AppendText("$(T 'MsgNoFiles')`r`n")
        return 
    }
    
    $files = $allFiles
    
    $txtLog.AppendText("`r`n$(T 'LogStartProcessing')`r`n")
    $txtLog.AppendText("$(T 'LogBinFound') $($files.Count)`r`n")
    
    if ($ClearGrid) {
        $dataGridView.Rows.Clear()
        $recognizedPlatforms.Clear()
        $script:filePathsMap.Clear()
        $script:customFileNames.Clear()
    }
    
    $processedFiles = @{}
    
    # Проверка на дубликаты
    $existingFiles = @()
    foreach ($row in $dataGridView.Rows) {
        $displayName = $row.Cells[0].Value
        if ($script:filePathsMap.ContainsKey($displayName)) {
            $existingFiles += $script:filePathsMap[$displayName]
        }
    }
    
    foreach ($file in $files) {
        if ($existingFiles -contains $file) {
            $txtLog.AppendText("$(T 'LogSkipped') $(Split-Path $file -Leaf)`r`n")
            continue
        }
        
        # Отзывчивость интерфейса
        [System.Windows.Forms.Application]::DoEvents()

        
        # Обработка CUE/GDI и т.д.
        if ($file -match "\.cue$|\.gdi$|\.mds$|\.ccd$|\.toc$") {
            if (-not $processedFiles.ContainsKey($file)) {
                $processedFiles[$file] = $true
                $fileSize = 0
                $binFiles = @(Get-BinFilesFromCueOrGdi $file)
                $fileCount = 1 + $binFiles.Count
                
                # Исключаем BIN файлы из списка обработки, если они уже есть в списке $files
                # чтобы не добавлять их отдельной строкой
                foreach ($b in $binFiles) { $processedFiles[$b] = $true }
                
                foreach ($binFile in $binFiles) {
                    $fileSize += (Get-Item -LiteralPath $binFile).Length
                }
                
                if (-not $binFiles) {
                    $txtLog.AppendText("$(T 'LogWarnData') ${file}`r`n")
                    continue
                }
                
                if ($individualFileMap.ContainsKey($file) -and $individualFileMap[$file]) {
                    $fileName = [System.IO.Path]::GetFileNameWithoutExtension($file)
                }
                else {
                    $fileName = Get-GameFolderName $file
                }
                
                $uniqueFileName = $fileName
                $counter = 1
                while ($script:filePathsMap.ContainsKey($uniqueFileName)) {
                    $uniqueFileName = "${fileName}_${counter}"
                    $counter++
                }
                
                $txtLog.AppendText("$(T 'LogAdded') $uniqueFileName ($fileCount files, $(Get-ReadableSize $fileSize))`r`n")
                
                $platform = if ($chkRecognition.Checked) { Get-PlatformFromDAT $file } else { "" }
                $extension = [System.IO.Path]::GetExtension($file).ToLower()
                $format = Get-FormatCategory $platform $fileSize $extension
                $txtLog.AppendText("$(T 'LogFormatDef') $format ($(T 'LogSize') $(Get-ReadableSize $fileSize))`r`n")
                
                # SHA1 берем от ПЕРВОГО BIN файла
                $sha1 = ""
                try {
                    if ($binFiles.Count -gt 0) {
                        $targetBin = $binFiles[0]
                        $txtLog.AppendText("  DEBUG: Вычисление SHA1 для: $targetBin`r`n")
                        
                        $cachedHash = $null
                        if ($script:hashCache.ContainsKey($targetBin)) { 
                            $cachedHash = $script:hashCache[$targetBin]
                        }
                        
                        if ($cachedHash -and $cachedHash -notmatch "Error" -and $cachedHash -ne "") {
                            $sha1 = $cachedHash
                            $txtLog.AppendText("  DEBUG: SHA1 из кэша: $sha1`r`n")
                        }
                        else { 
                            $hash = Get-SHA1-Responsive $targetBin
                            $script:hashCache[$targetBin] = $hash
                            Save-HashCache
                            $sha1 = $hash
                            $txtLog.AppendText("  DEBUG: SHA1 вычислен: $sha1`r`n")
                        }
                    }
                    else { 
                        $sha1 = "No BIN"
                        $txtLog.AppendText("  DEBUG: BIN файлы не найдены`r`n")
                    }
                }
                catch { 
                    $sha1 = "Error: $_"
                    $txtLog.AppendText("  DEBUG: Ошибка SHA1: $_`r`n")
                }
                
                $serial = Get-SerialFromImage $file
                
                # Авто-коррекция платформы если найден PSX серийник
                if ($serial -match '^S[CL][EUP][SAP][\-_]\d+' -and $platform -ne "Sony - PlayStation") {
                    $platform = "Sony - PlayStation"
                    $txtLog.AppendText("  DEBUG: Платформа скорректирована на Sony - PlayStation по серийнику $serial`r`n")
                    $format = Get-FormatCategory $platform $fileSize $extension
                }
                
                # Если серийник не найден (или вернулся T "MsgSerialNotFound"), то оставляем как есть
                # В Update-Grid мы уже получаем готовый текст
                
                $script:filePathsMap[$uniqueFileName] = $file
                $dataGridView.Rows.Add($uniqueFileName, $fileCount, $platform, $format, (T "StatusAdded"), (Get-ReadableSize $fileSize), "", "", $sha1, $serial)
            }
        } 
        # Обработка ISO/CHD и т.д.
        elseif ($file -match "\.iso$|\.nrg$|\.chd$|\.mdf$|\.img$") {
            if (-not $processedFiles.ContainsKey($file)) {
                $processedFiles[$file] = $true
                $fileSize = (Get-Item -LiteralPath $file).Length
                
                if ($individualFileMap.ContainsKey($file) -and $individualFileMap[$file]) {
                    $fileName = [System.IO.Path]::GetFileNameWithoutExtension($file)
                }
                else {
                    $fileName = Get-GameFolderName $file
                }
                
                $uniqueFileName = $fileName
                $counter = 1
                while ($script:filePathsMap.ContainsKey($uniqueFileName)) {
                    $uniqueFileName = "${fileName}_${counter}"
                    $counter++
                }
                
                $txtLog.AppendText("$(T 'LogAdded') $uniqueFileName ($(Get-ReadableSize $fileSize))`r`n")
                
                $platform = if ($chkRecognition.Checked) { Get-PlatformFromDAT $file } else { "" }
                $extension = [System.IO.Path]::GetExtension($file).ToLower()
                $format = Get-FormatCategory $platform $fileSize $extension
                
                $sha1 = try {
                    $cachedHash = $null
                    if ($script:hashCache.ContainsKey($file)) { 
                        $cachedHash = $script:hashCache[$file]
                    }
                    
                    if ($cachedHash -and $cachedHash -notmatch "Error" -and $cachedHash -ne "") {
                        $cachedHash
                    }
                    else {
                        if ($extension -eq ".chd") {
                            $chData = Get-CHD-Info $file
                            $hash = $chData.SHA1
                             
                            # Если chdman не вернул SHA1, считаем хэш файла
                            if (-not $hash) {
                                $hash = Get-SHA1-Responsive $file
                            }
                        }
                        else {
                            $hash = Get-SHA1-Responsive $file
                        }
                        $script:hashCache[$file] = $hash
                        Save-HashCache
                        $hash
                    }
                }
                catch { "Error SHA1" }
                
                $serial = ""
                # Пробуем достать Serial
                # Если это CHD, мы могли уже его получить выше, но по логике мы разделили это
                # Чтобы не вызывать extractraw дважды, лучше оптимизировать...
                
                # Однако Get-CHD-Info делает и то и другое.
                # Давайте оптимизируем: если расширение .chd, вызовем Get-CHD-Info один раз
                
                if ($extension -eq ".chd") {
                    # Проверяем кэш серийников
                    $cachedSerial = $null
                    if ($script:serialCache.ContainsKey($file)) {
                        $cachedSerial = $script:serialCache[$file]
                    }
                    
                    if ($cachedSerial -and $cachedSerial -ne "" -and $cachedSerial -ne (T "MsgSerialNotFound")) {
                        $serial = $cachedSerial
                    }
                    else {
                        # Если не вызывали выше (например SHA1 был в кэше), то вызываем сейчас
                        # Но у нас нет сохраненного результата Get-CHD-Info если мы взяли SHA1 из кэша
                        # Придется вызвать, если нужно.
                        
                        $chData = Get-CHD-Info $file
                        # Обновляем SHA1 если его не было
                        if ($sha1 -eq "" -or $sha1 -eq "Error SHA1") {
                            $sha1 = $chData.SHA1
                            if ($sha1) {
                                $script:hashCache[$file] = $sha1
                                Save-HashCache
                            }
                        }
                        $serial = $chData.Serial
                    }
                }
                else {
                    $serial = Get-SerialFromImage $file
                }
                
                if ($fileSize -gt 0) {
                    $script:filePathsMap[$uniqueFileName] = $file
                    $dataGridView.Rows.Add($uniqueFileName, 1, $platform, $format, (T "StatusAdded"), (Get-ReadableSize $fileSize), "", "", $sha1, $serial)
                }
            }
        }
    }
    $txtLog.AppendText("$(T 'LogTotalTable') $($dataGridView.Rows.Count)`r`n`r`n")
    Save-SerialCache
}

$datUrls = @(
    "http://redump.org/datfile/arch/", "http://redump.org/datfile/mac/", "http://redump.org/datfile/ajcd/",
    "http://redump.org/datfile/pippin/", "http://redump.org/datfile/qis/", "http://redump.org/datfile/acd/",
    "http://redump.org/datfile/cdtv/", "http://redump.org/datfile/fmt/", "http://redump.org/datfile/fpp/",
    "http://redump.org/datfile/pc/", "http://redump.org/datfile/ite/", "http://redump.org/datfile/kea/",
    "http://redump.org/datfile/kfb/", "http://redump.org/datfile/ks573/", "http://redump.org/datfile/ksgv/",
    "http://redump.org/datfile/ixl/", "http://redump.org/datfile/hs/", "http://redump.org/datfile/vis/",
    "http://redump.org/datfile/xbox/", "http://redump.org/datfile/xbox360/", "http://redump.org/datfile/trf/",
    "http://redump.org/datfile/ns246/", "http://redump.org/datfile/pce/", "http://redump.org/datfile/pc-88/",
    "http://redump.org/datfile/pc-98/", "http://redump.org/datfile/pc-fx/", "http://redump.org/datfile/ngcd/",
    "http://redump.org/datfile/gc/", "http://redump.org/datfile/wii/", "http://redump.org/datfile/palm/",
    "http://redump.org/datfile/3do/", "http://redump.org/datfile/cdi/", "http://redump.org/datfile/photo-cd/",
    "http://redump.org/datfile/psxgs/", "http://redump.org/datfile/ppc/", "http://redump.org/datfile/chihiro/",
    "http://redump.org/datfile/dc/", "http://redump.org/datfile/lindbergh/", "http://redump.org/datfile/mcd/",
    "http://redump.org/datfile/naomi/", "http://redump.org/datfile/naomi2/", "http://redump.org/datfile/sp21/",
    "http://redump.org/datfile/sre/", "http://redump.org/datfile/sre2/", "http://redump.org/datfile/ss/",
    "http://redump.org/datfile/x68k/", "http://redump.org/datfile/psx/", "http://redump.org/datfile/ps2/",
    "http://redump.org/datfile/ps3/", "http://redump.org/datfile/psp/", "http://redump.org/datfile/quizard/",
    "http://redump.org/datfile/ksite/", "http://redump.org/datfile/nuon/", "http://redump.org/datfile/vflash/",
    "http://redump.org/datfile/gamewave/", "http://redump.org/datfile/cd32/"
)

$chdmanExe = Join-Path $PSScriptRoot "chdman.exe"
if (-not (Test-Path -LiteralPath $chdmanExe)) {
    [System.Windows.Forms.MessageBox]::Show((T "MsgErrorCHDMan"), (T "MsgCritError"), [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
    exit
}

$form = New-Object System.Windows.Forms.Form
$form.Text = ""
$form.Size = New-Object System.Drawing.Size(1690, 960)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "None"
$form.MaximizeBox = $false
$form.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Regular)
$form.AllowDrop = $true
$form.Add_FormClosing({ 
        Kill-AllCHDManProcesses
        Save-Settings 
        Save-SerialCache
    })

$toolTip = New-Object System.Windows.Forms.ToolTip
$toolTip.AutoPopDelay = 5000
$toolTip.InitialDelay = 100
$toolTip.ReshowDelay = 500
$toolTip.ShowAlways = $true

# Translated Theme Names
$themes = @(
    @{ Name = "Charcoal Dark"; BackColor = "#2D2D2D"; ForeColor = "#E0E0E0"; ButtonColor = "#3C3C3C"; ButtonHover = "#4A4A4A"; FieldBackColor = "#3C3C3C"; FieldForeColor = "#E0E0E0"; HeaderColor = "#1A1A1A"; BorderColor = "#808080"; CheckColor = "#00FF00" },
    @{ Name = "Steel Storm"; BackColor = "#1C2526"; ForeColor = "#FFFFFF"; ButtonColor = "#2A3F4D"; ButtonHover = "#3B5B73"; FieldBackColor = "#2A3F4D"; FieldForeColor = "#FFFFFF"; HeaderColor = "#0D1517"; BorderColor = "#5A9FB5"; CheckColor = "#4ADE80" },
    @{ Name = "Platinum Light"; BackColor = "#F0F0F0"; ForeColor = "#000000"; ButtonColor = "#D3D3D3"; ButtonHover = "#B0B0B0"; FieldBackColor = "#FFFFFF"; FieldForeColor = "#000000"; HeaderColor = "#E0E0E0"; BorderColor = "#808080"; CheckColor = "#22C55E" },
    @{ Name = "Ocean Depth"; BackColor = "#1E3A8A"; ForeColor = "#FFFFFF"; ButtonColor = "#3B82F6"; ButtonHover = "#60A5FA"; FieldBackColor = "#3B82F6"; FieldForeColor = "#FFFFFF"; HeaderColor = "#0F1F4A"; BorderColor = "#93C5FD"; CheckColor = "#60A5FA" },
    @{ Name = "Emerald Forest"; BackColor = "#14532D"; ForeColor = "#FFFFFF"; ButtonColor = "#22C55E"; ButtonHover = "#4ADE80"; FieldBackColor = "#22C55E"; FieldForeColor = "#FFFFFF"; HeaderColor = "#0A2917"; BorderColor = "#86EFAC"; CheckColor = "#4ADE80" },
    @{ Name = "Amethyst"; BackColor = "#4C1D95"; ForeColor = "#FFFFFF"; ButtonColor = "#8B5CF6"; ButtonHover = "#A78BFA"; FieldBackColor = "#8B5CF6"; FieldForeColor = "#FFFFFF"; HeaderColor = "#2E0F5B"; BorderColor = "#C4B5FD"; CheckColor = "#A78BFA" },
    @{ Name = "Volcano"; BackColor = "#7C2D12"; ForeColor = "#FFFFFF"; ButtonColor = "#F97316"; ButtonHover = "#FB923C"; FieldBackColor = "#F97316"; FieldForeColor = "#FFFFFF"; HeaderColor = "#3E1709"; BorderColor = "#FED7AA"; CheckColor = "#FB923C" },
    @{ Name = "Blood Ruby"; BackColor = "#450A0A"; ForeColor = "#FFFFFF"; ButtonColor = "#EF4444"; ButtonHover = "#F87171"; FieldBackColor = "#EF4444"; FieldForeColor = "#FFFFFF"; HeaderColor = "#230505"; BorderColor = "#FECACA"; CheckColor = "#F87171" },
    @{ Name = "Gothic"; BackColor = "#101010"; ForeColor = "#A0A0A0"; ButtonColor = "#2E0000"; ButtonHover = "#5A0000"; FieldBackColor = "#1A1A1A"; FieldForeColor = "#8B0000"; HeaderColor = "#000000"; BorderColor = "#505050"; CheckColor = "#8B0000" },
    @{ Name = "Metallic"; BackColor = "#43464B"; ForeColor = "#FFFFFF"; ButtonColor = "#71797E"; ButtonHover = "#BCC6CC"; FieldBackColor = "#55555C"; FieldForeColor = "#E0E0E0"; HeaderColor = "#2C2F33"; BorderColor = "#BCC6CC"; CheckColor = "#71797E" },
    @{ Name = "Steam Engine"; BackColor = "#4A2C2A"; ForeColor = "#F3E5AB"; ButtonColor = "#B87333"; ButtonHover = "#CD7F32"; FieldBackColor = "#804A00"; FieldForeColor = "#F3E5AB"; HeaderColor = "#2F1E19"; BorderColor = "#D4AF37"; CheckColor = "#B87333" },
    @{ Name = "Deep Woods"; BackColor = "#0A210F"; ForeColor = "#C2B280"; ButtonColor = "#344E41"; ButtonHover = "#588157"; FieldBackColor = "#283618"; FieldForeColor = "#DAD7CD"; HeaderColor = "#011502"; BorderColor = "#656D4A"; CheckColor = "#A3B18A" },
    @{ Name = "Desert"; BackColor = "#F0E68C"; ForeColor = "#5D4037"; ButtonColor = "#CD853F"; ButtonHover = "#DAA520"; FieldBackColor = "#FFF8DC"; FieldForeColor = "#8B4513"; HeaderColor = "#8B7D6B"; BorderColor = "#87CEEB"; CheckColor = "#CD853F" },
    @{ Name = "Arctic"; BackColor = "#F0FFFF"; ForeColor = "#00008B"; ButtonColor = "#ADD8E6"; ButtonHover = "#B0E0E6"; FieldBackColor = "#FFFFFF"; FieldForeColor = "#000000"; HeaderColor = "#191970"; BorderColor = "#4682B4"; CheckColor = "#191970" },
    @{ Name = "Retro 80s"; BackColor = "#D4CFC7"; ForeColor = "#2C2C2C"; ButtonColor = "#A9A9A9"; ButtonHover = "#C0C0C0"; FieldBackColor = "#E6E6E6"; FieldForeColor = "#000000"; HeaderColor = "#5A5A5A"; BorderColor = "#FF4500"; CheckColor = "#A9A9A9" },
    @{ Name = "Coffee Shop"; BackColor = "#3B2F2F"; ForeColor = "#F5F5DC"; ButtonColor = "#6F4E37"; ButtonHover = "#8B4513"; FieldBackColor = "#D2B48C"; FieldForeColor = "#362511"; HeaderColor = "#1B1212"; BorderColor = "#A0522D"; CheckColor = "#6F4E37" },
    @{ Name = "Sakura Blossom"; BackColor = "#FFF0F5"; ForeColor = "#555555"; ButtonColor = "#FFB6C1"; ButtonHover = "#FFC0CB"; FieldBackColor = "#FFFFFF"; FieldForeColor = "#000000"; HeaderColor = "#DB7093"; BorderColor = "#800020"; CheckColor = "#DB7093" },
    @{ Name = "Sunny Day"; BackColor = "#FFFFE0"; ForeColor = "#483C32"; ButtonColor = "#FFD700"; ButtonHover = "#FFA500"; FieldBackColor = "#FFFFFF"; FieldForeColor = "#000000"; HeaderColor = "#87CEEB"; BorderColor = "#FF8C00"; CheckColor = "#FFA500" },
    @{ Name = "Futuristic"; BackColor = "#EAEFF2"; ForeColor = "#1A252F"; ButtonColor = "#B0C4DE"; ButtonHover = "#FFFFFF"; FieldBackColor = "#FFFFFF"; FieldForeColor = "#000000"; HeaderColor = "#2F4F4F"; BorderColor = "#778899"; CheckColor = "#4682B4" },
    @{ Name = "Cyberpunk"; BackColor = "#0a0a14"; ForeColor = "#E3E3E3"; ButtonColor = "#3D0052"; ButtonHover = "#F0F008"; FieldBackColor = "#1C1C2A"; FieldForeColor = "#08F7FE"; HeaderColor = "#000000"; BorderColor = "#FD5F00"; CheckColor = "#FF0054" },
    @{ Name = "Anime"; BackColor = "#F0F8FF"; ForeColor = "#333333"; ButtonColor = "#FFB6C1"; ButtonHover = "#87CEEB"; FieldBackColor = "#FFFFFF"; FieldForeColor = "#5D4037"; HeaderColor = "#4682B4"; BorderColor = "#FF69B4"; CheckColor = "#32CD32" },
    @{ Name = "Horror"; BackColor = "#010101"; ForeColor = "#A9A9A9"; ButtonColor = "#300000"; ButtonHover = "#600000"; FieldBackColor = "#121212"; FieldForeColor = "#8B0000"; HeaderColor = "#1A0000"; BorderColor = "#444444"; CheckColor = "#FF0000" },
    @{ Name = "Blue Neon"; BackColor = "#0A0E27"; ForeColor = "#00F0FF"; ButtonColor = "#1A1F3A"; ButtonHover = "#2D3561"; FieldBackColor = "#0F1629"; FieldForeColor = "#00F0FF"; HeaderColor = "#050812"; BorderColor = "#00F0FF"; CheckColor = "#FF00FF" },
    @{ Name = "Purple Neon"; BackColor = "#1A0A1F"; ForeColor = "#FF00FF"; ButtonColor = "#2D1A3A"; ButtonHover = "#4A2D61"; FieldBackColor = "#140A1A"; FieldForeColor = "#FF00FF"; HeaderColor = "#0A050F"; BorderColor = "#FF00FF"; CheckColor = "#00FFFF" },
    @{ Name = "Green Neon"; BackColor = "#0A1F0A"; ForeColor = "#00FF00"; ButtonColor = "#1A3A1A"; ButtonHover = "#2D612D"; FieldBackColor = "#0F1A0F"; FieldForeColor = "#00FF00"; HeaderColor = "#050F05"; BorderColor = "#00FF00"; CheckColor = "#FFFF00" },
    @{ Name = "Amber Glow"; BackColor = "#1F1A0A"; ForeColor = "#FFA500"; ButtonColor = "#3A2D1A"; ButtonHover = "#61492D"; FieldBackColor = "#1A140A"; FieldForeColor = "#FFA500"; HeaderColor = "#0F0A05"; BorderColor = "#FFA500"; CheckColor = "#FF0000" },
    @{ Name = "Rainbow Neon"; BackColor = "#0A0A0A"; ForeColor = "#00FFFF"; ButtonColor = "#1F1A2D"; ButtonHover = "#3A2D4A"; FieldBackColor = "#0F0F14"; FieldForeColor = "#FF00FF"; HeaderColor = "#050508"; BorderColor = "#00FF00"; CheckColor = "#FFA500" },
    @{ Name = "Cyberpunk Neon"; BackColor = "#0D0221"; ForeColor = "#00FFFF"; ButtonColor = "#260F3A"; ButtonHover = "#FF00FF"; FieldBackColor = "#0F1629"; FieldForeColor = "#39FF14"; HeaderColor = "#05010A"; BorderColor = "#FF00FF"; CheckColor = "#39FF14" },
    @{ Name = "Neon Sunset"; BackColor = "#240046"; ForeColor = "#FF9100"; ButtonColor = "#FF007F"; ButtonHover = "#FF79B4"; FieldBackColor = "#3C096C"; FieldForeColor = "#FFFF00"; HeaderColor = "#10002B"; BorderColor = "#FFFF00"; CheckColor = "#FF007F" },
    @{ Name = "Neon Galaxy"; BackColor = "#000000"; ForeColor = "#00BFFF"; ButtonColor = "#191970"; ButtonHover = "#FFD700"; FieldBackColor = "#1A1A1A"; FieldForeColor = "#FFFFFF"; HeaderColor = "#010101"; BorderColor = "#00BFFF"; CheckColor = "#FFD700" },
    @{ Name = "Toxic Neon"; BackColor = "#0A1F0A"; ForeColor = "#39FF14"; ButtonColor = "#2D1A3A"; ButtonHover = "#9D00FF"; FieldBackColor = "#000000"; FieldForeColor = "#FFFF00"; HeaderColor = "#050F05"; BorderColor = "#9D00FF"; CheckColor = "#39FF14" },
    @{ Name = "Electric Ocean"; BackColor = "#022B3A"; ForeColor = "#20B2AA"; ButtonColor = "#000080"; ButtonHover = "#FF7F50"; FieldBackColor = "#01161E"; FieldForeColor = "#7FFFD4"; HeaderColor = "#000D11"; BorderColor = "#FF7F50"; CheckColor = "#7FFFD4" },
    @{ Name = "Fiery Neon"; BackColor = "#2B0000"; ForeColor = "#FF0000"; ButtonColor = "#8B4000"; ButtonHover = "#FF4500"; FieldBackColor = "#000000"; FieldForeColor = "#FFFF00"; HeaderColor = "#150000"; BorderColor = "#FF4500"; CheckColor = "#FFFF00" },
    @{ Name = "Retrowave"; BackColor = "#10102A"; ForeColor = "#FF007F"; ButtonColor = "#4B0082"; ButtonHover = "#00FFFF"; FieldBackColor = "#0A0A1A"; FieldForeColor = "#FFFFE0"; HeaderColor = "#000000"; BorderColor = "#00FFFF"; CheckColor = "#FF007F" },
    @{ Name = "Ghost Neon"; BackColor = "#121212"; ForeColor = "#F8F8FF"; ButtonColor = "#483D8B"; ButtonHover = "#B0C4DE"; FieldBackColor = "#000000"; FieldForeColor = "#98FB98"; HeaderColor = "#080808"; BorderColor = "#98FB98"; CheckColor = "#B0C4DE" },
    @{ Name = "Candy Neon"; BackColor = "#1D0C26"; ForeColor = "#FF69B4"; ButtonColor = "#00A7E1"; ButtonHover = "#90EE90"; FieldBackColor = "#311432"; FieldForeColor = "#FFFACD"; HeaderColor = "#0E0613"; BorderColor = "#00A7E1"; CheckColor = "#FF69B4" },
    @{ Name = "Plasma Neon"; BackColor = "#000000"; ForeColor = "#00FF7F"; ButtonColor = "#8A2BE2"; ButtonHover = "#FF1493"; FieldBackColor = "#000033"; FieldForeColor = "#87CEEB"; HeaderColor = "#00001A"; BorderColor = "#FF1493"; CheckColor = "#00FF7F" }
)

function Set-Theme {
    param ($ThemeName)
    $theme = $themes | Where-Object { $_.Name -eq $ThemeName } | Select-Object -First 1
    if (-not $theme) { $theme = $themes[0] } # Fallback
    
    $form.BackColor = $theme.BackColor
    $form.ForeColor = $theme.ForeColor
    $customHeader.BackColor = $theme.HeaderColor
    $lblTitle.ForeColor = $theme.ForeColor
    
    foreach ($control in $form.Controls) {
        if ($control -is [System.Windows.Forms.Button] -or $control -is [System.Windows.Forms.ComboBox]) {
            $bgColor = $theme.ButtonColor
            if (($control -in @($diskCompression, $diskCDHunk, $diskDVDHunk)) -and -not $control.Enabled) {
                $bgColor = $theme.HeaderColor
            }
            $control.BackColor = [System.Drawing.ColorTranslator]::FromHtml($bgColor)
            $control.ForeColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldForeColor)
            if ($control -is [System.Windows.Forms.Button]) {
                $control.FlatAppearance.MouseOverBackColor = [System.Drawing.ColorTranslator]::FromHtml($theme.ButtonHover)
                $control.FlatAppearance.BorderColor = [System.Drawing.ColorTranslator]::FromHtml($theme.BorderColor)
            }
        }
        if ($control -is [System.Windows.Forms.TextBox] -or $control -is [System.Windows.Forms.DataGridView]) {
            $control.BackColor = $theme.FieldBackColor
            $control.ForeColor = $theme.FieldForeColor
        }
        if ($control -is [System.Windows.Forms.CheckBox] -or $control -is [System.Windows.Forms.Label] -or $control -is [System.Windows.Forms.Panel]) {
            if ($control -is [System.Windows.Forms.Panel]) {
                $control.BackColor = $theme.BackColor
                $control.BorderStyle = "FixedSingle"
            }
            if ($control -is [System.Windows.Forms.CheckBox]) {
                $control.ForeColor = $theme.ForeColor
            }
            if ($control -is [System.Windows.Forms.Label]) {
                $control.BackColor = $theme.BackColor
                $control.ForeColor = $theme.ForeColor
            }
        }
    }
    
    $panelForce.BackColor = $theme.BackColor
    $panelRecognition.BackColor = $theme.BackColor
    $panelAetherSX2.BackColor = $theme.BackColor
    $panelTextNotification.BackColor = $theme.BackColor
    $panelSoundNotification.BackColor = $theme.BackColor
    
    $chkForce.ForeColor = $theme.ForeColor
    $chkRecognition.ForeColor = $theme.ForeColor
    $chkAetherSX2.ForeColor = $theme.ForeColor
    $chkTextNotification.ForeColor = $theme.ForeColor
    $chkSoundNotification.ForeColor = $theme.ForeColor
    
    $borderColor = [System.Drawing.ColorTranslator]::FromHtml($theme.BorderColor)
    
    $dataGridView.BackgroundColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldBackColor)
    $dataGridView.DefaultCellStyle.BackColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldBackColor)
    $dataGridView.DefaultCellStyle.ForeColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldForeColor)
    $dataGridView.AlternatingRowsDefaultCellStyle.BackColor = [System.Drawing.ColorTranslator]::FromHtml($theme.ButtonColor)
    $dataGridView.AlternatingRowsDefaultCellStyle.ForeColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldForeColor)
    $dataGridView.ColumnHeadersDefaultCellStyle.BackColor = [System.Drawing.ColorTranslator]::FromHtml($theme.ButtonColor)
    $dataGridView.ColumnHeadersDefaultCellStyle.ForeColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldForeColor)
    $dataGridView.EnableHeadersVisualStyles = $false
    
    $dataGridView.GridColor = $borderColor
    $dataGridView.BorderStyle = "FixedSingle"
    $dataGridView.CellBorderStyle = [System.Windows.Forms.DataGridViewCellBorderStyle]::Single
    $dataGridView.RowHeadersBorderStyle = [System.Windows.Forms.DataGridViewHeaderBorderStyle]::Single
    $dataGridView.ColumnHeadersBorderStyle = [System.Windows.Forms.DataGridViewHeaderBorderStyle]::Single
    
    $dataGridView.DefaultCellStyle.SelectionBackColor = [System.Drawing.ColorTranslator]::FromHtml($theme.ButtonHover)
    $dataGridView.DefaultCellStyle.SelectionForeColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldForeColor)
    
    $contextMenu.BackColor = [System.Drawing.ColorTranslator]::FromHtml($theme.ButtonColor)
    $contextMenu.ForeColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldForeColor)
    
    $menuItemDelete.BackColor = [System.Drawing.ColorTranslator]::FromHtml($theme.ButtonColor)
    $menuItemDelete.ForeColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldForeColor)
    $menuItemOpenSourceFolder.BackColor = [System.Drawing.ColorTranslator]::FromHtml($theme.ButtonColor)
    $menuItemOpenSourceFolder.ForeColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldForeColor)
    $menuItemOpenOutputFolder.BackColor = [System.Drawing.ColorTranslator]::FromHtml($theme.ButtonColor)
    $menuItemOpenOutputFolder.ForeColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldForeColor)
    $menuItemCopySerial.BackColor = [System.Drawing.ColorTranslator]::FromHtml($theme.ButtonColor)
    $menuItemCopySerial.ForeColor = [System.Drawing.ColorTranslator]::FromHtml($theme.FieldForeColor)
    
    Save-Settings
}

function Update-Interface {
    $lblTitle.Text = T "Title"
    $btnDownloadDATs.Text = T "BtnDownloadDATs"
    $btnDeleteDATs.Text = T "BtnDeleteDATs"
    $btnClearSerialCache.Text = T "BtnClearCache"
    
    $lblOutput.Text = T "LblOutput"
    $btnBrowseOutput.Text = T "BtnBrowse"
    $btnClearOutput.Text = T "BtnClear"
    
    $lblCores.Text = T "LblCores"
    $lblCompression.Text = T "LblCompression"
    $lblCDHunk.Text = T "LblCDHunk"
    $lblDVDHunk.Text = T "LblDVDHunk"
    
    $chkForce.Text = T "ChkForce"
    $chkRecognition.Text = T "ChkRecognition"
    $chkAetherSX2.Text = T "ChkAetherSX2"
    $chkTextNotification.Text = T "ChkTextNotif"
    $chkSoundNotification.Text = T "ChkSoundNotif"
    
    $btnPause.Text = if ($script:isPaused) { T "BtnResume" } else { T "BtnPause" }
    $btnCancel.Text = T "BtnCancel"
    $btnExecute.Text = T "BtnExecute"
    $btnClose.Text = T "BtnClose"
    
    $lblCreatedBy.Text = T "LblCreatedBy"
    $lblVersion.Text = T "LblVersion"
    
    $dataGridView.Columns[0].HeaderText = T "ColFile"
    $dataGridView.Columns[1].HeaderText = T "ColCount"
    $dataGridView.Columns[2].HeaderText = T "ColPlatform"
    $dataGridView.Columns[3].HeaderText = T "ColFormat"
    $dataGridView.Columns[4].HeaderText = T "ColStatus"
    $dataGridView.Columns[5].HeaderText = T "ColSizeStart"
    $dataGridView.Columns[6].HeaderText = T "ColSizeEnd"
    $dataGridView.Columns[7].HeaderText = T "ColRatio"
    $dataGridView.Columns[8].HeaderText = T "ColSHA1"
    $dataGridView.Columns[9].HeaderText = T "ColSerial"
    
    $menuItemDelete.Text = T "MenuDeleteRow"
    $menuItemOpenSourceFolder.Text = T "MenuOpenSource"
    $menuItemOpenOutputFolder.Text = T "MenuOpenDest"
    $menuItemCopySerial.Text = T "MenuCopySerial"
}

$customHeader = New-Object System.Windows.Forms.Panel
$customHeader.Location = New-Object System.Drawing.Point(0, 0)
$customHeader.Size = New-Object System.Drawing.Size(1690, 40)
$customHeader.BackColor = "#1A1A1A"
$customHeader.Add_MouseDown({
        if ($_.Button -eq [System.Windows.Forms.MouseButtons]::Left) {
            [Win32]::ReleaseCapture()
            [Win32]::SendMessage($form.Handle, [Win32]::WM_NCLBUTTONDOWN, [Win32]::HT_CAPTION, 0)
        }
    })
$lblTitle = New-Object System.Windows.Forms.Label
$lblTitle.Location = New-Object System.Drawing.Point(10, 10)
$lblTitle.Size = New-Object System.Drawing.Size(600, 20)
$lblTitle.ForeColor = "#FFFFFF"
$lblTitle.Font = New-Object System.Drawing.Font("Century Gothic", 10, [System.Drawing.FontStyle]::Bold)
$lblTitle.Add_MouseDown({
        if ($_.Button -eq [System.Windows.Forms.MouseButtons]::Left) {
            [Win32]::ReleaseCapture()
            [Win32]::SendMessage($form.Handle, [Win32]::WM_NCLBUTTONDOWN, [Win32]::HT_CAPTION, 0)
        }
    })

$btnMinimize = New-Object System.Windows.Forms.Button
$btnMinimize.Location = New-Object System.Drawing.Point(1600, 5)
$btnMinimize.Size = New-Object System.Drawing.Size(30, 30)
$btnMinimize.Text = "_"
$btnMinimize.FlatStyle = "Flat"
$btnMinimize.FlatAppearance.BorderSize = 0
$btnMinimize.BackColor = "Transparent"
$btnMinimize.ForeColor = "#FFFFFF"
$btnMinimize.Font = New-Object System.Drawing.Font("Century Gothic", 12, [System.Drawing.FontStyle]::Bold)
$btnMinimize.Add_Click({ $form.WindowState = "Minimized" })

$btnHeaderClose = New-Object System.Windows.Forms.Button
$btnHeaderClose.Location = New-Object System.Drawing.Point(1640, 5)
$btnHeaderClose.Size = New-Object System.Drawing.Size(30, 30)
$btnHeaderClose.Text = "×"
$btnHeaderClose.FlatStyle = "Flat"
$btnHeaderClose.FlatAppearance.BorderSize = 0
$btnHeaderClose.BackColor = "Transparent"
$btnHeaderClose.ForeColor = "#FFFFFF"
$btnHeaderClose.Font = New-Object System.Drawing.Font("Century Gothic", 16, [System.Drawing.FontStyle]::Bold)
$btnHeaderClose.Add_Click({ $form.Close() })
$btnHeaderClose.Add_MouseEnter({ $btnHeaderClose.BackColor = "#E81123" })
$btnHeaderClose.Add_MouseLeave({ $btnHeaderClose.BackColor = "Transparent" })

$customHeader.Controls.AddRange(@($lblTitle, $btnMinimize, $btnHeaderClose))

$btnDownloadDATs = New-Object System.Windows.Forms.Button
$btnDownloadDATs.Location = New-Object System.Drawing.Point(10, 50)
$btnDownloadDATs.Size = New-Object System.Drawing.Size(250, 35)
$btnDownloadDATs.FlatStyle = "Flat"
$btnDownloadDATs.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$btnDownloadDATs.FlatAppearance.BorderSize = 1
$btnDownloadDATs.Cursor = [System.Windows.Forms.Cursors]::Hand
$btnDownloadDATs.Add_Click({
        $datsFolder = Join-Path $PSScriptRoot "DATs"
        if (-not (Test-Path -LiteralPath $datsFolder)) { New-Item -ItemType Directory -Path $datsFolder | Out-Null }
        
        # UI Toggle
        $lblProcessStatus.Visible = $false
        $progressProcess.Visible = $false
        $lblDownloadStatus.Visible = $true
        $progressDownload.Visible = $true
        
        $progressDownload.Maximum = $datUrls.Count
        $progressDownload.Value = 0
        $lblDownloadStatus.Text = "$(T 'StDownload') 0 $(T 'StFrom') $($datUrls.Count): "
        $txtLog.AppendText("`r`n$(T 'LogStartDl')`r`n")
    
        $webClient = New-Object System.Net.WebClient
        $downloadCount = 0
        foreach ($url in $datUrls) {
            $fileName = Split-Path $url -Leaf
            $outputPath = Join-Path $datsFolder "$fileName.zip"
            $downloadCount++
            $lblDownloadStatus.Text = "$(T 'StDownload') $($downloadCount.ToString('N0')) $(T 'StFrom') $($datUrls.Count.ToString('N0')): $fileName"
            try {
                $webClient.DownloadFile($url, $outputPath)
                [System.IO.Compression.ZipFile]::ExtractToDirectory($outputPath, $datsFolder)
                Remove-Item $outputPath
                $txtLog.AppendText("$(T 'LogDownloaded') $fileName`r`n")
            }
            catch {
                $txtLog.AppendText("$(T 'LogErrDl') ${fileName}: $_`r`n")
            }
            $progressDownload.Value = $downloadCount
            $form.Refresh()
        }
        $lblDownloadStatus.Text = "$(T 'StDownload') $($datUrls.Count.ToString('N0')) $(T 'StFrom') $($datUrls.Count.ToString('N0')): $(T 'StComplete')"
        $txtLog.AppendText("$(T 'LogDlComplete')`r`n`r`n")
        
        # Restore UI
        Start-Sleep -Milliseconds 1000
        $lblDownloadStatus.Visible = $false
        $progressDownload.Visible = $false
        $lblProcessStatus.Visible = $true
        $progressProcess.Visible = $true
        
        [System.Media.SystemSounds]::Beep.Play()
        $txtLog.AppendText("$(T 'MsgDatsDownloaded')`r`n")
    })

$btnDeleteDATs = New-Object System.Windows.Forms.Button
$btnDeleteDATs.Location = New-Object System.Drawing.Point(270, 50)
$btnDeleteDATs.Size = New-Object System.Drawing.Size(250, 35)
$btnDeleteDATs.FlatStyle = "Flat"
$btnDeleteDATs.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$btnDeleteDATs.FlatAppearance.BorderSize = 1
$btnDeleteDATs.Cursor = [System.Windows.Forms.Cursors]::Hand
$btnDeleteDATs.Add_Click({
        $datsFolder = Join-Path $PSScriptRoot "DATs"
        if (Test-Path -LiteralPath $datsFolder) {
            Remove-Item $datsFolder -Recurse -Force
            $txtLog.AppendText("$(T 'MsgFolderDeleted')`r`n")
        }
    })

$btnClearSerialCache = New-Object System.Windows.Forms.Button
$btnClearSerialCache.Location = New-Object System.Drawing.Point(530, 50)
$btnClearSerialCache.Size = New-Object System.Drawing.Size(250, 35)
$btnClearSerialCache.FlatStyle = "Flat"
$btnClearSerialCache.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$btnClearSerialCache.FlatAppearance.BorderSize = 1
$btnClearSerialCache.Cursor = [System.Windows.Forms.Cursors]::Hand
$btnClearSerialCache.Add_Click({
        $serialFile = Join-Path $PSScriptRoot "serials.json"
        if (Test-Path $serialFile) {
            Remove-Item $serialFile -Force
            $script:serialCache = @{}
            $txtLog.AppendText("$(T 'MsgCacheCleared')`r`n")
        }
        else {
            $txtLog.AppendText("$(T 'MsgCacheEmpty')`r`n")
        }
    })

# === Language Dropdown ===
$cmbLanguage = New-Object System.Windows.Forms.ComboBox
$cmbLanguage.Location = New-Object System.Drawing.Point(1270, 50)
$cmbLanguage.Size = New-Object System.Drawing.Size(200, 35)
$cmbLanguage.Items.AddRange(@("Русский", "English"))
$cmbLanguage.SelectedIndex = 0
$cmbLanguage.FlatStyle = "Flat"
$cmbLanguage.DropDownStyle = "DropDownList"
$cmbLanguage.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$cmbLanguage.Cursor = [System.Windows.Forms.Cursors]::Hand
$cmbLanguage.Add_SelectedIndexChanged({ 
        $script:currentLang = if ($cmbLanguage.SelectedItem -eq "Русский") { "RU" } else { "EN" }
        Update-Interface
        Save-Settings
    })

$diskTheme = New-Object System.Windows.Forms.ComboBox
$diskTheme.Location = New-Object System.Drawing.Point(1480, 50)
$diskTheme.Size = New-Object System.Drawing.Size(200, 35)
$diskTheme.Items.AddRange($themes.Name)
$diskTheme.SelectedIndex = 0
$diskTheme.FlatStyle = "Flat"
$diskTheme.DropDownStyle = "DropDownList"
$diskTheme.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$diskTheme.Cursor = [System.Windows.Forms.Cursors]::Hand
$diskTheme.Add_SelectedIndexChanged({ Set-Theme $diskTheme.SelectedItem })

$lblDownloadStatus = New-Object System.Windows.Forms.Label
$lblDownloadStatus.Location = New-Object System.Drawing.Point(10, 270)
$lblDownloadStatus.Size = New-Object System.Drawing.Size(700, 20)
$lblDownloadStatus.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$lblDownloadStatus.Visible = $false

$progressDownload = New-Object System.Windows.Forms.ProgressBar
$progressDownload.Location = New-Object System.Drawing.Point(10, 290)
$progressDownload.Size = New-Object System.Drawing.Size(700, 23)
$progressDownload.Style = "Continuous"
$progressDownload.Visible = $false

# === OUTPUT SECTION (Moved Up) ===

$lblOutput = New-Object System.Windows.Forms.Label
$lblOutput.Location = New-Object System.Drawing.Point(10, 95)
$lblOutput.Size = New-Object System.Drawing.Size(120, 20)
$lblOutput.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)

$txtOutput = New-Object System.Windows.Forms.TextBox
$txtOutput.Location = New-Object System.Drawing.Point(140, 95)
$txtOutput.Size = New-Object System.Drawing.Size(1540, 23)
$txtOutput.Font = New-Object System.Drawing.Font("Century Gothic", 9)
$txtOutput.AllowDrop = $true
$txtOutput.Add_DragEnter({
        if ($_.Data.GetDataPresent([System.Windows.Forms.DataFormats]::FileDrop)) {
            $_.Effect = [System.Windows.Forms.DragDropEffects]::Copy
        }
        else {
            $_.Effect = [System.Windows.Forms.DragDropEffects]::None
        }
    })
$txtOutput.Add_DragDrop({
        $items = $_.Data.GetData([System.Windows.Forms.DataFormats]::FileDrop)
        $validFolder = $items | Where-Object { Test-Path -LiteralPath $_ -PathType Container } | Select-Object -First 1
        if ($validFolder) {
            $txtOutput.Text = $validFolder
        }
    })

$btnBrowseOutput = New-Object System.Windows.Forms.Button
$btnBrowseOutput.Location = New-Object System.Drawing.Point(10, 125)
$btnBrowseOutput.Size = New-Object System.Drawing.Size(180, 35)
$btnBrowseOutput.FlatStyle = "Flat"
$btnBrowseOutput.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$btnBrowseOutput.FlatAppearance.BorderSize = 1
$btnBrowseOutput.Cursor = [System.Windows.Forms.Cursors]::Hand
$btnBrowseOutput.Add_Click({
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        if ($dialog.ShowDialog() -eq "OK") {
            $txtOutput.Text = $dialog.SelectedPath
        }
    })

$btnClearOutput = New-Object System.Windows.Forms.Button
$btnClearOutput.Location = New-Object System.Drawing.Point(200, 125)
$btnClearOutput.Size = New-Object System.Drawing.Size(180, 35)
$btnClearOutput.FlatStyle = "Flat"
$btnClearOutput.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$btnClearOutput.FlatAppearance.BorderSize = 1
$btnClearOutput.Cursor = [System.Windows.Forms.Cursors]::Hand
$btnClearOutput.Add_Click({ $txtOutput.Text = "" })

# === SETTINGS (Moved Up) ===

$lblCores = New-Object System.Windows.Forms.Label
$lblCores.Location = New-Object System.Drawing.Point(10, 170)
$lblCores.Size = New-Object System.Drawing.Size(150, 20)
$lblCores.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)

$lblCompression = New-Object System.Windows.Forms.Label
$lblCompression.Location = New-Object System.Drawing.Point(170, 170)
$lblCompression.Size = New-Object System.Drawing.Size(150, 20)
$lblCompression.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)

$lblCDHunk = New-Object System.Windows.Forms.Label
$lblCDHunk.Location = New-Object System.Drawing.Point(330, 170)
$lblCDHunk.Size = New-Object System.Drawing.Size(150, 20)
$lblCDHunk.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)

$lblDVDHunk = New-Object System.Windows.Forms.Label
$lblDVDHunk.Location = New-Object System.Drawing.Point(490, 170)
$lblDVDHunk.Size = New-Object System.Drawing.Size(160, 20)
$lblDVDHunk.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)

$diskCores = New-Object System.Windows.Forms.ComboBox
$diskCores.Location = New-Object System.Drawing.Point(10, 190)
$diskCores.Size = New-Object System.Drawing.Size(150, 30)
$diskCores.Items.AddRange(1..$([Environment]::ProcessorCount))
$diskCores.SelectedIndex = $([Environment]::ProcessorCount - 1)
$diskCores.FlatStyle = "Flat"
$diskCores.DropDownStyle = "DropDownList"
$diskCores.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$diskCores.Cursor = [System.Windows.Forms.Cursors]::Hand
$diskCores.Add_SelectedIndexChanged({ Save-Settings })

$diskCompression = New-Object System.Windows.Forms.ComboBox
$diskCompression.Location = New-Object System.Drawing.Point(170, 190)
$diskCompression.Size = New-Object System.Drawing.Size(150, 30)
$diskCompression.Items.AddRange(@("lzma", "zlib"))
$diskCompression.SelectedIndex = 0
$diskCompression.FlatStyle = "Flat"
$diskCompression.DropDownStyle = "DropDownList"
$diskCompression.Font = New-Object System.Drawing.Font("Century Gothic", 9)
$diskCompression.Cursor = [System.Windows.Forms.Cursors]::Hand
$diskCompression.Add_SelectedIndexChanged({ Save-Settings })

$diskCDHunk = New-Object System.Windows.Forms.ComboBox
$diskCDHunk.Location = New-Object System.Drawing.Point(330, 190)
$diskCDHunk.Size = New-Object System.Drawing.Size(150, 30)
$rangeCD = @(); for ($i = 1; $i -le 428; $i++) { $rangeCD += $i * 2448 }
$diskCDHunk.Items.Clear(); $diskCDHunk.Items.AddRange($rangeCD)
$diskCDHunk.SelectedItem = 1047744
$diskCDHunk.FlatStyle = "Flat"
$diskCDHunk.DropDownStyle = "DropDownList"
$diskCDHunk.Font = New-Object System.Drawing.Font("Century Gothic", 9)
$diskCDHunk.Cursor = [System.Windows.Forms.Cursors]::Hand
$diskCDHunk.Add_SelectedIndexChanged({ Save-Settings })

$diskDVDHunk = New-Object System.Windows.Forms.ComboBox
$diskDVDHunk.Location = New-Object System.Drawing.Point(490, 190)
$diskDVDHunk.Size = New-Object System.Drawing.Size(150, 30)
$rangeDVD = @(); for ($i = 1; $i -le 512; $i++) { $rangeDVD += $i * 2048 }
$diskDVDHunk.Items.AddRange($rangeDVD)
$diskDVDHunk.SelectedItem = 1048576
$diskDVDHunk.FlatStyle = "Flat"
$diskDVDHunk.DropDownStyle = "DropDownList"
$diskDVDHunk.Font = New-Object System.Drawing.Font("Century Gothic", 9)
$diskDVDHunk.Cursor = [System.Windows.Forms.Cursors]::Hand
$diskDVDHunk.Add_SelectedIndexChanged({ Save-Settings })

$panelForce = New-Object System.Windows.Forms.Panel
$panelForce.Location = New-Object System.Drawing.Point(10, 230)
$panelForce.Size = New-Object System.Drawing.Size(250, 30)
$panelForce.BorderStyle = "FixedSingle"

$chkForce = New-Object System.Windows.Forms.CheckBox
$chkForce.Location = New-Object System.Drawing.Point(5, 5)
$chkForce.Size = New-Object System.Drawing.Size(240, 20)
$chkForce.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$chkForce.Cursor = [System.Windows.Forms.Cursors]::Hand
$chkForce.FlatStyle = "Flat"
$chkForce.Add_CheckedChanged({ Save-Settings })

$panelRecognition = New-Object System.Windows.Forms.Panel
$panelRecognition.Location = New-Object System.Drawing.Point(270, 230)
$panelRecognition.Size = New-Object System.Drawing.Size(250, 30)
$panelRecognition.BorderStyle = "FixedSingle"

$chkRecognition = New-Object System.Windows.Forms.CheckBox
$chkRecognition.Location = New-Object System.Drawing.Point(5, 5)
$chkRecognition.Size = New-Object System.Drawing.Size(240, 20)
$chkRecognition.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$chkRecognition.Cursor = [System.Windows.Forms.Cursors]::Hand
$chkRecognition.FlatStyle = "Flat"
$chkRecognition.Add_CheckedChanged({ Save-Settings })

$panelAetherSX2 = New-Object System.Windows.Forms.Panel
$panelAetherSX2.Location = New-Object System.Drawing.Point(530, 230)
$panelAetherSX2.Size = New-Object System.Drawing.Size(250, 30)
$panelAetherSX2.BorderStyle = "FixedSingle"

$chkAetherSX2 = New-Object System.Windows.Forms.CheckBox
$chkAetherSX2.Location = New-Object System.Drawing.Point(5, 5)
$chkAetherSX2.Size = New-Object System.Drawing.Size(240, 20)
$chkAetherSX2.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$chkAetherSX2.Cursor = [System.Windows.Forms.Cursors]::Hand
$chkAetherSX2.FlatStyle = "Flat"
$chkAetherSX2.Add_CheckedChanged({ 
        Save-Settings 
        if ($chkAetherSX2.Checked) {
            $diskCompression.SelectedItem = "zlib"
            $diskCDHunk.SelectedItem = 4896
            $diskDVDHunk.SelectedItem = 4096
            $diskCompression.Enabled = $false
            $diskCDHunk.Enabled = $false
            $diskDVDHunk.Enabled = $false
        }
        else {
            $diskCompression.SelectedItem = "lzma"
            $diskCDHunk.SelectedItem = 1047744
            $diskDVDHunk.SelectedItem = 1048576
            $diskCompression.Enabled = $true
            $diskCDHunk.Enabled = $true
            $diskDVDHunk.Enabled = $true
        }
        Set-Theme $diskTheme.SelectedItem
    })

$panelTextNotification = New-Object System.Windows.Forms.Panel
$panelTextNotification.Location = New-Object System.Drawing.Point(1250, 230)
$panelTextNotification.Size = New-Object System.Drawing.Size(200, 30)
$panelTextNotification.BorderStyle = "FixedSingle"

$chkTextNotification = New-Object System.Windows.Forms.CheckBox
$chkTextNotification.Location = New-Object System.Drawing.Point(5, 5)
$chkTextNotification.Size = New-Object System.Drawing.Size(190, 20)
$chkTextNotification.Font = New-Object System.Drawing.Font("Century Gothic", 8, [System.Drawing.FontStyle]::Bold)
$chkTextNotification.Cursor = [System.Windows.Forms.Cursors]::Hand
$chkTextNotification.FlatStyle = "Flat"
$chkTextNotification.Add_CheckedChanged({ Save-Settings })

$panelSoundNotification = New-Object System.Windows.Forms.Panel
$panelSoundNotification.Location = New-Object System.Drawing.Point(1460, 230)
$panelSoundNotification.Size = New-Object System.Drawing.Size(200, 30)
$panelSoundNotification.BorderStyle = "FixedSingle"

$chkSoundNotification = New-Object System.Windows.Forms.CheckBox
$chkSoundNotification.Location = New-Object System.Drawing.Point(5, 5)
$chkSoundNotification.Size = New-Object System.Drawing.Size(190, 20)
$chkSoundNotification.Font = New-Object System.Drawing.Font("Century Gothic", 8, [System.Drawing.FontStyle]::Bold)
$chkSoundNotification.Cursor = [System.Windows.Forms.Cursors]::Hand
$chkSoundNotification.FlatStyle = "Flat"
$chkSoundNotification.Add_CheckedChanged({ Save-Settings })

$lblProcessStatus = New-Object System.Windows.Forms.Label
$lblProcessStatus.Location = New-Object System.Drawing.Point(10, 270)
$lblProcessStatus.Size = New-Object System.Drawing.Size(700, 20)
$lblProcessStatus.Text = ""
$lblProcessStatus.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)

$progressProcess = New-Object System.Windows.Forms.ProgressBar
$progressProcess.Location = New-Object System.Drawing.Point(10, 290)
$progressProcess.Size = New-Object System.Drawing.Size(700, 23)
$progressProcess.Style = "Continuous"

$txtLog = New-Object System.Windows.Forms.TextBox
$txtLog.Location = New-Object System.Drawing.Point(10, 323)
$txtLog.Size = New-Object System.Drawing.Size(1670, 100)
$txtLog.Multiline = $true
$txtLog.ScrollBars = "Vertical"
$txtLog.ReadOnly = $true
$txtLog.Font = New-Object System.Drawing.Font("Century Gothic", 8)
$txtLog.BorderStyle = "FixedSingle"

$contextMenu = New-Object System.Windows.Forms.ContextMenuStrip
$contextMenu.ShowImageMargin = $false
$contextMenu.ShowCheckMargin = $false

$menuItemDelete = New-Object System.Windows.Forms.ToolStripMenuItem
$menuItemDelete.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$menuItemDelete.Add_Click({
        if ($dataGridView.SelectedRows.Count -gt 0) {
            $selectedRows = $dataGridView.SelectedRows
            $filesToRemove = @()
            foreach ($row in $selectedRows) {
                $originalFileName = $row.Cells[0].Value
                if ($script:customFileNames.ContainsKey($originalFileName)) {
                    $originalFileName = $script:customFileNames[$originalFileName]
                }
                if ($script:filePathsMap.ContainsKey($originalFileName)) {
                    $filesToRemove += $script:filePathsMap[$originalFileName]
                    $script:filePathsMap.Remove($originalFileName)
                }
                $script:customFileNames.Remove($row.Cells[0].Value)
            }
            foreach ($row in $selectedRows) {
                $dataGridView.Rows.Remove($row)
            }
            $txtLog.AppendText("$(T 'MsgRowsDeleted')`r`n")
        }
    })

$menuItemOpenSourceFolder = New-Object System.Windows.Forms.ToolStripMenuItem
$menuItemOpenSourceFolder.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$menuItemOpenSourceFolder.Add_Click({
        if ($dataGridView.SelectedRows.Count -gt 0) {
            $selectedRow = $dataGridView.SelectedRows[0]
            $fileName = $selectedRow.Cells[0].Value
            $originalFileName = $fileName
            if ($script:customFileNames.ContainsKey($fileName)) {
                $originalFileName = $script:customFileNames[$fileName]
            }
            if ($script:filePathsMap.ContainsKey($originalFileName)) {
                $originalFile = $script:filePathsMap[$originalFileName]
                $folder = Split-Path $originalFile -Parent
                if (Test-Path -LiteralPath $folder) {
                    Start-Process "explorer.exe" -ArgumentList "/select,`"$originalFile`""
                    $txtLog.AppendText("$(T 'MenuOpenSource'): $folder`r`n")
                }
                else {
                    [System.Windows.Forms.MessageBox]::Show("$(T 'MsgFolderNotFound'): $folder", (T "StatusError"), [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
                }
            }
            else {
                [System.Windows.Forms.MessageBox]::Show((T "MsgPathNotFound"), (T "StatusError"), [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
            }
        }
    })

$menuItemOpenOutputFolder = New-Object System.Windows.Forms.ToolStripMenuItem
$menuItemOpenOutputFolder.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$menuItemOpenOutputFolder.Add_Click({
        if ($dataGridView.SelectedRows.Count -gt 0) {
            $selectedRow = $dataGridView.SelectedRows[0]
            $fileName = $selectedRow.Cells[0].Value
            $status = $selectedRow.Cells[4].Value
        
            if ($status -eq (T "StatusDone")) {
                $outputFolder = $txtOutput.Text
                if (-not $outputFolder) { $outputFolder = $PSScriptRoot }
                $gamesFolder = Join-Path $outputFolder "GAMES"
                $platform = $selectedRow.Cells[2].Value
                if ($platform -and $chkRecognition.Checked) {
                    $targetFolder = Join-Path $gamesFolder $platform
                }
                else {
                    $targetFolder = $gamesFolder
                }
                $outputFile = Join-Path $targetFolder "$fileName.chd"
            
                if (Test-Path -LiteralPath $outputFile) {
                    Start-Process "explorer.exe" -ArgumentList "/select,`"$outputFile`""
                }
                elseif (Test-Path -LiteralPath $targetFolder) {
                    Start-Process "explorer.exe" -ArgumentList $targetFolder
                }
                else {
                    [System.Windows.Forms.MessageBox]::Show("$(T 'MsgFolderNotFound'): $targetFolder", (T "StatusError"), [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
                }
            }
            else {
                [System.Windows.Forms.MessageBox]::Show("$(T 'MsgFileNotProcessed'): $status", "Info", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
            }
        }
    })

$menuItemCopySerial = New-Object System.Windows.Forms.ToolStripMenuItem
$menuItemCopySerial.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$menuItemCopySerial.Add_Click({
        if ($dataGridView.SelectedRows.Count -gt 0) {
            $selectedRow = $dataGridView.SelectedRows[0]
            $serial = $selectedRow.Cells[9].Value
            if ($serial -and $serial -ne (T "MsgSerialNotFound")) {
                [System.Windows.Forms.Clipboard]::SetText($serial)
                $txtLog.AppendText("$(T 'MsgSerialCopied'): $serial`r`n")
            }
            else {
                [System.Windows.Forms.MessageBox]::Show((T "MsgSerialNotFound"), "Info", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
            }
        }
    })

$contextMenu.Items.AddRange(@($menuItemDelete, $menuItemOpenSourceFolder, $menuItemOpenOutputFolder, $menuItemCopySerial))

# === GRID (Moved Up & DragDrop Enabled) ===

$dataGridView = New-Object System.Windows.Forms.DataGridView
$dataGridView.Location = New-Object System.Drawing.Point(10, 433)
$dataGridView.Size = New-Object System.Drawing.Size(1670, 460)
$dataGridView.ColumnCount = 10
$dataGridView.ColumnHeadersDefaultCellStyle.Font = New-Object System.Drawing.Font("Century Gothic", 8, [System.Drawing.FontStyle]::Bold)
$dataGridView.ColumnHeadersDefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleCenter
$dataGridView.DefaultCellStyle.Font = New-Object System.Drawing.Font("Century Gothic", 8)
$dataGridView.EnableHeadersVisualStyles = $false
$dataGridView.RowHeadersVisible = $false
$dataGridView.AllowUserToAddRows = $false
$dataGridView.SelectionMode = "FullRowSelect"
$dataGridView.ContextMenuStrip = $contextMenu

# ВКЛЮЧАЕМ DRAG AND DROP
$dataGridView.AllowDrop = $true
$dataGridView.Add_DragEnter({
        if ($_.Data.GetDataPresent([System.Windows.Forms.DataFormats]::FileDrop)) {
            $_.Effect = [System.Windows.Forms.DragDropEffects]::Copy
        }
        else {
            $_.Effect = [System.Windows.Forms.DragDropEffects]::None
        }
    })
$dataGridView.Add_DragDrop({
        $files = $_.Data.GetData([System.Windows.Forms.DataFormats]::FileDrop)
        Update-Grid -InputFiles $files -ClearGrid $false
    })

$dataGridView.Columns[0].Width = 355
$dataGridView.Columns[0].DefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleLeft
$dataGridView.Columns[0].ReadOnly = $false
$dataGridView.Columns[1].Width = 80
$dataGridView.Columns[1].DefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleCenter
$dataGridView.Columns[1].ReadOnly = $true
$dataGridView.Columns[2].Width = 200
$dataGridView.Columns[2].DefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleLeft
$dataGridView.Columns[2].ReadOnly = $true
$dataGridView.Columns[3].Width = 110
$dataGridView.Columns[3].DefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleCenter
$dataGridView.Columns[3].ReadOnly = $true
$dataGridView.Columns[4].Width = 140
$dataGridView.Columns[4].DefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleCenter
$dataGridView.Columns[4].ReadOnly = $true
$dataGridView.Columns[5].Width = 120
$dataGridView.Columns[5].DefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleCenter
$dataGridView.Columns[5].ReadOnly = $true
$dataGridView.Columns[6].Width = 120
$dataGridView.Columns[6].DefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleCenter
$dataGridView.Columns[6].ReadOnly = $true
$dataGridView.Columns[7].Width = 100
$dataGridView.Columns[7].DefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleCenter
$dataGridView.Columns[7].ReadOnly = $true
$dataGridView.Columns[8].Width = 290
$dataGridView.Columns[8].DefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleLeft
$dataGridView.Columns[8].ReadOnly = $true
$dataGridView.Columns[9].Width = 150
$dataGridView.Columns[9].DefaultCellStyle.Alignment = [System.Windows.Forms.DataGridViewContentAlignment]::MiddleCenter
$dataGridView.Columns[9].ReadOnly = $true
$dataGridView.RowTemplate.Height = 25
$dataGridView.BackgroundColor = [System.Drawing.Color]::Black
$dataGridView.BorderStyle = "FixedSingle"
$dataGridView.GridColor = [System.Drawing.Color]::Gray
$dataGridView.CellBorderStyle = [System.Windows.Forms.DataGridViewCellBorderStyle]::Single
$dataGridView.ColumnHeadersHeight = 35
$dataGridView.RowHeadersBorderStyle = [System.Windows.Forms.DataGridViewHeaderBorderStyle]::Single
$dataGridView.ColumnHeadersBorderStyle = [System.Windows.Forms.DataGridViewHeaderBorderStyle]::Single

$dataGridView.Add_CellEndEdit({
        param($sender, $e)
        if ($e.ColumnIndex -eq 0) {
            $newName = $dataGridView.Rows[$e.RowIndex].Cells[0].Value
            $newName = Sanitize-FileName $newName
            $dataGridView.Rows[$e.RowIndex].Cells[0].Value = $newName
        
            $oldName = $null
            foreach ($key in $script:filePathsMap.Keys) {
                if ($script:filePathsMap[$key] -and -not $script:customFileNames.ContainsValue($key)) {
                    $found = $false
                    foreach ($row in $dataGridView.Rows) {
                        if ($row.Index -eq $e.RowIndex) {
                            foreach ($cfnKey in $script:customFileNames.Keys) {
                                if ($script:customFileNames[$cfnKey] -eq $key) {
                                    $oldName = $cfnKey
                                    $found = $true
                                    break
                                }
                            }
                            if (-not $found) {
                                $oldName = $key
                            }
                            break
                        }
                    }
                    if ($found -or $oldName) { break }
                }
            }
        
            if (-not $oldName) {
                $rowIndex = 0
                foreach ($key in $script:filePathsMap.Keys) {
                    if ($rowIndex -eq $e.RowIndex) {
                        $oldName = $key
                        break
                    }
                    $rowIndex++
                }
            }
        
            if ($oldName -and $oldName -ne $newName) {
                $script:customFileNames[$newName] = $oldName
                $txtLog.AppendText("$(T 'LogRenamed') $oldName -> $newName`r`n")
            }
        }
    })

$dataGridView.Add_KeyDown({
        if ($_.KeyCode -eq [System.Windows.Forms.Keys]::Delete) {
            $menuItemDelete.PerformClick()
        }
        if ($_.Control -and $_.KeyCode -eq [System.Windows.Forms.Keys]::C) {
            if ($dataGridView.SelectedCells.Count -gt 0) {
                $cell = $dataGridView.SelectedCells[0]
                if ($cell.Value) {
                    [System.Windows.Forms.Clipboard]::SetText($cell.Value.ToString())
                }
            }
        }
    })

$lblCreatedBy = New-Object System.Windows.Forms.Label
$lblCreatedBy.Location = New-Object System.Drawing.Point(680, 915)
$lblCreatedBy.Size = New-Object System.Drawing.Size(180, 20)
$lblCreatedBy.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter
$lblCreatedBy.Cursor = [System.Windows.Forms.Cursors]::Hand
$lblCreatedBy.Add_Click({ Start-Process "https://4pda.to/forum/index.php?showuser=7365134" })

$lblVersion = New-Object System.Windows.Forms.Label
$lblVersion.Location = New-Object System.Drawing.Point(870, 915)
$lblVersion.Size = New-Object System.Drawing.Size(180, 20)
$lblVersion.TextAlign = [System.Drawing.ContentAlignment]::MiddleCenter

$btnPause = New-Object System.Windows.Forms.Button
$btnPause.Location = New-Object System.Drawing.Point(10, 910)
$btnPause.Size = New-Object System.Drawing.Size(100, 35)
$btnPause.FlatStyle = "Flat"
$btnPause.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$btnPause.FlatAppearance.BorderSize = 1
$btnPause.Cursor = [System.Windows.Forms.Cursors]::Hand
$btnPause.Add_Click({
        if ($script:isPaused) {
            $script:isPaused = $false
            $btnPause.Text = (T "BtnPause")
            $txtLog.AppendText("$(T 'MsgProcessResumed')`r`n")
        }
        else {
            $script:isPaused = $true
            $btnPause.Text = (T "BtnResume")
            $txtLog.AppendText("$(T 'MsgProcessPaused')`r`n")
        }
    })

$btnCancel = New-Object System.Windows.Forms.Button
$btnCancel.Location = New-Object System.Drawing.Point(120, 910)
$btnCancel.Size = New-Object System.Drawing.Size(100, 35)
$btnCancel.FlatStyle = "Flat"
$btnCancel.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$btnCancel.FlatAppearance.BorderSize = 1
$btnCancel.Cursor = [System.Windows.Forms.Cursors]::Hand
$btnCancel.Add_Click({
        $result = [System.Windows.Forms.MessageBox]::Show((T "MsgCancelProcess"), (T "MsgConfirmation"), [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
        if ($result -eq "Yes") {
            $script:isCancelled = $true
            Kill-AllCHDManProcesses
            $txtLog.AppendText("$(T 'MsgProcessCancelled')`r`n")
        }
    })

$btnExecute = New-Object System.Windows.Forms.Button
$btnExecute.Location = New-Object System.Drawing.Point(1580, 910)
$btnExecute.Size = New-Object System.Drawing.Size(100, 35)
$btnExecute.FlatStyle = "Flat"
$btnExecute.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$btnExecute.FlatAppearance.BorderSize = 1
$btnExecute.Cursor = [System.Windows.Forms.Cursors]::Hand
$btnExecute.Add_Click({
        # Обновленная логика получения файлов (только из таблицы)
        $gamesToProcess = @()
        foreach ($row in $dataGridView.Rows) {
            $displayName = $row.Cells[0].Value
            $originalFileName = $displayName
            if ($script:customFileNames.ContainsKey($displayName)) {
                $originalFileName = $script:customFileNames[$displayName]
            }
            if ($script:filePathsMap.ContainsKey($originalFileName)) {
                $gamesToProcess += @{
                    DisplayName = $displayName
                    FileName    = $originalFileName
                    FilePath    = $script:filePathsMap[$originalFileName]
                    RowIndex    = $row.Index
                }
            }
        }
    
        if ($gamesToProcess.Count -eq 0) {
            [System.Windows.Forms.MessageBox]::Show((T "MsgNoFilesSelected"), (T "StatusError"), [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
            return
        }
    
        $outputFolder = $txtOutput.Text
        if (-not $outputFolder) { $outputFolder = $PSScriptRoot }
    
        $gamesFolder = Join-Path $outputFolder "GAMES"
        if (-not (Test-Path -LiteralPath $gamesFolder)) {
            New-Item -ItemType Directory -Path $gamesFolder | Out-Null
        }
    
        $progressProcess.Maximum = [Math]::Max($gamesToProcess.Count, 1)
        $progressProcess.Value = 0
        $currentGameIndex = 0
        $script:isPaused = $false
        $script:isCancelled = $false
        $script:activeProcesses = @()
    
        $txtLog.AppendText("`r`n$(T 'MsgStartProcessing')`r`n")
        $txtLog.AppendText("$(T 'MsgTotalGames'): $($gamesToProcess.Count)`r`n`r`n")
    
        foreach ($gameInfo in $gamesToProcess) {
            if ($script:isCancelled) { break }
            while ($script:isPaused) {
                Start-Sleep -Milliseconds 100
                [System.Windows.Forms.Application]::DoEvents()
            }
        
            try {
                $file = $gameInfo.FilePath
                $displayName = $gameInfo.DisplayName
                $rowIndex = $gameInfo.RowIndex
            
                $fileItem = Get-Item -LiteralPath $file -ErrorAction Stop
                if ($fileItem.PSIsContainer) { continue }
                if (-not (Test-Path -LiteralPath $file)) { 
                    $txtLog.AppendText("$(T 'LogFileNotFound') $file`r`n")
                    continue 
                }
            
                $fileSize = 0
                if ($file -match "\.cue$|\.gdi$|\.mds$|\.ccd$|\.toc$") {
                    $binFiles = Get-BinFilesFromCueOrGdi $file
                    foreach ($binFile in $binFiles) {
                        $fileSize += (Get-Item -LiteralPath $binFile).Length
                    }
                    if (-not $binFiles) { 
                        $txtLog.AppendText("$(T 'LogNoLinkedFiles') $file`r`n")
                        continue 
                    }
                }
                else {
                    $fileSize = $fileItem.Length
                }
            
                $currentGameIndex++
                $lblProcessStatus.Text = "$(T 'LogProcessingItem') $currentGameIndex $(T 'StFrom') $($gamesToProcess.Count): $displayName"
                $txtLog.AppendText("[$currentGameIndex/$($gamesToProcess.Count)] $(T 'LogProcessingItem') $displayName`r`n")
            
                $platform = $dataGridView.Rows[$rowIndex].Cells[2].Value
                $format = $dataGridView.Rows[$rowIndex].Cells[3].Value
            
                $txtLog.AppendText("$(T 'LogFormatDef') $format ($(T 'LogSize') $(Get-ReadableSize $fileSize))`r`n")
            
                $command = if ($fileItem.Extension -eq ".chd") {
                    if ($format -match "CD-ROM") { "extractcd" } else { "extractdvd" }
                }
                else {
                    if ($format -match "CD-ROM") { "createcd" } else { "createdvd" }
                }
            
                $compression = if ($chkAetherSX2.Checked) { "zlib" } else { $diskCompression.SelectedItem }
                $hunkSize = if ($format -match "CD-ROM") { $diskCDHunk.SelectedItem } else { $diskDVDHunk.SelectedItem }
            
                $txtLog.AppendText("$(T 'LogCommand') $command, $(T 'LblCompression') $compression, $(T 'LblCDHunk') $hunkSize`r`n")
            
                $outputPath = if ($platform -and $chkRecognition.Checked) {
                    $platformFolder = Join-Path $gamesFolder $platform
                    if (-not (Test-Path -LiteralPath $platformFolder)) { New-Item -ItemType Directory -Path $platformFolder | Out-Null }
                    $platformFolder
                }
                else { $gamesFolder }
            
                $outputFile = Join-Path $outputPath ($displayName + ".chd")
                $dataGridView.Rows[$rowIndex].Cells[4].Value = (T "StatusWorking")
            
                $args = @($command, "-i", "`"$file`"", "-o", "`"$outputFile`"")
                if ($command -in @("createcd", "createdvd")) {
                    $args += "-c", $compression, "-hs", $hunkSize, "--numprocessors", $diskCores.SelectedItem
                }
                if ($chkForce.Checked) { $args += "-f" }
            
                $txtLog.AppendText("$(T 'LogSourceFile') $file`r`n")
                $txtLog.AppendText("$(T 'LogCommand') $chdmanExe $($args -join ' ')`r`n")
                $txtLog.AppendText("$(T 'LogStartProcess')`r`n")
            
                $psi = New-Object System.Diagnostics.ProcessStartInfo
                $psi.FileName = $chdmanExe
                $psi.Arguments = $args -join ' '
                $psi.UseShellExecute = $false
                $psi.RedirectStandardOutput = $true
                $psi.RedirectStandardError = $true
                $psi.CreateNoWindow = $true
                $psi.WorkingDirectory = $PSScriptRoot
            
                $process = New-Object System.Diagnostics.Process
                $process.StartInfo = $psi
                $null = $process.Start()
                $script:activeProcesses += $process
            
                $output = New-Object System.Text.StringBuilder
                $errorOutput = New-Object System.Text.StringBuilder
            
                $outputHandler = { if (-not [String]::IsNullOrEmpty($EventArgs.Data)) { $Event.MessageData.AppendLine($EventArgs.Data) } }
                $outputEvent = Register-ObjectEvent -InputObject $process -EventName 'OutputDataReceived' -Action $outputHandler -MessageData $output
                $errorEvent = Register-ObjectEvent -InputObject $process -EventName 'ErrorDataReceived' -Action $outputHandler -MessageData $errorOutput
            
                $process.BeginOutputReadLine()
                $process.BeginErrorReadLine()
            
                $startTime = [DateTime]::Now
                $progressCheckInterval = 5
                $lastLogTime = 0
            
                while (-not $process.HasExited -and -not $script:isCancelled) {
                    if ($script:isPaused) {
                        Start-Sleep -Milliseconds 100
                        [System.Windows.Forms.Application]::DoEvents()
                        continue
                    }
                    $elapsedSeconds = [int](([DateTime]::Now - $startTime).TotalSeconds)
                    if ($elapsedSeconds -gt 0 -and $elapsedSeconds % $progressCheckInterval -eq 0 -and $elapsedSeconds -ne $lastLogTime) {
                        $txtLog.AppendText("$(T 'LogProcessRunning') $elapsedSeconds $(T 'LogSec')`r`n")
                        $lastLogTime = $elapsedSeconds
                    }
                    $process.WaitForExit(2000)
                    [System.Windows.Forms.Application]::DoEvents()
                }
            
                if ($script:isCancelled) {
                    if (-not $process.HasExited) { try { $process.Kill(); $process.WaitForExit(2000) } catch { } }
                    Unregister-Event -SourceIdentifier $outputEvent.Name -ErrorAction SilentlyContinue
                    Unregister-Event -SourceIdentifier $errorEvent.Name -ErrorAction SilentlyContinue
                    $dataGridView.Rows[$rowIndex].Cells[4].Value = (T "StatusCancelled")
                    $txtLog.AppendText("$(T 'MsgProcessCancelled')`r`n`r`n")
                    $script:activeProcesses = $script:activeProcesses | Where-Object { $_ -ne $process }
                    continue
                }
            
                $process.WaitForExit()
                Unregister-Event -SourceIdentifier $outputEvent.Name -ErrorAction SilentlyContinue
                Unregister-Event -SourceIdentifier $errorEvent.Name -ErrorAction SilentlyContinue
            
                $exitCode = $process.ExitCode
                $stdout = $output.ToString()
                $stderr = $errorOutput.ToString()
                $totalTime = [int](([DateTime]::Now - $startTime).TotalSeconds)
            
                if ($exitCode -eq 0 -and (Test-Path -LiteralPath $outputFile)) {
                    $dataGridView.Rows[$rowIndex].Cells[4].Value = (T "StatusDone")
                    $outputSize = (Get-Item -LiteralPath $outputFile).Length
                    $dataGridView.Rows[$rowIndex].Cells[6].Value = (Get-ReadableSize $outputSize)
                    $ratio = ($outputSize / $fileSize) * 100
                    $dataGridView.Rows[$rowIndex].Cells[7].Value = "{0:N1}%" -f $ratio
                    $txtLog.AppendText("$(T 'LogSuccess') $displayName`r`n")
                    $txtLog.AppendText("$(T 'LogOriginalSize') $(Get-ReadableSize $fileSize)`r`n")
                    $txtLog.AppendText("$(T 'LogFinalSize') $(Get-ReadableSize $outputSize)`r`n")
                    $txtLog.AppendText("$(T 'LogCompRatio') {0:N1}%`r`n" -f $ratio)
                    $txtLog.AppendText("$(T 'LogTime') $totalTime $(T 'LogSec')`r`n`r`n")
                }
                else {
                    $dataGridView.Rows[$rowIndex].Cells[4].Value = (T "StatusError")
                    $txtLog.AppendText("$(T 'LogErrorProcess') $displayName $(T 'LogExitCode') $exitCode)`r`n")
                    if ($stdout) { $txtLog.AppendText("$(T 'LogOutput') $($stdout.Substring(0, [Math]::Min(500, $stdout.Length)))`r`n") }
                    if ($stderr) { $txtLog.AppendText("$(T 'LogErrors') $($stderr.Substring(0, [Math]::Min(500, $stderr.Length)))`r`n") }
                    $txtLog.AppendText("`r`n")
                }
            
                $script:activeProcesses = $script:activeProcesses | Where-Object { $_ -ne $process }
                $process.Dispose()
            
            }
            catch {
                if ($rowIndex -ne -1) { $dataGridView.Rows[$rowIndex].Cells[4].Value = (T "StatusError") }
                $txtLog.AppendText("$(T 'LogException') $_`r`n")
            }
        
            if ($currentGameIndex -le $progressProcess.Maximum) { $progressProcess.Value = $currentGameIndex }
            [System.Windows.Forms.Application]::DoEvents()
        }
    
        $txtLog.AppendText("$(T 'MsgEndProcessing')`r`n")
        $txtLog.AppendText("$(T 'MsgProcessedCount'): $currentGameIndex $(T 'StFrom') $($gamesToProcess.Count)`r`n`r`n")
        Kill-AllCHDManProcesses
    
        if ($chkSoundNotification.Checked -and -not $script:isCancelled) { [System.Media.SystemSounds]::Beep.Play() }
        if ($chkTextNotification.Checked -and -not $script:isCancelled) {
            [System.Windows.Forms.MessageBox]::Show((T "MsgProcessingComplete") + "`r`n" + (T "MsgProcessedCount") + ": $currentGameIndex " + (T "StFrom") + " $($gamesToProcess.Count)", (T "StatusDone"), [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
        }
    })

$btnClose = New-Object System.Windows.Forms.Button
$btnClose.Location = New-Object System.Drawing.Point(1470, 910)
$btnClose.Size = New-Object System.Drawing.Size(100, 35)
$btnClose.FlatStyle = "Flat"
$btnClose.Font = New-Object System.Drawing.Font("Century Gothic", 9, [System.Drawing.FontStyle]::Bold)
$btnClose.FlatAppearance.BorderSize = 1
$btnClose.Cursor = [System.Windows.Forms.Cursors]::Hand
$btnClose.Add_Click({ $form.Close() })

$form.Controls.AddRange(@(
        $customHeader,
        $btnDownloadDATs, $btnDeleteDATs, $btnClearSerialCache,
        $cmbLanguage, $diskTheme,
        $lblDownloadStatus, $progressDownload,
        # REMOVED: Input controls
        $lblOutput, $txtOutput, $btnBrowseOutput, $btnClearOutput,
        $lblCores, $lblCompression, $lblCDHunk, $lblDVDHunk,
        $diskCores, $diskCompression, $diskCDHunk, $diskDVDHunk,
        $panelForce, $panelRecognition, $panelAetherSX2, $panelTextNotification, $panelSoundNotification,
        $lblProcessStatus, $progressProcess, $txtLog, $dataGridView,
        $lblCreatedBy, $lblVersion,
        $btnPause, $btnCancel, $btnExecute, $btnClose
    ))

$panelForce.Controls.Add($chkForce)
$panelRecognition.Controls.Add($chkRecognition)
$panelAetherSX2.Controls.Add($chkAetherSX2)
$panelTextNotification.Controls.Add($chkTextNotification)
$panelSoundNotification.Controls.Add($chkSoundNotification)

Load-HashCache
Load-SerialCache
Load-Settings
Update-Interface
Set-Theme $diskTheme.SelectedItem

$txtLog.AppendText("$(T 'LogStarted')`r`n")
$txtLog.AppendText("$(T 'LogReady')`r`n`r`n")

$form.ShowDialog()