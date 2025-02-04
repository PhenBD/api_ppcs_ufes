python3 -m venv venv
source venv/bin/activate
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
sudo apt-get update
sudo apt-get install ghostscript
uvicorn main:app --reload