param(
    [string]$Root = "pics"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $scriptDir

Add-Type -AssemblyName System.Drawing

$dates = @("20260622", "20260623", "20260624")
$siteCode = "SC01"
$pictureNames = @("a.JPG", "b.JPG", "c.JPG")
$labelPrefixes = @("PUMP", "VALVE", "RISER", "LIGHT", "PANEL", "DRAIN", "PIPE", "METER")

function New-RandomLabel {
    $prefix = $labelPrefixes | Get-Random
    $number = Get-Random -Minimum 100 -Maximum 999
    return "$prefix-$number"
}

function New-RandomColor {
    $red = Get-Random -Minimum 35 -Maximum 210
    $green = Get-Random -Minimum 35 -Maximum 210
    $blue = Get-Random -Minimum 35 -Maximum 210
    return [System.Drawing.Color]::FromArgb($red, $green, $blue)
}

function Save-Jpeg {
    param(
        [Parameter(Mandatory = $true)]
        [System.Drawing.Bitmap]$Bitmap,

        [Parameter(Mandatory = $true)]
        [string]$Path,

        [long]$Quality = 90
    )

    $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() |
        Where-Object { $_.MimeType -eq "image/jpeg" } |
        Select-Object -First 1

    $qualityEncoder = [System.Drawing.Imaging.Encoder]::Quality
    $encoderParameters = New-Object System.Drawing.Imaging.EncoderParameters 1
    $encoderParameters.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter $qualityEncoder, $Quality

    try {
        $Bitmap.Save($Path, $codec, $encoderParameters)
    }
    finally {
        $encoderParameters.Dispose()
    }
}

function New-SamplePicture {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$DateText,

        [Parameter(Mandatory = $true)]
        [string]$SiteCode,

        [Parameter(Mandatory = $true)]
        [string]$PictureLabel,

        [Parameter(Mandatory = $true)]
        [System.Drawing.Color]$BackgroundColor
    )

    $width = 1200
    $height = 800
    $bitmap = New-Object System.Drawing.Bitmap $width, $height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)

    try {
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.Clear($BackgroundColor)

        $whiteBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
        $softBrush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(70, 255, 255, 255))
        $borderPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(220, 255, 255, 255)), 8
        $gridPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(55, 255, 255, 255)), 2
        $titleFont = New-Object System.Drawing.Font "Arial", 64, ([System.Drawing.FontStyle]::Bold)
        $labelFont = New-Object System.Drawing.Font "Arial", 180, ([System.Drawing.FontStyle]::Bold)
        $smallFont = New-Object System.Drawing.Font "Arial", 34, ([System.Drawing.FontStyle]::Regular)
        $centerFormat = New-Object System.Drawing.StringFormat
        $centerFormat.Alignment = [System.Drawing.StringAlignment]::Center
        $centerFormat.LineAlignment = [System.Drawing.StringAlignment]::Center

        for ($x = 0; $x -le $width; $x += 120) {
            $graphics.DrawLine($gridPen, $x, 0, $x, $height)
        }
        for ($y = 0; $y -le $height; $y += 120) {
            $graphics.DrawLine($gridPen, 0, $y, $width, $y)
        }

        $graphics.FillEllipse($softBrush, 780, 120, 260, 260)
        $graphics.DrawRectangle($borderPen, 32, 32, $width - 64, $height - 64)

        $graphics.DrawString("Cleaners Report Sample", $titleFont, $whiteBrush, 60, 70)
        $graphics.DrawString("$DateText  |  $SiteCode", $smallFont, $whiteBrush, 66, 165)

        $labelRect = New-Object System.Drawing.RectangleF 0, 260, $width, 270
        $graphics.DrawString($PictureLabel, $labelFont, $whiteBrush, $labelRect, $centerFormat)

        $graphics.DrawString((Split-Path -Leaf $Path), $smallFont, $whiteBrush, 66, 660)

        Save-Jpeg -Bitmap $bitmap -Path $Path
    }
    finally {
        if ($centerFormat) { $centerFormat.Dispose() }
        if ($smallFont) { $smallFont.Dispose() }
        if ($labelFont) { $labelFont.Dispose() }
        if ($titleFont) { $titleFont.Dispose() }
        if ($gridPen) { $gridPen.Dispose() }
        if ($borderPen) { $borderPen.Dispose() }
        if ($softBrush) { $softBrush.Dispose() }
        if ($whiteBrush) { $whiteBrush.Dispose() }
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}

$rootPath = Join-Path $scriptDir $Root

foreach ($date in $dates) {
    $targetFolder = Join-Path $rootPath (Join-Path $date $siteCode)
    New-Item -ItemType Directory -Force -Path $targetFolder | Out-Null

    foreach ($pictureName in $pictureNames) {
        $picturePath = Join-Path $targetFolder $pictureName
        New-SamplePicture `
            -Path $picturePath `
            -DateText $date `
            -SiteCode $siteCode `
            -PictureLabel (New-RandomLabel) `
            -BackgroundColor (New-RandomColor)

        Write-Host "CREATED $picturePath"
    }
}

Write-Host ""
Write-Host "Sample pics folder created at: $rootPath"
