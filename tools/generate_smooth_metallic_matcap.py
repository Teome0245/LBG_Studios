import numpy as np
from PIL import Image, ImageFilter

size = 512
cx, cy = size / 2.0, size / 2.0
radius = size / 2.0

y, x = np.ogrid[:size, :size]
dx = (x - cx) / radius
dy = (y - cy) / radius
r2 = dx**2 + dy**2
mask = r2 <= 1.0

# Normale 3D de la sphère
dz = np.sqrt(np.maximum(0.0, 1.0 - r2))

# 1. Source lumineuse principale (légèrement en haut à droite, lumière studio douce)
lx, ly, lz = 0.25, -0.45, 0.85
llen = np.sqrt(lx**2 + ly**2 + lz**2)
lx, ly, lz = lx/llen, ly/llen, lz/llen

# Éclairage spéculaire Blinn-Phong doux et large
dot_l = np.maximum(0.0, dx*lx + (-dy)*ly + dz*lz)
specular = dot_l ** 12.0 # Point spéculaire soyeux

# 2. Lumière secondaire de remplissage (ambiance mecha bleue)
lx2, ly2, lz2 = -0.35, 0.35, 0.87
dot_l2 = np.maximum(0.0, dx*lx2 + (-dy)*ly2 + dz*lz2)
specular2 = dot_l2 ** 18.0

# 3. Rim / Fresnel métallique (très fort sur les bords sphériques)
fresnel = (1.0 - dz) ** 1.8

# 4. Dégradé de chrome continu et soyeux (pas de coupure brutale, pas de ligne d'horizon tranchante)
# Dégradé vertical zénithal doux
vert_grad = 0.5 + 0.5 * (-dy)

# Base titane métallisé
# R, G, B
base_r = 75 + 45 * vert_grad + 80 * fresnel + 90 * specular + 40 * specular2
base_g = 105 + 65 * vert_grad + 110 * fresnel + 120 * specular + 60 * specular2
base_b = 155 + 85 * vert_grad + 130 * fresnel + 130 * specular + 90 * specular2

img_arr = np.zeros((size, size, 4), dtype=np.uint8)
img_arr[:, :, 0] = np.clip(base_r * mask, 0, 255).astype(np.uint8)
img_arr[:, :, 1] = np.clip(base_g * mask, 0, 255).astype(np.uint8)
img_arr[:, :, 2] = np.clip(base_b * mask, 0, 255).astype(np.uint8)
img_arr[:, :, 3] = (mask * 255).astype(np.uint8)

matcap_img = Image.fromarray(img_arr, mode='RGBA')
# Antialiasing du cercle extérieur
matcap_img = matcap_img.filter(ImageFilter.SMOOTH)

out_desktop = 'packages/compagnon-desktop/overlay/vrm/metallic_matcap.png'
out_cortex = 'packages/cortex/compagnon_ui/public/vrm/metallic_matcap.png'
matcap_img.save(out_desktop)
matcap_img.save(out_cortex)
matcap_img.save('tools/metallic_matcap_smooth_preview.png')

print("Smooth metallic matcap generated successfully without any harsh stripes!")
