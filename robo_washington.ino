/*
  SCARA Robot - Firmware com Comandos Separados
  - CORREÇÃO: A lógica de comunicação foi refeita para separar os comandos de
    movimento dos eixos (J1, J2, Phi, Z) dos comandos da garra.
  - Movimentar os eixos pela interface NÃO envia mais comandos para o servo.
  - A garra só se move quando o seu controle específico é acionado.
  - A funcionalidade de playback (sequenciador) continua operando com o estado completo.
*/
#include <AccelStepper.h>
#include <Servo.h>

// --- Definições de Pinos e Motores ---
#define limitSwitch1 11
#define limitSwitch2 10
#define limitSwitch3 9
#define limitSwitch4 A3
#define ENABLE_PIN 8

AccelStepper stepper3(1, 2, 5);   // Rotação da Garra (phi)
AccelStepper stepper1(1, 4, 7);   // Junta 1 (theta1) <- USA PINOS 4, 7
AccelStepper stepper2(1, 3, 6);   // Junta 2 (theta2) <- USA PINOS 3, 6
AccelStepper stepper4(1, 12, 13); // Eixo Z
Servo gripperServo;

// --- Factores de Conversão ---
const float theta1AngleToSteps = 35.555555;
const float theta2AngleToSteps = 22.222222;
const float phiAngleToSteps = 35;
const float zDistanceToSteps = 100;

long last_report_time = 0;
float g_val_last = 0;

// Função para processar o comando completo (eixos + garra), usada pelo sequenciador.
void parseFullCommand(String cmd) {
    int initialIndex = 0;
    int separatorIndex = 0;
    float values[5];
    
    for (int i = 0; i < 5; i++) {
        separatorIndex = cmd.indexOf(',', initialIndex);
        if (separatorIndex == -1) {
            separatorIndex = cmd.length();
        }
        String part = cmd.substring(initialIndex, separatorIndex);
        values[i] = part.toFloat();
        initialIndex = separatorIndex + 1;
    }
    
    float t1_val = values[0];
    float t2_val = values[1];
    float p_val = values[2];
    float z_val = values[3];
    float g_val = values[4];

    // Move todos os eixos
    stepper1.moveTo(t1_val * theta1AngleToSteps);
    stepper2.moveTo(t2_val * theta2AngleToSteps);
    stepper3.moveTo(p_val * phiAngleToSteps);
    stepper4.moveTo(z_val * zDistanceToSteps);
    
    // E também a garra
    g_val_last = g_val;
    gripperServo.attach(A0, 500, 2500);
    gripperServo.write(g_val);
    delay(500);
    gripperServo.detach();
}

// NOVA FUNÇÃO: Processa comandos de movimento apenas para os 4 eixos principais.
void parseStepperCommand(String cmd) {
    int initialIndex = 0;
    int separatorIndex = 0;
    float values[4]; // Apenas 4 valores
    
    for (int i = 0; i < 4; i++) {
        separatorIndex = cmd.indexOf(',', initialIndex);
        if (separatorIndex == -1) {
            separatorIndex = cmd.length();
        }
        String part = cmd.substring(initialIndex, separatorIndex);
        values[i] = part.toFloat();
        initialIndex = separatorIndex + 1;
    }
    
    float t1_val = values[0];
    float t2_val = values[1];
    float p_val = values[2];
    float z_val = values[3];

    // Move apenas os steppers
    stepper1.moveTo(t1_val * theta1AngleToSteps);
    stepper2.moveTo(t2_val * theta2AngleToSteps);
    stepper3.moveTo(p_val * phiAngleToSteps);
    stepper4.moveTo(z_val * zDistanceToSteps);
}

// NOVA FUNÇÃO: Processa comandos exclusivos para a garra.
void parseGripperCommand(String cmd) {
    float g_val = cmd.toFloat();

    g_val_last = g_val; // Atualiza o estado para o relatório de posição
    gripperServo.attach(A0, 500, 2500);
    gripperServo.write(g_val);
    delay(500);
    gripperServo.detach();
}


void setup() {
  pinMode(A0, OUTPUT);
  digitalWrite(A0, LOW);

  Serial.begin(115200);
  while (!Serial) { ; }
  delay(1000);

  Serial.println("status:Arduino a inicializar...");

  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);

  pinMode(limitSwitch1, INPUT_PULLUP);
  pinMode(limitSwitch2, INPUT_PULLUP);
  pinMode(limitSwitch3, INPUT_PULLUP);
  pinMode(limitSwitch4, INPUT_PULLUP);

  stepper1.setMaxSpeed(4000); stepper1.setAcceleration(2000);
  stepper2.setMaxSpeed(4000); stepper2.setAcceleration(2000);
  stepper3.setMaxSpeed(4000); stepper3.setAcceleration(2000);
  stepper4.setMaxSpeed(4000); stepper4.setAcceleration(2000);

  stepper2.setPinsInverted(true, false, false);

  homing();

  Serial.println("status:Arduino pronto para receber comandos!");
}

void loop() {
  stepper1.run();
  stepper2.run();
  stepper3.run();
  stepper4.run();

  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.length() > 0) {
      // Lógica para direcionar o comando para a função correta
      if (command.startsWith("S")) {
          command.remove(0, 1); // Remove o prefixo 'S'
          parseStepperCommand(command);
      } else if (command.startsWith("G")) {
          command.remove(0, 1); // Remove o prefixo 'G'
          parseGripperCommand(command);
      } else if (command.indexOf(',') != -1) {
          // Se não tem prefixo mas tem vírgula, é um comando completo (do sequenciador)
          parseFullCommand(command);
      }
    }
  }

  bool isMoving = stepper1.distanceToGo() != 0 || stepper2.distanceToGo() != 0 || stepper3.distanceToGo() != 0 || stepper4.distanceToGo() != 0;
  if (!isMoving && (millis() - last_report_time > 100)) {
    float current_t1 = stepper1.currentPosition() / theta1AngleToSteps;
    float current_t2 = stepper2.currentPosition() / theta2AngleToSteps;
    float current_phi = stepper3.currentPosition() / phiAngleToSteps;
    float current_z = stepper4.currentPosition() / zDistanceToSteps;

    Serial.print("pos:");
    Serial.print(current_t1);  Serial.print(",");
    Serial.print(current_t2);  Serial.print(",");
    Serial.print(current_phi); Serial.print(",");
    Serial.print(current_z);   Serial.print(",");
    Serial.print(g_val_last);
    Serial.print("\n");
    last_report_time = millis();
  }
}

void homing() {
  Serial.println("status:Iniciando Homing...");
  digitalWrite(ENABLE_PIN, LOW);

  Serial.println("status:Homing Eixo Z...");
  stepper4.setMaxSpeed(2000); stepper4.setAcceleration(1000);
  while (digitalRead(limitSwitch4) == LOW) { stepper4.setSpeed(-1500); stepper4.runSpeed(); }
  stepper4.setCurrentPosition(0);
  stepper4.setSpeed(0);
  Serial.println("status:Homing Eixo Z... OK");

  Serial.println("status:Homing Rotação (Phi)...");
  stepper3.setMaxSpeed(2000); stepper3.setAcceleration(1000);
  while (digitalRead(limitSwitch3) == LOW) { stepper3.setSpeed(-1100); stepper3.runSpeed(); }
  stepper3.setCurrentPosition(0);
  stepper3.setSpeed(0);
  Serial.println("status:Homing Rotação (Phi)... OK");

  Serial.println("status:Homing Junta 2...");
  stepper2.setMaxSpeed(2000); stepper2.setAcceleration(1000);
  while (digitalRead(limitSwitch2) == LOW) { stepper2.setSpeed(-1200); stepper2.runSpeed(); }
  stepper2.setCurrentPosition(0);
  stepper2.setSpeed(0);
  Serial.println("status:Homing Junta 2... OK");

  Serial.println("status:Homing Junta 1...");
  stepper1.setMaxSpeed(2000); stepper1.setAcceleration(1000);
  while (digitalRead(limitSwitch1) == LOW) { stepper1.setSpeed(-1300); stepper1.runSpeed(); }
  stepper1.setCurrentPosition(0);
  stepper1.setSpeed(0);
  Serial.println("status:Homing Junta 1... OK");

  Serial.println("status:Homing completo!");
}