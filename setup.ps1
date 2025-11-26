# ROOMie v2.0 - Quick Setup Script
# Run this script to set up both backend and frontend

Write-Host "🚀 ROOMie v2.0 Setup Script" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Check Python
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 16+" -ForegroundColor Red
    exit 1
}

# Backend Setup
Write-Host "`n📦 Setting up Backend..." -ForegroundColor Cyan
Set-Location backend

Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check for .env file
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "⚠️  IMPORTANT: Edit backend/.env and add your OPENAI_API_KEY" -ForegroundColor Red
    Write-Host "   Get your API key from: https://platform.openai.com/api-keys`n" -ForegroundColor Yellow
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# Create audio directory
if (-not (Test-Path audio)) {
    New-Item -ItemType Directory -Path audio | Out-Null
    Write-Host "✓ Created audio directory" -ForegroundColor Green
}

Set-Location ..

# Frontend Setup
Write-Host "`n🎨 Setting up Frontend..." -ForegroundColor Cyan
Set-Location frontend

Write-Host "Installing Node dependencies..." -ForegroundColor Yellow
npm install

Set-Location ..

# Final Instructions
Write-Host "`n✅ Setup Complete!" -ForegroundColor Green
Write-Host "================================`n" -ForegroundColor Cyan

Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Edit backend/.env and add your OPENAI_API_KEY" -ForegroundColor White
Write-Host "2. Start the backend:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   python app.py" -ForegroundColor Gray
Write-Host "3. In a new terminal, start the frontend:" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host "4. Open http://localhost:5173 in your browser`n" -ForegroundColor White

Write-Host "🎉 Enjoy ROOMie v2.0!" -ForegroundColor Cyan
