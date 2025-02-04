# Setup do Ambiente Virtual

1. **Crie o ambiente virtual**:

```bash
python3 -m venv venv
```

2. **Ative o ambiente virtual:**

* No Linux ou macOS:
```bash
source venv/bin/activate
```

* No Windows:
```bash
venv\Scripts\activate
```

3. **Instale as dependências:**

```bash
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

4. **Instale o Ghostscript:**

```bash
sudo apt-get update
sudo apt-get install ghostscript
```

5. **Execute a aplicação:**

```bash
uvicorn main:app --reload
```
