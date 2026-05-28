import cv2
import os
import numpy as np

# Création du dossier de test
os.makedirs("test_couleurs", exist_ok=True)

# 1. Capture depuis la webcam (0 est l'index de la caméra par défaut)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Erreur : Impossible d'accéder à la caméra.")
    exit()

print("Capture d'une frame dans 2 secondes... Mets-toi devant la caméra ! ")
cv2.waitKey(2000) 

ret, frame_brute = cap.read()
cap.release()

if not ret:
    print("Erreur de capture.")
    exit()

# ------------------------------------------------------------------
# ÉTAPE 1 : Test du flux natif de ta caméra
# ------------------------------------------------------------------
# OpenCV lit nativement en BGR. Si cette image est NORMALE, la caméra sort du BGR.
cv2.imwrite("test_couleurs/1_camera_brute_bgr.png", frame_brute)

# ------------------------------------------------------------------
# ÉTAPE 2 : Simulation de la conversion RGB pour l'IA
# ------------------------------------------------------------------
frame_rgb = cv2.cvtColor(frame_brute, cv2.COLOR_BGR2RGB)

# On l'enregistre brute sans re-conversion. 
# Si elle est BLEUE à l'écran, c'est la preuve que cette variable est bien en RGB !
cv2.imwrite("test_couleurs/2_simulation_variable_rgb.png", frame_rgb)

# ------------------------------------------------------------------
# ÉTAPE 3 : Ce que tu envoies à ton affichage final
# ------------------------------------------------------------------
# C'est ce que tu fais à la fin de ton '_ai_loop' avec le cv2.imencode
# Si cette image a des couleurs NORMALES, ton affichage attend du BGR.
_, buf = cv2.imencode('.jpg', frame_brute)
with open("test_couleurs/3_rendu_final_bgr.jpg", "wb") as f:
    f.write(buf.tobytes())

print("\n--- Diagnostic terminé ! ---")
print("Ouvre le dossier 'test_couleurs' et regarde les images :")
print("1. Si '1_camera_brute_bgr.png' est normale : Ta caméra et tes fonctions de détection reçoivent du BGR.")
print("2. Si '2_simulation_variable_rgb.png' est BLEUE : C'est le format PARFAIT à envoyer à ArcFace.")


