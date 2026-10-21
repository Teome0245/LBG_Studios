import numpy as np
from PIL import Image, ImageFilter

# 1. Charger l'image source envoyée par l'utilisateur
src_path = '/home/lbg/.gemini/antigravity-ide/brain/1165e65b-2952-49ad-8ee9-8135d868d941/.user_uploaded/media_1792609186732.png'
src_img = Image.open(src_path).convert('RGBA')
arr = np.array(src_img, dtype=np.float32)
r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]

# 2. Identifier les zones et éléments protégés
# A. Zone doigts / ongles / semelles (X: 220..805, Y: 710..1024)
is_protected_bottom = np.zeros(arr.shape[:2], dtype=bool)
is_protected_bottom[710:1024, 220:805] = True

# B. Néons cyan purs
is_neon = (g > 165) & (b > 175) & (r < 125)

# C. Combinaison de fond bleu nuit sombre (r < 45, g < 52, b < 85)
is_suit = (r < 45) & (g < 52) & (b < 85)

# D. Lignes de joints creux et connectiques noires (r < 30, g < 30, b < 40)
is_crevice = (r < 30) & (g < 30) & (b < 40)

# 3. Masque des plaques
# Hors zone protégée du bas, hors néon, hors combinaison, hors creux noirs
is_plate = (~is_protected_bottom) & (~is_neon) & (~is_suit) & (~is_crevice) & (b >= 70) & (g >= 45)

# 4. Nettoyage de la symétrie du dôme gauche sur le buste
# Le dôme droit (X: 512..780, Y: 180..340) est sain et propre.
# On utilise son miroir pour combler les zones bruitées / mouchetées du dôme gauche:
right_dome = is_plate[180:340, 512:780]
left_dome_mirrored = np.fliplr(right_dome)
is_plate[180:340, 512-left_dome_mirrored.shape[1]:512] |= left_dome_mirrored

# Protéger les rivets et les néons à l'intérieur du dôme gauche (rivets circulaires à X ~ 360 et X ~ 440)
# En réappliquant les masques néon et crevice
is_plate = is_plate & (~is_neon) & (~is_crevice)

# 5. Calcul de la carte de relief 3D (Heightmap)
# On construit une carte d'élévation continue sur chaque pièce d'armure
plate_mask_img = Image.fromarray((is_plate * 255).astype(np.uint8), mode='L')

h1 = np.array(plate_mask_img.filter(ImageFilter.GaussianBlur(radius=2)), dtype=np.float32) / 255.0
h2 = np.array(plate_mask_img.filter(ImageFilter.GaussianBlur(radius=6)), dtype=np.float32) / 255.0
h3 = np.array(plate_mask_img.filter(ImageFilter.GaussianBlur(radius=15)), dtype=np.float32) / 255.0
h4 = np.array(plate_mask_img.filter(ImageFilter.GaussianBlur(radius=30)), dtype=np.float32) / 255.0

height = (h1 * 0.35 + h2 * 0.35 + h3 * 0.20 + h4 * 0.10) * is_plate

# Dômes pectoraux sphériques galbés (centres 412, 255 et 612, 255)
y_grid, x_grid = np.ogrid[:1024, :1024]
r_dome = 82.0
d_left = np.sqrt((x_grid - 412.0)**2 + (y_grid - 255.0)**2) / r_dome
d_right = np.sqrt((x_grid - 612.0)**2 + (y_grid - 255.0)**2) / r_dome
dome_sphere_l = np.sqrt(np.maximum(0.0, 1.0 - d_left**2)) * (d_left < 1.0)
dome_sphere_r = np.sqrt(np.maximum(0.0, 1.0 - d_right**2)) * (d_right < 1.0)
height += (dome_sphere_l + dome_sphere_r) * 0.45 * is_plate

# 6. Calcul des normales de surface 3D
dy, dx = np.gradient(height * 20.0)
nz = 1.0
norm = np.sqrt(dx**2 + dy**2 + nz**2)
nx, ny, nz = -dx / norm, -dy / norm, nz / norm

# 7. Éclairage Studio Mecha Blinn-Phong (Lumière zénithale douce)
lx, ly, lz = 0.15, -0.60, 0.78
llen = np.sqrt(lx**2 + ly**2 + lz**2)
lx, ly, lz = lx/llen, ly/llen, lz/llen

# Vecteur médian Blinn-Phong
hx, hy, hz = lx, ly, lz + 1.0
hlen = np.sqrt(hx**2 + hy**2 + hz**2)
hx, hy, hz = hx/hlen, hy/hlen, hz/hlen

dot_l = np.maximum(0.0, nx*lx + ny*ly + nz*lz)
dot_h = np.maximum(0.0, nx*hx + ny*hy + nz*hz)
specular = dot_h ** 14.0
fresnel = (1.0 - nz) ** 2.0

# 8. Modèle de couleur Titane Satiné Mecha
# - Base d'acier titane mecha
# - Reflet zénithal doux
# - Highlight spéculaire chrome poli
# - Effet Fresnel doux sur les biseaux des plaques
metal_r = 54.0 + 48.0 * dot_l + 85.0 * specular + 35.0 * fresnel
metal_g = 88.0 + 68.0 * dot_l + 95.0 * specular + 50.0 * fresnel
metal_b = 138.0 + 72.0 * dot_l + 95.0 * specular + 60.0 * fresnel

metal_r = np.clip(metal_r, 0, 255)
metal_g = np.clip(metal_g, 0, 255)
metal_b = np.clip(metal_b, 0, 255)

# 9. Assemblage de l'image finale
out_arr = arr.copy()
out_arr[is_plate, 0] = metal_r[is_plate]
out_arr[is_plate, 1] = metal_g[is_plate]
out_arr[is_plate, 2] = metal_b[is_plate]

final_img = Image.fromarray(out_arr.astype(np.uint8), mode='RGBA')

# Sauvegarde des versions
final_img.save('tools/metallic_skin_clean_1024.png')
final_img.save('packages/compagnon-desktop/overlay/vrm/body_skin_android.png')
final_img.save('packages/cortex/compagnon_ui/public/vrm/body_skin_android.png')

print("Clean metallic skin successfully generated and saved!")
print(f"Total metallic plate pixels shaded: {np.count_nonzero(is_plate)}")
