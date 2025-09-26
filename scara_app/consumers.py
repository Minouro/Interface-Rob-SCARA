import json
import asyncio
import serial
import serial.tools.list_ports
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)
ser = None
active_clients = set()

def find_arduino_port():
    """Escaneia as portas seriais e tenta encontrar o Arduino."""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Arduino" in port.description or "CH340" in port.description:
            logger.info(f"[Conexão] Arduino encontrado na porta: {port.device}")
            return port.device
    return None

async def broadcast_status(status, message):
    """Envia uma mensagem de status para todas as interfaces web conectadas."""
    if not active_clients: return
    logger.info(f"[Broadcast] Enviando status: {status} - {message}")
    event = {'type': 'connection_status', 'status': status, 'message': message}
    await asyncio.gather(*[client.send(text_data=json.dumps(event)) for client in active_clients])

async def manage_arduino_connection():
    """Tarefa em segundo plano que gerencia a conexão com o Arduino."""
    global ser
    logger.info("[Conexão] Tarefa de gerenciamento com Arduino iniciada.")
    while True:
        try:
            if ser is None or not ser.is_open:
                await broadcast_status('connecting', "Procurando Arduino...")
                arduino_port = find_arduino_port()
                if arduino_port:
                    await broadcast_status('connecting', f"Conectando em {arduino_port}...")
                    ser = serial.Serial(arduino_port, 115200, timeout=1)
                    await asyncio.sleep(2)
                    ser.reset_input_buffer()
                else:
                    await broadcast_status('disconnected', "⚠️ Arduino não encontrado. Verifique o cabo USB.")
            else:
                _ = ser.in_waiting
        except serial.SerialException as e:
            if ser: ser.close()
            ser = None
            logger.error(f"[Conexão] Erro na porta serial: {e}")
            await broadcast_status('disconnected', f"⚠️ Erro de conexão: {e}")
        except Exception as e:
            logger.error(f"[Conexão] Erro inesperado no gerenciador: {e}")
        await asyncio.sleep(3)

class RobotConsumer(AsyncWebsocketConsumer):
    connection_manager_task = None

    async def connect(self):
        logger.info("[WebSocket] Novo navegador conectado.")
        await self.accept()
        active_clients.add(self)
        if RobotConsumer.connection_manager_task is None:
            RobotConsumer.connection_manager_task = asyncio.create_task(manage_arduino_connection())
        asyncio.create_task(self.read_from_arduino())

    async def disconnect(self, close_code):
        logger.info("[WebSocket] Navegador desconectado.")
        active_clients.remove(self)

    # ======================= INÍCIO DA CORREÇÃO =======================
    async def receive(self, text_data):
        """
        Recebe a string de comando diretamente da interface e a envia para o Arduino.
        A variável 'text_data' já está no formato "t1,t2,p,z,g".
        Não é mais necessário analisar JSON para esta operação.
        """
        command = text_data + "\n" # Apenas adicionamos a quebra de linha final

        if ser and ser.is_open:
            try:
                ser.write(command.encode())
                logger.info(f"[Comando] --> Enviado para Arduino: {command.strip()}")
            except serial.SerialException:
                logger.warning("Falha ao enviar comando para o Arduino.")
    # ======================= FIM DA CORREÇÃO ==========================

    async def read_from_arduino(self):
        while self in active_clients:
            if ser and ser.is_open:
                try:
                    if ser.in_waiting > 0:
                        line = ser.readline().decode('utf-8').strip()
                        if not line: continue

                        if line.startswith("ack:"):
                            logger.info(f"[Comando] <-- Arduino confirmou recebimento: {line}")
                        elif line.startswith("pos:"):
                            await self.send(text_data=json.dumps({'type': 'robot_status', 'data': line}))
                        elif line.startswith("status:"):
                            message = line.replace("status:", "").strip()
                            logger.info(f"[Arduino Status] <-- {message}")
                            if "pronto" in message.lower():
                                await broadcast_status('connected', f"✅ {message}")
                            else:
                                await broadcast_status('connecting', f"Arduino: {message}")
                except (serial.SerialException, OSError):
                    await asyncio.sleep(1)
            await asyncio.sleep(0.05)
