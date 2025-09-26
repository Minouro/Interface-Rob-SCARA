# run.py (Versão Final com QR Code usando o IP para máxima compatibilidade)

import os
import socket
import qrcode
import sys
import subprocess
import threading
from zeroconf import ServiceInfo, Zeroconf

def find_local_ip():
    """Encontra o endereço IP local da máquina de forma confiável."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except (socket.error, IndexError):
        print("ERRO: Não foi possível encontrar o IP local. Verifique sua conexão de rede.")
        return None
    finally:
        s.close()
    return ip

def register_service(zeroconf, info):
    """Registra o serviço 'meu-robo.local' na rede."""
    print("Anunciando serviço 'meu-robo.local.' na rede...")
    zeroconf.register_service(info)

def run_server():
    """
    Inicia o servidor ASGI (Daphne) de forma robusta e anuncia o serviço mDNS.
    """
    local_ip = find_local_ip()
    if not local_ip:
        sys.exit(1)

    port = 8000
    hostname = "meu-robo.local"
    full_url_by_name = f"http://{hostname}:{port}"
    full_url_by_ip = f"http://{local_ip}:{port}" # Cria a URL com o IP

    # --- Configuração do Zeroconf/mDNS ---
    service_type = "_http._tcp.local."
    service_name = f"SCARA Robot Interface.{service_type}"
    info = ServiceInfo(
        service_type, service_name,
        addresses=[socket.inet_aton(local_ip)],
        port=port, server=f"{hostname}.",
    )
    zeroconf = Zeroconf()
    daemon_thread = threading.Thread(target=register_service, args=(zeroconf, info), daemon=True)
    daemon_thread.start()
    
    # --- Exibição das Instruções e do QR Code ---
    print("="*60)
    print("🎉 SERVIDOR PRONTO PARA ACESSO MÓVEL 🎉")
    print(f"   Acesse pelo nome: {full_url_by_name}")
    print(f"   Ou pelo IP:     {full_url_by_ip}")
    print("="*60)
    print("\nUse a câmera do seu tablet/celular para escanear o QR Code abaixo:")
    
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
    # **MUDANÇA AQUI: O QR Code agora usa a URL com o endereço de IP**
    qr.add_data(full_url_by_ip)
    qr.print_tty()
    
    print(f"\nIniciando servidor Daphne...")
    print("Aguardando conexões... Pressione CTRL+C para parar o servidor.")

    try:
        # Configura a variável de ambiente para o ALLOWED_HOSTS do Django
        allowed_hosts_list = f"{local_ip},127.0.0.1,{hostname}"
        os.environ['DJANGO_ALLOWED_HOSTS'] = allowed_hosts_list
        
        # Comando para iniciar o servidor Daphne de forma robusta.
        command = [
            sys.executable, "-m", "daphne",
            "-b", "0.0.0.0",
            "-p", str(port),
            "scara_project.asgi:application"
        ]
        
        # Inicia o processo e espera ele terminar (o que só acontece com Ctrl+C).
        subprocess.run(command, check=True)

    except KeyboardInterrupt:
        print("\nComando de parada recebido (Ctrl+C). Encerrando...")
    except Exception as e:
        print(f"\nERRO AO INICIAR O SERVIDOR: {e}")
    finally:
        print("Parando o anúncio de rede...")
        zeroconf.unregister_service(info)
        zeroconf.close()
        print("Serviço 'meu-robo.local.' removido da rede. Até logo!")

if __name__ == "__main__":
    run_server()
