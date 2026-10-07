from flask import Flask, request, jsonify, render_template_string
import serial
import time

app = Flask(__name__)

# Configurações da Serial
PORTA = "/dev/ttyUSB0"
BAUD = 115200
ENTER = "\r"

# Tenta iniciar a conexão serial ao rodar o servidor
try:
    ser = serial.Serial(PORTA, BAUD, timeout=1)
    print(f"Porta {PORTA} aberta com sucesso.")
except Exception as e:
    ser = None
    print(f"Erro ao abrir a porta: {e}")

# Interface HTML/CSS/JS (Estilo Digital/Gamer/Cyberpunk)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DOCKLITE - DIGITAL</title>
    <style>
        /* Reset e fundo Dark/Gamer */
        body { 
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; 
            background-color: #09090b; /* Preto profundo */
            color: #e4e4e7; 
            margin: 0; 
            padding: 20px; 
            display: flex;
            justify-content: center;
        }
        
        /* Painel Principal com efeito Glass/Neon */
        .container { 
            width: 100%; 
            max-width: 650px; 
            background: #18181b; /* Cinza escuro */
            padding: 25px; 
            border-radius: 12px; 
            border: 1px solid #27272a;
            box-shadow: 0 0 25px rgba(16, 185, 129, 0.08); 
        }
        
        /* Título com brilho */
        h2 { 
            text-align: center; 
            color: #10b981; /* Verde esmeralda */
            text-transform: uppercase; 
            letter-spacing: 3px; 
            text-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
            margin-top: 5px;
            margin-bottom: 25px;
        }

        /* Campo de texto (Input) - Estilo Console */
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
        input[type="text"]:focus {
            border-color: #10b981;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.3);
        }
        input::placeholder { color: #52525b; font-weight: normal; }
        
        /* Botão Enviar (Destaque Principal) */
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
            letter-spacing: 1px;
            transition: all 0.3s ease;
        }
        button[type="submit"]:hover { 
            box-shadow: 0 0 20px rgba(5, 150, 105, 0.6); 
            transform: translateY(-2px);
        }
        button[type="submit"]:active { transform: translateY(0); }
        
        /* Botões de Macro (Estilo Outlined Cyber) */
        .macros { 
            display: flex; 
            flex-wrap: wrap; 
            gap: 12px; 
            margin-top: 25px; 
        }
        .macros button { 
            flex: 1 1 30%; 
            background: transparent; 
            padding: 12px 10px;
            border: 1px solid #0284c7; /* Azul Cyber */
            color: #38bdf8;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            text-transform: uppercase;
            font-size: 13px;
            letter-spacing: 0.5px;
        }
        .macros button:hover { 
            background: #0284c7; 
            color: #ffffff; 
            box-shadow: 0 0 15px rgba(2, 132, 199, 0.5); 
        }
        .macros button:active { transform: scale(0.96); }
        
        /* Terminal de Respostas (Simulação de tela de hardware) */
        #terminal { 
            width: 100%; 
            height: 350px; 
            margin-top: 30px; 
            background: #050505; 
            color: #4ade80; /* Verde neon */
            padding: 15px; 
            border-radius: 6px; 
            border: 1px solid #27272a;
            font-family: 'Consolas', 'Courier New', monospace; 
            font-size: 14px;
            overflow-y: auto; 
            white-space: pre-wrap; 
            box-sizing: border-box; 
            box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
            line-height: 1.4;
        }
        
        /* Barra de rolagem customizada (Webkit) */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #18181b; border-radius: 4px; }
        ::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #10b981; }
    </style>
</head>
<body>
    <div class="container">
        <h2>⚡ DOCKLITE - DIGITAL</h2>
        
        <form id="cmdForm" onsubmit="enviarComando(event)">
            <input type="text" id="comando" placeholder="Digite o comando AT..." required autocomplete="off">
            <button type="submit">Executar Comando</button>
        </form>

        <div class="macros">
            <button onclick="enviarMacro('ATIC')">ATIC</button>
            <button onclick="enviarMacro('ATI0')">VERSÃO</button>
            <button onclick="enviarMacro('AT$APP PEG ACTION 62 197')">TECLA-11</button>
        </div>

        <div id="terminal">System Initialized. Awaiting commands...</div>
    </div>

    <script>
        const terminal = document.getElementById('terminal');
        const inputComando = document.getElementById('comando');

        // Foca automaticamente no campo de texto ao carregar
        window.onload = () => inputComando.focus();

        function adicionarLog(texto) {
            terminal.innerHTML += '\\n' + texto;
            terminal.scrollTop = terminal.scrollHeight;
        }

        async function enviarComando(event) {
            if(event) event.preventDefault();
            let cmd = inputComando.value.trim();
            if(!cmd) return;

            // Log formatado para o comando de envio
            adicionarLog("\\n<span style='color:#38bdf8'>[TX] > " + cmd + "</span>");
            inputComando.value = '';
            inputComando.focus();
            
            try {
                let formData = new FormData();
                formData.append('comando', cmd);

                let resposta = await fetch('/enviar', { method: 'POST', body: formData });
                let dados = await resposta.json();
                
                // Formata a resposta com um indicador RX (Recebimento)
                adicionarLog("<span style='color:#a1a1aa'>[RX]:</span>\\n" + dados.resposta);
            } catch (erro) {
                adicionarLog("<span style='color:#ef4444'>[ERRO SISTEMA] Falha na comunicação com Raspberry: " + erro + "</span>");
            }
        }

        function enviarMacro(cmd) {
            inputComando.value = cmd;
            enviarComando();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/enviar', methods=['POST'])
def enviar():
    if not ser or not ser.is_open:
        return jsonify({'resposta': '[FALHA DE HARDWARE] Porta serial indisponível!'})
    
    cmd = request.form.get('comando', '')
    
    try:
        ser.reset_input_buffer()
        ser.write((cmd + ENTER).encode())
        time.sleep(1)
        resposta_bytes = ser.read_all()
        resposta_texto = resposta_bytes.decode(errors="replace").strip()
        
        if not resposta_texto:
            resposta_texto = "[Timeout] Nenhuma resposta do módulo."
            
        return jsonify({'resposta': resposta_texto})
    except Exception as e:
        return jsonify({'resposta': f'[ERRO SERIAL] {e}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
