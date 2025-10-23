#!/usr/bin/env pwsh
<#
.SYNOPSIS
    End-to-end smoke test for Retrovue streaming system.

.DESCRIPTION
    This script performs a complete smoke test of the Retrovue streaming system:
    1. Starts the FastAPI server
    2. Requests a stream from /iptv/channel/1.ts for 3 seconds
    3. Analyzes the output with ffprobe
    4. Performs hex sync check using Python module
    5. Exits with appropriate error codes

.PARAMETER ServerPort
    Port for the FastAPI server (default: 8000)

.PARAMETER OutputFile
    Output file for the stream capture (default: out.ts)

.PARAMETER ChannelId
    Channel ID to test (default: 1)

.EXAMPLE
    .\scripts\smoke_e2e.ps1
    .\scripts\smoke_e2e.ps1 -ServerPort 8001 -ChannelId 2
#>

param(
  [int]$ServerPort = 8000,
  [string]$OutputFile = "out.ts",
  [string]$ChannelId = "1"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Colors for output
$Red = "`e[31m"
$Green = "`e[32m"
$Yellow = "`e[33m"
$Blue = "`e[34m"
$Reset = "`e[0m"

function Write-ColorOutput {
  param([string]$Message, [string]$Color = $Reset)
  Write-Host "${Color}${Message}${Reset}"
}

function Test-Command {
  param([string]$Command)
  try {
    Get-Command $Command -ErrorAction Stop | Out-Null
    return $true
  }
  catch {
    return $false
  }
}

function Start-Server {
  Write-ColorOutput "🚀 Starting FastAPI server on port $ServerPort..." $Blue
    
  # Check if Python is available
  if (-not (Test-Command "python")) {
    Write-ColorOutput "❌ Python not found in PATH" $Red
    exit 1
  }
    
  # Start server in background
  $serverJob = Start-Job -ScriptBlock {
    param($port)
    Set-Location $using:PWD
    python run_server.py --port $port
  } -ArgumentList $ServerPort
    
  # Wait for server to start (give it 5 seconds)
  Write-ColorOutput "⏳ Waiting for server to start..." $Yellow
  Start-Sleep -Seconds 5
    
  # Check if server is responding
  try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$ServerPort/" -TimeoutSec 10 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
      Write-ColorOutput "✅ Server started successfully" $Green
    }
    else {
      Write-ColorOutput "❌ Server not responding properly" $Red
      Stop-Job $serverJob
      Remove-Job $serverJob
      exit 1
    }
  }
  catch {
    Write-ColorOutput "❌ Failed to connect to server: $($_.Exception.Message)" $Red
    Stop-Job $serverJob
    Remove-Job $serverJob
    exit 1
  }
    
  return $serverJob
}

function Test-StreamCapture {
  param([string]$Url, [string]$OutputFile, [int]$DurationSeconds = 3)
    
  Write-ColorOutput "📡 Capturing stream from $Url for $DurationSeconds seconds..." $Blue
    
  # Check if curl is available
  if (-not (Test-Command "curl")) {
    Write-ColorOutput "❌ curl not found in PATH" $Red
    exit 1
  }
    
  # Remove output file if it exists
  if (Test-Path $OutputFile) {
    Remove-Item $OutputFile -Force
  }
    
  # Use curl to capture stream with timeout
  $curlArgs = @(
    "-L",  # Follow redirects
    "-o", $OutputFile,  # Output file
    "-m", $DurationSeconds,  # Max time
    "--connect-timeout", "10",  # Connection timeout
    $Url
  )
    
  try {
    $curlProcess = Start-Process -FilePath "curl" -ArgumentList $curlArgs -NoNewWindow -Wait -PassThru
        
    if ($curlProcess.ExitCode -ne 0) {
      Write-ColorOutput "❌ curl failed with exit code $($curlProcess.ExitCode)" $Red
      exit 1
    }
        
    if (-not (Test-Path $OutputFile)) {
      Write-ColorOutput "❌ Output file not created" $Red
      exit 1
    }
        
    $fileSize = (Get-Item $OutputFile).Length
    if ($fileSize -eq 0) {
      Write-ColorOutput "❌ Output file is empty" $Red
      exit 1
    }
        
    Write-ColorOutput "✅ Stream captured successfully ($fileSize bytes)" $Green
        
  }
  catch {
    Write-ColorOutput "❌ Failed to capture stream: $($_.Exception.Message)" $Red
    exit 1
  }
}

function Test-FFProbe {
  param([string]$InputFile)
    
  Write-ColorOutput "🔍 Analyzing stream with ffprobe..." $Blue
    
  # Check if ffprobe is available
  if (-not (Test-Command "ffprobe")) {
    Write-ColorOutput "❌ ffprobe not found in PATH" $Red
    exit 1
  }
    
  try {
    # Run ffprobe to get stream information
    $ffprobeArgs = @(
      "-v", "quiet",
      "-print_format", "json",
      "-show_streams",
      $InputFile
    )
        
    $ffprobeProcess = Start-Process -FilePath "ffprobe" -ArgumentList $ffprobeArgs -NoNewWindow -Wait -PassThru -RedirectStandardOutput "ffprobe_output.json" -RedirectStandardError "ffprobe_error.txt"
        
    if ($ffprobeProcess.ExitCode -ne 0) {
      $errorContent = Get-Content "ffprobe_error.txt" -Raw
      Write-ColorOutput "❌ ffprobe failed: $errorContent" $Red
      exit 1
    }
        
    # Parse JSON output
    $probeData = Get-Content "ffprobe_output.json" -Raw | ConvertFrom-Json
        
    # Extract and display codec information
    Write-ColorOutput "📊 Stream Analysis:" $Blue
    Write-ColorOutput "Total streams: $($probeData.streams.Count)" $Yellow
        
    foreach ($stream in $probeData.streams) {
      $codecType = $stream.codec_type
      $codecName = $stream.codec_name
      $index = $stream.index
            
      if ($codecType -eq "video") {
        $width = $stream.width
        $height = $stream.height
        $bitrate = $stream.bit_rate
        Write-ColorOutput "  Video Stream $index`: $codecName (${width}x${height})" $Green
        if ($bitrate) {
          Write-ColorOutput "    Bitrate: $bitrate bps" $Yellow
        }
      }
      elseif ($codecType -eq "audio") {
        $sampleRate = $stream.sample_rate
        $channels = $stream.channels
        $bitrate = $stream.bit_rate
        Write-ColorOutput "  Audio Stream $index`: $codecName" $Green
        if ($sampleRate) {
          Write-ColorOutput "    Sample Rate: $sampleRate Hz" $Yellow
        }
        if ($channels) {
          Write-ColorOutput "    Channels: $channels" $Yellow
        }
        if ($bitrate) {
          Write-ColorOutput "    Bitrate: $bitrate bps" $Yellow
        }
      }
    }
        
    # Clean up temporary files
    Remove-Item "ffprobe_output.json" -ErrorAction SilentlyContinue
    Remove-Item "ffprobe_error.txt" -ErrorAction SilentlyContinue
        
    Write-ColorOutput "✅ FFprobe analysis completed" $Green
        
  }
  catch {
    Write-ColorOutput "❌ FFprobe analysis failed: $($_.Exception.Message)" $Red
    exit 1
  }
}

function Test-HexSync {
  param([string]$InputFile)
    
  Write-ColorOutput "🔍 Performing hex sync check..." $Blue
    
  # Check if Python is available
  if (-not (Test-Command "python")) {
    Write-ColorOutput "❌ Python not found in PATH" $Red
    exit 1
  }
    
  try {
    # Create a Python script to perform hex sync check
    $pythonScript = @"
import sys
import os
sys.path.insert(0, 'src')

from retrovue.web.server import analyze_ts_cadence

def main():
    input_file = '$InputFile'
    
    if not os.path.exists(input_file):
        print("❌ Input file not found: " + input_file)
        sys.exit(1)
    
    with open(input_file, 'rb') as f:
        data = f.read(4096)  # Read first 4KB for analysis
    
    if len(data) < 16:
        print("❌ Insufficient data for analysis")
        sys.exit(1)
    
    # Perform cadence analysis
    result = analyze_ts_cadence(data)
    
    print("🔍 Hex Sync Analysis:")
    print(f"  Valid: {result['valid']}")
    print(f"  Sync bytes found: {result['sync_count']}")
    
    if 'intervals' in result:
        print(f"  Intervals: {result['intervals']}")
        print(f"  Expected interval: {result['expected_interval']}")
    
    if 'first_sync_position' in result and result['first_sync_position'] is not None:
        print(f"  First sync at position: {result['first_sync_position']}")
    
    if not result['valid']:
        print("❌ Hex sync check failed")
        sys.exit(1)
    else:
        print("✅ Hex sync check passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
"@
        
    # Write Python script to temporary file
    $tempScript = "temp_sync_check.py"
    $pythonScript | Out-File -FilePath $tempScript -Encoding UTF8
        
    # Run the Python script
    $pythonProcess = Start-Process -FilePath "python" -ArgumentList $tempScript -NoNewWindow -Wait -PassThru
        
    # Clean up temporary script
    Remove-Item $tempScript -ErrorAction SilentlyContinue
        
    if ($pythonProcess.ExitCode -ne 0) {
      Write-ColorOutput "❌ Hex sync check failed" $Red
      exit 1
    }
        
    Write-ColorOutput "✅ Hex sync check completed successfully" $Green
        
  }
  catch {
    Write-ColorOutput "❌ Hex sync check failed: $($_.Exception.Message)" $Red
    exit 1
  }
}

function Cleanup {
  param([object]$ServerJob, [string]$OutputFile)
    
  Write-ColorOutput "🧹 Cleaning up..." $Blue
    
  # Stop server job if it exists
  if ($ServerJob) {
    Stop-Job $ServerJob -ErrorAction SilentlyContinue
    Remove-Job $ServerJob -ErrorAction SilentlyContinue
  }
    
  # Remove output file
  if (Test-Path $OutputFile) {
    Remove-Item $OutputFile -ErrorAction SilentlyContinue
  }
    
  # Clean up any temporary files
  Get-ChildItem -Path "." -Name "ffprobe_*" -ErrorAction SilentlyContinue | Remove-Item -ErrorAction SilentlyContinue
}

# Main execution
try {
  Write-ColorOutput "🧪 Starting Retrovue E2E Smoke Test" $Blue
  Write-ColorOutput "=====================================" $Blue
    
  $serverJob = $null
    
  try {
    # Step 1: Start FastAPI server
    $serverJob = Start-Server
        
    # Step 2: Capture stream
    $streamUrl = "http://127.0.0.1:$ServerPort/iptv/channel/$ChannelId.ts"
    Test-StreamCapture -Url $streamUrl -OutputFile $OutputFile -DurationSeconds 3
        
    # Step 3: Analyze with ffprobe
    Test-FFProbe -InputFile $OutputFile
        
    # Step 4: Perform hex sync check
    Test-HexSync -InputFile $OutputFile
        
    Write-ColorOutput "🎉 All tests passed successfully!" $Green
        
  }
  finally {
    # Always cleanup
    Cleanup -ServerJob $serverJob -OutputFile $OutputFile
  }
    
  exit 0
    
}
catch {
  Write-ColorOutput "💥 Smoke test failed: $($_.Exception.Message)" $Red
  Cleanup -ServerJob $serverJob -OutputFile $OutputFile
  exit 1
}
