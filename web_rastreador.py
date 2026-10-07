# Importa as ferramentas necessárias do Flask para criar o servidor web
from flask import Flask, request, jsonify, render_template_string
import serial # Biblioteca para conversar com a porta USB (FTDI)
import time   # Biblioteca para lidar com pausas (esperar o rastreador responder)

# Inicializa o aplicativo web Flask
app = Flask(__name__)

# ==========================================
# CONFIGURAÇÕES DA PORTA SERIAL (HARDWARE)
# ==========================================
PORTA = "/dev/ttyUSB0"  # Caminho do cabo FTDI no Linux da Raspberry
BAUD = 115200           # Velocidade de comunicação dos CalAmps modernos
ENTER = "\r"            # Caractere de "fim de linha" que o rastreador exige

# Tenta abrir a porta serial assim que o script roda.
# Usamos try/except para que o site não quebre (crash) se o cabo estiver desconectado.
try:
    ser = serial.Serial(PORTA, BAUD, timeout=1)
    print(f"Porta {PORTA} aberta com sucesso.")
except Exception as e:
    ser = None # Se falhar, avisa que não tem porta
    print(f"Erro ao abrir a porta: {e}")

# ==========================================
# INTERFACE DO USUÁRIO (FRONTEND)
# ==========================================
# Todo o visual do site (HTML, CSS e JavaScript) está guardado nesta variável de texto.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <!-- Faz o site se adaptar perfeitamente à tela do celular -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DOCKLITE - DIGITAL</title>
    
    <!-- CSS: Controla as cores, fontes e estilo hacker/gamer -->
    <style>
        /* Fundo da página (Preto profundo) */
        body { 
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
            background-color: #09090b; 
            color: #e4e4e7; 
            margin: 0; 
            padding: 20px; 
            display: flex;
            justify-content: center;
        }
        
        /* A caixa central do aplicativo */
        .container { 
            width: 100%; 
            max-width: 650px; 
            background: #18181b; /* Cinza bem escuro */
            padding: 25px; 
            border-radius: 12px; 
            border: 1px solid #27272a;
            box-shadow: 0 0 25px rgba(16, 185, 129, 0.08); /* Brilho verde de fundo */
        }
        
        /* Estilo do título principal */
        h2 { 
            text-align: center; 
            color: #10b981; 
            text-transform: uppercase; 
            letter-spacing: 3px; 
            text-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
            margin-top: 5px;
            margin-bottom: 25px;
        }

        /* Estilo da barra onde você digita o comando */
        input[type="text"] { 
            width: 100%; 
            padding: 15px; 
            background: #000000; 
            border: 1px solid #3f3f46; 
            border-radius: 6px; 
            box-sizing: border-box; 
            font-size: 16px; 
            color: #10b981; 
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            outline: none; 
            transition: all 0.3s ease;
        }
        /* Efeito quando clica na barra de digitar (Glow) */
        input[type="text"]:focus {
            border-color: #10b981;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.3);
        }
        
        /* Botão principal de Executar */
        button[type="submit"] { 
            width: 100%; 
            padding: 15px; 
            margin-top: 15px;
            background: linear-gradient(90deg, #047857, #059669); 
            color: #ffffff; 
            border: none; 
            border-radius: 6px; 
            font-size: 16px; 
            cursor: pointer; 
            font-weight: bold; 
            text-transform: uppercase; 
        }
        
        /* Botões rápidos (Macros CalAmp) */
        .macros { 
            display: flex; 
            flex-wrap: wrap; /* Permite quebrar linha se não couber na tela */
            gap: 12px; 
            margin-top: 25px; 
        }
        .macros button { 
            flex: 1 1 30%; 
            background: transparent; 
            padding: 12px 10px;
            border: 1px solid #0284c7; 
            color: #38bdf8;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
        }
        /* Efeito de passar o mouse nos botões macros */
        .macros button:hover { 
            background: #0284c7; 
            color: #ffffff; 
            box-shadow: 0 0 15px rgba(2, 132, 199, 0.5); 
        }
        
        /* Tela preta de respostas (Terminal Virtual) */
        #terminal { 
            width: 100%; 
            height: 350px; 
            margin-top: 30px; 
            background: #050505; 
            color: #4ade80; /* Letra verde neon */
            padding: 15px; 
            border-radius: 6px; 
            border: 1px solid #27272a;
            font-family: 'Consolas', 'Courier New', monospace; 
            font-size: 14px;
            overflow-y: auto; /* Cria a barra de rolagem se o texto for longo */
            white-space: pre-wrap; /* Mantém as quebras de linha enviadas pelo CalAmp */
            box-sizing: border-box; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>⚡ DOCKLITE - DIGITAL</h2>
        
        <!-- Formulário de envio -->
        <form id="cmdForm" onsubmit="enviarComando(event)">
            <input type="text" id="comando" placeholder="Digite o comando AT..." required autocomplete="off">
            <button type="submit">Executar Comando</button>
        </form>

        <!-- Botões de Macros -->
        <div class="macros">
            <button onclick="enviarMacro('ATIC')">ATIC</button>
            <button onclick="enviarMacro('ATI0')">VERSÃO</button>
            <button onclick="enviarMacro('AT$APP PEG ACTION 62 197')">TECLA-11</button>
        </div>

        <!-- Onde o texto de log vai aparecer -->
        <div id="terminal">System Initialized. Awaiting commands...</div>
    </div>

    <!-- JAVASCRIPT: Controla a lógica da página sem precisar recarregar -->
    <script>
        const terminal = document.getElementById('terminal');
        const inputComando = document.getElementById('comando');

        // Já deixa o teclado/cursor pronto no campo ao abrir o site
        window.onload = () => inputComando.focus();

        // Função para escrever linhas na tela preta
        function adicionarLog(texto) {
            terminal.innerHTML += '\\n' + texto;
            terminal.scrollTop = terminal.scrollHeight; // Rola a barra sempre para o final
        }

        // Função principal que envia o comando para o Python
        async function enviarComando(event) {
            if(event) event.preventDefault(); // Impede o site de recarregar a página
            
            let cmd = inputComando.value.trim();
            if(!cmd) return; // Se estiver vazio, não faz nada

            // Pinta o comando que VOCÊ enviou de azul [TX]
            adicionarLog("\\n<span style='color:#38bdf8'>[TX] > " + cmd + "</span>");
            inputComando.value = ''; // Limpa a barra
            inputComando.focus();    // Devolve o cursor para a barra
            
            try {
                // Prepara o pacote de dados para enviar ao servidor Python
                let formData = new FormData();
                formData.append('comando', cmd);

                // Faz um requisição invisível para a rota '/enviar' do Flask
                let resposta = await fetch('/enviar', { method: 'POST', body: formData });
                let dados = await resposta.json();
                
                // Exibe a resposta do rastreador pintada de cinza/verde [RX]
                adicionarLog("<span style='color:#a1a1aa'>[RX]:</span>\\n" + dados.resposta);
            } catch (erro) {
                // Se der erro no Wi-Fi ou a placa desligar
                adicionarLog("<span style='color:#ef4444'>[ERRO SISTEMA] Falha na comunicação com Raspberry: " + erro + "</span>");
            }
        }

        // Função que é acionada pelos botões rápidos
        function enviarMacro(cmd) {
            inputComando.value = cmd; // Preenche a barra de digitar com o botão clicado
            enviarComando();          // Aperta "enter" virtualmente
        }
    </script>
</body>
</html>
"""

# ==========================================
# ROTAS DO SERVIDOR WEB (FLASK)
# ==========================================

# ROTA 1: Quando alguém acessar apenas o IP (ex: 192.168.0.10:5000)
@app.route('/')
def index():
    # Ele devolve todo aquele HTML/CSS que escrevemos acima
    return render_template_string(HTML_TEMPLATE)

# ROTA 2: A rota invisível que o JavaScript acessa para mandar os comandos
@app.route('/enviar', methods=['POST'])
def enviar():
    # Verifica se o cabo FTDI está realmente conectado e aberto
    if not ser or not ser.is_open:
        return jsonify({'resposta': '[FALHA DE HARDWARE] Porta serial indisponível!'})
    
    # Pega o texto que o JavaScript mandou
    cmd = request.form.get('comando', '')
    
    try:
        ser.reset_input_buffer()               # Limpa sujeiras antigas da porta
        ser.write((cmd + ENTER).encode())      # Transforma Texto em Bytes e envia pro CalAmp
        time.sleep(1)                          # Dorme 1 segundo pro rastreador processar
        resposta_bytes = ser.read_all()        # Puxa todos os bytes que o rastreador devolveu
        
        # Transforma os Bytes de volta em Texto. 
        # errors="replace" impede falhas se houver ruído elétrico.
        resposta_texto = resposta_bytes.decode(errors="replace").strip()
        
        if not resposta_texto:
            resposta_texto = "[Timeout] Nenhuma resposta do módulo."
            
        # Devolve a resposta para o navegador do celular em formato JSON
        return jsonify({'resposta': resposta_texto})
    except Exception as e:
        return jsonify({'resposta': f'[ERRO SERIAL] {e}'})

# ==========================================
# INICIADOR DO SERVIDOR
# ==========================================
if __name__ == '__main__':
    # host='0.0.0.0' é o truque mágico que permite que o site seja acessado 
    # por qualquer celular conectado no mesmo roteador Wi-Fi da Raspberry Pi.
    app.run(host='0.0.0.0', port=5000)
