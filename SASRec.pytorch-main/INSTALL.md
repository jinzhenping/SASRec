# Installation Guide

## Quick Start

### 1. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

**For GPU training (CUDA):**
```bash
# First install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
# Then install other dependencies
pip install -r requirements-cuda.txt
```

**For CPU only:**
```bash
# First install PyTorch CPU version
pip install torch torchvision torchaudio
# Then install other dependencies
pip install -r requirements-cpu.txt
```

**Or install everything manually:**
```bash
# GPU version
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install numpy

# CPU version
pip install torch torchvision torchaudio
pip install numpy
```

### 3. Verify Installation

```bash
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 4. Run Training

```bash
cd python
python main.py --dataset=MIND --train_dir=default --device=cuda:0 --maxlen=200
```

## Requirements

- Python 3.6 or higher
- PyTorch 1.6.0 or higher
- NumPy 1.19.0 or higher
- CUDA (optional, for GPU training)

