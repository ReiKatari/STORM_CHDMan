
# Load required assemblies for ZipFile
Add-Type -AssemblyName System.IO.Compression.FileSystem

$datsFolder = "F:\MY SOFT\STORM CHDMan (Github)\PythonVersion\DATs"
$datUrls = @(
    "http://redump.org/datfile/arch/", "http://redump.org/datfile/mac/", "http://redump.org/datfile/ajcd/", "http://redump.org/datfile/pippin/", "http://redump.org/datfile/qis/", "http://redump.org/datfile/acd/", "http://redump.org/datfile/cdtv/", "http://redump.org/datfile/fmt/", "http://redump.org/datfile/fpp/", "http://redump.org/datfile/pc/", "http://redump.org/datfile/ite/", "http://redump.org/datfile/kea/", "http://redump.org/datfile/kfb/", "http://redump.org/datfile/ks573/", "http://redump.org/datfile/ksgv/", "http://redump.org/datfile/ixl/", "http://redump.org/datfile/hs/", "http://redump.org/datfile/vis/", "http://redump.org/datfile/xbox/", "http://redump.org/datfile/xbox360/", "http://redump.org/datfile/trf/", "http://redump.org/datfile/ns246/", "http://redump.org/datfile/pce/", "http://redump.org/datfile/pc-88/", "http://redump.org/datfile/pc-98/", "http://redump.org/datfile/pc-fx/", "http://redump.org/datfile/ngcd/", "http://redump.org/datfile/gc/", "http://redump.org/datfile/wii/", "http://redump.org/datfile/palm/", "http://redump.org/datfile/3do/", "http://redump.org/datfile/cdi/", "http://redump.org/datfile/photo-cd/", "http://redump.org/datfile/psxgs/", "http://redump.org/datfile/ppc/", "http://redump.org/datfile/chihiro/", "http://redump.org/datfile/dc/", "http://redump.org/datfile/lindbergh/", "http://redump.org/datfile/mcd/", "http://redump.org/datfile/naomi/", "http://redump.org/datfile/naomi2/", "http://redump.org/datfile/sp21/", "http://redump.org/datfile/sre/", "http://redump.org/datfile/sre2/", "http://redump.org/datfile/ss/", "http://redump.org/datfile/x68k/", "http://redump.org/datfile/psx/", "http://redump.org/datfile/ps2/", "http://redump.org/datfile/ps3/", "http://redump.org/datfile/psp/", "http://redump.org/datfile/quizard/", "http://redump.org/datfile/ksite/", "http://redump.org/datfile/nuon/", "http://redump.org/datfile/vflash/", "http://redump.org/datfile/gamewave/", "http://redump.org/datfile/cd32/"
)

# Reuse single WebClient instance as per original script
$webClient = New-Object System.Net.WebClient
# Enable TLS 1.2/1.3 explicitly to be safe, although original script didn't need it, sometimes Py+PS environment differs
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12 -bor [System.Net.SecurityProtocolType]::Tls13

$count = 0
foreach ($url in $datUrls) {
    $count++
    $fileName = $url.TrimEnd('/').Split('/')[-1] + ".zip"
    if ($fileName -eq ".zip") { $fileName = "dat_$count.zip" }
    $outputPath = Join-Path $datsFolder $fileName
    
    # Use Console.WriteLine to BYPASS PIPELINE BUFFERING
    [Console]::WriteLine("START|$count|$fileName")
    
    try {
        # Force remove before download to ensure clean state
        if (Test-Path $outputPath) { Remove-Item -LiteralPath $outputPath -Force -ErrorAction SilentlyContinue }
        
        $webClient.DownloadFile($url, $outputPath)
        
        if (Test-Path $outputPath) {
            if ((Get-Item $outputPath).Length -gt 0) {
                try {
                    # Overwrite if exists logic for ZipFile
                    $zip = [System.IO.Compression.ZipFile]::OpenRead($outputPath)
                    foreach ($entry in $zip.Entries) {
                        $targetPath = Join-Path $datsFolder $entry.FullName
                        if (Test-Path $targetPath) { Remove-Item -LiteralPath $targetPath -Force }
                        [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $targetPath)
                    }
                    $zip.Dispose()
                    
                    Remove-Item -LiteralPath $outputPath -Force -ErrorAction SilentlyContinue
                    [Console]::WriteLine("SUCCESS")
                } catch {
                    [Console]::WriteLine("FAIL|Extract: $($_.Exception.Message)")
                }
            } else {
                Remove-Item -LiteralPath $outputPath -Force -ErrorAction SilentlyContinue
                [Console]::WriteLine("FAIL|EmptyFile")
            }
        } else {
            [Console]::WriteLine("FAIL|NoFile")
        }
    } catch {
        [Console]::WriteLine("FAIL|$($_.Exception.Message)")
    }
}
