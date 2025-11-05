📠 Leitor de Códigos de Barras e QR Code para NF-e
Um sistema web simples e local para escanear chaves de acesso de Notas Fiscais Eletrônicas (NF-e) de 44 dígitos, ideal para otimizar processos de entrada de notas.

✨ Funcionalidades
💻 Modo Desktop: Permite o uso de múltiplos leitores de código de barras USB conectados a um computador.

📱 Modo Mobile: Utilize a câmera do seu celular para escanear QR Codes de NF-e.

👤 Sessão por Funcionário: Inicie uma sessão com seu nome para registrar os códigos lidos em um arquivo separado.

📄 Geração de Arquivos: Cada sessão gera um arquivo .txt com a data e o nome do funcionário, contendo todas as chaves lidas.

⏱️ Cronômetro: Monitore o tempo de cada sessão de trabalho.

🌐 Acesso Local: Funciona inteiramente na sua rede local, sem necessidade de internet (apenas para o primeiro download das bibliotecas).

🚀 Tecnologias Utilizadas
Backend: Python

Framework Web: Flask

Frontend: HTML5, Tailwind CSS, JavaScript

Leitura de QR Code: html5-qrcode

🔧 Instalação e Execução
Siga os passos abaixo para colocar o sistema em funcionamento.

1. Pré-requisitos
Python 3: É necessário ter o Python instalado. Caso não tenha, baixe em python.org.

Dica: Ao instalar no Windows, marque a caixa "Add Python to PATH".

2. Instalação das Bibliotecas
Abra o seu terminal (CMD, PowerShell, Git Bash, etc.) e execute os seguintes comandos, um por um:

pip install Flask
pip install requests
pip install pyopenssl

3. Executando o Servidor
Garanta que os arquivos servidor_qr.py, index.html e desktop.html estão na mesma pasta.

No seu terminal, navegue até a pasta do projeto.

# Exemplo: se a pasta está na sua Área de Trabalho
cd Desktop/LeitorNF

Inicie o servidor com o comando:

python servidor_qr.py

O terminal irá exibir os endereços para acessar o sistema.

📱 Como Acessar o Sistema
Após iniciar o servidor, use os seguintes endereços no seu navegador:

No mesmo computador: https://127.0.0.1:5000

No celular ou outro computador na mesma rede: https://192.168.X.X:5000 (substitua pelo IP que aparece no seu terminal)

⚠️ Aviso Importante sobre HTTPS
Para que a câmera do celular funcione, o servidor usa uma conexão segura (HTTPS). Como o certificado é local, o navegador exibirá um alerta de segurança.

Isto é normal. Você deve clicar em "Avançado" e depois em "Continuar para o site (não seguro)".

📸 Telas do Sistema
(Aqui você pode adicionar screenshots do sistema em funcionamento para deixar o README mais visual)

Tela de Login

Menu Principal

Tela Mobile com Câmera

**

**

**

📄 Licença
Este projeto é distribuído sob a licença MIT.
