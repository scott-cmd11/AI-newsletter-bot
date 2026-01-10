# ============================================================================
# AI This Week - Vibecoding Framework Orchestration Script
# ============================================================================
# This script runs the complete Scout -> Editor -> Publisher pipeline
# with manual curation checkpoints.
#
# Usage: .\run_report.ps1
# ============================================================================

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  AI This Week - Newsletter Generator" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Run the Scout Agent
Write-Host "[1/4] Running Scout Agent..." -ForegroundColor Yellow
python -m src.agents.scout

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Scout agent failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Scout complete. Raw intelligence saved to data/raw_intel.json" -ForegroundColor Green
Write-Host ""

# Curation Checkpoint 1
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "  CURATION CHECKPOINT 1" -ForegroundColor Magenta
Write-Host "  Review/edit: data\raw_intel.json" -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta
Read-Host "Press Enter to continue to the Editor..."

# Step 2: Run the Editor Agent
Write-Host ""
Write-Host "[2/4] Running Editor Agent (YODA Filter)..." -ForegroundColor Yellow
python -c "from src.processors.summarizer import generate_curated_report; generate_curated_report()"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Editor agent failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Editor complete. Curated report saved to data/curated_report.json" -ForegroundColor Green
Write-Host ""

# Curation Checkpoint 2
Write-Host "==========================================" -ForegroundColor Magenta
Write-Host "  CURATION CHECKPOINT 2" -ForegroundColor Magenta
Write-Host "  Review/edit: data\curated_report.json" -ForegroundColor Magenta
Write-Host "==========================================" -ForegroundColor Magenta
Read-Host "Press Enter to continue to the Publisher..."

# Step 3: Run the Publisher Agent
Write-Host ""
Write-Host "[3/4] Running Publisher Agent (PDF Generation)..." -ForegroundColor Yellow
python -m src.agents.publisher

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Publisher agent failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Publisher complete!" -ForegroundColor Green

# Step 4: Open the generated PDF
Write-Host ""
Write-Host "[4/4] Opening generated PDF..." -ForegroundColor Yellow

$pdfFile = Get-ChildItem -Path "output" -Filter "AI_This_Week_*.pdf" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($pdfFile) {
    Write-Host "Opening: $($pdfFile.FullName)" -ForegroundColor Green
    Start-Process $pdfFile.FullName
} else {
    Write-Host "WARNING: No PDF found in output directory" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Pipeline Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
