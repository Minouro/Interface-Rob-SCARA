# scara_app/kinematics.py
import math

# Constantes físicas do robô (em mm)
L1 = 228.0
L2 = 136.5

def calculate_inverse_kinematics(x, y):
    """
    Calcula os ângulos das juntas (theta1, theta2) para uma dada posição (x, y).
    Retorna (theta1, theta2) em graus.
    """
    # Equação para theta2
    try:
        cos_theta2_num = x**2 + y**2 - L1**2 - L2**2
        cos_theta2_den = 2 * L1 * L2
        cos_theta2 = cos_theta2_num / cos_theta2_den

        # Verifica se a posição é alcançável
        if not (-1 <= cos_theta2 <= 1):
            print("Posição X, Y fora de alcance.")
            return None, None

        theta2_rad = math.acos(cos_theta2)
        
        # Equação para theta1
        k1 = L1 + L2 * math.cos(theta2_rad)
        k2 = L2 * math.sin(theta2_rad)
        
        theta1_rad = math.atan2(y, x) - math.atan2(k2, k1)

        # Converte de radianos para graus
        theta1_deg = math.degrees(theta1_rad)
        theta2_deg = math.degrees(theta2_rad)

        return theta1_deg, theta2_deg

    except (ValueError, ZeroDivisionError) as e:
        print(f"Erro no cálculo de cinemática: {e}")
        return None, None