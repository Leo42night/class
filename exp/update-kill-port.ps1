# Mencari semua file package.json di struktur folder \*\apps\frontend\
# run: buka powershell -> ./update
$targetFiles = Get-ChildItem -Path ".\*\apps\frontend\package.json"

if ($targetFiles.Count -eq 0) {
    Write-Host "Tidak ditemukan file package.json di struktur .\*\apps\frontend\" -ForegroundColor Yellow
} else {
    foreach ($file in $targetFiles) {
        # Membaca isi file
        $content = Get-Content -Path $file.FullName -Raw
        
        # Cek apakah kata "vite" ada untuk diganti
        if ($content -match '"dev":\s*"vite"') {
            # Melakukan replace
            $newContent = $content -replace '"dev":\s*"vite"', '"dev": "bunx kill-port 5173 && vite"'
            
            # Menyimpan kembali ke file
            $newContent | Set-Content -Path $file.FullName -Encoding UTF8
            Write-Host "Berhasil Update: $($file.FullName)" -ForegroundColor Green
        } else {
            Write-Host "Sudah terupdate atau format berbeda: $($file.FullName)" -ForegroundColor Cyan
        }
    }
}

Write-Host "`nProses Selesai!" -ForegroundColor White
pause