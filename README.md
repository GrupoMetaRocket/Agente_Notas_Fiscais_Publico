# Agente_Notas_Fiscais

Implementação de um agente para consultar e responder perguntas referentes à notas fiscais fornecidas.

> ⚠️ Este repositório **não possui** uma chave de acesso da API da **Perplexity**. É preciso fornecer uma no arquivo **config.yaml**.

## Clonar o repositório

```bash
git clone https://github.com/GrupoMetaRocket/Agente_Notas_Fiscais_Publico.git
```

## Configuração do ambiente

Navegue até a pasta raiz do projeto (`Agente_Notas_Fiscais_Publico`) e execute os seguintes passos:

### 1. Criar ambiente virtual

```bash
python -m venv agent
```

### 2. Ativar ambiente virtual

No Windows:

```bash
.\agent\Scripts\activate
```

> Lembre-se de sempre ativar o ambiente virtual antes de rodar os comandos abaixo.

### 3. Instalar dependências

```bash
pip install -r .\requirements.txt
```

> 💡 Isso pode demorar um pouco. Aproveite para tomar um café ☕.

## Executar a aplicação

Em terminais diferentes:

### 1. Rodar a API

```bash
python app.py
```

### 2. Rodar a interface (Streamlit)

```bash
python -m streamlit run chat.py
```

> ✅ Certifique-se de que o ambiente virtual está ativado para os comandos acima.
