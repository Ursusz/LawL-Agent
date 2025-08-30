## Configurare Locala

### Cerinte

* **Python >= 3.12**
* **Node.js** de [aici](https://nodejs.org/en/download)
* **uv** - Se poate instala cu `pipx` pentru a evita conflictele de sistem:
    ```bash
    pipx install uv
    ```
* **antiword** - sudo apt-get update && sudo apt-get install antiword

***

### 1. Configure Backend

### Atentie! backend/src/utilities -> parse_law_title.py. Prima oara cand este rulat codul trebuie sters comentariul de la linia cu stanza.download("ro") apoi comentat inapoi.

#### Google Gemini API KEY -> https://aistudio.google.com/app/apikey

#### Brave Search API KEY -> https://brave.com/search/api/

 > In folderul backend se va crea un fisier **.env** cu urmatorul continut: GEMINI_API_KEY=your_api_key


1. 
    ```bash
    cd backend
    ```
2. 
    ```bash
    uv venv lawl
    source lawl/bin/activate
    ```
3. 
    ```bash
    uv pip install -r requirements.lock
    ```
4.
    ```bash
    cd src
    ```
5. 
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