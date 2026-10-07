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

# Interface HTML/CSS/JS (Embutida para facilitar)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Painel CalAmp</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f9; color: #333; }
        h2 { text-align: center; color: #2c3e50; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        input[type="text"] { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 12px; background-color: #3498db; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; font-weight: bold; }
        button:active { background-color: #2980b9; }
        
        /* O flex-wrap permite que os botões quebrem para a linha de baixo se não couberem */
        .macros { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; }
        .macros button { flex: 1 1 30%; background-color: #2ecc71; padding: 10px; }
        .macros button:active { background-color: #27ae60; }
        
        #terminal { width: 100%; height: 300px; margin-top: 20px; background: #222; color: #0f0; padding: 10px; border-radius: 4px; font-family: monospace; overflow-y: auto; white-space: pre-wrap; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📡 Rastreador CalAmp</h2>
        
        <form id="cmdForm" onsubmit="enviarComando(event)">
            <input type="text" id="comando" placeholder="Digite o comando AT..." required autocomplete="off">
            <button type="submit">Enviar Comando</button>
        </form>

        <div class="macros">
            <button onclick="enviarMacro('AT')">Teste (AT)</button>
            <button onclick="enviarMacro('AT+CSQ')">Sinal GSM</button>
            <button onclick="enviarMacro('AT+CCID')">Ler Chip</button>
            
            <!-- Novos botões CalAmp adicionados aqui -->
            <button onclick="enviarMacro('ATIC')">ATIC</button>
            <button onclick="enviarMacro('ATI0')">VERSÃO</button>
            <button onclick="enviarMacro('AT$APP PEG ACTION 62 197')">TECLA-11</button>
        </div>

        <div id="terminal">Aguardando comandos...</div>
    </div>

    <script>
        const terminal = document.getElementById('terminal');
        const inputComando = document.getElementById('comando');

        function adicionarLog(texto) {
            terminal.innerHTML += '\\n' + texto;
            terminal.scrollTop = terminal.scrollHeight;
        }

        async function enviarComando(event) {
            if(event) event.preventDefault();
            let cmd = inputComando.value.trim();
            if(!cmd) return;

            adicionarLog("> " + cmd);
            inputComando.value = '';
            
            try {
                let formData = new FormData();
                formData.append('comando', cmd);

                let resposta = await fetch('/enviar', { method: 'POST', body: formData });
                let dados = await resposta.json();
                adicionarLog(dados.resposta);
            } catch (erro) {
                adicionarLog("Erro de conexão com a Raspberry: " + erro);
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
        return jsonify({'resposta': '[ERRO] Porta serial não está aberta na Raspberry!'})
    
    cmd = request.form.get('comando', '')
    
    try:
        ser.reset_input_buffer()
        ser.write((cmd + ENTER).encode())
        time.sleep(1)
        resposta_bytes = ser.read_all()
        resposta_texto = resposta_bytes.decode(errors="replace").strip()
        
        if not resposta_texto:
            resposta_texto = "[Sem resposta do rastreador]"
            
        return jsonify({'resposta': resposta_texto})
    except Exception as e:
        return jsonify({'resposta': f'[ERRO SERIAL] {e}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
