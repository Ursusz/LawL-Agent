## Configurare Locala

### Cerinte

Dependinte:

* **Python > 3.12**
* **Node.js** de [aici](https://nodejs.org/en/download)
* **uv** - Se poate instala cu `pipx` pentru a evita conflictele de sistem:
    ```bash
    pipx install uv
    ```

***

### 1. Configure Backend

1. 
    ```bash
    cd backend
    ```
2. 
    ```bash
    uv venv
    source venv/bin/activate
    ```
3. 
    ```bash
    uv pip install -r requirements.txt
    ```
4. 
    ```bash
    uvicorn main:app --reload
    ```
    Serverul va porni pe `http://127.0.0.1:8000`.

***

### 2. Configurare Frontend

1. 
    ```bash
    cd ../frontend
    ```
2.
    ```bash
    npm install
    ```
3.
    ```bash
    npm start
    ```
    Aplicatia se va deschide pe `http://localhost:3000`.