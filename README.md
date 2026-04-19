## Setup Instructions

**1. Clone this repository:**
```bash
gh repo clone rezzraj/LegalLens
```
**2.Download the model weights from Google Drive:**
Download model weights: [Click here](https://drive.google.com/file/d/1WBj6kP0iH8ti0FJ4vVhnKsH0cKrqyJob/view?usp=sharing)
```bash
Two Folders:
model/
model_emb/
```
*Place the downloaded file inside the project folder without changing its name.***

**3.Clone the Gemma PyTorch repository:**
```bash
gh repo clone google/gemma_pytorch
```
**4.Install dependencies:**
```bash
pip install -r requirements.txt
```

**5.Run the application:**
streamlit run app.py


*Keep all files inside the project folder and do not rename any files, otherwise the app may not work correctly.***
